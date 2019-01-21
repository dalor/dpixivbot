from flask import Flask, request, render_template, redirect
from dtelbot import Bot, inputmedia as inmed, reply_markup as repl, inlinequeryresult as iqr
from arguments import default_arguments as all_params
from user import User
import re
import os
import json
from dpixivcore import DPixiv

BOT_ID = os.environ['BOT_ID']
PIX_LOGIN = os.environ['PIX_LOGIN']
PIX_PASSWORD = os.environ['PIX_PASSWORD']
PIX_SESSION = os.environ.get('PIX_SESSION')
PACK_OF_SIMILAR_POSTS = int(os.environ['PACK_OF_SIMILAR_POSTS'])
MAX_COUNT_POSTS = int(os.environ['MAX_COUNT_POSTS'])
BOTNAME = os.environ['BOTNAME']
LOGIN_URL = os.environ['LOGIN_URL']
INFO_TEXT = '''
You can get picture by:
/pic {id} OR /pic_{id}
Reply /pic to picture
Forward pictures with description from this bot
Send the url of picture from pixiv (in text also)
\nOther:
/file {id} OR /file_{id} - Sending file by ID
/helpingif - Cool type of help
/login - to connect your pixiv account
\nFor loggined users:
/settings
/recommends
/following
/bookmarks
\nFor inline enter:
ID
URL of picture from pixiv (in text also)
\nHave a nice day :-)
'''
DATABASE = os.environ['DATABASE_URL']

GIF_HELP = [
    {'name': 'Base usage', 'file_id': 'CgADAgAD2gIAAhFWKUrF2QABsAOBqoMC'}, 
    {'name': 'Load similar pictures', 'file_id': 'CgADAgAD2QIAAhFWKUokVmThHkRdogI'},
    {'name': 'Navigation and sharing', 'file_id': 'CgADAgAD2AIAAhFWKUocJxto68RDiAI'}
    ]

assert PACK_OF_SIMILAR_POSTS <= 10

app = Flask(__name__)
b = Bot(BOT_ID)
pix = User(PIX_LOGIN, PIX_PASSWORD, PIX_SESSION)

dpix = DPixiv(b, pix, DATABASE, BOTNAME, PACK_OF_SIMILAR_POSTS, MAX_COUNT_POSTS)

@b.inline_query('([0-9]+)_?([0-9]*)')
def picture_id__(a):
    dpix.answer_inline_picture(a)

@b.inline_query('https\:\/\/www\.pixiv\.net\/member\_illust\.php\?.*illust\_id\=([0-9]+)()')
def picture_id_url__(a):
    dpix.answer_inline_picture(a)

@b.channel_post('/?pic[ _]?([0-9]+)_?([0-9]*)')
def channel_pic(a):
    dpix.send_to_channel(a)

@b.message('/?pic[ _]?([0-9]*)_?([0-9]*)')
def pic_(a):
    dpix.pic_command(a)

@b.message('.*https\:\/\/www\.pixiv\.net\/member\_illust\.php\?.*illust\_id\=([0-9]+)()')
def pic__(a):
    dpix.send_by_id(a)
    
@b.message('/start token_([0-9a-z\-]+)')
def start_token(a):
    dpix.connect_user_to_id(a)

@b.message('/following[ _]?([0-9]*)')
def ufollowing(a):
    dpix.user_following(a)
    
@b.message('/recommends')
def urecommender(a):
    dpix.user_recommender(a)
    
@b.message('/bookmarks[ _]?([0-9]*)')
def ubookmarks(a):
    dpix.user_bookmarks(a)

@b.message('/start ?([0-9]*)_?([0-9]*)')
def start(a):
    if not dpix.send_by_id(a):
        help_in_gif(a)

def reply_markup_for_gifhelp(id_=None):
    return [[repl.inlinekeyboardbutton(GIF_HELP[i]['name'], callback_data='help {}'.format(i))] for i in range(len(GIF_HELP)) if i != id_]

@b.message('/helpingif')
def help_in_gif(a):
    id_ = 0
    a.animation(GIF_HELP[id_]['file_id'], caption=GIF_HELP[id_]['name'],
        reply_markup=repl.inlinekeyboardmarkup(reply_markup_for_gifhelp(id_))).send()

@b.message('/help')
def help(a):
    a.msg(INFO_TEXT).send()

@b.message('/login')
def login_url(a):
    a.msg('Use this url to log in your pixiv account', 
        reply_markup=repl.inlinekeyboardmarkup([[repl.inlinekeyboardbutton('Log in', url=LOGIN_URL)]])).send()

@b.message('/settings')
def default_settings(a):
    dpix.change_default_settings(a)

@b.message('/file[ _]([0-9]+)_?p?([0-9]*)')
def file(a):
    dpix.send_file_by_id(a)

@b.callback_query('show {}'.format(all_params))
def show_more(a):
    dpix.make_show_or_hide(a, 1)

@b.callback_query('hide {}'.format(all_params))
def hide_more(a):
    dpix.make_show_or_hide(a, 0)
    
@b.callback_query('count_plus {}'.format(all_params))
def count_plus(a):
    dpix.count_plus_or_minus(a, 1)
    
@b.callback_query('count_minus {}'.format(all_params))
def count_minus(a):
    dpix.count_plus_or_minus(a, -1)
 
@b.callback_query('opics {}'.format(all_params))
def opics(a):
    dpix.only_pics_or_not(a)

@b.callback_query('group {}'.format(all_params))
def group(a):
    dpix.by_one_or_not(a)

@b.callback_query('next {}'.format(all_params))
def next_pic(a):
    dpix.turn_right_or_left(a, 1)
    
@b.callback_query('prev {}'.format(all_params))
def prev_pic(a):
    dpix.turn_right_or_left(a, -1)

@b.callback_query('similar {}'.format(all_params))
def call_sim(a):
    dpix.send_similar(a)

@b.callback_query('file')
def ffile(a):
    dpix.send_file_by_tag(a)
    
@b.callback_query('default_minus')
def default_minus(a):
    dpix.default_plus_or_minus(a, -1)

@b.callback_query('default_plus')
def default_plus(a):
    dpix.default_plus_or_minus(a, 1)
    
@b.callback_query('default_opics')
def default_opics(a):
    dpix.default_only_pics(a)
    
@b.callback_query('default_group')
def default_group(a):
    dpix.default_by_one(a)
    
@b.callback_query('help ([0-9]+)')
def spec_help(a):
    id_ = int(a.args[1])
    help_ = GIF_HELP[id_]
    b.editmedia(
            json.dumps(inmed.animation(help_['file_id'], caption=help_['name'])),
            chat_id=a.data['message']['chat']['id'],
            message_id=a.data['message']['message_id'],
            reply_markup=repl.inlinekeyboardmarkup(reply_markup_for_gifhelp(id_))
        ).send()

@b.message(True)
def check_tag_in_mess(a):
    dpix.send_by_tag(a.data)

@b.channel_post(True)
def check_tag_in_post(a):
    dpix.send_to_channel(a, by_tag=True)

@app.route('/')
def index_login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def logn_form():
    token = dpix.reg_temp_token(request.form.get('login'), request.form.get('password'))
    if token:
        return redirect('https://t.me/{}?start=token_{}'.format(BOTNAME, token))
    else:
        return redirect('/')

@app.route('/this_is_hook', methods=['POST']) #Telegram should be connected to this hook
def webhook():
    b.check(request.get_json())
    return 'ok', 200

if __name__ == '__main__':
    app.run()

