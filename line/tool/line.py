import os, sys
import logging
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, FollowEvent, UnfollowEvent, TextSendMessage, TemplateSendMessage, ButtonsTemplate, ConfirmTemplate, CarouselTemplate, MessageAction
)

import line.tool.user as LineUser
import line.tool.state as UserState
import line.tool.message as Message

from django.utils.translation import gettext_lazy as _

line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

logger = logging.getLogger(__name__)

def callback_handler(body, signature):
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        raise
    except LineBotApiError as e:
        raise

    return

@handler.add(FollowEvent)
def follow(event):
    message = Message.menu()

    try:
        LineUser.create(event.source.user_id)
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'使用者加入失敗 {etype}', exc_info=True)
        message = _('註冊失敗QQ，請先封鎖後再解封所試試')

    try:
        reply_message(event, message)
    except:
        logger.error('Follow reply message error', exc_info=True)

@handler.add(UnfollowEvent)
def unfollow(event):
    try:
        LineUser.delete(event.source.user_id)
    except:
        logger.error(f'無法刪除使用者 {event.source.user_id}', exc_info=True)
    else:
        logger.info(f'{event.source.user_id} 成功unfollow')


@handler.add(MessageEvent)
def echo(event):
    message = None
    try:
        user = LineUser.info(event.source.user_id)
    except:
        logging.error(f'使用者 {event.source.user_id} 查找失敗', exc_info=True)
        message = _(f'好像出了問題，請試著先封鎖帳號再解封鎖試試')
    else:
        mtype, msg_text, emoji_start_at, oids = detect_message_type(event)

        result = UserState.action(user, mtype=mtype, emoji_start_at=emoji_start_at, message=msg_text)

        if result['ok']:
            message = result['msg']
        else:
            message = result['err_msg']

    try:
        reply_message(event, message)
    except:
        logger.error('Echo reply message error', exc_info=True)

def reply_message(event, message=None):
    if not message:
        message = _('系統維護中，稍等一下喔QQ')

    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f'{message}'))
    except LineBotApiError as e:
        etype, value, tb = sys.exc_info()
        logger.error(f'Reply api error {etype}', exc_info=True)
        return False
    return True

def push_message(user_id, message=None):
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=f'{message}'))
    except:
        logger.error('主動通知失敗', exc_info=True)
        return False

    return True


def is_only_emoji_or_sticker(mtype):
    '''
    只有emoji符號或是貼圖
    '''
    return mtype == 'emoji' or mtype == 'sticker'


def start_with_emoji(mtype, emojis, message):
    '''
    emoji符號後跟著字串
    '''
    if not message:
        return False


def has_text(mtype):
    '''
    訊息中含有emoji或text
    '''
    return mtype == 'emoji' or mtype == 'text'

def detect_message_type(event):
    '''
    訊息中如果
        - 只有一個emoji符號而沒有任何文字則會被視為sticker: 回傳sticker
        - 有多個emoji或是一個emoji加上文字，則會被視為text，且會有emoji欄位
            - 僅有text: 回傳text
            - 僅有emoji: 回傳emoji
            - 包含emoji和text: 回傳emoji_text
    '''
    msg_type = None
    msg = None
    emojis = None
    emoji_start_at = None
    try:
        if event.message.type == 'text':
            if event.message.emojis:
                emojis = [(e['productId'], e['emojiId']) for e in event.message.emojis]

            emoji_start_at, msg = parse_message(emojis, event.message.text)

            if emojis and msg:
                msg_type = 'emoji_text'
            elif emojis:
                msg_type = 'emoji'
            else:
                msg_type = 'text'

            return (msg_type, msg, emoji_start_at, emojis)

        elif event.message.type == 'sticker':
            msg_type = 'sticker'
            return (msg_type, msg, 0, [(event.message.package_id, event.message.sticker_id)])
        else:
            logger.error(f'尚未定義的使用者的訊息類別: {event.message.type}')
    except:
        logger.error('判斷使用者所發出的訊息類別錯誤', exc_info=True)

    return (None, msg, None)


def parse_message(emojis=None, message=None):
    if not emojis:
        return None, message

    msg = []
    emoji_start_at = int(emojis[0]['index'])
    m_start = 0
    for e in emojis:
        e_start = int(e['index'])
        e_end = e_start + int(e['length'])

        msg.append(message[m_start:e_start])
        m_start = e_end + 1
    msg.append(message[m_start:])
    return emoji_start_at, ' '.join(msg).strip()
