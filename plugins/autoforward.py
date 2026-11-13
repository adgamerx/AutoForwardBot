# Developed by ADx
"""Auto forward watcher.

Every active rule keeps a background task that polls its source channel and
forwards messages newer than the last id it already handled. Polling (instead
of relying on channel_post updates) means it works the same for bots and
userbots, for public channels the account is not admin in, and after restarts.
"""
import asyncio
import logging
import time
from html import escape

from config import Config
from database import db
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton,
                            ReplyKeyboardMarkup, ReplyKeyboardRemove)
from translation import Translation
from .filters import custom_caption, should_forward_message
from .test import CLIENT, start_clone_bot, parse_buttons
from .utils import parse_chat_link, parse_forwarded_post

CLIENT = CLIENT()

logger = logging.getLogger(__name__)


def _int(value, default, minimum=1):
    try:
        return max(minimum, int(value))
    except (TypeError, ValueError):
        return default


def filter_options(configs):
    """Translate a user's /settings into the keyword arguments of
    should_forward_message()."""
    extensions = [str(x).lower().lstrip('.') for x in (configs.get('extension') or []) if str(x).strip()]
    keywords = [str(x).lower() for x in (configs.get('keywords') or []) if str(x).strip()]
    media_size = None
    if configs.get('file_size'):
        media_size = [configs.get('file_size'), configs.get('size_limit')]
    return {'keywords': keywords, 'extensions': extensions, 'media_size': media_size}


def is_missing(message):
    """Telegram returns empty messages for ids that do not exist."""
    return message is None or getattr(message, 'empty', False)


def is_skippable(message):
    """Missing and service messages cannot be forwarded."""
    return is_missing(message) or getattr(message, 'service', False)


