from line.models import User, Keyword

import traceback
import sys
from collections import defaultdict

from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from elasticsearch import Elasticsearch
import json
import logging
import logging.config


logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv
load_dotenv()

import time
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, FollowEvent, UnfollowEvent, TextMessage, TextSendMessage
)

line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

client = Elasticsearch(
    http_auth=(os.getenv('ES_USER'), os.getenv("ES_PASSWD")),
    hosts=os.getenv('ES_HOSTS').split(','),
    use_ssl=True,
    verify_cert=False,
    ssl_show_warn=False,
    scheme='https',
    port=int(os.getenv('ES_PORT')),
)
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
    message = _('註冊成功，可以開始訂閱關鍵字囉')
    try:
        User.objects.create(user_id=event.source.user_id)
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
        user = User.objects.get(user_id=event.source.user_id)
        user.delete()
    except:
        logger.error(f'無法刪除使用者 {event.source.user_id}')
    else:
        logger.info(f'{event.source.user_id} 成功unfollow')


@handler.add(MessageEvent, message=TextMessage)
def echo(event):
    # TODO
    '''
    1. 訂閱關鍵字操作
        - 下特殊指令視為開始輸入訂閱字
        - 下特殊指令視為結束輸入訂閱字
        - 回傳當前訂閱字做確認
        - 確認訂閱字
            - 特殊字符確認
            - 特殊字符修改
        - 關鍵字加入db
            - keyword db
            - user db
            - user-keyword many-to-many db
        - 回傳成功訂閱結果
    '''

    # patterns = [
    #     {
    #         "match": {
    #             "content": {
    #                 "operator": "and", # 使用and 或 or來決定搜尋字詞(斷詞後)要全部符合或是有其中一項即可，預設or
    #                 #"minimum_should_match": 3,  # 若operator為
    #                 "query": f"{event.message.text}"
    #             }
    #         },
    #     }
    # ]

    # filters = [
    #     #{"term":  {"is_reply": False}},
    #     {"range": {"time": {"gte": "now-15d"}}}
    # ]
    # message = find(event.message.text, patterns, filters)
    message = _("hello")
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))
    except LineBotApiError as e:
        etype, value, tb = sys.exc_info()
        logger.error(f'Reply api error {etype}', exc_info=True)

def push_notice(request):
    try:
        line_bot_api.push_message(
            'U2b3104fdaef9c190510326b414c1611d', TextSendMessage(
                text=_('主動通知~')))
    except:
        logger.error('主動通知失敗')

def format_message(keyword, result):
    hits = result['hits']['hits']
    count_board = defaultdict(list)
    for index, hit in enumerate(hits):
        count_board[hit['_source']['board']].append(hit)

    board_info = ' ,'.join(
        [f'{key}({len(value)})' for key, value in count_board.items()])

    message = f'共有 {len(hits)} 筆 {keyword} 結果, {board_info}\n'
    for board, infos in count_board.items():
        index = 1
        meta = board.center(25, '=')
        message += meta+'\n'
        for info in infos:
            message += f"{index}. {info['_source']['category']} {info['_source']['title']}\n"
            message += f"發文時間: {info['_source']['time']}\n"
            message += f"{info['_source']['url']}\n"
            index += 1
    message += f'--\n'
    return message


def find(keyword=None, patterns=None, filters=None):
    search = {
        "query": {
            "bool": {
                "must": patterns,
                "filter": filters
            }
        }
    }
    result = client.search(body=search)
    return format_message(keyword, result)


