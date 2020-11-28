from line.models import Keyword, User
from django.utils.translation import gettext_lazy as _
import logging, sys
from collections import defaultdict
logger = logging.getLogger(__name__)

KEYWORD_TMP = defaultdict(list)

def subscribe_keyword(user):
    exist_keys = []
    success_keys = []
    wait_to_be_subscribed = []
    err_msg = None
    try:
        for key in KEYWORD_TMP[user.user_id]:
            if not keyword_exists(key):
                key_object = add_keyword(key)
            else:
                key_object = Keyword.objects.get(keyword=key)

            if not is_subscribed(user, key):
                wait_to_be_subscribed.append(key_object)
                success_keys.append(key)
            else:
                exist_keys.append(key)

        add_subscribe(user, keywords=wait_to_be_subscribed)
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'關鍵字加入失敗: {key}', exc_info=True)
        err_msg = _(f'關鍵字加入失敗，請重新操作')
        return False, success_keys, exist_keys, err_msg

    return True, success_keys, exist_keys, err_msg


def keyword_exists(keyword):
    return Keyword.objects.filter(keyword=keyword).exists()

def is_subscribed(user, keyword):
    return user.keyword_set.filter(keyword=keyword).exists()

def add_keyword(keyword):
    key_object = None
    try:
        key_object = Keyword(keyword=keyword)
        key_object.save()
    except:
        raise

    return key_object

def add_subscribe(user, *, keywords):
    if len(keywords) == 0:
        return

    try:
        user.keyword_set.add(*keywords)
    except:
        raise

def get_subscribed_keywords(user):
    pass

def remove_tmp_subscribing(user, message=None):
    if not message:
        return []

    remove_all = False
    remove_keys = []
    keys_num = len(KEYWORD_TMP[user.user_id])

    numbers = [int(n) if int(n) > 0 and int(n) <= keys_num else -
               1 for n in message.split(' ') if n.isnumeric()]

    for n in sorted(numbers, reverse=True):
        if n <= 0: continue
        remove_keys.append(KEYWORD_TMP[user.user_id].pop(n-1))

    if len(remove_keys) == keys_num:
        remove_all = True

    return remove_all, remove_keys
