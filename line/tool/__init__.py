import redis

import line.tool.user as LineUser
import line.tool.state as UserState
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
    def update_user_state(user, new_state):
        return LineUser.update_state(user, new_state)

    logger.info(
        f"User {user['user_id']} action, current state: {user['state']}, mtype: {mtype}, message: {message}")
    result = {
        'ok': False,
        'msg': None,
        'err_msg': None,
    }

    handler = COMMAND_STATES.get(user['state'], None)
    if handler:
        new_state = handler(user['user_id'], result, mtype, message)
    else:
        logger.error(f"尚未定義的 {user['user_id']} state: {new_state}")
        result['err_msg'] = _(f'服務好像出了點問題QQ')
        return result

    if new_state not in COMMAND_STATES:
        logger.error(f'新的state尚未定義，故無法更新 {user["user_id"]} state: {new_state}')
        result['err_msg'] = _(f'服務好像出了點問題QQ')
        return result

    try:
        update_user_state(user['user_id'], new_state)
    except:
        logger.error(f'無法更新 {user["user_id"]} state', exc_info=True)
        result['err_msg'] = _(f'服務好像出了點問題QQ')
        result['ok'] = False

    return result


def get_user_info(user_id):
    return LineUser.info(user_id)

