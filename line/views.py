from line.tool.line import callback_handler

from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import logging
import os
import sys
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def record_meta(func):
    def wrap(*args, **kwargs):
        request = args[0]
        logger.info(f"{request.headers}, {request.META['REMOTE_ADDR']}, {request.META['REMOTE_HOST']}")
        return func(*args, **kwargs)
    return wrap


# Create your views here.
@csrf_exempt
@record_meta
@require_http_methods(['POST'])
def callback(request):
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
    except LineBotApiError:
        etype, value, tb = sys.exc_info()
        logger.error(f"Line bot api error {etype}", exc_info=True)
        return HttpResponseBadRequest()

    return HttpResponse()


@record_meta
def test(request):
    return JsonResponse({'message': 'Hi'})
