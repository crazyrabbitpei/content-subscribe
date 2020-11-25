import traceback
import sys
from collections import defaultdict

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from elasticsearch import Elasticsearch
import json
import logging
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
    MessageEvent, TextMessage, TextSendMessage, QuickReplyButton
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
    logger.info(f'Receive body: {body}')
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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        with open('event.record', 'w') as fp:
            json.dump(event, fp, indent=2, ensure_ascii=False)
    except:
        logger.error(exc_info=True)
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
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='hello'))
    except LineBotApiError as e:
        etype, value, tb = sys.exc_info()
        logger.error(f'Reply api error {etype}', exc_info=True)

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

def test(request):
    result = {"message": "hello"}
    return JsonResponse(result)
