import line.tool.cache as Cache

from line.models import Keyword, User
from django.utils.translation import gettext_lazy as _
import logging, sys, os
from collections import defaultdict, Counter
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

def get_tmp(user_id):
    return Cache.get_tmp_keywords(user_id)

def add_tmp(user_id, keyword):
    Cache.add_tmp_keyword(user_id, keyword)

def delete_tmp(user_id, keys=None):
    if not keys:
        return []

    deleted_keys = [key for key in keys]
    Cache.delete_tmp_keywords(user_id, deleted_keys)

    return deleted_keys

def subscribe(user_id):
    """
    訂閱cache中的關鍵字
    """
    exist_keywords = []
    success_keywords = []
    wait_to_be_subscribed = []
    err_msg = None
    tmp_keys = get_tmp(user_id)
    try:
        wait_to_be_subscribed, has_been_subscribed = get_subed_and_unsubed_keyword_list(user_id, tmp_keys)
        success_keywords = connect_keywords_to_user(user_id, wait_to_be_subscribed)
        exist_keywords = [key for key in has_been_subscribed]
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'關鍵字加入失敗', exc_info=True)
        err_msg = _(f'關鍵字加入失敗，請重新操作')
        return False, success_keywords, exist_keywords, err_msg

    delete_tmp(user_id, tmp_keys)
    return True, success_keywords, exist_keywords, err_msg

def unsubscribe(user_id, *, keywords):
    def rds(user_id, keywords):
        logger.info(f'Delete {user_id} keywords from rds')
        user = User.objects.get(pk=user_id)
        key_objects = [user.keyword_set.get(keyword=keyword) for keyword in keywords]
        user.keyword_set.remove(*key_objects)
        return [key.keyword for key in key_objects]

    def cache(user_id, keywords):
        logger.info(f'Delete {user_id} keywords from cache')
        Cache.delete_user_keywords(user_id, keywords)

    cache(user_id, keywords)
    deleted_keys = rds(user_id, keywords)

    return deleted_keys

def get_subed_and_unsubed_keyword_list(user_id, keywords, to_rds=True, to_cache=True):
    if len(keywords) == 0:
        return [], []

    key_objects = [] # 尚未在db的keyword
    wait_to_be_subscribed = [] # 有在db但尚未被該使用者訂閱
    has_been_subscribed = [] # 已在db且該使用者已訂閱
    for keyword in keywords:
        if not exists(user_id, keyword):
            key_objects.append(Keyword(keyword=keyword))
        elif not is_subscribed(user_id, keyword):
            wait_to_be_subscribed.append(Keyword.objects.get(keyword=keyword))
        else:
            has_been_subscribed.append(keyword)
    wait_to_be_subscribed.extend(Keyword.objects.bulk_create(key_objects))
    return wait_to_be_subscribed, has_been_subscribed

def connect_keywords_to_user(user_id, wait_to_be_subscribed, to_rds=True, to_cache=True):
    def rds(user_id, wait_to_be_subscribed):
        logger.info(f'{user_id} connect keywords to rds')

        user = User.objects.get(pk=user_id)
        user.keyword_set.add(*wait_to_be_subscribed)

    def cache(user_id, keywords):
        logger.info(f'{user_id} connect keywords to cache')
        Cache.update_user_keywords(user_id, keywords)

    if len(wait_to_be_subscribed) == 0:
        return []

    keywords = [keyword.keyword for keyword in wait_to_be_subscribed]

    if to_rds:
        rds(user_id, wait_to_be_subscribed)
    if to_cache:
        cache(user_id, keywords)

    return keywords

def exists(user_id, keyword):
    def rds(keyword):
        logger.info('Check whether keyword exists by rds')
        return Keyword.objects.filter(keyword=keyword).exists()

    def cache(keyword):
        logger.info('Check whether keyword exists by cache')
        return Cache.get_global_keyword(keyword)

    def update_cache(keyword):
        logger.info(f'Init global keywords to cache')
        keyword_counts = Counter([Keyword.objects.get(pk=i.keyword_id).keyword for i in Keyword.users.through.objects.all()])
        Cache.init_global_keywords(keyword_counts)

    e = cache(keyword)
    if not e:
        e = rds(keyword)
        if e:
            update_cache(keyword)

    return e

def is_subscribed(user_id, keyword):
    def rds(user_id, keyword):
        logger.info('Check whether keyword is subscribed by rds')
        user = User.objects.get(pk=user_id)
        return user.keyword_set.filter(keyword=keyword).exists()

    def cache(user_id, keyword):
        logger.info('Check whether keyword is subscribed by cache')
        return keyword in Cache.get_user_keywords(user_id)

    def update_cache(user_id, subscribed_keys):
        logger.info(f'Update {user_id} subscribed keywords to cache')
        Cache.update_user_keywords(user_id, subscribed_keys)
        return True

    is_s = cache(user_id, keyword)
    if not is_s:
        is_s = rds(user_id, keyword)
        if is_s:
            update_cache(user_id, subscribed_keys=[keyword])

    return is_s


def get_subscribed(user_id):
    def rds(user_id):
        logger.info(f'Get {user_id} keywords from rds')
        user = User.objects.get(pk=user_id)
        return [key.keyword for key in user.keyword_set.all()]

    def cache(user_id):
        logger.info(f'Get {user_id} keywords from cache')
        return Cache.get_user_keywords(user_id)

    def update_cache(user_id, subscribed_keys=None):
        if not subscribed_keys:
            return
        logger.info(f'Update {user_id} keywords to cache')
        Cache.update_user_keywords(user_id, subscribed_keys)

    subscribed_keys = cache(user_id)
    if not subscribed_keys:
        subscribed_keys = rds(user_id)
        update_cache(user_id, subscribed_keys)

    return subscribed_keys
