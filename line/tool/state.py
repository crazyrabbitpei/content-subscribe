import line.tool.cache as Cache
import line.tool.user as LineUser
import line.tool.keyword as Kw
import line.tool.line as Line
import line.tool.message as Message
import line.tool.pttcontent as Source
import line.tool.es as Es

from django.utils.translation import gettext_lazy as _

import logging, os
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

class State:
    @classmethod
    def action_free(cls, *, user_id, result, mtype, emoji_start_at=None, message=None, state='0'):
        if Line.is_only_emoji_or_sticker(mtype):
            state = '1'
            result['msg'] = '可以開始輸入關鍵字囉\n'
            result['msg'] += Message.format_subscribed_keywords(user_id)
            result['ok'] = True
        # 依照編號刪除現有訂閱清單中的關鍵字
        elif mtype == 'emoji_text' and emoji_start_at == 0:
            delete_keys = get_delete_keys(key_list=Kw.get_subscribed(user_id), delete_msg=message)
            deleted_keys = Kw.unsubscribe(user_id, keywords=delete_keys)
            if len(deleted_keys) > 0:
                result['msg'] = f'已移除關鍵字: {",".join(deleted_keys)}\n'
                result['msg'] += Message.format_subscribed_keywords(user_id)
                result['ok'] = True
            else:
                result['msg'] = '沒有任何關鍵字被移除\n'
                result['msg'] += Message.format_subscribed_keywords(user_id)
                result['ok'] = True

        elif Line.has_text(mtype):
            msg = Source.find(index=os.getenv('ES_INDEX'), message=message)
            result['msg'] = msg
            if not msg:
                result['msg'] = '搜尋好像出了點問題orz'

            result['ok'] = msg != None

        return state

    @classmethod
    def action_subscribing(cls, *, user_id, result, mtype, emoji_start_at=None, message=None, state='1'):
        if Line.is_only_emoji_or_sticker(mtype):
            if len(Kw.get_tmp(user_id)) > 0:
                state = '2'
                result['msg'] = Message.format_keyword_confirm_message(user_id)
            else:
                state = '0'
                result['msg'] = '已結束關鍵字輸入，若要重新開始訂閱請輸入一個emoji\n'
                result['msg'] += Message.format_subscribed_keywords(user_id)

            result['ok'] = True
        elif Line.has_text(mtype):
            Kw.add_tmp(user_id, message)
            result['msg'] = '繼續輸入下一筆，或是用一個emoji來結束關鍵字輸入'
            result['ok'] = True

        return state

    @classmethod
    def action_confirming(cls, *, user_id, result, mtype, emoji_start_at=None, message=None, state='2'):
        if Line.is_only_emoji_or_sticker(mtype):
            state = '0'
            ok, success_keys, exist_keys, err_msg = Kw.subscribe(user_id)
            result['ok'] = ok
            msg = ''
            if not ok:
                result['err_msg'] = err_msg
            elif len(success_keys) > 0:
                msg = f'成功訂閱關鍵字: {",".join(success_keys)}\n'
            else:
                msg = '沒有任何新的關鍵字被訂閱喔!\n'

            msg += Message.format_subscribed_keywords(user_id)

            result['msg'] = msg
        elif Line.has_text(mtype):
            tmp_keys = Kw.get_tmp(user_id)
            delete_keys = get_delete_keys(key_list=tmp_keys, delete_msg=message)
            deleted_keys = Kw.delete_tmp(user_id, delete_keys)
            if len(deleted_keys) == len(tmp_keys):
                state = '0'
                result['msg'] = '此次輸入的關鍵字已都移除，若要重新開始訂閱請輸入一個emoji\n'
                result['msg'] += Message.format_subscribed_keywords(user_id)

            elif len(deleted_keys) > 0:
                result['msg'] = f'已移除關鍵字: {",".join(deleted_keys)}\n'
                result['msg'] += Message.format_keyword_confirm_message(user_id)
            else:
                result['msg'] = '沒有任何關鍵字被移除\n'
                result['msg'] += Message.format_keyword_confirm_message(user_id)

            result['ok'] = True

        return state


COMMAND_STATES = {
    '0': State.action_free,
    '1': State.action_subscribing,
    '2': State.action_confirming,
}


def action(user, /, *, mtype, emoji_start_at=None, message=None):
    def update_user_state(user, new_state):
        return LineUser.update_state(user, new_state)
    if message:
        message = message.strip()
    logger.info(
        f"User {user['user_id']} action, current state: {user['state']}, mtype: {mtype}, message: {message}")
    result = {
        'ok': False,
        'msg': None,
        'err_msg': None,
    }

    handler = COMMAND_STATES.get(user['state'], None)
    if handler:
        new_state = handler(
            user_id=user['user_id'], result=result, mtype=mtype, emoji_start_at=emoji_start_at, message=message)
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


def get_delete_keys(*, key_list, delete_msg):
    return [key_list[int(n)-1] for n in delete_msg.split(' ') if n.isnumeric() and int(n) > 0 and int(n) <= len(key_list)]

