from config import Config

BOT_LINK = f"https://t.me/{Config.BOT_USERNAME}"

class Translation(object):
  START_TXT = f"""<b>Hey {{}}, {{}}</b>

◈ I am an advanced auto forward bot.
◈ I can forward all messages from one channel to another channel.
◈ Use auto forward to keep a channel in sync 24x7.
◈ Click the help button to know more about me.

<blockquote>Maintained by: <a href='{Config.UPDATES_CHANNEL}'>{Config.DEVELOPER_NAME}</a></blockquote></b>"""


  HELP_TXT = """<b><u>🛠️ HELP</b></u>

<u>**📚 Available commands:**</u>
<b>⏣ __/start - check I'm alive__ 
⏣ __/forward - forward messages__ 
⏣ __/autoforward - forward every new post automatically__
⏣ __/unequify - delete duplicate messages in channels__ 
⏣ __/settings - configure your settings__ 
⏣ __/reset - reset your settings__</b>

<b><u>💢 Features:</b></u>
<b>► __Forward message from public channel to your channel without admin permission. if the channel is private need admin permission__
► __Forward message from private channel to your channel by using userbot(user must be member in there)__
► __Forward the last N messages, only new posts or the whole channel__
► __Auto forward: every new post in the source channel is forwarded instantly__
► __custom caption__
► __custom button__
► __support restricted chats__
► __skip duplicate messages__
► __filter type of messages__
► __skip messages based on extensions & keywords & size__</b>
"""
  
  HOW_USE_TXT = """<b><u>⚠️ Before Forwarding:</b></u>
  
<b>► __Add A Bot Or Userbot__ 
► __Add At Least One Channel (Your Bot/Userbot Must Be Admin In There)
► __You Can Add Chats Or Bots By Using /settings__ 
► __if the **From Channel** is private your userbot must be member in there or your bot must need admin permission in there also__ 
► __Then use /forward to forward messages or /autoforward to forward every new post automatically__</b>"""
  
  ABOUT_TXT = f"""<b>
╭───────────⍟
├◈ My name : <a href={BOT_LINK}>{Config.BOT_NAME}</a>
├◈ Developer : <a href={Config.SUPPORT_GROUP}>{Config.DEVELOPER_NAME}</a> 
├◈ Updates channel: <a href={Config.UPDATES_CHANNEL}>{Config.DEVELOPER_NAME} Updates</a>   
├◈ Library : <a href=https://github.com/pyrogram>Pyrogram</a>
├◈ Language: <a href=https://www.python.org/>Python 3</a>
├◈ Database: <a href=https://cloud.mongodb.com/>MongoDB</a>
├◈ Bot version: <a href={Config.REPO_URL}>{Config.VERSION}</a>
├◈ Bot source: <a href={Config.REPO_URL}>{Config.BOT_NAME}</a>
╰───────────────⍟</b>"""
  
  STATUS_TXT = """<b><u>Bot Status</u>

👨 Users     : {}

🤖 Bots      : {}

📣 Channels  : {}
</b>""" 
  
  FROM_MSG = "<b>❪ SET SOURCE CHAT ❫\n\nForward the last message or last message link of source chat.\n/cancel - cancel this process</b>"
  TO_MSG = "<b>❪ CHOOSE TARGET CHAT ❫\n\nChoose your target chat from the given buttons.\n/cancel - Cancel this process</b>"
  SKIP_MSG = "<b>❪ SET MESSAGE SKIPPING NUMBER ❫</b>\n\n<b>Skip the message as much as you enter the number and the rest of the message will be forwarded\nDefault Skip Number =</b> <code>0</code>\n<code>eg: You enter 0 = 0 messages skipped\n You enter 5 = 5 messages skipped</code>\n/cancel <b>- cancel this process</b>"
  COUNT_MSG = "<b>❪ HOW MANY LATEST MESSAGES ❫</b>\n\n<b>Send how many of the newest messages you want to forward.\nOnly those messages are forwarded, older ones are left behind.\nDefault =</b> <code>0</code>\n<code>eg: You enter 0 = all messages after the skip number\n You enter 10 = only the latest 10 messages</code>\n/cancel <b>- cancel this process</b>"
  CANCEL = "<b>Process cancelled successfully!</b>"
  FORWARDING_STARTED = f"<b>🚥 Forwarding started via</b> <b><a href=\"{BOT_LINK}\">{Config.BOT_NAME}</a></b>"
  BOT_DETAILS = "<b><u>📄 BOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ BOT ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}"
  USER_DETAILS = "<b><u>📄 USERBOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ USER ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}"  
         
  TEXT = """<b>╭────❰ <u>Forwarded Status</u> ❱────❍
┃
┣⊸<b>🕵 Fetched msg :</b> <code>{}</code>
┣⊸<b>✅ Successfully fwd :</b> <code>{}</code>
┣⊸<b>👥 Duplicate msg :</b> <code>{}</code>
┣⊸<b>🗑️ Deleted msg :</b> <code>{}</code>
┣⊸<b>🪆 Skipped msg :</b> <code>{}</code>
┣⊸<b>📊 Status  :</b> <code>{}</code>
┣⊸<b>⏳ Progress  :</b> <code>{}</code> %
┣⊸<b>⏰ ETA :</b> <code>{}</code>
┃
╰────⌊ <b>{}</b> ⌉───❍</b>"""

  TEXT1 = """
╔════❰ Forward status ❱➠
║╭━━━━━━━━━━━━━━━➣
║┃
║┣⪼**🕵 Fetched msg :** `{}`
║┃
║┣⪼**✅ Successfully fwd :** `{}`
║┃
║┣⪼**👥 Duplicate msg :** `{}`
║┃
║┣⪼**🗑️ Deleted msg :** `{}`
║┃
║┣⪼**🪆 Skipped msg :** `{}`
║┃
║┣⪼**📊 Status  :** `{}`
║┃
║┣⪼**⏳ Progress :** `{}`
║┃
║┣⪼**⏰ ETA :** `{}`
║┃
║╰━━━━━━━━━━━━━━━➣ 
╚════❰ **{}** ❱➠ """

  DUPLICATE_TEXT = """
╔════❰ Unequify status ❱
║╭━━━━━━━━━━━━━━━➣
║┣⪼ <b>Fetched files:</b> <code>{}</code>
║┃
║┣⪼ <b>Duplicate deleted:</b> <code>{}</code> 
║┃
║┣⪼ <b>Status:</b> <code>{}</code>
║╰━━━━━━━━━━━━━━━➣
╚════❰ ❱
"""
  DOUBLE_CHECK = """<b><u>DOUBLE CHECKING ⚠️</b></u>
<code>Before forwarding the messages Click the Yes button only after checking the following</code>

<b>★ YOUR BOT:</b> [{botname}](t.me/{botuname})
<b>★ FROM CHANNEL:</b> `{from_chat}`
<b>★ TO CHANNEL:</b> `{to_chat}`
<b>★ SKIP MESSAGES:</b> `{skip}`
<b>★ LATEST MESSAGES:</b> `{count}`

<i>° [{botname}](t.me/{botuname}) must be admin in **TARGET CHAT**</i> (`{to_chat}`)
<i>° If the **SOURCE CHAT** is private your userbot must be member or your bot must be admin in there also</b></i>

<b>If the above is checked then the yes button can be clicked</b>"""

  AUTOFORWARD_TXT = """<b><u>🔁 AUTO FORWARD</u></b>

Every new post in the source channel is forwarded to the target channel automatically.

<b>Rules:</b> <code>{}</code> · <b>Active:</b> <code>{}</code>"""

  AUTOFORWARD_INFO = """<b><u>❔ HOW AUTO FORWARD WORKS</u></b>

<b>1.</b> Pick the bot or userbot that should do the work.
<b>2.</b> Pick one of your target channels from /settings.
<b>3.</b> Send the source channel link, its @username, or forward one of its posts.
<b>4.</b> Choose how new posts are delivered:
    • <b>Copy</b> - no forward tag, your custom caption and buttons are applied
    • <b>Forward</b> - keeps the original forward tag
<b>5.</b> Optionally forward the latest N existing messages once.

After that the bot checks the source channel every few minutes and forwards anything new, even after a restart.

<i>Your /settings filters (message types, keywords, extensions, size) apply to auto forward as well.</i>"""

  AUTOFORWARD_SETUP = "<b>🔁 CREATING A NEW AUTO FORWARD</b>\n\n<i>Send /cancel at any step to stop.</i>"
  AUTOFORWARD_ACCOUNT = "<b>❪ CHOOSE ACCOUNT ❫</b>\n\n<b>Which bot/userbot should run this auto forward?</b>"
  AUTOFORWARD_TARGET = "<b>❪ CHOOSE TARGET CHAT ❫</b>\n\n<b>Where should new posts be forwarded?</b>\n\n<i>Add more chats in /settings if yours is missing.</i>"
  AUTOFORWARD_SOURCE = "<b>❪ SET SOURCE CHAT ❫</b>\n\n<b>Forward the last message of the source channel, or send its link / @username.</b>\n/cancel - cancel this process"
  AUTOFORWARD_MODE = "<b>❪ DELIVERY MODE ❫</b>\n\n<b>🔇 Copy</b> - no forward tag, your custom caption/buttons apply\n<b>🔁 Forward</b> - keeps the original forward tag"
  AUTOFORWARD_BACKFILL = "<b>❪ ONE TIME BACKFILL ❫</b>\n\n<b>How many of the latest existing messages should be forwarded once?</b>\n\nSend <code>0</code> to start from the newest post only."

  AUTOFORWARD_NO_SOURCE = "<b>Invalid source chat.</b>\n\nForward one of its posts or send a t.me link / @username."
  AUTOFORWARD_NO_ACCOUNTS = "<b>You haven't added any bot or userbot yet.</b>\n\nAdd one in /settings first, then create an auto forward."
  AUTOFORWARD_NO_CHANNELS = "<b>You haven't added a target channel yet.</b>\n\nAdd one in /settings → Channels, then create an auto forward."
  AUTOFORWARD_CREATED = "<b>✅ AUTO FORWARD STARTED</b>\n\n<i>Only posts published from now on are forwarded automatically.</i>"

  AUTOFORWARD_RULE = """<b><u>🔁 AUTO FORWARD #{}</u></b>

<b>➣ Source:</b> {} (<code>{}</code>)
<b>➣ Target:</b> {} (<code>{}</code>)
<b>➣ Mode:</b> {}
<b>➣ Status:</b> {} {}
<b>➣ Forwarded:</b> <code>{}</code> · <b>Filtered:</b> <code>{}</code> · <b>Failed:</b> <code>{}</code>
<b>➣ Last check:</b> <code>{}</code>"""
