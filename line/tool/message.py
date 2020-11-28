import line.tool.keyword as Kw
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

def format_keyword_confirm_message(user):
    msg = '請確認以下關鍵字是否正確:\n'
    msg += '\n'.join([f'[{index+1}] {key}' for index,
                      key in enumerate(Kw.KEYWORD_TMP[user.user_id])])
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
            category = info['_source'].get('category', '')
            if category == None or category == 'None':
                category = ''

            title = info['_source'].get('title', '')
            time = info['_source'].get('time', '')
            message += f"[{index}]{category} {title}\n"
            message += f"發文時間: {time}\n"
            message += f"{info['_source']['url']}\n"
            index += 1
    message += f'--\n'
    return message
