import redis
import os
from collections import defaultdict

KEYWORD_TMP = defaultdict(list)
pool = redis.ConnectionPool.from_url(os.getenv('REDIS_URL'), decode_responses=True)

def get_user_info(user_id):
    '''
    {state, follow_date, user_id}
    '''
    r = redis.StrictRedis(connection_pool=pool)
    return r.hgetall(f'user_info:{user_id}')

def update_user_info(user_id, user_info):
    r = redis.StrictRedis(connection_pool=pool)
    r.hset(f'user_info:{user_id}', mapping=user_info)

def update_state(user_id, new_state):
    r = redis.StrictRedis(connection_pool=pool)
    return r.hset(f'user_info:{user_id}', 'state', new_state)

def add_tmp_keyword(user_id, keyword):
    r = redis.StrictRedis(connection_pool=pool)
    return r.sadd(f'user_typing_keywords:{user_id}', keyword)

def delete_tmp_keywords(user_id, keywords):
    r = redis.StrictRedis(connection_pool=pool)
    return r.srem(f'user_typing_keywords:{user_id}', *keywords)

def get_tmp_keywords(user_id):
    r = redis.StrictRedis(connection_pool=pool)
    return list(r.smembers(f'user_typing_keywords:{user_id}'))

def add_global_keyword(keyword, last_user_id):
    r = redis.StrictRedis(connection_pool=pool)
    return r.set('keyword:{keyword}', last_user_id, ex=60*60*24*5, keepttl=True)

def get_global_keyword(keyword):
    r = redis.StrictRedis(connection_pool=pool)
    return r.get('keyword:{keyword}')

def update_user_keywords(user_id, keywords):
    r = redis.StrictRedis(connection_pool=pool)
    return r.sadd(f'user_keywords:{user_id}', *keywords)

def get_user_keywords(user_id):
    r = redis.StrictRedis(connection_pool=pool)
    return list(r.smembers(f'user_keywords:{user_id}'))

def delete_user(user_id):
    r = redis.StrictRedis(connection_pool=pool)
    r.delete(f'user_info:{user_id}')
    r.delete(f'user_typing_keywords:{user_id}')
    r.delete(f'user_keywords:{user_id}')

def get_search_result(message):
    r = redis.StrictRedis(connection_pool=pool)
    return r.get(message)
