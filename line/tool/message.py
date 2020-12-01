import line.tool.cache as Cache

import line.tool.keyword as Kw
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)


def format_keyword_confirm_message(user_id):
    msg = '請確認以下關鍵字是否正確:\n'
    msg += '\n'.join([f'[{index+1}] {key}' for index,
                      key in enumerate(Cache.get_tmp_keywords(user_id))])
    msg += '\n--'
    msg += '\n確認: 輸入emoji符號'
    msg += '\n刪除: 輸入關鍵字編號，若要刪除多筆則用空格區隔'
    return msg


def format_subscribed_keywords(user_id):
    msg = f'==以下是您目前的訂閱清單==\n'
    subscribed_keywords = Kw.get_subscribed(user_id)
    if len(subscribed_keywords) > 0:
        msg += '\n'.join([f'{index+1}) {key}' for index, key in enumerate(subscribed_keywords)])
    else:
        msg += '\n還沒有任何訂閱喔!'

    return msg

def menu():
    msg = '==功能==\n'
    msg += '1) 查詢: 輸入任何想查詢的字詞\n'
    msg += '2) 訂閱關鍵字: 輸入任何一個emoji\n'
    msg += '3) 刪除已訂閱的關鍵字: 輸入一個emoji然後加上要刪除的關鍵字編號，可一次輸入多筆，每筆以空格區隔'

    return msg
