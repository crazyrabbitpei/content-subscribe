import line.tool.cache as Cache

from line.models import Keyword, User
from django.utils.translation import gettext_lazy as _
import logging, sys
from collections import defaultdict
logger = logging.getLogger(__name__)

# TODO: 取消訂閱

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
    exist_keys = []
    success_keys = []
    wait_to_be_subscribed = []
    err_msg = None
    tmp_keys = get_tmp(user_id)
    try:
        wait_to_be_subscribed, has_been_subscribed = update_keywords(user_id, tmp_keys)
        success_keys = connect_keywords_to_user(user_id, wait_to_be_subscribed)
        exist_keys = [key for key in has_been_subscribed]
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'關鍵字加入失敗', exc_info=True)
        err_msg = _(f'關鍵字加入失敗，請重新操作')
        return False, success_keys, exist_keys, err_msg

    delete_tmp(user_id, tmp_keys)
    return True, success_keys, exist_keys, err_msg


def unsubscribe(user_id):
    success_keys = []
    err_msg = None
    try:
        pass
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'關鍵字取消訂閱失敗', exc_info=True)
        err_msg = _(f'關鍵字取消訂閱失敗，請重新操作')
        return False, success_keys, err_msg

    return True, success_keys, err_msg

def update_keywords(user_id, keywords, to_rds=True, to_cache=True):
    def rds(user_id, keywords):
        logger.info(f'{user_id} update keywords to rds')

        user = User.objects.get(pk=user_id)

        key_objects = []
        wait_to_be_subscribed = []
        has_been_subscribed = []
        for keyword in keywords:
            if not exists(keyword)[0]:
                key_objects.append(Keyword(keyword=keyword))
            elif not is_subscribed(user, keyword):
                wait_to_be_subscribed.append(Keyword.objects.get(keyword=keyword))
            else:
                has_been_subscribed.append(keyword)
        wait_to_be_subscribed.extend(Keyword.objects.bulk_create(key_objects)  )# 關鍵字已新增到db但是尚未與user做連結
        return wait_to_be_subscribed, has_been_subscribed

    def cache(user_id, keywords):
        logger.info(f'{user_id} update keywords to cache')

        for keyword in keywords:
            if not exists(keyword)[1]:
                Cache.add_global_keyword(keyword, user_id)

    if len(keywords) == 0:
        return [], []

    if to_rds:
        wait_to_be_subscribed, has_been_subscribed = rds(user_id, keywords)
    if to_cache:
        cache(user_id, keywords)

    return wait_to_be_subscribed, has_been_subscribed


def connect_keywords_to_user(user_id, wait_to_be_subscribed, to_rds=True, to_cache=True):
    def rds(user_id, wait_to_be_subscribed):
        logger.info(f'{user_id} connect keywords to rds')

        user = User.objects.get(pk=user_id)
        user.keyword_set.add(*wait_to_be_subscribed)

    def cache(user_id, keys):
        logger.info(f'{user_id} connect keywords to cache')
        Cache.update_user_keywords(user_id, keys)

    if len(wait_to_be_subscribed) == 0:
        return []

    keys = [key.keyword for key in wait_to_be_subscribed]

    if to_rds:
        rds(user_id, wait_to_be_subscribed)
    if to_cache:
        cache(user_id, keys)

    return keys

def exists(keyword):
    def rds(keyword):
        return Keyword.objects.filter(keyword=keyword).exists()
    def cache(keyword):
        return Cache.get_global_keyword(keyword)

    return (rds(keyword), cache(keyword))

def is_subscribed(user, keyword):
    return user.keyword_set.filter(keyword=keyword).exists()


def get_subscribed(user_id):
    def rds(user_id):
        logger.info(f'Get {user_id} keywords from rds')
        user = User.objects.get(pk=user_id)
        return [key.keyword for key in user.keyword_set.all()]

    def cache(user_id):
        logger.info(f'Get {user_id} keywords from cache')
        return Cache.get_user_keywords(user_id)

    def update_cache(user_id, subscribed=None):
        if not subscribed:
            return
        logger.info(f'Update {user_id} keywords to cache')
        Cache.update_user_keywords(user_id, subscribed)

    subscribed = cache(user_id)
    if not subscribed:
        subscribed = rds(user_id)
        update_cache(user_id, subscribed)

    return subscribed


def delete_keywords(user_id, keywords):
    def rds(user_id, keywords):
        logger.info(f'Delete {user_id} keywords from rds')
        user = User.objects.get(pk=user_id)
        key_objects = [user.keyword_set.get(keyword=keyword) for keyword in keywords]
        user.keyword_set.remove(*key_objects)
        return [key.keyword for key in key_objects]

    def cache(user_id, keywords):
        logger.info(f'Delete {user_id} keywords from cache')
        Cache.delete_user_keywords(user_id, keywords)

    deleted_keys = rds(user_id, keywords)
    cache(user_id, keywords)
    return deleted_keys
