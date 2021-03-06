from dtelbot import Bot
from dtelbot.inline import photo as iphoto, article as iarticle
from dtelbot.inline_keyboard import markup, button
from dtelbot.input_media import photo as imphoto
from user import User
from arguments import Parameters
from tools import Tools
from database import Database
import re
import json
from uuid import uuid4 as random_token

change_url_page_pattern = re.compile('\_p[0-9]+')
check_pixiv_id = re.compile('.*https\:\/\/i\.pximg\.net.+\/([0-9]+)_p([0-9]+)')
get_clear_pic_url = re.compile('.*(https\:\/\/i\.pximg\.net.+)')
parse_saucenao = re.compile('pixiv\.net\/member\_illust\.php\?mode\=medium\&illust\_id\=([0-9]+)')

class DPixiv:
    def __init__(self, dbot, dpixiv, DATABASE_URL, BOTNAME, PACK_OF_SIMILAR_POSTS, MAX_COUNT_POSTS, SITE_URL):
        self.b = dbot
        self.db = Database(DATABASE_URL, dpixiv)
        self.BOTNAME = BOTNAME
        self.PACK_OF_SIMILAR_POSTS = PACK_OF_SIMILAR_POSTS
        self.MAX_COUNT_POSTS = MAX_COUNT_POSTS
        self.SITE_URL = SITE_URL
        self.tokens = {}
        self.ranking  = {
            1: {'id': 'daily', 'name': 'Daily'},
            2: {'id': 'daily_r18', 'name': 'Daily 🔞'},
            3: {'id': 'weekly', 'name': 'Weekly'},
            4: {'id': 'weekly_r18', 'name': 'Weekly 🔞'},
            5: {'id': 'monthly', 'name': 'Monthly'},
            6: {'id': 'rookie', 'name': 'Rookie'},
            7: {'id': 'original', 'name': 'Original'},
            8: {'id': 'male', 'name': 'Male'},
            9: {'id': 'male_r18', 'name': 'Male 🔞'},
            10: {'id': 'female', 'name': 'Female'},
            11: {'id': 'female_r18', 'name': 'Female 🔞'}
        }
        self.ranking_buttons = [
            [1, 2],
            [3, 4],
            [5],
            [6],
            [7],
            [8, 9],
            [10, 11]
        ]
    
    def parse_args(self, a):
        args = a.args
        return Parameters(
            pic_id=args[1],
            page=int(args[2]),
            count=int(args[3]),
            only_pics=int(args[4]),
            by_one=int(args[5]),
            ppic=int(args[6]),
            mppic=int(args[7]),
            show=int(args[8])
        )
        
    def reply(self, args):
        reply_result = []
        params = args.format()
        pic_id = int(args.pic_id)
        if pic_id > 10000:
            if args.mppic > 1:
                reply_result.append([
                    button('◀️', callback_data='prev {}'.format(params)),
                    button('▶️', callback_data='next {}'.format(params))
                    ])
            reply_result.append([
                button('Source', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(pic_id)),
                button('Download file', callback_data='file'),
                button('Share', switch_inline_query=pic_id if not args.ppic else '{}_{}'.format(pic_id, args.ppic)),
                button('🔽', callback_data='show {}'.format(params)) 
                if not args.show else button('🔼', callback_data='hide {}'.format(params))
                ])
        elif pic_id <= 11 and pic_id >= 1: #For ranking
            reply_result.extend([[button(('✅ ' if pic_id == btn else '') + self.ranking[btn]['name'], callback_data='rank {} m{}'.format(params, btn)) for btn in btn_line] for btn_line in self.ranking_buttons])
        if args.show or pic_id < 10001:
            reply_result.append([
                button('➖', callback_data='count_minus {}'.format(params)),
                  button('{} ⬇️'.format(args.count), callback_data='similar {}'.format(params)),
                  button('➕', callback_data='count_plus {}'.format(params)),
                  button('🖼' if args.only_pics else '📰', callback_data='opics {}'.format(params)),
                  button('📄' if args.by_one else '📂', callback_data='group {}'.format(params))
                  ])
        return reply_result
    
    def shared_reply(self, pic_id, ppic=0):
        new_pic_id = pic_id if not ppic else '{}_{}'.format(pic_id, ppic)
        return [[
            button('Source', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(pic_id)),
            button('More', url='t.me/{}?start={}'.format(self.BOTNAME, new_pic_id)),
            button('Share', switch_inline_query=new_pic_id)
            ]]

    def channel_reply(self, pic_id, ppic=0):
        new_pic_id = pic_id if not ppic else '{}_{}'.format(pic_id, ppic)
        return [[
            button('Source', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(pic_id)),
            button('More', url='t.me/{}?start={}'.format(self.BOTNAME, new_pic_id))
            ]]
    
    def prepare_picture(self, pic, ppic=0):
        url = pic['urls']['regular']
        thumbnail = pic['urls']['thumb']
        original = pic['urls']['original']
        if ppic and ppic < pic['pageCount']:
            url = self.change_url_page(url, ppic)
            thumbnail = self.change_url_page(thumbnail, ppic)
            original = self.change_url_page(original, ppic)
        description = '<a href=\"{}fix?url={}\">{}</a>{}\n<b>Tags:</b> {}'.format(self.SITE_URL, original, self.fix_chars(pic['title']), ' ({}/{})'.format(ppic + 1, pic['pageCount']) if pic['pageCount'] > 1 else '', self.pixiv_tags(pic))
        return {'url': url, 'caption': description, 'thumbnail': thumbnail, 'original': original}
        
    def change_url_page(self, old_url, new_page):
        return change_url_page_pattern.sub('_p{}'.format(new_page), old_url)
    
    def fix_chars(self, chars):
        return chars.replace('<', '&#60;').replace('>', '&#62;')

    def pixiv_tags(self, pic):
        return ', '.join(['<code>{}</code>{}'.format(t['tag'], '({})'.format(t['translation']['en']) if 'translation' in t else '') for t in pic['tags']['tags']])
    
    def get_pix(self, chat_id, anyway=True):
        return self.db.get_user(chat_id, anyway)
    
    def send_picture(self, pic_id, chat_id, ppic=0, reply_to_message_id=None, is_desc=True, pix=None):
        pix = self.get_pix(chat_id) if not pix else pix
        pic_info = pix.info(pic_id)
        if pic_info:
            reply_args = Parameters(pic_id=pic_id, mppic=pic_info['pageCount'],
                ppic=ppic if ppic < pic_info['pageCount'] and ppic > 0 else 0,
                count=pix.count, only_pics=pix.only_pics, by_one=pix.by_one)
            pic = self.prepare_picture(pic_info, reply_args.ppic)
            reply_markup = markup(self.reply(reply_args)) if is_desc else ''
            result = self.b.photo(pic['url'], chat_id=chat_id, caption=pic['caption'] if is_desc else '', parse_mode='HTML',
                reply_to_message_id=reply_to_message_id if reply_to_message_id else '', reply_markup=reply_markup).send()
            if not result['ok'] and is_desc:
                self.b.msg(pic['caption'], chat_id=chat_id, parse_mode='HTML',
                    reply_to_message_id=reply_to_message_id if reply_to_message_id else '', reply_markup=reply_markup).send()
            return True
    
    def answer_inline_picture(self, a):
        pic_info = self.get_pix(a.data['from']['id']).info(a.args[1])
        if pic_info:
            ppic = int(a.args[2]) if a.args[2] else 0
            pic = self.prepare_picture(pic_info, ppic)
            reply_markup = {'inline_keyboard': self.shared_reply(a.args[1], ppic)}
            a.answer([
                iphoto(id=0, photo_url=pic['url'], thumb_url=pic['thumbnail'],
                    reply_markup=reply_markup, description='Without description'),
                iphoto(id=2, photo_url=pic['url'], caption=pic['caption'], parse_mode='HTML', thumb_url=pic['thumbnail'],
                    reply_markup=reply_markup, description='With description'),
                iarticle(id=1, title=pic_info['title'], input_message_content={'message_text': pic['caption'], 'parse_mode': 'HTML'},
                    reply_markup=reply_markup, thumb_url=pic['thumbnail'])
                ]).send()

    def search_inline(self, a):
        page = int(a.data['offset']) if a.data['offset'] else 1
        pix = self.get_pix(a.data['from']['id'])
        search = pix.search(a.args[1], page)
        if search:
            results = []; i = 0
            for id in pix.illust_list(search):
                results.append(iarticle(i, id['illust_title'], {'message_text': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(id['illust_id']), 'parse_mode': 'HTML'}, thumb_url=id['url']))
                i += 1
            a.answer(results, next_offset=page+1).send()
    
    def saucenao_search(self, picture_id):
        pic_url = self.b.fileurl(picture_id)
        data = {'url': pic_url, 'frame': 1, 'hide': 0, 'database': 5}
        page = Tools().post('http://saucenao.com/search.php', data=data)
        find = parse_saucenao.search(page)
        return find[1] if find else None
    
    def send_by_id(self, a):
        if a.args[1]:
            return self.send_picture(a.args[1], a.data['chat']['id'], ppic=int(a.args[2]) if a.args[2] else 0)
    
    def pic_command(self, a):
        if not self.send_by_id(a) and 'reply_to_message' in a.data and not self.send_by_tag(a.data['reply_to_message']) and 'photo' in a.data['reply_to_message']:
            find = self.saucenao_search(a.data['reply_to_message']['photo'][-1]['file_id'])
            if not (find and self.send_picture(find, a.data['chat']['id'])):
                a.msg('¯\_(ツ)_/¯', reply_to_message_id=a.data['reply_to_message']['message_id']).send()
    
    def get_first_url(self, mess):
        first = None
        if 'caption_entities' in mess:
            first = mess['caption_entities'][0]
        elif 'entities' in mess:
            first = mess['entities'][0]
        if first and first['type'] == 'text_link':
            return first['url']
    
    def find_pixiv_id_in_mess(self, mess):
        pic_url = self.get_first_url(mess)
        if pic_url:
            return check_pixiv_id.match(pic_url)
    
    def send_by_tag(self, mess):
        pixiv_id = self.find_pixiv_id_in_mess(mess)
        if pixiv_id:
            self.send_picture(pixiv_id[1], mess['chat']['id'], ppic=int(pixiv_id[2]))
            return True
    
    def send_by_pic(self, a):
        if not self.send_by_tag(a.data):
            pix = self.get_pix(a.data['chat']['id'], False)
            if pix and 'photo' in a.data:
                find = self.saucenao_search(a.data['photo'][-1]['file_id'])
                if not (find and self.send_picture(find, a.data['chat']['id'], pix=pix)):
                    a.msg('¯\_(ツ)_/¯', reply_to_message_id=a.data['message_id']).send()
                    return
            else:
                return
        a.delete().send()

    def send_to_channel(self, a, by_tag=False):
        pixiv_id = self.find_pixiv_id_in_mess(a.data) if by_tag else a.args
        if pixiv_id:
            picture = self.get_pix(None).info(pixiv_id[1])
            ppic = int(pixiv_id[2]) if pixiv_id[2] else 0
            pic = self.prepare_picture(picture, ppic)
            self.b.more([
                a.photo(pic['url'], reply_markup=markup(self.channel_reply(pixiv_id[1], ppic))),
                a.delete()])
    
    def send_file_by_id(self, a):
        pic_info = self.get_pix(a.data['chat']['id']).info(a.args[1])
        if pic_info:
            pic_url = pic_info['urls']['original']
            if a.args[2] and int(a.args[2]) < pic_info['pageCount']:
                pic_url = self.change_url_page(pic_url, a.args[2])
            a.document(pic_url).send()
        else:
            a.msg('Can`t find such picture').send()
    
    def send_file_by_tag(self, a):
        pic_url = self.get_first_url(a.data['message'])
        if pic_url:
            a.answer(text='Sending...').send()
            clear_url = get_clear_pic_url.match(pic_url)
            self.b.document(clear_url[1] if clear_url else pic_url, chat_id=a.data['message']['chat']['id'], reply_to_message_id=a.data['message']['message_id']).send()
        else:
            a.answer(text='Wrong url').send()
    
    def edit_reply_for_callback(self, a, reply):
        self.b.editreplymarkup(chat_id=a.data['message']['chat']['id'],
            message_id=a.data['message']['message_id'],
            reply_markup=markup(reply)).send()
    
    def edit_reply(self, a, args):
        self.edit_reply_for_callback(a, self.reply(args))
        
    def make_show_or_hide(self, a, show):
        args = self.parse_args(a)
        args.show = show
        self.edit_reply(a, args)
        a.answer(text='Show' if show else 'Hide').send()
        
    def count_plus_or_minus(self, a, turn):
        args = self.parse_args(a)
        count = args.count - self.PACK_OF_SIMILAR_POSTS if turn < 0 else args.count + self.PACK_OF_SIMILAR_POSTS
        if count < self.PACK_OF_SIMILAR_POSTS or count > self.MAX_COUNT_POSTS:
            a.answer(text='This is limit').send()
        else:
            args.count = count
            self.edit_reply(a, args)
            a.answer(text='After {}{} >> {}'.format('-' if turn < 0 else '+', self.PACK_OF_SIMILAR_POSTS, count)).send()
    
    def only_pics_or_not(self, a):
        args = self.parse_args(a)
        if args.only_pics:
            args.only_pics = 0
            a.answer(text='Will send without any description').send()
        else:
            args.only_pics = 1
            a.answer(text='Will send with title and text').send()
        self.edit_reply(a, args)
            
    def by_one_or_not(self, a):
        args = self.parse_args(a)
        if args.by_one:
            args.by_one = 0
            a.answer(text='Will send in group').send()
        else:
            args.by_one = 1
            a.answer(text='Will send by one').send()
        self.edit_reply(a, args)

    def choose_ranking(self, a):
        args = self.parse_args(a)
        args.pic_id = a.args[9]
        args.page = 0
        self.edit_reply(a, args)
        
    def return_format_to_text(self, caption, caption_entities):
        new_caption = ''
        end_other = 0
        for format in caption_entities:
            new_caption += caption[end_other:format['offset']]
            end_other = format['offset'] + format['length']
            text = self.fix_chars(caption[format['offset']:end_other])
            if format['type'] == 'text_link':
                new_caption += '<a href=\"{}\">{}</a>'.format(format['url'], text)
            elif format['type'] == 'bold':
                new_caption += '<b>{}</b>'.format(text)
            elif format['type'] == 'code':
                new_caption += '<code>{}</code>'.format(text)
            elif format['type'] == 'italic':
                new_caption += '<i>{}</i>'.format(text)
            else:
                new_caption += text
        new_caption += caption[end_other:len(caption)]
        return new_caption
        
    def change_pic(self, a, s):
        args = self.parse_args(a)
        npic = args.ppic + s
        mppic = args.mppic
        entities = None; text = None
        message = a.data['message']
        is_photo = False
        if 'caption_entities' in message:
            is_photo = True
            entities = message['caption_entities']
            text = message['caption']
        elif 'entities' in message:
            entities = message['entities']
            text = message['text']
        if npic >= mppic:
            npic = 0
        elif npic < 0:
            npic = mppic - 1
        if not entities or not text:
            return 'Nothing'
        temp_pic_url = self.change_url_page(entities[0]['url'], npic)
        entities[0]['url'] = temp_pic_url
        caption = self.return_format_to_text(text, entities)
        caption = caption.replace('({}/{})\n'.format(args.ppic + 1, mppic), '({}/{})\n'.format(npic + 1, mppic))
        pic_url = get_clear_pic_url.match(temp_pic_url)[1].replace('_p{}'.format(npic), '_p{}_master1200'.format(npic)).replace('img-original', 'img-master').replace('.png', '.jpg')
        args.ppic = npic
        reply_markup = markup(self.reply(args))
        if is_photo:
            result = self.b.editmedia(
                imphoto(pic_url, caption=caption, parse_mode='HTML'),
                chat_id=a.data['message']['chat']['id'],
                message_id=a.data['message']['message_id'],
                reply_markup=reply_markup).send()
            if not result['ok']:
                return None
        else:
            self.b.edittext(caption, parse_mode='HTML',
            chat_id=a.data['message']['chat']['id'],
            message_id=a.data['message']['message_id'],
            reply_markup=reply_markup).send()
        return '{}/{}'.format(npic + 1, mppic)
    
    def turn_right_or_left(self, a, s):
        mess = self.change_pic(a, s)
        while not mess and abs(s) < self.PACK_OF_SIMILAR_POSTS:
            s = s - 1 if s < 0 else s + 1
            mess = self.change_pic(a, s)
        a.answer(text=mess).send()

    def send_pack_by_one(self, ids, chat_id, reply_to_message_id=None, is_desc=True, pix=None):
        pix = self.get_pix(chat_id) if not pix else pix
        for id_ in ids:
            self.send_picture(id_, chat_id, reply_to_message_id=reply_to_message_id, is_desc=is_desc, pix=pix)
    
    def send_packs(self, ids, chat_id, reply_to_message_id=None, is_desc=True, pix=None):
        pix = self.get_pix(chat_id) if not pix else pix
        for pack in Tools().min_split(ids, self.PACK_OF_SIMILAR_POSTS):
            all_info = pix.info_packs(pack)
            all_media = []
            for one in all_info:
                pic = self.prepare_picture(one)
                all_media.append(imphoto(pic['url'], caption=pic['caption'] if is_desc else '', parse_mode='HTML'))
            result = self.b.media(all_media, chat_id=chat_id,
                reply_to_message_id=reply_to_message_id if reply_to_message_id else '').send()
            if not result['ok']:
                self.send_pack_by_one(pack, chat_id, reply_to_message_id=reply_to_message_id, is_desc=is_desc, pix=pix)
    
    def send_pictures(self, ids, chat_id, args=None, reply_to_message_id=None, pix=None):
        is_desc = not ((args and args.only_pics) or (pix and pix.only_pics))
        pix = self.get_pix(chat_id) if not pix else pix
        by_one = args.by_one if args else pix.by_one
        if by_one:
            self.send_pack_by_one(ids, chat_id,
                reply_to_message_id=reply_to_message_id, is_desc=is_desc, pix=pix)
        else:
            self.send_packs(ids, chat_id,
                reply_to_message_id=reply_to_message_id, is_desc=is_desc, pix=pix)
    
    def send_similar(self, a):
        args = self.parse_args(a)
        count = args.count
        limit = args.page * self.PACK_OF_SIMILAR_POSTS + count
        if limit > self.MAX_COUNT_POSTS:
            a.answer(text='This is limit').send()
        else:
            args.page = limit // self.PACK_OF_SIMILAR_POSTS
            pix = self.get_pix(a.data['message']['chat']['id'])
            sim_ids = pix.similar(args.pic_id, limit=limit)[limit - count:]
            a.answer(text='Loading {} similar pictures from {} to {}'.format(count, limit + 1 - count, limit)).send()
            self.edit_reply(a, args)
            self.send_pictures(sim_ids, a.data['message']['chat']['id'], args=args,
                reply_to_message_id=a.data['message']['message_id'], pix=pix)

    def send_ranking(self, a):
        args = self.parse_args(a)
        first = args.page * self.PACK_OF_SIMILAR_POSTS
        last = first + args.count
        if last > self.MAX_COUNT_POSTS:
            a.answer(text='This is limit').send()
        else:
            args.page = last // self.PACK_OF_SIMILAR_POSTS
            pix = self.get_pix(a.data['message']['chat']['id'])
            mode = self.ranking[int(args.pic_id)]
            if (first // 50 == last // 50) :
                ids = pix.ranking(mode['id'])
            else:
                ids = pix.ranking_packs(mode['id'], from_page=first // 50 + 1, to_page=last // 50 + 1)
            first_in_pack = first if first < 50 else first % 50
            pics = ids[first_in_pack:first_in_pack + args.count]
            a.answer(text='Loading {} {} pictures from {} to {}'.format(args.count, mode['name'].lower(), first + 1, last)).send()
            self.edit_reply(a, args)
            self.send_pictures(pics, a.data['message']['chat']['id'], args=args,
                reply_to_message_id=a.data['message']['message_id'], pix=pix)

    def send_ranking_list(self, a):
        pix = self.get_pix(a.data['chat']['id'])
        reply_args = Parameters(pic_id='1',
                count=pix.count, only_pics=pix.only_pics, by_one=pix.by_one)
        a.msg('<b>Rankings:</b>', parse_mode='HTML',
            reply_markup=markup(self.reply(reply_args))).send()
    
    def reg_temp_token(self, login, password, captcha_token):
        new_acc = User()
        new_acc.auth(login, password, captcha_token)
        if new_acc.is_auth:
            token = str(random_token())
            while token in self.tokens:
                token = str(random_token())
            self.tokens[token] = new_acc
            return {'token': token, 'session': new_acc.session}
    
    def connect_user_to_id(self, a):
        token = a.args[1]
        user_acc = self.tokens.get(token)
        if user_acc:
            self.db.set_user(a.data['chat']['id'], user_acc)
            del self.tokens[token]
            a.msg('Succesfull connected').send()
        else:
            a.msg('Wrong token').send()
            
    def is_logged(old):
        def new(self, a, *args):
            chat_id = None
            if a.type == 'message':
                chat_id = a.data['chat']['id']
            elif a.type == 'callback_query':
                chat_id = a.data['message']['chat']['id']
            if chat_id:
                pix = self.get_pix(chat_id, False)
                if pix:
                    return old(self, a, pix, *args)
                else:
                    self.b.msg('Try to /login at first', chat_id=chat_id).send()
        return new
    
    @is_logged
    def logout(self, a, pix):
        self.db.del_user(a.data['chat']['id'])
        a.msg('Disconnected').send()

    @is_logged
    def user_following(self, a, pix):
        follow_ids = []
        last_id = int(pix.last_id)
        count = int(pix.count)
        if a.args[1]:
            count = 20
            follow_ids = pix.new_work_following(page=a.args[1])
        elif last_id:
            for i in range(self.MAX_COUNT_POSTS // 20 // self.PACK_OF_SIMILAR_POSTS): #Max_pages (5 * 5 * 200) with 500 pics
                ids = pix.new_work_following(from_page=self.PACK_OF_SIMILAR_POSTS * i + 1, to_page=self.PACK_OF_SIMILAR_POSTS * (i + 1))
                if ids:
                    new_ids = [id_ for id_ in ids if int(id_) > last_id]
                    follow_ids.extend(new_ids)
                    if len(ids) != len(new_ids):
                        break
                else:
                    break
        else:
            follow_ids = pix.new_work_following(page=1)
        follow_ids.reverse()
        if follow_ids:
            if len(follow_ids) > count:
                follow_ids = follow_ids[-count - 1:]
            pix.last_id = follow_ids[-1]
            self.db.save_user_settings(a.data['chat']['id'])
            self.send_pictures(follow_ids, a.data['chat']['id'], pix=pix)
        else:
            a.msg('¯\_(ツ)_/¯').send()
    
    @is_logged
    def user_recommender(self, a, pix):
        recommended_ids = pix.recommender(count=pix.count)
        self.send_pictures(recommended_ids, a.data['chat']['id'], pix=pix)
    
    @is_logged
    def user_bookmarks(self, a, pix):
        bookmarks_ids = pix.bookmarks(a.args[1] if a.args[1] else 1)
        self.send_pack_by_one(bookmarks_ids, a.data['chat']['id'])

    @is_logged
    def change_default_settings(self, a, pix):
        reply_args = Parameters(pic_id='0',
                count=pix.count, only_pics=pix.only_pics, by_one=pix.by_one)
        a.msg('<b>Change default settings</b>\nPress ⬇️ to save', parse_mode='HTML',
            reply_markup=markup(self.reply(reply_args))).send()

    @is_logged
    def save_default_settings(self, a, pix):
        args = self.parse_args(a)
        pix.count = args.count
        pix.only_pics = args.only_pics
        pix.by_one = args.by_one
        self.db.save_user_settings(a.data['message']['chat']['id'])
        a.answer(text='Saved').send()

    @is_logged
    def add_tag(self, a, pix):
        pixiv_id = self.find_pixiv_id_in_mess(a.data['reply_to_message'])
        if pixiv_id:
            pixiv_id = pixiv_id[1]
            pic_info = pix.info(pixiv_id, token=True)
            if pic_info:
                if pix.add_tag(pixiv_id, a.args[1], pic_info[pixiv_id]['token']):
                    text = 'Success'
                else:
                    text = 'Fail'
                a.msg(text).send()

    @is_logged
    def send_session(self, a, pix):
        a.msg('Your session:\n<code>{}</code>\n<i>Use it to connect browser extension to this profile</i>'.format(pix.session), parse_mode='HTML').send()

    def send_everyone(self, mess):
        self.b.more([self.b.msg(mess, chat_id=chat_id, parse_mode='HTML') for chat_id in self.db.get_all_ids()])

    def from_plugin(old):
        def new(self, session, *args):
            if session:
                pix = self.db.get_user_by_session(session)
                if pix:
                    return old(self, pix, *args)
        return new

    @from_plugin
    def send_picture_from_plugin(self, pix, id):
        return self.send_picture(id, pix.chat_id, pix=pix)
    