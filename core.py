from flask import Flask, request
from dtelbot import Bot, inputmedia as inmed, reply_markup as repl, inlinequeryresult as iqr
import json
from dpixiv import DPixivIllusts
import re

app = Flask(__name__)

b = Bot('636422131:AAG3nwuiN60xbOwpBR4V6jl031czOKMs5Tc')

pix = DPixivIllusts('mupagosad@idx4.com', 'mupagosad')

PACK_OF_SIMILAR_POSTS = 5 #<= 10

MAX_COUNT_POSTS = 500

assert PACK_OF_SIMILAR_POSTS <= 10

change_to_ = re.compile('[\.\-\/\!\★\・\☆\(\)]')

pixiv_tags = lambda pic: ['#{}{}'.format(change_to_.sub('_', t['tag']), '({})'.format(t['translation']['en']) if 'translation' in t else '') for t in pic['tags']['tags']]

def min_split(list_, count):
    new_list = [list_[sp-count:sp] for sp in range(count, len(list_)+1, count)]
    if len(list_) % count: new_list.append(list_[-(len(list_) % count):])
    return new_list

def usual_reply(pic_id, page=0, count=PACK_OF_SIMILAR_POSTS, only_pics=0, by_one=0, show=True):
    return [[repl.inlinekeyboardbutton('On pixiv', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(pic_id)),
            repl.inlinekeyboardbutton('Download file', callback_data='file {}'.format(pic_id)),
            repl.inlinekeyboardbutton('Share', switch_inline_query=pic_id),
            repl.inlinekeyboardbutton('Show more', callback_data='show i{} p{} c{} o{} b{}'.format(pic_id, page, count, only_pics, by_one)) if show else repl.inlinekeyboardbutton('Hide more', callback_data='hide i{} p{} c{} o{} b{}'.format(pic_id, page, count, only_pics, by_one))]]

def more_reply(pic_id, page=0, count=PACK_OF_SIMILAR_POSTS, only_pics=0, by_one=0):
    usual = usual_reply(pic_id, page, count, only_pics, by_one, False)
    params = 'i{} p{} c{} o{} b{}'.format(pic_id, page, count, only_pics, by_one)
    usual.append([repl.inlinekeyboardbutton('➖', callback_data='count_minus {}'.format(params)),
                  repl.inlinekeyboardbutton('{} ⬇️'.format(count), callback_data='similar {}'.format(params)),
                  repl.inlinekeyboardbutton('➕', callback_data='count_plus {}'.format(params)),
                  repl.inlinekeyboardbutton('{}🖼'.format('✅' if int(only_pics) else ''), callback_data='opics {}'.format(params)),
                  repl.inlinekeyboardbutton('{}📂'.format('' if int(by_one) else '✅'), callback_data='group {}'.format(params))])
    return usual

def prepare_picture(pic_id, pix_info, is_desc):
    pic = pix_info['preload']['illust'][pic_id]
    if is_desc:
        tags = pixiv_tags(pic)
        tags.append('#pic_{}'.format(pic_id))
        description = '{}\n<b>Tags:</b> {}'.format(pic['title'], ', '.join(tags))
    else:
        description = ''
    pic_url = pic['urls']['original']
    return pic_url, description

def send_picture(pic_id, chat_id, reply_to_message_id=None, is_desc=True):
    pic_url, description = prepare_picture(pic_id, pix.info(pic_id), is_desc)
    reply_markup = repl.inlinekeyboardmarkup(usual_reply(pic_id))
    result = b.photo(pic_url, chat_id=chat_id, caption=description, parse_mode='HTML', reply_to_message_id=reply_to_message_id if reply_to_message_id else '', reply_markup=reply_markup).send()
    if not result['ok']:
        b.msg('[The picture on pixiv or download it via button]\n{}'.format(description), chat_id=chat_id, parse_mode='HTML', reply_to_message_id=reply_to_message_id if reply_to_message_id else '', reply_markup=reply_markup).send()

