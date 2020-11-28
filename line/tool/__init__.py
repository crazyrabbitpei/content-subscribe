import line.tool.user_info as UserInfo
import line.tool.user_states as UserState
from elasticsearch import Elasticsearch

from django.utils.translation import gettext_lazy as _

import sys, os
import logging
from collections import defaultdict

from line.models import Keyword, User

logger = logging.getLogger(__name__)

COMMAND_STATES = {
    '0': UserState.action_free,
    '1': UserState.action_subscribing,
    '2': UserState.action_confirming,
}

def action(user, /, *, mtype, message=None):
    logger.info(
        f'User action, current state: {user.state}, mtype: {mtype}, message: {message}')
    result = {
        'ok': False,
        'msg': None,
        'err_msg': None,
    }

    handler = COMMAND_STATES.get(user.state, None)
    if handler:
        new_state = handler(user, result, mtype, message)
    else:
        logger.error(f'尚未定義的user state: {user.state}')
        result['err_msg'] = _(f'服務好像出了點問題QQ')
        return result

    if new_state not in COMMAND_STATES:
        logger.error(f'新的state尚未定義，故無法更新user state: {new_state}')
        result['err_msg'] = _(f'服務好像出了點問題QQ')
        return result

    try:
        update_user_state(user, new_state)
    except:
        logger.error('無法更新', exc_info=True)

    return result

# TODO: update to cache
def update_user_state(user, new_state):
    user.state = new_state
    try:
        user.save()
    except:
        raise

def get_user_info(user_id):
    return UserInfo.from_cache(user_id) or UserInfo.from_rds(user_id)
