from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from elasticsearch import Elasticsearch
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
    except LineBotApiError:
        logger.error("Line bot api error")
        return HttpResponseBadRequest()

    return HttpResponse()

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    search = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"board": "BoardGame"}},
                    {"match": {"content": "古墓"}},
                    {"match": {"category": "交易"}}
                ],
                "filter": [
                    {"term":  {"is_reply": False}},
                    {"range": {"time": {"gte": "2020-11-19T17:47:03+08:00"}}}
                ]
            }
        }
    }
    result = client.search(body=search)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result))


def test(request):
    result = {"message": "hello"}
    return JsonResponse(result)