def check_inline_error(func):
    def new_func(a):
        try:
            func(a)
        except:
            a.answer([iqr(type='article', id=1, title='Error!!!', input_message_content={'message_text': 'Error!!!'}, reply_markup = {'inline_keyboard': [[repl.inlinekeyboardbutton('On pixiv', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + a.args[1])]]})]).send()
    return new_func

def check_message_error(func):
    def new_func(a):
        try:
            func(a)
        except:
            a.msg('Error!!! Write to creator', reply_markup=repl.inlinekeyboardmarkup([[repl.inlinekeyboardbutton('On pixiv', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + a.args[1])]])).send()
    return new_func
    
def check_callback_error(func):
    def new_func(a):
        try:
            func(a)
        except:
            a.answer(text='Error!!! Write to creator').send()
    return new_func

@b.inline_query('([0-9]+)')
@check_inline_error
def picture_id__(a):
    pix_info = pix.info(a.args[1])
    if pix_info:
        pic = pix_info['preload']['illust'][a.args[1]]
        reply_markup = {'inline_keyboard': [[repl.inlinekeyboardbutton('On pixiv', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + a.args[1]), repl.inlinekeyboardbutton('More', url='t.me/dpixivbot?start=' + a.args[1]), repl.inlinekeyboardbutton('Share', switch_inline_query=a.args[1])]]}
        a.answer([iqr(type='photo', id=0, photo_url=pic['urls']['original'], thumb_url=pic['urls']['thumb'], reply_markup=reply_markup), iqr(type='article', id=1, title=pic['title'], input_message_content={'message_text': '<a href="{}">{}</a>\n<b>Tags:</b> {}'.format(pic['urls']['original'], pic['title'], ', '.join(pixiv_tags(pic))), 'parse_mode': 'HTML'}, reply_markup=reply_markup)]).send()

@b.inline_query('https\:\/\/www\.pixiv\.net\/member\_illust\.php\?.*illust\_id\=([0-9]+)')
def picture_id_url__(a):
    picture_id__(a)

@b.channel_post('/pic[ _]([0-9]+)')
@b.message('/pic[ _]([0-9]+)')
@check_message_error
def pic_(a):
    send_picture(a.args[1], a.data['chat']['id'])

@b.channel_post('.*https\:\/\/www\.pixiv\.net\/member\_illust\.php\?.*illust\_id\=([0-9]+)()')
@b.message('.*https\:\/\/www\.pixiv\.net\/member\_illust\.php\?.*illust\_id\=([0-9]+)()')
def pic__(a):
    pic_(a)

@b.message('/start ?([0-9]*)')
def start(a):
    if a.args[1]:
        pic_(a)
    else:
        a.msg('/pic {picure_id}\nOr enter pixiv url').send()

@b.channel_post('/file[ _]([0-9]+)')
@b.message('/file[ _]([0-9]+)')
@check_message_error
def file(a):
    pic = pix.info(a.args[1])['preload']['illust'][a.args[1]]
    a.document(pic['urls']['original']).send()

all_params = 'i([0-9]+) p([0-9]+) c([0-9]+) o([01]) b([01])'

def edit_reply(a, reply):
    b.editreplymarkup(chat_id=a.data['message']['chat']['id'], message_id=a.data['message']['message_id'], reply_markup=repl.inlinekeyboardmarkup(reply)).send()

def get_args(a, page=None, count=None, only_pics=None, by_one=None):
    return (a.args[1], page if page else a.args[2], count if count else a.args[3], a.args[4] if only_pics is None else only_pics, a.args[5] if by_one is None else by_one)

@b.callback_query('show {}'.format(all_params))
@check_callback_error
def show_more(a):
    reply = more_reply(*get_args(a))
    edit_reply(a, reply)
    a.answer(text='Show').send()

@b.callback_query('hide {}'.format(all_params))
@check_callback_error
def hide_more(a):
    reply = usual_reply(*get_args(a))
    edit_reply(a, reply)
    a.answer(text='Hide').send()
    
