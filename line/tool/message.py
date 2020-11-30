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
