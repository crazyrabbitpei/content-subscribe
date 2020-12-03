import os
from elasticsearch import Elasticsearch
import logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

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


def find(*, source, keyword=None, patterns=None, filters=None):
    result = None
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
        logger.error('搜尋es失敗', exc_info=True)
        raise

    return result
