# Developed by ADx
import re
import time as tm
from typing import Optional, Tuple, Union
from database import db 
from pyrogram import enums
from .test import parse_buttons

STATUS = {}

# Supports t.me/name/123, t.me/c/1234567890/123 and the same links with a
# ?single query suffix.
CHAT_LINK_REGEX = re.compile(
    r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$"
)


def parse_chat_link(text) -> Optional[Tuple[Union[int, str], int]]:
    """Return (chat, message_id) for a Telegram message link, else None."""
    if not text:
        return None
    match = CHAT_LINK_REGEX.match(str(text).strip().replace("?single", ""))
    if not match:
        return None
    chat = match.group(4)
    if chat.isnumeric():
        chat = int("-100" + chat)
    return chat, int(match.group(5))


def parse_forwarded_post(message) -> Optional[Tuple[Union[int, str], int]]:
    """Return (chat, last_message_id) when message is a forwarded channel post."""
    chat = getattr(message, 'forward_from_chat', None)
    if not chat or chat.type != enums.ChatType.CHANNEL:
        return None
    last_id = getattr(message, 'forward_from_message_id', None)
    if not last_id:
        return None
    return (chat.username or chat.id), int(last_id)

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS
    
    def verify(self):
        return self.data.get(self.id)

    async def load(self):
        values = await db.nfy.find_one({'forward_id': str(self.id)})
        if not values:
            return False
        values = values.get('state') or values
        values.pop('_id', None)
        values.pop('user_id', None)
        values.pop('forward_id', None)
        self.data[self.id] = values
        self.get(full=True)
        return True

    async def persist(self, user_id):
        values = dict(self.data.get(self.id) or {})
        if not values:
            return
        await db.update_frwd(int(user_id), {
            'forward_id': str(self.id),
            'state': values
        })
    
    def store(self, From, to, skip, limit, account_id=None, count=0):
        skip = max(0, int(skip))
        limit = max(skip, int(limit))
        count = max(0, int(count or 0))
        # skip removes the oldest messages, count keeps only the newest ones.
        # Both options can be combined, so the effective range starts at the
        # later of the two lower bounds.
        start_id = skip + 1
        if count:
            start_id = max(start_id, limit - count + 1)
        self.data[self.id] = {"FROM": From, 'TO': to, 'total_files': 0, 'skip': skip, 'count': count,
                      'start_id': start_id, 'limit': limit, 'fetched': 0, 'filtered': 0,
                      'deleted': 0, 'duplicate': 0, 'total': max(0, limit - start_id + 1),
                      'start': 0, 'account_id': account_id}
        self.get(full=True)
        return STS(self.id)
        
    def get(self, value=None, full=False):
        values = self.data.get(self.id)
        if not full:
           return values.get(value)
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def add(self, key=None, value=1, time=False):
        if time:
          return self.data[self.id].update({'start': tm.time()})
        self.data[self.id].update({key: self.get(key) + value}) 
    
    def divide(self, no, by):
       by = 1 if int(by) == 0 else by 
       return int(no) / by 
    
    async def get_data(self, user_id, account_id=None):
        bot = await db.get_bot_by_id(user_id, account_id) if account_id else await db.get_bot(user_id)
        k, filters = self, await db.get_filters(user_id)
        size, configs = None, await db.get_configs(user_id)
        if configs['duplicate']:
           duplicate = [configs['db_uri'], self.TO]
        else:
           duplicate = False
        button = parse_buttons(configs['button'] if configs['button'] else '')
        if configs['file_size'] != 0:
            size = [configs['file_size'], configs['size_limit']]
        return bot, configs['caption'], configs['forward_tag'], {'chat_id': k.FROM, 'limit': k.limit, 'offset': k.skip, 'filters': filters,
                'keywords': configs['keywords'], 'media_size': size, 'extensions': configs['extension'], 'skip_duplicate': duplicate}, configs['protect'], button
        
