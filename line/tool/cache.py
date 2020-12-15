import redis
import os
from collections import defaultdict

USER_INFO_TTL = 60*60*24*7
USER_TYPING_KETWORDS_TTL = 60*60

pool = redis.ConnectionPool.from_url(os.getenv('REDIS_URL'), decode_responses=True)


def get_user_info(user_id):
    '''
    {state, user_id}
    '''
    r = redis.StrictRedis(connection_pool=pool)
    user_info = r.hgetall(f'user_info:{user_id}')
    refresh_user_info_ttl(r, user_id)
    return user_info

def update_user_info(user_id, user_info):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_user_info_ttl(r, user_id)
    r.hset(f'user_info:{user_id}', mapping=user_info)

def update_state(user_id, new_state):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_user_info_ttl(r, user_id)
    r.hset(f'user_info:{user_id}', 'state', new_state)

def refresh_user_info_ttl(r, user_id):
    r.expire(f'user_info:{user_id}', USER_INFO_TTL)

def add_tmp_keyword(user_id, keyword):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_tmp_keywords_ttl(r, user_id)
    r.sadd(f'user_typing_keywords:{user_id}', keyword)

def delete_tmp_keywords(user_id, keywords):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_tmp_keywords_ttl(r, user_id)
    r.srem(f'user_typing_keywords:{user_id}', *keywords)

def get_tmp_keywords(user_id):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_tmp_keywords_ttl(r, user_id)
    return list(r.smembers(f'user_typing_keywords:{user_id}'))

def refresh_tmp_keywords_ttl(r, user_id):
    r.expire(f'user_typing_keywords:{user_id}', USER_TYPING_KETWORDS_TTL)

def get_total_of_global_keyword():
    r = redis.StrictRedis(connection_pool=pool)
    return r.zcard(f'keyword:subcount')

def get_global_keyword(keyword):
    """
    return 關鍵字目前有有多少人訂閱
    """
    r = redis.StrictRedis(connection_pool=pool)
    return r.zscore(f'keyword:subcount', keyword)

def sub_global_keywords(user_id, *, keywords):
    r = redis.StrictRedis(connection_pool=pool)
    ks = set(keywords) - set(get_user_keywords(user_id))
    for k in ks:
        r.zincrby(f'keyword:subcount', k, 1)

def init_global_keywords(keyword_counts):
    r = redis.StrictRedis(connection_pool=pool)
    r.delete(f'keyword:subcount')
    for key, count in keyword_counts.items():
        r.zincrby(f'keyword:subcount', key, count)

def unsub_global_keywords(user_id, *, keywords):
    r = redis.StrictRedis(connection_pool=pool)
    ks = set(keywords) & set(get_user_keywords(user_id))
    for k in ks:
        if get_global_keyword(k) == 1:
            r.zrem(f'keyword:subcount', k)
        else:
            r.zincrby(f'keyword:subcount', k, -1)

def update_user_keywords(user_id, keywords):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_user_keywords_ttl(r, user_id)

    r.sadd(f'user_keywords:{user_id}', *keywords)
    sub_global_keywords(user_id, keywords=keywords)

def get_user_keywords(user_id):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_user_keywords_ttl(r, user_id)
    return list(r.smembers(f'user_keywords:{user_id}'))

def delete_user_keywords(user_id, keywords):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_tmp_keywords_ttl(r, user_id)
    unsub_global_keywords(user_id, keywords=keywords)
    r.srem(f'user_keywords:{user_id}', *keywords)

def refresh_user_keywords_ttl(r, user_id):
    r.expire(f'user_keywords:{user_id}', USER_INFO_TTL)

def delete_user(user_id):
    r = redis.StrictRedis(connection_pool=pool)
    unsub_global_keywords(user_id, keywords=get_user_keywords(user_id))
    r.delete(f'user_keywords:{user_id}')
    r.delete(f'user_info:{user_id}')
    r.delete(f'user_typing_keywords:{user_id}')
