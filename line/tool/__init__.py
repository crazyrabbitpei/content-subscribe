from elasticsearch import Elasticsearch

from django.utils.translation import gettext_lazy as _

import sys, os
import logging
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

from line.models import Keyword, User


logger = logging.getLogger(__name__)

client = Elasticsearch(
    http_auth=(os.getenv('ES_USER'), os.getenv("ES_PASSWD")),
    hosts=os.getenv('ES_HOSTS').split(','),
    use_ssl=True,
    verify_cert=False,
    ssl_show_warn=False,
    scheme='https',
    port=int(os.getenv('ES_PORT')),
)
es_search_patterns = [
    {
        "match": {
            "content": {
                # 使用and 或 or來決定搜尋字詞(斷詞後)要全部符合或是有其中一項即可，預設or
                "operator": "and",
                #"minimum_should_match": 3,  # 若operator為
                "query": ""
            }
        },
    }
]

es_search_filters = [
    #{"term":  {"is_reply": False}},
    {"range": {"time": {"gte": "now-15d"}}}
]

COMMAND_STATES = {
    '0': action_free,
    '1': action_subscribing,
    '2': action_confirming,
}

KEYWORD_TMP = defaultdict(list)

def detect_message_type(event):
    try:
        if event.message.type == 'text':
            emojis = event.message.emojis
            if emojis:
                return ('emoji', [(e.product_id, e.emoji_id) for e in emojis])
            else:
                return ('text', None)
        if event.message.type == 'sticker':
            return ('sticker', [(event.message.package_id, event.message.sticker_id)])
    except:
        logger.error('判斷使用者所發出的訊息類別錯誤', exc_info=True)

    return (None, None)

def get_user_info(user_id):
    return get_user_info_from_cache(user_id) or get_user_info_from_rds(user_id)

def get_user_info_from_rds(user_id):
    return User.objects.get(pk=user_id)

#TODO
def get_user_info_from_cache(user_id):
    return None

def action(user, /, *, mtype, message=None):
    logger.info(
        f'User action, current state: {user.state}, mtype: {mtype}, message: {message}')
    result = {
        'ok': False,
        'msg': None,
        'err_msg': None,
    }

    handler = COMMAND_STATES.get(user.state, None)
    if handler:
        new_state = handler(user, result, mtype, message)
    else:
        logger.error(f'尚未定義的user state: {user.state}')
        result['err_msg'] = _(f'服務好像出了點問題QQ')
        return result

    if new_state not in COMMAND_STATES:
        logger.error(f'新的state尚未定義，故無法更新user state: {new_state}')
        result['err_msg'] = _(f'服務好像出了點問題QQ')
        return result

    try:
        update_user_state(user, new_state)
    except:
        logger.error('無法更新', exc_info=True)

    return result

def action_free(user, result, mtype, message=None, state='0'):
    if is_emoji_or_sticker(mtype):
        state = '1'
        result['msg'] = '可以開始輸入關鍵字囉'
        result['ok'] = True
    elif mtype == 'text':
        es_search_patterns[0]['match']['content']['query'] = message
        result['msg'] = find(message, es_search_patterns, es_search_patterns)
        result['ok'] = True

    return state

def action_subscribing(user, result, mtype, message=None, state='1'):
    if is_emoji_or_sticker(mtype):
        state = '2'
        result['msg'] = format_keyword_confirm_message(user)
        result['ok'] = True
    elif mtype == 'text':
        KEYWORD_TMP[user.user_id].append(message)
        result['msg'] = '繼續輸入下一筆，或是用一個emoji來結束關鍵字輸入'
        result['ok'] = True

    return state

def action_confirming(user, result, mtype, message=None, state='2'):
    if is_emoji_or_sticker(mtype):
        state = '0'
        ok, success_keys, exist_keys, err_msg = subscribe_keyword(user)
        result['ok'] = ok
        if not ok:
            result['err_msg'] = err_msg
        elif len(success_keys) > 0:
            result['msg'] = f'成功訂閱關鍵字: {",".join(success_keys)}'

        if len(exist_keys) > 0:
            result['msg'] += f'已訂閱過的關鍵字: {",".join(exist_keys)}'

        KEYWORD_TMP[user.user_id].clear()
    elif mtype == 'text':
        remove_all, remove_keys = remove_tmp_subscribing(user, message)
        if remove_all:
            state = '0'
            result['msg'] = '此次輸入的關鍵字已都移除，若要重新開始訂閱請輸入一個emoji'
        elif len(remove_keys) > 0:
            result['msg'] = f'已移除關鍵字: {",".join(remove_keys)}\n'
            result['msg'] += format_keyword_confirm_message(user)
        else:
            result['msg'] = '沒有任何關鍵字被移除'

        result['ok'] = True

    return state

def remove_tmp_subscribing(user, message=None):
    if not message:
        return []

    remove_all = False
    remove_keys = []
    keys_num = len(KEYWORD_TMP[user.user_id])

    numbers = [int(n) if int(n) > 0 and int(n) <= keys_num else -1 for n in message.split(' ') if n.isnumeric()]
    if len(numbers) == keys_num:
        remove_all = True

    if remove_all:
        remove_keys = KEYWORD_TMP[user.user_id][:]
        KEYWORD_TMP[user.user_id].clear()
        return remove_all, remove_keys

    for n in sorted(numbers, reverse=True):
        remove_keys.append(KEYWORD_TMP[user.user_id].pop(n-1))

    return remove_all, remove_keys

def update_user_state(user, new_state):
    user.state = new_state
    try:
        user.save()
    except:
        raise

def is_emoji_or_sticker(mtype):
    return mtype == 'emoji' or mtype == 'sticker'

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
            elif not user.keyword_set.filter(pk=key.pk).exists():
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

def format_keyword_confirm_message(user):
    msg = '請確認以下關鍵字是否正確:\n'
    msg += '\n'.join([f'[{index+1}] {key}' for index, key in enumerate(KEYWORD_TMP[user.user_id])])
    msg += '\n--'
    msg += '\n確認: 輸入emoji符號'
    msg += '\n刪除: 輸入關鍵字編號，若要刪除多筆則用空格區隔'
    return msg

def format_searh_message(keyword, result):
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
            message += f"[{index}] {info['_source']['category']} {info['_source']['title']}\n"
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
    try:
        result = client.search(body=search)
    except:
        logger.error('搜尋db失敗', exc_info=True)

    return format_searh_message(keyword, result)
