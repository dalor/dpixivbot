from dtelbot import Bot, inputmedia as inmed, reply_markup as repl, inlinequeryresult as iqr
from dpixiv import DPixivIllusts
from arguments import Parameters
from tools import Tools
from database import Database
import re
import json
from uuid import uuid4 as random_token

change_url_page_pattern = re.compile('\_p[0-9]+')
check_pixiv_id = re.compile('https\:\/\/i\.pximg\.net.+\/([0-9]+)_p([0-9]+)\.')
parse_saucenao = re.compile('pixiv\.net\/member\_illust\.php\?mode\=medium\&illust\_id\=([0-9]+)')

class DPixiv:
    def __init__(self, dbot, dpixiv, DATABASE_URL, BOTNAME, PACK_OF_SIMILAR_POSTS, MAX_COUNT_POSTS):
        self.b = dbot
        self.db = Database(DATABASE_URL, dpixiv)
        self.BOTNAME = BOTNAME
        self.PACK_OF_SIMILAR_POSTS = PACK_OF_SIMILAR_POSTS
        self.MAX_COUNT_POSTS = MAX_COUNT_POSTS
        self.tokens = {}
    
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
        if args.mppic > 1:
            reply_result.append([
                repl.inlinekeyboardbutton('◀️', callback_data='prev {}'.format(params)),
                repl.inlinekeyboardbutton('▶️', callback_data='next {}'.format(params))
                ])
        reply_result.append([
            repl.inlinekeyboardbutton('On pixiv', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(args.pic_id)),
            repl.inlinekeyboardbutton('Download file', callback_data='file'),
            repl.inlinekeyboardbutton('Share', switch_inline_query=args.pic_id if not args.ppic else '{}_{}'.format(args.pic_id, args.ppic)),
            repl.inlinekeyboardbutton('🔽', callback_data='show {}'.format(params)) 
            if not args.show else repl.inlinekeyboardbutton('🔼', callback_data='hide {}'.format(params))
            ])
        if args.show:
            reply_result.append([
                repl.inlinekeyboardbutton('➖', callback_data='count_minus {}'.format(params)),
                  repl.inlinekeyboardbutton('{} ⬇️'.format(args.count), callback_data='similar {}'.format(params)),
                  repl.inlinekeyboardbutton('➕', callback_data='count_plus {}'.format(params)),
                  repl.inlinekeyboardbutton('🖼' if args.only_pics else '📰', callback_data='opics {}'.format(params)),
                  repl.inlinekeyboardbutton('📄' if args.by_one else '📂', callback_data='group {}'.format(params))
                  ])
        return reply_result
    
    def shared_reply(self, pic_id, ppic=0):
        new_pic_id = pic_id if not ppic else '{}_{}'.format(pic_id, ppic)
        return [[
            repl.inlinekeyboardbutton('On pixiv', url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(pic_id)),
            repl.inlinekeyboardbutton('More', url='t.me/{}?start={}'.format(self.BOTNAME, new_pic_id)),
            repl.inlinekeyboardbutton('Share', switch_inline_query=new_pic_id)
            ]]
    
    def prepare_picture(self, pic, ppic=0):
        url = pic['urls']['original']
        thumbnail = pic['urls']['thumb']
        if ppic and ppic < pic['pageCount']:
            url = self.change_url_page(url, ppic)
            thumbnail = self.change_url_page(thumbnail, ppic)
        description = '<a href=\"{}\">{}</a>\n<b>Tags:</b> {}'.format(url, pic['title'], self.pixiv_tags(pic))
        return {'url': url, 'caption': description, 'thumbnail': thumbnail}
        
    def change_url_page(self, old_url, new_page):
        return change_url_page_pattern.sub('_p{}'.format(new_page), old_url)
    
    def pixiv_tags(self, pic):
        return ', '.join(['<code>{}</code>{}'.format(t['tag'], '({})'.format(t['translation']['en']) if 'translation' in t else '') for t in pic['tags']['tags']])
    
    def get_pix(self, chat_id, anyway=True):
        return self.db.get_user(chat_id, anyway)
    
    def send_picture(self, pic_id, chat_id, ppic=0, reply_to_message_id=None, is_desc=True):
        pix = self.get_pix(chat_id)
        pic_info = pix.info(pic_id)
        if pic_info:
            pic_info = pic_info[pic_id]
            reply_args = Parameters(pic_id=pic_id, mppic=pic_info['pageCount'],
                ppic=ppic if ppic < pic_info['pageCount'] and ppic > 0 else 0)
            pic = self.prepare_picture(pic_info, reply_args.ppic)
            reply_markup = repl.inlinekeyboardmarkup(self.reply(reply_args)) if is_desc else ''
            result = self.b.photo(pic['url'], chat_id=chat_id, caption=pic['caption'] if is_desc else '', parse_mode='HTML',
                reply_to_message_id=reply_to_message_id if reply_to_message_id else '', reply_markup=reply_markup).send()
            if not result['ok'] and is_desc:
                self.b.msg(pic['caption'], chat_id=chat_id, parse_mode='HTML',
                    reply_to_message_id=reply_to_message_id if reply_to_message_id else '', reply_markup=reply_markup).send()
            return True
    
    def answer_inline_picture(self, a):
        pix_info = self.get_pix(a.data['from']['id']).info(a.args[1])
        if pix_info:
            pic_info = pix_info[a.args[1]]
            ppic = int(a.args[2]) if a.args[2] else 0
            pic = self.prepare_picture(pic_info, ppic)
            reply_markup = {'inline_keyboard': self.shared_reply(a.args[1], ppic)}
            a.answer([
                iqr(type='photo', id=0, photo_url=pic['url'], thumb_url=pic['thumbnail'],
                    reply_markup=reply_markup, description='Without description'),
                iqr(type='photo', id=2, photo_url=pic['url'], caption=pic['caption'], parse_mode='HTML', thumb_url=pic['thumbnail'],
                    reply_markup=reply_markup, description='With description'),
                iqr(type='article', id=1, title=pic_info['title'], input_message_content={'message_text': pic['caption'], 'parse_mode': 'HTML'},
                    reply_markup=reply_markup, thumb_url=pic['thumbnail'])
                ]).send()
    
    def saucenao_search(self, picture_id):
        pic_url = self.b.fileurl(picture_id)
        data = {'url': pic_url, 'frame': 1, 'hide': 0, 'database': 5}
        page = Tools().post('http://saucenao.com/search.php', data=data)
        return parse_saucenao.search(page)
    
    def send_by_id(self, a):
        if a.args[1]:
            return self.send_picture(a.args[1], a.data['chat']['id'], ppic=int(a.args[2]) if a.args[2] else 0)
    
    def pic_command(self, a):
        if not self.send_by_id(a) and 'reply_to_message' in a.data and 'photo' in a.data['reply_to_message'] and not self.send_by_tag(a.data['reply_to_message']):
            find = self.saucenao_search(a.data['reply_to_message']['photo'][-1]['file_id'])
            if not (find and self.send_picture(find[1], a.data['chat']['id'])):
                a.msg('Can`t find such picture').send()
    
    def get_first_url(self, mess):
        first = None
        if 'caption_entities' in mess:
            first = mess['caption_entities'][0]
        elif 'entities' in mess:
            first = mess['entities'][0]
        if first and first['type'] == 'text_link':
            return first['url']
            
    def send_by_tag(self, mess):
        pic_url = self.get_first_url(mess)
        if pic_url:
            pixiv_id = check_pixiv_id.match(pic_url)
            if pixiv_id:
                self.send_picture(pixiv_id[1], mess['chat']['id'], ppic=int(pixiv_id[2]))
                return True
          
    def send_file_by_id(self, a):
        pic_info = self.get_pix(a.data['chat']['id']).info(a.args[1])[a.args[1]]
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
            self.b.document(pic_url, chat_id=a.data['message']['chat']['id'], reply_to_message_id=a.data['message']['message_id']).send()
        else:
            a.answer(text='Wrong url').send()
    
    def edit_reply(self, a, args):
        self.b.editreplymarkup(chat_id=a.data['message']['chat']['id'],
            message_id=a.data['message']['message_id'],
            reply_markup=repl.inlinekeyboardmarkup(self.reply(args))).send()
        
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
            self.edit_reply(a, args)
            a.answer(text='Will send without any description')
        else:
            args.only_pics = 1
            self.edit_reply(a, args)
            a.answer(text='Will send with title and text')
            
    def by_one_or_not(self, a):
        args = self.parse_args(a)
        if args.by_one:
            args.by_one = 0
            self.edit_reply(a, args)
            a.answer(text='Will send in group')
        else:
            args.by_one = 1
            self.edit_reply(a, args)
            a.answer(text='Will send by one')
    
    def return_format_to_text(self, caption, caption_entities):
        new_caption = ''
        end_other = 0
        for format in caption_entities:
            new_caption += caption[end_other:format['offset']]
            end_other = format['offset'] + format['length']
            text = caption[format['offset']:end_other]
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
        pic_url = self.change_url_page(entities[0]['url'], npic)
        entities[0]['url'] = pic_url
        caption = self.return_format_to_text(text, entities)
        args.ppic = npic
        reply_markup = repl.inlinekeyboardmarkup(self.reply(args))
        if is_photo:
            result = self.b.editmedia(
                json.dumps(inmed.photo(pic_url, caption=caption, parse_mode='HTML')),
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
        first_s = s
        mess = self.change_pic(a, s)
        while not mess:
            s = s - 1 if s < 0 else s + 1
            mess = self.change_pic(a, s)
        a.answer(text=mess).send()

    def send_pack_by_one(self, ids, chat_id, reply_to_message_id=None, is_desc=True):
        for id_ in ids:
            self.send_picture(id_, chat_id, reply_to_message_id=reply_to_message_id, is_desc=is_desc)
    
    def send_packs(self, ids, chat_id, reply_to_message_id=None, is_desc=True):
        for pack in Tools().min_split(ids, self.PACK_OF_SIMILAR_POSTS):
            all_info = self.get_pix(chat_id).info_packs(pack)
            all_media = []
            for one in all_info:
                key, value = list(one.items())[0]
                pic = self.prepare_picture(value)
                all_media.append(inmed.photo(pic['url'], caption=pic['caption'] if is_desc else '', parse_mode='HTML'))
            result = self.b.media(all_media, chat_id=chat_id,
                reply_to_message_id=reply_to_message_id if reply_to_message_id else '').send()
            if not result['ok']:
                self.send_pack_by_one(pack, chat_id, reply_to_message_id=reply_to_message_id, is_desc=is_desc)
    
    def send_similar(self, a):
        args = self.parse_args(a)
        page = args.page
        count = args.count
        limit = page * self.PACK_OF_SIMILAR_POSTS + count
        if limit > self.MAX_COUNT_POSTS:
            a.answer(text='This is limit').send()
        else:
            args.page = limit // self.PACK_OF_SIMILAR_POSTS
            self.edit_reply(a, args)
            sim_ids = self.get_pix(a.data['message']['chat']['id']).similar(args.pic_id, limit=limit)[limit - count:]
            a.answer(text='Loading {} similar pictures from {} to {}'.format(count, limit + 1 - count, limit)).send()
            is_desc = not args.only_pics
            if args.by_one:
                self.send_pack_by_one(sim_ids, a.data['message']['chat']['id'],
                    reply_to_message_id=a.data['message']['message_id'], is_desc=is_desc)
            else:
                self.send_packs(sim_ids, a.data['message']['chat']['id'],
                    reply_to_message_id=a.data['message']['message_id'], is_desc=is_desc)
    
    def reg_temp_token(self, login, password):
        new_acc = DPixivIllusts(login, password)
        if new_acc.tt:
            token = str(random_token())
            while token in self.tokens:
                token = str(random_token())
            self.tokens[token] = new_acc
            return token
    
    def connect_user_to_id(self, a):
        token = a.args[1]
        user_acc = self.tokens.get(token)
        if user_acc:
            self.db.set_user(a.data['chat']['id'], user_acc)
            a.msg('Succesfull connected').send()
        else:
            a.msg('Wrong token').send()
            
    def is_logged(old):
        def new(self, a):
            pix = self.get_pix(a.data['chat']['id'], False)
            if pix:
                return old(self, a, pix)
            else:
                a.msg('Try to /login at first').send()
        return new
    
    @is_logged
    def user_following(self, a, pix):
        follow_ids = pix.new_work_following(a.args[1] if a.args[1] else 1)
        self.send_pack_by_one(follow_ids, a.data['chat']['id'])
    
    @is_logged
    def user_recommender(self, a, pix):
        recommended_ids = pix.recommender(count=a.args[1] if a.args[1] else 10)
        self.send_pack_by_one(recommended_ids, a.data['chat']['id'])
    
    @is_logged
    def user_bookmarks(self, a, pix):
        bookmarks_ids = pix.bookmarks(a.args[1] if a.args[1] else 1)
        self.send_pack_by_one(bookmarks_ids, a.data['chat']['id'])
    
    