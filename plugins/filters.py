# Developed by ADx
"""Pure message helpers shared by the bulk forwarder and the auto forwarder.

Nothing in this module talks to Telegram, so it can run against any message
object that exposes the usual Pyrogram attributes.
"""


def message_type(msg):
  """Return the setting key corresponding to a Telegram message."""
  if getattr(msg, "poll", None):
    return "poll"
  for key in ("text", "document", "video", "photo", "audio",
              "voice", "animation", "sticker"):
    if getattr(msg, key, None) is not None:
      return key
  return None


def get_message_file_id(msg):
  """Return a stable Telegram file id for duplicate detection."""
  for key in ("document", "video", "photo", "audio", "voice",
              "animation", "sticker"):
    obj = getattr(msg, key, None)
    if obj is None:
      continue
    if key == "photo" and isinstance(obj, (list, tuple)):
      obj = obj[-1] if obj else None
    file_id = getattr(obj, "file_unique_id", None) or getattr(obj, "file_id", None)
    if file_id:
      return file_id
  return None


def should_forward_message(msg, disabled_filters, keywords=None,
                           extensions=None, media_size=None):
  """
  Check every forwarding filter.
  disabled_filters contains keys that are OFF in Settings.
  """
  msg_type = message_type(msg)

  # Known message types are controlled by the matching toggle.
  if msg_type in disabled_filters:
    return False

  # If a media type is configured but Telegram returned an unknown type,
  # don't accidentally treat it as an enabled file type.
  if msg_type is None:
    return False

  # Keyword/extension/size settings apply to files/media with a filename.
  media_obj = None
  for key in ("document", "video", "audio", "voice", "animation", "photo"):
    obj = getattr(msg, key, None)
    if obj is not None:
      if key == "photo" and isinstance(obj, (list, tuple)):
        obj = obj[-1] if obj else None
      media_obj = obj
      break

  if media_obj is not None:
    file_name = str(getattr(media_obj, "file_name", "") or "")
    lower_name = file_name.lower()

    if keywords and not any(word in lower_name for word in keywords):
      return False

    if extensions:
      ext = lower_name.rsplit(".", 1)[-1] if "." in lower_name else ""
      if ext in extensions:
        return False

    if media_size and getattr(media_obj, "file_size", None) is not None:
      limit_mb, mode = media_size
      try:
        limit_bytes = float(limit_mb) * 1024 * 1024
        size_bytes = float(media_obj.file_size)
        if mode is True and size_bytes <= limit_bytes:
          return False
        if mode is False and size_bytes >= limit_bytes:
          return False
        if mode is None and size_bytes != limit_bytes:
          return False
      except (TypeError, ValueError):
        pass

  return True


def custom_caption(msg, caption):
  if msg.media:
    if (msg.video or msg.document or msg.audio or msg.photo):
      media = getattr(msg, msg.media.value, None)
      if media:
        file_name = getattr(media, 'file_name', '')
        file_size = getattr(media, 'file_size', '')
        fcaption = getattr(msg, 'caption', '')
        if fcaption:
          fcaption = fcaption.html
        if caption:
          return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
        return fcaption
  return None


def get_size(size):
  units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
  size = float(size)
  i = 0
  while size >= 1024.0 and i < len(units):
     i += 1
     size /= 1024.0
  return "%.2f %s" % (size, units[i])


def media(msg):
  if msg.media:
     media = getattr(msg, msg.media.value, None)
     if media:
        return getattr(media, 'file_id', None)
  return None
