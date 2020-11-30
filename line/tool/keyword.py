import line.tool.cache as Cache

from line.models import Keyword, User
from django.utils.translation import gettext_lazy as _
import logging, sys
from collections import defaultdict
logger = logging.getLogger(__name__)


def add_tmp(user_id, keyword):
    return Cache.add_tmp_keyword(user_id, keyword)

def delete_tmp(user_id, tmp_keys=None, delete_keys=None, *, delete_all=False):
    if not delete_keys:
        return []

    deleted_keys = [key for key in delete_keys]
    if delete_all:
        deleted_keys = tmp_keys

    Cache.delete_tmp_keywords(user_id, deleted_keys)

    return deleted_keys

def get_tmp(user_id):
    return Cache.get_tmp_keywords(user_id)

def subscribe(user_id):
    exist_keys = []
    success_keys = []
    wait_to_be_subscribed = []
    err_msg = None
    try:
        wait_to_be_subscribed, has_been_subscribed = update_keywords(user_id, get_tmp(user_id))
        success_keys = connect_keywords_to_user(user_id, wait_to_be_subscribed)
        exist_keys = [key for key in has_been_subscribed]
    except:
        etype, value, tb = sys.exc_info()
        logger.error(f'關鍵字加入失敗', exc_info=True)
        err_msg = _(f'關鍵字加入失敗，請重新操作')
        return False, success_keys, exist_keys, err_msg

    delete_tmp(user_id, delete_all=True)
    return True, success_keys, exist_keys, err_msg


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

    try:
        if to_rds:
            wait_to_be_subscribed, has_been_subscribed = rds(user_id, keywords)
        if to_cache:
            cache(user_id, keywords)
    except:
        raise

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
    try:
        if to_rds:
            rds(user_id, wait_to_be_subscribed)
        if to_cache:
            cache(user_id, keys)
    except:
        raise

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
    return Cache.get_user_keywords(user_id)
