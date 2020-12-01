import redis
import os
from collections import defaultdict

GLOBAL_KEYWORD_TTL = 60*60*24*5
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

def add_global_keyword(keyword, last_user_id):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_global_keyword_ttl(r, keyword)
    r.set(f'keyword:{keyword}', last_user_id)

def get_global_keyword(keyword):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_global_keyword_ttl(r, keyword)
    return r.get(f'keyword:{keyword}')

def refresh_global_keyword_ttl(r, keyword):
    r.expire(f'keyword:{keyword}', GLOBAL_KEYWORD_TTL)

def update_user_keywords(user_id, keywords):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_user_keywords_ttl(r, user_id)
    r.sadd(f'user_keywords:{user_id}', *keywords)

def get_user_keywords(user_id):
    r = redis.StrictRedis(connection_pool=pool)
    refresh_user_keywords_ttl(r, user_id)
    return list(r.smembers(f'user_keywords:{user_id}'))

def refresh_user_keywords_ttl(r, user_id):
    r.expire(f'user_keywords:{user_id}', USER_INFO_TTL)

def delete_user(user_id):
    r = redis.StrictRedis(connection_pool=pool)
    r.delete(f'user_info:{user_id}')
    r.delete(f'user_typing_keywords:{user_id}')
    r.delete(f'user_keywords:{user_id}')

def get_search_result(message):
    r = redis.StrictRedis(connection_pool=pool)
    return r.get(message)
