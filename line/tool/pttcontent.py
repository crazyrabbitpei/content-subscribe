import line.tool.cache as Cache

import line.tool.es as Es
from collections import defaultdict

import logging, os
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

def format_find_message(keyword, result):
    hits = result['hits']['hits']
    count_board = defaultdict(list)
    for index, hit in enumerate(hits):
        count_board[hit['_source']['board']].append(hit)

    board_info = ', '.join(
        [f'{key}({len(value)})' for key, value in count_board.items()])

    message = f'共有 {len(hits)} 筆 {keyword} 結果, {board_info}\n'
    for board, infos in count_board.items():
        index = 1
        meta = f'==={board}'
        message += meta+'\n'
        for info in infos:
            category = info['_source'].get('category', '')
            if category == None or category == 'None':
                category = ''

            title = info['_source'].get('title', '')
            time = info['_source'].get('time', '')
            is_reply = info['_source'].get('is_reply', False)
            message += f"{index})"
            if is_reply:
                message += f" Re:"
            if category:
                message += f" [{category}]"

            message += f" {title}\n"

            message += f"發文時間: {time}\n"
            message += f"{info['_source']['url']}\n"
            index += 1
    message += f'--\n'
    return message


def find(index, message):
    def es(message):
        Es.es_search_patterns[0]['match_phrase']['content']['query'] = message
        result = Es.find(index=index, keyword=message, patterns=Es.es_search_patterns, filters=Es.es_search_patterns)
        return format_find_message(message, result)

    def cache(message):
        return (False, {})

    try:
        exists, result = cache(message)
        if not exists:
            result = es(message)
    except:
        logger.error(f'搜尋 {message} 失敗', exc_info=True)
        return None

    return result


