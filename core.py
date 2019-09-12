from flask import Flask, request, render_template, redirect, jsonify, send_file
from dtelbot import Bot
from dtelbot.inline import photo as iphoto, article as iarticle
from dtelbot.inline_keyboard import markup, button
from dtelbot.input_media import photo as imphoto, animation as imanimation
from arguments import default_arguments as all_params
from user import User
import re
import os
import json
from dpixivcore import DPixiv, check_pixiv_id
import requests
from io import BytesIO

BOT_ID = os.environ['BOT_ID']
PIX_LOGIN = os.environ['PIX_LOGIN']
PIX_PASSWORD = os.environ['PIX_PASSWORD']
PIX_SESSION = os.environ.get('PIX_SESSION')
PACK_OF_SIMILAR_POSTS = int(os.environ['PACK_OF_SIMILAR_POSTS'])
MAX_COUNT_POSTS = int(os.environ['MAX_COUNT_POSTS'])
BOTNAME = os.environ['BOTNAME']
LOGIN_URL = os.environ['LOGIN_URL']
DATABASE = os.environ['DATABASE_URL']

INFO_TEXT = '''
<b>You can get picture by:</b>
/pic <i>id</i> OR /pic_<i>id</i>
Reply /pic to picture
Forward pictures with description from this bot
Send the url of picture from pixiv
Share from PixivApp to bot
\n<b>Other:</b>
/file <i>id</i> OR /file_<i>id</i> - Sending picture as document by ID
/helpingif - Cool type of help
Reply /instant to get Instant View
/login - To connect your pixiv account and use next commands:
Reply /tag <i>new_tag</i> OR /t <i>new_tag</i> to add <i>new_tag</i> for picture if it possible
/settings - Change <b>parameters</b> of sending pictures (works with <b>next</b> commands)
/recommends - Get pictures similar to your bookmarks(depends on <b>parameters</b>)
/following - Get new pictures from your following
/following <i>page</i> OR /following_<i>page</i> - Get 20 pictures from <i>page</i> from your following feed
/bookmarks <i>page</i> OR /bookmarks_<i>page</i> - Get 20 pictures from <i>page</i> from your bookmarks
/logout
\nFor inline enter:
ID
URL of picture from pixiv (in text also)
\n<b>Buttons</b>:
🔽 - Show parameters
🔼 - Hide parameters
<b>Parameters</b>:
📰 - With description(<b>recommended</b>)
OR
🖼 - Without description

📂 - In group of 5 or less pictures
OR
📄 - By one with buttons of navigation

More info -> https://t.me/dbots_dalor
\nHave a nice day :-)
'''

GIF_HELP = [
    {'name': 'Base usage', 'file_id': 'CgADAgAD3wMAAsM_OUr6G1uUmZssjgI'}, 
    {'name': 'Load similar pictures', 'file_id': 'CgADAgAD3gMAAsM_OUqWHAXLTS60zwI'},
    {'name': 'Navigation and sharing', 'file_id': 'CgADAgADmwIAAnjbOUrDbE1UkPG8TQI'}
    ]

assert PACK_OF_SIMILAR_POSTS <= 10

app = Flask(__name__)
b = Bot(BOT_ID)
pix = User(PIX_LOGIN, PIX_PASSWORD, PIX_SESSION)

dpix = DPixiv(
    b, 
    pix, 
    DATABASE, 
    BOTNAME,
    PACK_OF_SIMILAR_POSTS,
    MAX_COUNT_POSTS, 
    LOGIN_URL
    )

@b.inline_query('([0-9]+)_?([0-9]*)')
@b.inline_query('https\:\/\/www\.pixiv\.net\/member\_illust\.php\?.*illust\_id\=([0-9]+)()')
def picture_id__(a):
    dpix.answer_inline_picture(a)

@b.inline_query('(.+)')
def search(a):
    dpix.search_inline(a)

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
    a.delete().send()

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

@b.message('/t (.+)')
@b.message('/tag (.+)')
def add_tag(a):
    dpix.add_tag(a)

@b.message('/instant')
def inst_view(a):
    repl_mess = a.data.get('reply_to_message')
    if repl_mess:
        pixiv_id = dpix.find_pixiv_id_in_mess(repl_mess)
        if pixiv_id:
            a.msg('<a href=\"https://t.me/iv?rhash=d78b7da75fefb6&url={}pic/{}\">View</a>'.format(LOGIN_URL, pixiv_id[1]), parse_mode='HTML').send()

def reply_markup_for_gifhelp(id_=None):
    return [[button(GIF_HELP[i]['name'], callback_data='help {}'.format(i))] for i in range(len(GIF_HELP)) if i != id_]

@b.message('/helpingif')
def help_in_gif(a):
    id_ = 0
    a.animation(GIF_HELP[id_]['file_id'], caption=GIF_HELP[id_]['name'],
        reply_markup=markup(reply_markup_for_gifhelp(id_))).send()

