import logging
import json
import time
import os
import traceback
import sys
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

from line.models import User, Keyword
from line.tool import detect_message_type, action

from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt


from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, FollowEvent, UnfollowEvent, TextSendMessage, TemplateSendMessage, ButtonsTemplate, ConfirmTemplate, CarouselTemplate, MessageAction
)

logger = logging.getLogger(__name__)
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# Create your views here.
@csrf_exempt
def callback(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.body.decode('utf-8')
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check your channel access token/channel secret.")
        return HttpResponseForbidden()
    except LineBotApiError as e:
        etype, value, tb = sys.exc_info()
        logger.error(f"Line bot api error {etype}", exc_info=True)
        return HttpResponseBadRequest()

    return HttpResponse()


@handler.add(FollowEvent)
def follow(event):
    try:
        User.objects.create(pk=event.source.user_id)
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'使用者加入失敗 {etype}', exc_info=True)
        message = _('註冊失敗QQ，請先封鎖後再解封所試試')

        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text=f'{message}'))
        except:
            logger.error('Reply error', exc_info=True)

@handler.add(UnfollowEvent)
def unfollow(event):
    try:
        user = User.objects.get(pk=event.source.user_id)
        user.delete()
    except:
        logger.error(f'無法刪除使用者 {event.source.user_id}')
    else:
        logger.info(f'{event.source.user_id} 成功unfollow')


@handler.add(MessageEvent)
def echo(event):
    message = None
    try:
        user = User.objects.get(pk=event.source.user_id)
    except:
        logging.error(f'使用者 {event.source.user_id} 查找失敗', exc_info=True)
        message = _(f'好像出了問題，請試著先封鎖帳號再解封鎖試試')
    else:
        mtype, oids = detect_message_type(event)
        user_message = None
        if mtype == 'text':
            user_message = event.message.text.strip()
        result = action(user, mtype=mtype, message=user_message)

        if result['ok']:
            message = result['msg']
        else:
            message = result['err_msg']
    # TODO: 傳送confirm button確認訂閱資訊
    # TODO: 傳送Carousel template顯示搜尋結果
    # TemplateSendMessage(
    #     template=ConfirmTemplate(
    #        text=_(f'{message}'),
    #        actions=[
    #            MessageAction(
    #                label=_('是'),
    #                text='😀'
    #            ),
    #            MessageAction(
    #                label=_(''),
    #                text=''
    #            ),
    #        ]
    #     )
    # )
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))
    except LineBotApiError as e:
        etype, value, tb = sys.exc_info()
        logger.error(f'Reply api error {etype}', exc_info=True)

def push_notice(request):
    message = _('主動通知~')
    try:
        line_bot_api.push_message(
            'U2b3104fdaef9c190510326b414c1611d', TextSendMessage(text=f'{message}'))
    except:
        logger.error('主動通知失敗')

    return JsonResponse({"message": "ok"})




