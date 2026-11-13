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

from config import Config
from database import db
from pyrogram.errors import FloodWait
from .filters import custom_caption, should_forward_message
from .test import CLIENT, start_clone_bot, parse_buttons

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


def is_skippable(message):
    """Deleted / service messages cannot be forwarded."""
    return message is None or getattr(message, 'empty', False) or getattr(message, 'service', False)


class AutoForwarder:
    """Owns one polling task per active rule."""

    def __init__(self):
        self.tasks = {}
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
        finally:
            self.tasks.pop(af_id, None)
            if client is not None:
                try:
                    await client.stop()
                except Exception:
                    pass

    async def _start_client(self, rule):
        user_id = int(rule['user_id'])
        account_id = rule.get('account_id')
        account = await db.get_bot_by_id(user_id, int(account_id)) if account_id else await db.get_bot(user_id)
        if not account:
            await db.update_autoforward(rule['id'], {
                'status': 'error',
                'last_error': 'Account not found. Add the bot/userbot again in /settings.',
            })
            return None
        try:
            return await start_clone_bot(CLIENT.client(account, name=f"AUTOFWD_{rule['id']}"))
        except Exception as exc:
            logger.exception("unable to start account for auto forward %s", rule['id'])
            await db.update_autoforward(rule['id'], {
                'status': 'error',
                'last_error': f'Unable to start account: {exc}'[:400],
            })
            return None

    async def _loop(self, rule, client):
        af_id = int(rule['id'])
        if not int(rule.get('last_id') or 0):
            # A rule always starts from the newest post, never from history.
            latest = await self._latest_id(client, rule['from_chat'])
            if latest:
                await db.update_autoforward(af_id, {'last_id': latest})
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
            if start:
                await db.update_autoforward(rule['id'], {'backfill_start': None})
            return
        await self._forward_range(rule, client, start, end)
        await db.update_autoforward(rule['id'], {'backfill_start': None})

    async def _poll_once(self, rule, client):
        latest = await self._latest_id(client, rule['from_chat'])
        if not latest:
            return
        last_id = int(rule.get('last_id') or 0)
        if latest <= last_id:
            await db.update_autoforward(rule['id'], {'last_run': time.time()})
            return
        end = min(latest, last_id + self.max_per_cycle)
        await self._forward_range(rule, client, last_id + 1, end)

    async def _forward_range(self, rule, client, start, end):
        configs = await db.get_configs(int(rule['user_id']))
        disabled = set(await db.get_filters(int(rule['user_id'])))
        options = filter_options(configs)
        button = parse_buttons(configs['button']) if configs.get('button') else None
        totals = {'forwarded': 0, 'filtered': 0, 'failed': 0}

        for batch_start in range(start, end + 1, self.batch):
            batch_end = min(batch_start + self.batch - 1, end)
            messages = await self._get_messages(client, rule['from_chat'], list(range(batch_start, batch_end + 1)))
            counters = {'forwarded': 0, 'filtered': 0, 'failed': 0}

            for message in messages:
                if is_skippable(message):
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
            # Persist per batch so a restart repeats at most one batch.
            await db.increment_autoforward(rule['id'], counters, {
                'last_id': batch_end,
                'last_run': time.time(),
                'last_error': None,
            })

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
        messages = await self._get_messages(client, chat, 1)
        message = messages[0] if messages else None
        if is_skippable(message):
            return 0
        return int(message.id)


forwarder = AutoForwarder()


def start_rule(rule):
    return forwarder.start(rule)


def stop_rule(af_id):
    return forwarder.stop(af_id)


async def resume_autoforwards(bot=None):
    """Start a watcher for every rule that is still marked active."""
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
