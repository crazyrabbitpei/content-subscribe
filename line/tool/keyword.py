from line.models import Keyword, User
from django.utils.translation import gettext_lazy as _
import logging, sys
from collections import defaultdict
logger = logging.getLogger(__name__)

KEYWORD_TMP = defaultdict(list)

def subscribe_keyword(user):
    exist_keys = []
    success_keys = []
    keys = []
    err_msg = None
    try:
        for key in KEYWORD_TMP[user.user_id]:
            if not Keyword.objects.filter(keyword=key).exists():
                key_object = Keyword(keyword=key)
                keys.append(key_object)
                key_object.save()
            elif not user.keyword_set.filter(keyword=key).exists():
                keys.append(Keyword.objects.get(keyword=key))
                success_keys.append(key)
            else:
                exist_keys.append(key)
        user.keyword_set.add(*keys)
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'關鍵字加入失敗 {etype}', exc_info=True)
        err_msg = _(f'關鍵字加入失敗，請重新操作')
        return False, success_keys, exist_keys, err_msg

    return True, success_keys, exist_keys, err_msg


def remove_tmp_subscribing(user, message=None):
    if not message:
        return []

    remove_all = False
    remove_keys = []
    keys_num = len(KEYWORD_TMP[user.user_id])

    numbers = [int(n) if int(n) > 0 and int(n) <= keys_num else -
               1 for n in message.split(' ') if n.isnumeric()]
    if len(numbers) == keys_num:
        remove_all = True

    if remove_all:
        remove_keys = KEYWORD_TMP[user.user_id][:]
        KEYWORD_TMP[user.user_id].clear()
        return remove_all, remove_keys

    for n in sorted(numbers, reverse=True):
        remove_keys.append(KEYWORD_TMP[user.user_id].pop(n-1))

    return remove_all, remove_keys