class AutoForwarder:
    """Owns one polling task per active rule."""

    def __init__(self):
        self.tasks = {}
        self.bot = None
        self.interval = _int(Config.AUTOFORWARD_INTERVAL, 30, minimum=10)
        self.batch = min(_int(Config.AUTOFORWARD_BATCH, 100), 200)
        # Everything that piled up while the bot was down is drained over a few
        # cycles instead of one very long burst towards the target channel.
        self.max_per_cycle = max(self.batch, _int(getattr(Config, 'AUTOFORWARD_MAX_PER_CYCLE', 300), 300))

    # ------------------------------------------------------------------ #
    # Task control
    # ------------------------------------------------------------------ #
    def is_running(self, af_id):
        task = self.tasks.get(int(af_id))
        return task is not None and not task.done()

    def start(self, rule):
        af_id = int(rule['id'])
        if self.is_running(af_id) or rule.get('status') != 'active':
            return False
        self.tasks[af_id] = asyncio.create_task(self._run(rule))
        return True

    def stop(self, af_id):
        task = self.tasks.pop(int(af_id), None)
        if task and not task.done():
            task.cancel()
        return bool(task)

    async def stop_all(self):
        for task in list(self.tasks.values()):
            if not task.done():
                task.cancel()
        self.tasks.clear()

    # ------------------------------------------------------------------ #
    # Worker
    # ------------------------------------------------------------------ #
    async def _run(self, rule):
        af_id = int(rule['id'])
        client = None
        try:
            client = await self._start_client(rule)
            if client is None:
                return
            await self._loop(rule, client)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("auto forward %s stopped unexpectedly", af_id)
            await db.update_autoforward(af_id, {
                'status': 'error',
                'last_error': str(exc)[:400],
                'last_run': time.time(),
            })
            await self.notify(rule['user_id'],
                              f"⚠️ <b>Auto forward #{af_id} stopped.</b>\n\n<code>{str(exc)[:400]}</code>\n\nOpen /autoforward to fix it and resume.")
        finally:
            # A paused-and-resumed rule may already have a newer task stored,
            # so only drop the entry that belongs to this worker.
            if self.tasks.get(af_id) is asyncio.current_task():
                self.tasks.pop(af_id, None)
            if client is not None:
                try:
                    await client.stop()
                except Exception:
                    pass

    async def notify(self, user_id, text):
        """Tell the owner that a rule needs attention (best effort)."""
        if self.bot is None:
            return
        try:
            await self.bot.send_message(int(user_id), text, disable_web_page_preview=True)
        except Exception:
            logger.warning("could not notify %s about an auto forward problem", user_id)

    async def _start_client(self, rule):
        user_id = int(rule['user_id'])
        account_id = rule.get('account_id')
        account = await db.get_bot_by_id(user_id, int(account_id)) if account_id else await db.get_bot(user_id)
        if not account:
            await db.update_autoforward(rule['id'], {
                'status': 'error',
                'last_error': 'Account not found. Add the bot/userbot again in /settings.',
            })
            await self.notify(user_id, f"⚠️ <b>Auto forward #{rule['id']} stopped.</b>\n\nThe bot/userbot it was using is no longer added. Add it again in /settings and resume the rule.")
            return None
        try:
            return await start_clone_bot(CLIENT.client(account, name=f"AUTOFWD_{rule['id']}"))
        except Exception as exc:
            logger.exception("unable to start account for auto forward %s", rule['id'])
            await db.update_autoforward(rule['id'], {
                'status': 'error',
                'last_error': f'Unable to start account: {exc}'[:400],
            })
            await self.notify(user_id, f"⚠️ <b>Auto forward #{rule['id']} could not start.</b>\n\n<code>{str(exc)[:400]}</code>")
            return None

    async def _prepare(self, rule, client):
        """Seed last_id for a new rule and open its one-time backfill window."""
        pending = max(0, int(rule.get('backfill') or 0))
        last_id = int(rule.get('last_id') or 0)
        state = {}
        if not last_id:
            try:
                last_id = await self._latest_id(client, rule['from_chat'])
            except Exception as exc:
                raise RuntimeError(
                    'Could not read the source channel history. Add the account as an admin there, '
                    'or create the rule from a message link / forwarded post so the start point is known.'
                ) from exc
            if last_id:
                state['last_id'] = last_id
        if pending and last_id and not rule.get('backfill_start'):
            state['backfill_start'] = max(1, last_id - pending + 1)
        if not state:
            return rule
        await db.update_autoforward(rule['id'], state)
        prepared = dict(rule)
        prepared.update(state)
        return prepared

    async def _loop(self, rule, client):
        af_id = int(rule['id'])
        # A rule always starts from the newest post, never from full history.
        rule = await self._prepare(rule, client)
        await self._run_backfill(rule, client)

        while True:
            rule = await db.get_autoforward(af_id)
            if not rule or rule.get('status') != 'active':
                return
            try:
                await self._poll_once(rule, client)
            except asyncio.CancelledError:
                raise
            except FloodWait as exc:
                await asyncio.sleep(exc.value)
            except Exception as exc:
                logger.exception("auto forward %s poll failed", af_id)
                await db.update_autoforward(af_id, {
                    'last_error': str(exc)[:400],
                    'last_run': time.time(),
                })
            await asyncio.sleep(self.interval)

    async def _run_backfill(self, rule, client):
        """Forward the "latest N" window captured when the rule was created."""
        start = int(rule.get('backfill_start') or 0)
        end = int(rule.get('last_id') or 0)
        if not start or end < start:
            if start or rule.get('backfill'):
                await db.update_autoforward(rule['id'], {'backfill_start': None, 'backfill': 0})
            return
        await self._forward_range(rule, client, start, end)
        # Clearing both fields keeps a restart from replaying the window.
        await db.update_autoforward(rule['id'], {'backfill_start': None, 'backfill': 0})

    async def _poll_once(self, rule, client):
        last_id = int(rule.get('last_id') or 0)
        try:
            latest = await self._latest_id(client, rule['from_chat'])
        except Exception:
            # History can be unreadable (public source where the account is not
            # an admin). Probe the next message ids directly instead.
            latest = 0

        if latest:
            if latest <= last_id:
                await db.update_autoforward(rule['id'], {'last_run': time.time()})
                return
            end = min(latest, last_id + self.max_per_cycle)
        else:
            if not await self._message_exists(client, rule['from_chat'], last_id + 1):
                await db.update_autoforward(rule['id'], {'last_run': time.time()})
                return
            end = last_id + self.batch

        await self._forward_range(rule, client, last_id + 1, end)

    async def _forward_range(self, rule, client, start, end):
        configs = await db.get_configs(int(rule['user_id']))
        disabled = set(await db.get_filters(int(rule['user_id'])))
        options = filter_options(configs)
        button = parse_buttons(configs['button']) if configs.get('button') else None
        totals = {'forwarded': 0, 'filtered': 0, 'failed': 0}
        last_seen = 0

        for batch_start in range(start, end + 1, self.batch):
            batch_end = min(batch_start + self.batch - 1, end)
            messages = await self._get_messages(client, rule['from_chat'], list(range(batch_start, batch_end + 1)))
            counters = {'forwarded': 0, 'filtered': 0, 'failed': 0}

            for message in messages:
                if is_missing(message):
                    continue
                # Remember every id that exists, including service and filtered
                # messages, so they are never read twice and last_id never jumps
                # over a gap that was simply not published yet.
                last_seen = max(last_seen, int(message.id))
                if getattr(message, 'service', False):
                    continue
                if not should_forward_message(message, disabled, **options):
                    counters['filtered'] += 1
                    continue
                try:
                    await self._deliver(client, rule, message, configs, button)
                    counters['forwarded'] += 1
                except FloodWait as exc:
                    await asyncio.sleep(exc.value)
                    try:
                        await self._deliver(client, rule, message, configs, button)
                        counters['forwarded'] += 1
                    except Exception:
                        logger.exception("auto forward %s could not deliver message %s", rule['id'], message.id)
                        counters['failed'] += 1
                except Exception:
                    logger.exception("auto forward %s could not deliver message %s", rule['id'], message.id)
                    counters['failed'] += 1

            for key in totals:
                totals[key] += counters[key]
            state = {'last_run': time.time(), 'last_error': None}
            if last_seen:
                state['last_id'] = last_seen
            # Persist per batch so a restart repeats at most one batch.
            await db.increment_autoforward(rule['id'], counters, state)

        return totals

    async def _deliver(self, client, rule, message, configs, button):
        to_chat = int(rule['to_chat'])
        from_chat = rule['from_chat']
        protect = configs.get('protect')
        if rule.get('mode') == 'forward':
            await client.forward_messages(
                chat_id=to_chat,
                from_chat_id=from_chat,
                message_ids=message.id,
                protect_content=protect,
            )
        else:
            await client.copy_message(
                chat_id=to_chat,
                from_chat_id=from_chat,
                message_id=message.id,
                caption=custom_caption(message, configs.get('caption')),
                reply_markup=button,
                protect_content=protect,
            )

    async def _get_messages(self, client, chat, message_ids):
        try:
            messages = await asyncio.wait_for(
                client.get_messages(chat, message_ids), timeout=30
            )
        except asyncio.TimeoutError:
            messages = await asyncio.wait_for(
                client.get_messages(chat, message_ids), timeout=30
            )
        if not isinstance(messages, (list, tuple)):
            messages = [messages]
        return messages

    async def _latest_id(self, client, chat):
        """Id of the newest message in the source chat.

        get_chat_history always yields newest first; get_messages(chat, 1) would
        mean "message id 1", and get_messages without ids raises ValueError.
        """
        message = await self._newest_message(client, chat)
        if is_missing(message):
            return 0
        return int(message.id)

    async def _newest_message(self, client, chat):
        history = client.get_chat_history(chat, limit=1)
        if not hasattr(history, '__aiter__'):
            # Client versions that return a coroutine resolving to a generator.
            history = await history
        if hasattr(history, '__aiter__'):
            async for message in history:
                return message
            return None
        if isinstance(history, (list, tuple)):
            return history[0] if history else None
        return history

    async def _message_exists(self, client, chat, message_id):
        messages = await self._get_messages(client, chat, message_id)
        return not is_missing(messages[0] if messages else None)


