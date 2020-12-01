import logging
logger = logging.getLogger(__name__)

def is_emoji_or_sticker(mtype):
    return mtype == 'emoji' or mtype == 'sticker'

def detect_message_type(event):
    try:
        if event.message.type == 'text':
            emojis = event.message.emojis
            if emojis:
                return ('emoji', [(e['product_id'], e['emoji_id']) for e in emojis])
            else:
                return ('text', None)
        if event.message.type == 'sticker':
            return ('sticker', [(event.message.package_id, event.message.sticker_id)])
    except:
        logger.error('判斷使用者所發出的訊息類別錯誤', exc_info=True)

    return (None, None)
