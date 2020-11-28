import line.tool.keyword as Kw
import line.tool.line as Line
import line.tool.message as Message
import line.tool.es as Es
import logging
logger = logging.getLogger(__name__)

def action_free(user, result, mtype, message=None, state='0'):

    if Line.is_emoji_or_sticker(mtype):
        state = '1'
        result['msg'] = '可以開始輸入關鍵字囉'
        result['ok'] = True
    elif mtype == 'text':
        Es.es_search_patterns[0]['match']['content']['query'] = message
        result['msg'] = Es.find(
            message, Es.es_search_patterns, Es.es_search_patterns)
        result['ok'] = True

    return state


def action_subscribing(user, result, mtype, message=None, state='1'):
    if Line.is_emoji_or_sticker(mtype):
        if len(Kw.KEYWORD_TMP[user.user_id]) > 0:
            state = '2'
            result['msg'] = Message.format_keyword_confirm_message(user)
        else:
            state = '0'
            result['msg'] = '已結束關鍵字輸入，若要重新開始訂閱請輸入一個emoji'
        result['ok'] = True
    elif mtype == 'text':
        Kw.KEYWORD_TMP[user.user_id].append(message)
        result['msg'] = '繼續輸入下一筆，或是用一個emoji來結束關鍵字輸入'
        result['ok'] = True

    return state


def action_confirming(user, result, mtype, message=None, state='2'):
    if Line.is_emoji_or_sticker(mtype):
        state = '0'
        ok, success_keys, exist_keys, err_msg = Kw.subscribe_keyword(user)
        result['ok'] = ok
        msg = ''
        if not ok:
            result['err_msg'] = err_msg
        elif len(success_keys) > 0:
            msg = f'成功訂閱關鍵字: {",".join(success_keys)}'

        if len(exist_keys) > 0:
            msg += f'\n已訂閱過的關鍵字: {",".join(exist_keys)}'

        result['msg'] = msg
        Kw.KEYWORD_TMP[user.user_id].clear()
    elif mtype == 'text':
        remove_all, remove_keys = Kw.remove_tmp_subscribing(user, message)
        if remove_all:
            state = '0'
            result['msg'] = '此次輸入的關鍵字已都移除，若要重新開始訂閱請輸入一個emoji'
        elif len(remove_keys) > 0:
            result['msg'] = f'已移除關鍵字: {",".join(remove_keys)}\n'
            result['msg'] += Message.format_keyword_confirm_message(user)
        else:
            result['msg'] = '沒有任何關鍵字被移除'
            result['msg'] += Message.format_keyword_confirm_message(user)

        result['ok'] = True

    return state