forwarder = AutoForwarder()


def start_rule(rule):
    return forwarder.start(rule)


def stop_rule(af_id):
    return forwarder.stop(af_id)


async def resume_autoforwards(bot=None):
    """Start a watcher for every rule that is still marked active."""
    if bot is not None:
        forwarder.bot = bot
    cursor = await db.get_all_autoforwards()
    restarted = 0
    async for rule in cursor:
        if rule.get('status') != 'active' or forwarder.is_running(rule['id']):
            continue
        if forwarder.start(rule):
            restarted += 1
    if restarted:
        logger.info("resumed %s auto forward rule(s)", restarted)
    return restarted


# ---------------------------------------------------------------------- #
# /autoforward UI
# ---------------------------------------------------------------------- #
STATUS_ICONS = {'active': '🟢', 'paused': '⏸️', 'error': '🔴'}
MODE_LABELS = {'copy': 'Copy (no forward tag)', 'forward': 'Forward (keep tag)'}
MODE_CHOICES = {'🔇 Copy without forward tag': 'copy', '🔁 Forward with tag': 'forward'}
MAX_BACKFILL = 5000


def short(text, limit=26):
    """Plain text label helper for keyboard buttons."""
    text = str(text or 'unknown').replace('\n', ' ').strip()
    return text if len(text) <= limit else text[:limit - 1] + '…'