@b.callback_query('count_plus {}'.format(all_params))
@check_callback_error
def count_plus(a):
    count = int(a.args[3]) + PACK_OF_SIMILAR_POSTS
    if count > MAX_COUNT_POSTS:
        a.answer(text='This is limit').send()
    else:
        reply = more_reply(*get_args(a, count=count))
        edit_reply(a, reply)
        a.answer(text='{} + {} = {}'.format(a.args[3], PACK_OF_SIMILAR_POSTS, count)).send()
    
@b.callback_query('count_minus {}'.format(all_params))
@check_callback_error
def count_minus(a):
    count = int(a.args[3]) - PACK_OF_SIMILAR_POSTS
    if count < 0:
        a.answer(text='This is limit').send()
    else:
        reply = more_reply(*get_args(a, count=count))
        edit_reply(a, reply)
        a.answer(text='{} - {} = {}'.format(a.args[3], PACK_OF_SIMILAR_POSTS, count)).send()

@b.callback_query('opics {}'.format(all_params))
@check_callback_error
def opics(a):
    if int(a.args[4]):
        edit_reply(a, more_reply(*get_args(a, only_pics=0)))
        a.answer(text='Will send without any description')
    else:
        edit_reply(a, more_reply(*get_args(a, only_pics=1)))
        a.answer(text='Will send with title and text')

@b.callback_query('group {}'.format(all_params))
@check_callback_error
def group(a):
    if int(a.args[5]):
        edit_reply(a, more_reply(*get_args(a, by_one=0)))
        a.answer(text='Will send in group')
    else:
        edit_reply(a, more_reply(*get_args(a, by_one=1)))
        a.answer(text='Will send by one')

@b.callback_query('similar {}'.format(all_params))
@check_callback_error
def call_sim(a):
    page = int(a.args[2])
    count = int(a.args[3])
    limit = page * PACK_OF_SIMILAR_POSTS + count
    if limit > MAX_COUNT_POSTS:
        a.answer(text='This is limit').send()
    else:
        args = get_args(a, page=limit // PACK_OF_SIMILAR_POSTS)
        edit_reply(a, more_reply(*args))
        sim_ids = pix.similar(args[0], limit=limit)[limit - count:]
        a.answer(text='Loading {} similar pictures from {} to {}'.format(count, limit + 1 - count, limit)).send()
        is_desc = not int(args[3])
        if int(args[4]):
            for sim_id in sim_ids:
                send_picture(sim_id, a.data['message']['chat']['id'], a.data['message']['message_id'], is_desc)
        else:
            packs = min_split(sim_ids, PACK_OF_SIMILAR_POSTS)
            for pack in packs:
                all_info = pix.info_packs(pack)
                all_media = []
                for one in all_info:
                    pic_url, description = prepare_picture(one['id'], one['info'], is_desc)
                    all_media.append(inmed.photo(pic_url, caption=description, parse_mode='HTML'))
                result = b.media(all_media, chat_id=a.data['message']['chat']['id'], reply_to_message_id=a.data['message']['message_id']).send()
                if not result['ok']:
                    for sim_id in pack:
                        send_picture(sim_id, a.data['message']['chat']['id'], a.data['message']['message_id'], is_desc)

@b.callback_query('file ([0-9]+)')
@check_callback_error
def ffile(a):
    a.answer(text='Sending...').send()
    pic = pix.info(a.args[1])['preload']['illust'][a.args[1]]
    b.document(pic['urls']['original'], chat_id=a.data['message']['chat']['id'], reply_to_message_id=a.data['message']['message_id']).send()

@b.message(True)
def check_tag_in_mess(a):
    if 'caption_entities' in a.data:
        last_entiti = a.data['caption_entities'][-1]
        tag = a.data['caption'][last_entiti['offset']:last_entiti['offset'] + last_entiti['length']]
        check_tag = re.match('#pic_([0-9]+)', tag)
        if check_tag:
            send_picture(check_tag[1], a.data['chat']['id'])

@app.route('/this_is_hook', methods=['POST']) #Telegram should be connected to this hook
def webhook():
    b.check(request.get_json())
    return 'ok', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