@b.message('/help')
def help(a):
    a.msg(INFO_TEXT, parse_mode='HTML').send()

@b.message('/login')
def login_url(a):
    a.msg('Use this url to log in your pixiv account', 
        reply_markup=markup([[button('Log in', url=LOGIN_URL)]])).send()

@b.message('/logout')
def logout(a):
    dpix.logout(a)

@b.message('/settings')
def default_settings(a):
    dpix.change_default_settings(a)

@b.message('/file[ _]([0-9]+)_?p?([0-9]*)')
def file(a):
    dpix.send_file_by_id(a)

@b.message('/everyone ([\s\S]+)')
def exveryone(a):
    if a.chat_id == 361959653:
        dpix.send_everyone(a.args[1])

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
    if a.args[1] == '0':
        dpix.save_default_settings(a)
    else:
        dpix.send_similar(a)

@b.callback_query('file')
def ffile(a):
    dpix.send_file_by_tag(a)

@b.callback_query('help ([0-9]+)')
def spec_help(a):
    id_ = int(a.args[1])
    help_ = GIF_HELP[id_]
    b.editmedia(
            imanimation(help_['file_id'], caption=help_['name']),
            chat_id=a.data['message']['chat']['id'],
            message_id=a.data['message']['message_id'],
            reply_markup=markup(reply_markup_for_gifhelp(id_))
        ).send()

@b.message(True)
@b.message(True, path=['photo'])
def check_tag_in_mess(a):
    dpix.send_by_pic(a)

@b.channel_post(True, path=['photo'])
def check_tag_in_post(a):
    dpix.send_to_channel(a, by_tag=True)

@app.route('/')
def index_login():
    return redirect('https://t.me/{}'.format(BOTNAME))

@app.route('/login', methods=['POST'])
def logn_form():
    token = dpix.reg_temp_token(request.form.get('login'), request.form.get('password'), request.form.get('captcha_token'))
    print(request.form)
    print(token)
    if token:
        return jsonify({'ok': True, 'result': token})
    else:
        return jsonify({'ok': False})

@app.route('/{}'.format(BOT_ID), methods=['POST']) #Telegram should be connected to this hook
def webhook():
    b.check(request.get_json())
    return 'ok', 200

def render_pics(ids, title):
    pics = [tuple(pic.values())[0] for pic in pix.info_packs(ids)]
    return render_template('pic_list.html', title=title, list=pics)
     
@app.route('/fix')
def fix_url():
    url = request.args.get('url')
    if url:
        res = check_pixiv_id.match(url)
        if res:
            picture = requests.get(url, headers={'Referer': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(res[1])})
            return send_file(BytesIO(picture.content), mimetype=picture.headers['Content-Type'], attachment_filename='{}_p{}'.format(res[1], res[2]))
    return 'null'

@app.route('/load/<id>')
def load_pic(id):
    pic = pix.info(id)
    if pic:
        p = request.args.get('p')
        url = pic['urls'].get(request.args.get('quality'))
        if not url:
            url = pic['urls']['original']
        if p:
            url = dpix.change_url_page(url, p)
        return redirect('/fix?url={}'.format(url))
    else: return 'null' 

@app.route('/info/<id>')
def info_pic(id):
    return jsonify(pix.info(id))

@app.route('/pic/<id>')
def get_pic(id):
    pic = pix.info(id)
    if pic:
        url = pic['urls']['original']
        if pic['pageCount']:
            urls = [dpix.change_url_page(url, i) for i in range(pic['pageCount'])]
        else: urls = [url]
        return render_template('only_pics.html', title='Load...', list=urls)
    else:
        return 'null'
        
@app.route('/pics/<ids>')
def load_group(ids):
    return render_pics(ids.split(','), 'Pictures')

@app.route('/similar/<id>')
def load_similar(id):
    COUNT = 20
    p = request.args.get('p')
    if p and int(p) > 0:
        count = COUNT * int(p)
    else:
        count = COUNT
    ids = pix.similar(id, count)
    if ids and count - COUNT < len(ids):
        ids = ids[count - COUNT:]
        return render_pics(ids, 'Similar')
    else:
        return 'null'

check_pixiv_url = re.compile('.+(pixiv|pximg)\.net.+\/([0-9]+|([0-9]+)(_[a-z]+|)_p([0-9]+))')

@app.route('/danbooru')
def danbooru():
    pics = requests.get('https://danbooru.donmai.us/posts.json', params=request.args).json()
    pictures = []
    for pic in pics:
        check = check_pixiv_url.match(pic['source'])
        if check:
            if check[3]:
                url = 'https://t.me/dpixivbot?start={}_{}'.format(check[3], check[5])
                file_url = '/load/{}?p={}'.format(check[3], check[5])
            else:
                url = 'https://t.me/dpixivbot?start={}'.format(check[2])
                file_url = '/load/{}'.format(check[2])
            pictures.append({'url': url, 'file_url': file_url})
    return render_template('danbooru_pics.html', list=pictures, title='danbooru')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

