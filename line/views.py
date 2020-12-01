import line.tool.user as LineUser
from line.tool.line import detect_message_type, reply_message, push_message, callback_handler
from line.models import User, Keyword

from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)

import logging
import json
import time
import os
import traceback
import sys
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


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
        callback_handler(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check your channel access token/channel secret.")
        return HttpResponseForbidden()
    except LineBotApiError as e:
        etype, value, tb = sys.exc_info()
        logger.error(f"Line bot api error {etype}", exc_info=True)
        return HttpResponseBadRequest()

    return HttpResponse()

def push_notice(request):
    message = _('主動通知~')
    push_message('000', f'{message}')