def safe(text):
    """Escape user controlled text (chat titles, errors) for HTML output."""
    return escape(str(text if text is not None else ''))


def selected_message(message):
    return message is not None and bool(message.text)


def is_cancel(message):
    text = (message.text or '').strip().lower()
    return text == 'cancel' or text.startswith('/')


def panel_markup(rules):
    buttons = []
    for rule in rules:
        icon = STATUS_ICONS.get(rule.get('status'), '⚪')
        buttons.append([InlineKeyboardButton(
            f"{icon} {short(rule.get('from_title'))} → {short(rule.get('to_title'))}",
            callback_data=f"af#view_{rule['id']}"
        )])
    buttons.append([InlineKeyboardButton('➕ New Auto Forward', callback_data='af#new')])
    buttons.append([InlineKeyboardButton('❔ How it works', callback_data='af#info')])
    buttons.append([InlineKeyboardButton('↩ Back', callback_data='back')])
    return InlineKeyboardMarkup(buttons)


async def panel_text(user_id):
    rules = await db.get_user_autoforwards(user_id)
    active = sum(1 for rule in rules if rule.get('status') == 'active')
    lines = [Translation.AUTOFORWARD_TXT.format(len(rules), active)]
    if not rules:
        lines.append("\n<i>No rule yet. Create one with the button below.</i>")
    else:
        lines.append("")
        for rule in rules:
            icon = STATUS_ICONS.get(rule.get('status'), '⚪')
            lines.append(
                f"{icon} <code>{rule['id']}</code> "
                f"{safe(short(rule.get('from_title'), 22))} → {safe(short(rule.get('to_title'), 22))}"
            )
    return "\n".join(lines)


def rule_text(rule):
    last_run = rule.get('last_run')
    last_run = time.strftime('%Y-%m-%d %H:%M', time.localtime(last_run)) if last_run else 'not yet'
    text = Translation.AUTOFORWARD_RULE.format(
        rule['id'],
        safe(rule.get('from_title')), safe(rule.get('from_chat')),
        safe(rule.get('to_title')), safe(rule.get('to_chat')),
        MODE_LABELS.get(rule.get('mode'), MODE_LABELS['copy']),
        STATUS_ICONS.get(rule.get('status'), '⚪'), rule.get('status'),
        rule.get('forwarded', 0), rule.get('filtered', 0), rule.get('failed', 0),
        last_run,
    )
    if rule.get('backfill'):
        text += f"\n<b>➣ One time backfill:</b> <code>{rule['backfill']}</code> messages"
    if rule.get('last_error'):
        text += f"\n\n⚠️ <b>Last error:</b>\n<code>{safe(rule['last_error'])}</code>"
    return text


def rule_markup(rule):
    if rule.get('status') == 'active':
        toggle = ('⏸️ Pause', f"af#pause_{rule['id']}")
    else:
        toggle = ('▶️ Resume', f"af#start_{rule['id']}")
    mode = 'forward' if rule.get('mode') == 'copy' else 'copy'
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle[0], callback_data=toggle[1])],
        [InlineKeyboardButton(f"🔀 Switch to {MODE_LABELS[mode]}", callback_data=f"af#mode_{rule['id']}")],
        [InlineKeyboardButton('🗑️ Delete', callback_data=f"af#delete_{rule['id']}")],
        [InlineKeyboardButton('↩ Back', callback_data='af#main')],
    ])


