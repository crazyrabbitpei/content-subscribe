import os
from elasticsearch import Elasticsearch
import logging
import configparser

config = configparser.ConfigParser()
config.read(os.environ.get('SETTING', 'settings.ini'))

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

client = Elasticsearch(
    http_auth=(os.getenv('ES_USER'), os.getenv("ES_PASSWD")),
    hosts=os.getenv('ES_HOSTS').split(','),
    use_ssl=True,
    verify_cert=False,
    ssl_show_warn=False,
    port=int(os.getenv('ES_PORT')),
    timeout=int(config['REQUEST']['timeout']),
    max_retries=int(config['REQUEST']['max_retries']),
    retry_on_timeout=True
)
es_search_patterns = [
    {
        "match_phrase": {
            "content": {
                #"minimum_should_match": 3,  # 若operator為
                "query": ""
            }
        },
    }
]

es_search_filters = [
    #{"term":  {"is_reply": False}},
    {"range": {"time": {"gte": "now-14d"}}}
]


def find(*, index, keyword=None, patterns=None, filters=None):
    result = None

    try:
        result = client.search(index=index, body=gen_body(patterns=patterns, filters=filters))
    except:
        logger.error('搜尋es失敗', exc_info=True)
        raise

    return result


def gen_body(*, patterns, filters):
    return {
        "size": 20,
        "sort": [
            {
                "time": {
                    "order": "desc"
                }
            }
        ],
        "query": {
            "bool": {
                "must": patterns,
                "filter": filters
            }
        }
    }
