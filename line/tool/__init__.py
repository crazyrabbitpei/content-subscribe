import sys, os
import logging
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

from line.models import Keyword, User

from elasticsearch import Elasticsearch

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

def action(user, /, *, mtype, message=None):
    logger.info(f'User action, current status: {user.status}, mtype: {mtype}, message: {message}')
    result = {
        'ok': False,
        'msg': None,
        'err_msg': None,
    }

    if user.status == '0':
        action_0(user, result, mtype, message)
    elif user.status == '1':
        action_1(user, result, mtype, message)
    elif user.status == '2':
        action_2(user, result, mtype, message)
    try:
        user.save()
    except:
        logger.error('無法將關鍵字儲存到db', exc_info=True)

    return result

def action_0(user, result, mtype, message=None):
    if is_emoji_or_sticker(mtype):
        user.status = '1'
        result['msg'] = '可以開始輸入關鍵字囉'
        result['ok'] = True
    elif mtype == 'text':
        es_search_patterns[0]['match']['content']['query'] = message
        result['msg'] = find(message, es_search_patterns, es_search_patterns)
        result['ok'] = True

def action_1(user, result, mtype, message=None):
    if is_emoji_or_sticker(mtype):
        user.status = '2'
        result['msg'] = format_keyword_confirm_message(user)
        result['ok'] = True
    elif mtype == 'text':
        KEYWORD_TMP[user.pk].append(message)
        result['msg'] = '繼續輸入下一筆，或是用一個emoji來結束關鍵字輸入'
        result['ok'] = True

def action_2(user, result, mtype, message=None):
    if is_emoji_or_sticker(mtype):
        user.status = '0'
        if not subscribe_keyword(user):
            result['err_msg'] = f'關鍵字加入失敗，請重新操作'
        else:
            result['msg'] = f'成功訂閱關鍵字: {",".join(KEYWORD_TMP[user.pk])}'
            result['ok'] = True
        KEYWORD_TMP[user.pk].clear()
    elif mtype == 'text':
        if message.strip() == '0':
            user.status = '0'
            result['msg'] = '此次輸入的關鍵字已都移除，若要重新開始訂閱請輸入一個emoji'
            KEYWORD_TMP[user.pk].clear()
        else:
            numbers = [int(n) if int(n) > 0 and int(n) <= len(
                KEYWORD_TMP[user.pk]) else -1 for n in message.split(' ') if n.isnumeric()]
            remove_keys = []
            for n in sorted(numbers, reverse=True):
                remove_keys.append(KEYWORD_TMP[user.pk].pop(n-1))
            result['msg'] = f'已移除關鍵字: {",".join(remove_keys)}\n'
            result['msg'] += format_keyword_confirm_message(user)
        result['ok'] = True

def is_emoji_or_sticker(mtype):
    return mtype == 'emoji' or mtype == 'sticker'

def subscribe_keyword(user):
    keys = []
    try:
        for key in KEYWORD_TMP[user.pk]:
            if not Keyword.objects.filter(keyword=key).exists():
                key_object = Keyword(keyword=key)
                keys.append(key_object)
                key_object.save()
            else:
                keys.append(Keyword.objects.get(keyword=key))
        user.keyword_set.add(*keys)
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'關鍵字加入失敗 {etype}', exc_info=True)
    else:
        return True
    return False

def format_keyword_confirm_message(user):
    msg = '請確認以下關鍵字是否正確:\n'
    msg += '\n'.join([f'[{index+1}] {key}' for index, key in enumerate(KEYWORD_TMP[user.pk])])
    msg += '\n--'
    msg += '\n確認: 輸入emoji符號'
    msg += '\n刪除: 輸入關鍵字編號，若要刪除多筆則用空格區隔，若要刪除所有關鍵字請輸入0'
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