async def ask(bot, chat_id, text, markup=None):
    try:
        return await bot.ask(chat_id, text, reply_markup=markup, timeout=300)
    except (asyncio.TimeoutError, AttributeError):
        return None


async def choose_account(bot, chat_id, accounts):
    if len(accounts) == 1:
        return accounts[0]
    buttons, mapping = [], {}
    for account in accounts:
        icon = '🤖' if account.get('is_bot') else '👤'
        username = f"@{account['username']}" if account.get('username') else 'private'
        label = short(f"{icon} {account['name']} ({username})", 60)
        if label in mapping:
            label = short(f"{label} {account['id']}", 60)
        mapping[label] = account['id']
        buttons.append([KeyboardButton(label)])
    buttons.append([KeyboardButton('cancel')])
    answer = await ask(bot, chat_id, Translation.AUTOFORWARD_ACCOUNT,
                       ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
    if not selected_message(answer) or is_cancel(answer):
        return None
    account_id = mapping.get(answer.text)
    return next((a for a in accounts if a['id'] == account_id), None)


async def choose_target(bot, chat_id, channels):
    if len(channels) == 1:
        return channels[0]
    buttons, mapping = [], {}
    for channel in channels:
        label = short(channel['title'], 60)
        if label in mapping:
            label = short(f"{label} {channel['chat_id']}", 60)
        mapping[label] = channel['chat_id']
        buttons.append([KeyboardButton(label)])
    buttons.append([KeyboardButton('cancel')])
    answer = await ask(bot, chat_id, Translation.AUTOFORWARD_TARGET,
                       ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
    if not selected_message(answer) or is_cancel(answer):
        return None
    target_id = mapping.get(answer.text)
    return next((c for c in channels if c['chat_id'] == target_id), None)


async def choose_source(bot, chat_id):
    answer = await ask(bot, chat_id, Translation.AUTOFORWARD_SOURCE, ReplyKeyboardRemove())
    if answer is None:
        return None
    # A forwarded channel post may be media only, so it is checked before the
    # text based cancel/validation path.
    forwarded = parse_forwarded_post(answer)
    if forwarded:
        return forwarded
    if is_cancel(answer):
        return None
    linked = parse_chat_link(answer.text)
    if linked:
        return linked
    username = (answer.text or '').strip()
    if username.startswith('@') and len(username) > 4:
        # Resolved to a message id by the watcher once it starts.
        return username, 0
    return None


async def choose_mode(bot, chat_id):
    buttons = [[KeyboardButton(label)] for label in MODE_CHOICES]
    buttons.append([KeyboardButton('cancel')])
    answer = await ask(bot, chat_id, Translation.AUTOFORWARD_MODE,
                       ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
    if not selected_message(answer) or is_cancel(answer):
        return None
    return MODE_CHOICES.get(answer.text)


async def choose_backfill(bot, chat_id):
    answer = await ask(bot, chat_id, Translation.AUTOFORWARD_BACKFILL, ReplyKeyboardRemove())
    if not selected_message(answer) or is_cancel(answer):
        return None
    try:
        value = int(answer.text.strip())
    except (TypeError, ValueError):
        return None
    if value < 0 or value > MAX_BACKFILL:
        return None
    return value


@Client.on_message(filters.private & filters.command(['autoforward', 'af']))
async def autoforward_command(bot, message):
    forwarder.bot = bot
    user_id = message.from_user.id
    await message.reply_text(
        await panel_text(user_id),
        reply_markup=panel_markup(await db.get_user_autoforwards(user_id)),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex(r'^af#'))
async def autoforward_query(bot, query):
    forwarder.bot = bot
    user_id = query.from_user.id
    action, _, arg = query.data.split('#', 1)[1].partition('_')

    if action == 'main':
        await query.answer()
        return await query.message.edit_text(
            await panel_text(user_id),
            reply_markup=panel_markup(await db.get_user_autoforwards(user_id)),
            disable_web_page_preview=True,
        )

    if action == 'info':
        await query.answer()
        return await query.message.edit_text(
            Translation.AUTOFORWARD_INFO,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('↩ Back', callback_data='af#main')]]),
            disable_web_page_preview=True,
        )

    if action == 'new':
        await query.answer()
        return await create_rule(bot, query)

    if not arg.isdigit():
        return await query.answer('Rule not found', show_alert=True)
    rule = await db.get_autoforward(int(arg))
    if not rule or int(rule.get('user_id', 0)) != user_id:
        return await query.answer('Rule not found', show_alert=True)

    if action == 'view':
        await query.answer()
        return await query.message.edit_text(
            rule_text(rule), reply_markup=rule_markup(rule), disable_web_page_preview=True)

    if action == 'pause':
        await db.update_autoforward(rule['id'], {'status': 'paused'})
        stop_rule(rule['id'])
        await query.answer('Auto forward paused')

    elif action == 'start':
        await db.update_autoforward(rule['id'], {'status': 'active', 'last_error': None})
        rule = await db.get_autoforward(rule['id'])
        start_rule(rule)
        await query.answer('Auto forward resumed')

    elif action == 'mode':
        mode = 'forward' if rule.get('mode') == 'copy' else 'copy'
        await db.update_autoforward(rule['id'], {'mode': mode})
        rule = await db.get_autoforward(rule['id'])
        await query.answer(f"Mode: {MODE_LABELS[mode]}")

    elif action == 'delete':
        stop_rule(rule['id'])
        await db.remove_autoforward(rule['id'], user_id)
        await query.answer('Auto forward deleted')
        return await query.message.edit_text(
            await panel_text(user_id),
            reply_markup=panel_markup(await db.get_user_autoforwards(user_id)),
            disable_web_page_preview=True,
        )

    else:
        return await query.answer()

    rule = await db.get_autoforward(rule['id'])
    return await query.message.edit_text(
        rule_text(rule), reply_markup=rule_markup(rule), disable_web_page_preview=True)


