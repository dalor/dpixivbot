from flask import Flask, request
from dbot import Bot, inputmedia as inmed, reply_markup as repl, inlinequeryresult as iqr
import json
from dpixiv import DPixivIllusts
import re

app = Flask(__name__)

b = Bot('636422131:AAG3nwuiN60xbOwpBR4V6jl031czOKMs5Tc')

pix = DPixivIllusts('mupagosad@idx4.com', 'mupagosad')

PACK_OF_SIMILAR_POSTS = 10

change_to_ = re.compile('[\.\-\/]')

pixiv_tags = lambda pic: ['#{}{}'.format(change_to_.sub('_', t['tag']), '({})'.format(t['translation']['en']) if 'translation' in t else '') for t in pic['tags']['tags']]

def usual_reply(pic_id, sim_page=''):
    return [[repl.inlinekeyboardbutton('On pixiv', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(pic_id)),
            repl.inlinekeyboardbutton('Download file', callback_data='file {}'.format(pic_id)),
            repl.inlinekeyboardbutton('Similar pictures', callback_data='similar {} {}'.format(pic_id, sim_page)),
            repl.inlinekeyboardbutton('Share', switch_inline_query=pic_id)]]

def send_picture(pic_id, chat_id, reply_to_message_id=None):
    pic = pix.info(pic_id)['preload']['illust'][pic_id] 
    tags = pixiv_tags(pic)
    text = '<a href="{}">{}</a>\n<b>Tags:</b> {}'.format(pic['urls']['original'], pic['title'], ', '.join(tags))
    reply_markup = repl.inlinekeyboardmarkup(usual_reply(pic_id))
    if reply_to_message_id:
        b.msg(text, chat_id=chat_id, parse_mode='HTML', reply_to_message_id=reply_to_message_id, reply_markup=reply_markup).send()
    else:
        b.msg(text, chat_id=chat_id, parse_mode='HTML', reply_markup=reply_markup).send()

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
            a.msg('Error!!!', reply_markup=repl.inlinekeyboardmarkup([[repl.inlinekeyboardbutton('On pixiv', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + a.args[1])]])).send()
    return new_func
    
def check_callback_error(func):
    def new_func(a):
        try:
            func(a)
        except:
            a.answer(text='Error!!!').send()
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
        print(a.msg('/pic {picure_id}\nOr enter pixiv url').send())

@b.channel_post('/file[ _]([0-9]+)')
@b.message('/file[ _]([0-9]+)')
@check_message_error
def file(a):
    pic = pix.info(a.args[1])['preload']['illust'][a.args[1]]
    a.document(pic['urls']['original']).send()

@b.callback_query('similar ([0-9]+) ?([0-9]*)')
@check_callback_error
def call_sim(a):
    limit = (int(a.args[2]) + 1) * PACK_OF_SIMILAR_POSTS if a.args[2] else PACK_OF_SIMILAR_POSTS
    if limit > 500:
        a.answer(text='This is limit').send()
    else:
        b.editreplymarkup(chat_id=a.data['message']['chat']['id'], message_id=a.data['message']['message_id'], reply_markup=repl.inlinekeyboardmarkup(usual_reply(a.args[1], limit / PACK_OF_SIMILAR_POSTS))).send()
        a.answer(text='Loading {} similar pictures from {} to {}'.format(PACK_OF_SIMILAR_POSTS, limit + 1 - PACK_OF_SIMILAR_POSTS, limit)).send()
        sim_ids = pix.similar(a.args[1], limit=limit)[limit - PACK_OF_SIMILAR_POSTS:]
        for sim_id in sim_ids:
            send_picture(sim_id, a.data['message']['chat']['id'], a.data['message']['message_id'])

@b.callback_query('file ([0-9]+)')
@check_callback_error
def ffile(a):
    a.answer(text='Sending...').send()
    pic = pix.info(a.args[1])['preload']['illust'][a.args[1]]
    b.document(pic['urls']['original'], chat_id=a.data['message']['chat']['id'], reply_to_message_id=a.data['message']['message_id']).send()

@app.route('/this_is_hook', methods=['POST']) #Telegram should be connected to this hook
def webhook():
    b.check(request.get_json())
    return 'ok', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
