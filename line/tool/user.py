import line.tool.cache as Cache

import sys
from line.models import Keyword, User

from line.models import User, Keyword

import logging
logger = logging.getLogger(__name__)


def create(user_id):
    def rds(user_id):
        logger.info(f'Create user {user_id} to rds')
        User.objects.create(pk=user_id)

    try:
        rds(user_id)
    except:
        raise

def delete(user_id):
    def rds(user_id):
        logger.info(f'Delete user {user_id} from rds')
        user = User.objects.get(pk=user_id)
        user.delete()

    def cache(user_id):
        logger.info(f'Delete user {user_id} from cache')
        Cache.delete_user(user_id)

    try:
        cache(user_id)
        rds(user_id)
    except:
        raise


def update_state(user_id, new_state):
    # def rds(user, new_state):
    #     user = User.objects.get(pk=user["user_id"])
    #     user.state = new_state
    #     user.save()

    def cache(user_id, new_state):
        logger.info(f'Update {user_id} state to cache')
        Cache.update_state(user_id, new_state)

    try:
        #rds(user, new_state)
        cache(user_id, new_state)
    except:
        raise

def info(user_id):
    def rds(user_id):
        logger.info(f'Get {user_id} info from rds')
        user = User.objects.get(pk=user_id)
        return {
            'user_id': user.user_id,
            'state': user.state,
        }

    def cache(user_id):
        logger.info(f'Get {user_id} info from cache')
        return Cache.get_user_info(user_id)

    def update_cache(user_id, user_info):
        logger.info(f'Update {user_id} info to cache')
        Cache.update_user_info(user_id, user_info)

    try:
        user_info = cache(user_id)
        if not user_info:
            user_info = rds(user_id)
            update_cache(user_id, user_info)
    except:
        raise

    return user_info