async def create_rule(bot, query):
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    accounts = await db.get_bots(user_id)
    channels = await db.get_user_channels(user_id)

    if not accounts or not channels:
        text = Translation.AUTOFORWARD_NO_ACCOUNTS if not accounts else Translation.AUTOFORWARD_NO_CHANNELS
        return await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('⚙️ Settings', callback_data='settings#bots')],
                [InlineKeyboardButton('↩ Back', callback_data='af#main')],
            ])
        )

    await query.message.edit_text(Translation.AUTOFORWARD_SETUP, reply_markup=None)

    account = await choose_account(bot, chat_id, accounts)
    target = await choose_target(bot, chat_id, channels) if account else None
    source = await choose_source(bot, chat_id) if target else None
    if not source:
        if account and target:
            await bot.send_message(chat_id, Translation.AUTOFORWARD_NO_SOURCE)
        return await bot.send_message(chat_id, Translation.CANCEL, reply_markup=ReplyKeyboardRemove())

    from_chat, last_id = source
    mode = await choose_mode(bot, chat_id)
    if not mode:
        return await bot.send_message(chat_id, Translation.CANCEL, reply_markup=ReplyKeyboardRemove())
    backfill = await choose_backfill(bot, chat_id)
    if backfill is None:
        return await bot.send_message(chat_id, Translation.CANCEL, reply_markup=ReplyKeyboardRemove())

    try:
        source_title = (await bot.get_chat(from_chat)).title
    except Exception:
        source_title = str(from_chat)

    rule = await db.add_autoforward({
        'user_id': user_id,
        'account_id': account['id'],
        'from_chat': from_chat,
        'from_title': source_title,
        'to_chat': target['chat_id'],
        'to_title': target['title'],
        'mode': mode,
        'status': 'active',
        'last_id': last_id or 0,
        'backfill': backfill,
        'backfill_start': None,
    })
    start_rule(rule)

    return await bot.send_message(
        chat_id,
        Translation.AUTOFORWARD_CREATED + "\n\n" + rule_text(rule),
        reply_markup=rule_markup(rule),
        disable_web_page_preview=True,
        reply_to_message_id=query.message.id if query.message else None,
    )
