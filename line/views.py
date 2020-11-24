import traceback
import sys
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
    MessageEvent, TextMessage, TextSendMessage,
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
        logger.error(f"Line bot api errorL {etype}", exc_info=True)
        return HttpResponseBadRequest()

    return HttpResponse()

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    patterns = [
        {"match": {"board": "BoardGame"}},
        {"match": {"content": "古墓"}},
        {"match": {"category": "交易"}}
    ]

    filters = [
        {"term":  {"is_reply": False}},
        #{"range": {"time": {"gte": "2020-11-19T17:47:03+08:00"}}}
    ]
    message = find(patterns, filters)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))


def format_message(result):
    hits = result['hits']['hits']
    message = f'共有 {len(hits)} 筆結果\n'
    message += f'--\n'
    for index, hit in enumerate(hits):
        message += f"{index+1}: {hit['_source']['category']} {hit['_source']['title']}\n"
        message += f"發文時間: {hit['_source']['time']}\n"
        message += f"{hit['_source']['url']}\n"
    message += f'--\n'
    return message


def find(patterns=None, filters=None):
    search = {
        "query": {
            "bool": {
                "must": patterns,
                "filter": filters
            }
        }
    }
    result = client.search(body=search)
    return format_message(result)

def test(request):
    result = {"message": "hello"}
    return JsonResponse(result)
