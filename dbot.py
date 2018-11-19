import re
from threading import Thread
import json
import asyncio
import aiohttp

def inlinequeryresult(type, id, **kwargs):
    kwargs['type'] = type
    kwargs['id'] = id
    return kwargs

class inputmedia:
    def photo(media, **kwargs):
        kwargs['type'] = 'photo'
        kwargs['media'] = media
        return kwargs

class reply_markup:
    def inlinekeyboardmarkup(inline_keyboard):
        return json.dumps({'inline_keyboard': inline_keyboard})
        
    def inlinekeyboardbutton(text, **kwargs):
        kwargs['text'] = text
        return kwargs
    
    def replykeyboardmarkup(keyboard, **kwargs):
        kwargs['keyboard'] = keyboard
        return json.dumps(kwargs)
        
    def keyboardbutton(text, **kwargs):
        kwargs['text'] = text
        return kwargs
        
    def replykeyboardmarkup(remove_keyboard=True, **kwargs):
        kwargs['remove_keyboard'] = remove_keyboard
        return json.dumps(kwargs)
    
    def forsereply(forsereply=True, **kwargs):
        kwargs['forse_reply'] = forsereply
        return json.dumps(kwargs)

class URL:
    def __init__(self, method, data, bot):
        #self.loop = bot.loop
        self.params = data
        self.token = bot.token
        self.method = method
    
    def send(self):
        async def fetch(session):
            if 'data' in self.params:
                file = self.params['data']
                del self.params['data']
                async with session.post('https://api.telegram.org/bot{}/{}'.format(self.token, self.method), params=self.params, data=file) as response:
                    return json.loads(await response.text())
            else:
                async with session.get('https://api.telegram.org/bot{}/{}'.format(self.token, self.method), params=self.params) as response:
                    return json.loads(await response.text())
        async def get():
            async with aiohttp.ClientSession() as session:
                return await fetch(session)
        return asyncio.new_event_loop().run_until_complete(get())
        

class Message:
    def __init__(self, data, bot, type='message', args=[]):
        self.data = data
        self.args = args
        self.type = type
        self.bot = bot
        
    def msg(self, text, chat_id=None, **kwargs):
        return self.bot.msg(text, self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def photo(self, photo, chat_id=None, **kwargs):
        return self.bot.photo(photo, self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def audio(self, chat_id=None, **kwargs):
        return self.bot.audio(self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def document(self, document, chat_id=None, **kwargs):
        return self.bot.document(document, self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def video(self, video, chat_id=None, **kwargs):
        return self.bot.video(video, self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def animation(self, animation, chat_id=None, **kwargs):
        return self.bot.animation(animation, self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def voice(self, voice, chat_id=None, **kwargs):
        return self.bot.voice(voice, self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def video_note(self, video_note, chat_id=None, **kwargs):
        return self.bot.video_note(video_note, self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def media(self, media, chat_id=None, **kwargs):
        return self.bot.media(media, self.data['chat']['id'] if not chat_id else chat_id, **kwargs)
        
    def delete(self, message_id, chat_id=None):
        return self.bot.delete(message_id, self.data['chat']['id'] if not chat_id else chat_id)
    
    def editmessagetext(self, text, chat_id=None, **kwargs):
        return self.bot.editmessagetext(text, chat_id=self.data['chat']['id'] if not (chat_id and 'inline_message_id' in kwargs) else chat_id, **kwargs)
        
    def editreplymarkup(self, **kwargs):
        if not 'chat_id' in kwargs:
            kwargs['chat_id'] = self.data['chat_id']
        return self.bot.editreplymarkup(**kwargs)
        
class InlineQuery:
    def __init__(self, data, bot, args=[]):
        self.data = data
        self.args = args
        self.type = 'inline_query'
        self.bot = bot
        
    def answer(self, results, **kwargs):
        kwargs['inline_query_id'] = self.data['id']
        kwargs['results'] = json.dumps(results)
        return self.bot.method('answerInlineQuery', **kwargs)

class ChosenInlineResult:
    def __init__(self, data, bot, args=[]):
        self.data = data
        self.args = args
        self.type = 'chosen_inline_result'
        self.bot = bot

class CallbackQuery:
    def __init__(self, data, bot, args=[]):
        self.data = data
        self.args = args
        self.type = 'callback_query'
        self.bot = bot
        
    def answer(self, **kwargs):
        kwargs['callback_query_id'] = self.data['id']
        return self.bot.method('answerCallbackQuery', **kwargs)
        
class Bot:
    def __init__(self, token):
        self.commands = {'message': {'checker': self.message_checker, 'commands': [], 'free': None},
                         'edited_message': {'checker': self.edited_message_checker, 'commands': [], 'free': None},   
                         'channel_post': {'checker': self.channel_post_checker, 'commands': [], 'free': None},
                         'edited_channel_post': {'checker': self.edited_channel_post_checker, 'commands': [], 'free': None},
                         'inline_query': {'checker': self.inline_query_checker, 'commands': []},
                         'chosen_inline_result': {'checker': self.chosen_inline_result_checker, 'commands': []},
                         'callback_query': {'checker': self.callback_query_checker, 'commands': []}}
        self.token = token
        #self.loop = asyncio.get_event_loop()
    
    def method(self, method_, **kwargs):
        return URL(method_, kwargs, self)
     
    def msg(self, text, chat_id, **kwargs):
        kwargs['text'] = text
        kwargs['chat_id'] = chat_id
        return self.method('sendMessage', **kwargs)
    
    def photo(self, photo, chat_id, **kwargs):
        kwargs['photo'] = photo
        kwargs['chat_id'] = chat_id
        return self.method('sendPhoto', **kwargs)
        
    def audio(self, chat_id, **kwargs):
        kwargs['chat_id'] = chat_id
        return self.method('sendAudio', **kwargs)
        
    def document(self, document, chat_id, **kwargs):
        kwargs['document'] = document
        kwargs['chat_id'] = chat_id
        return self.method('sendDocument', **kwargs)
        
    def video(self, video, chat_id, **kwargs):
        kwargs['video'] = video
        kwargs['chat_id'] = chat_id
        return self.method('sendVideo', **kwargs)
        
    def voice(self, voice, chat_id, **kwargs):
        kwargs['voice'] = voice
        kwargs['chat_id'] = chat_id
        return self.method('sendVoice', **kwargs)
        
    def video_note(self, video_note, chat_id, **kwargs):
        kwargs['video_note'] = video_note
        kwargs['chat_id'] = chat_id
        return self.method('sendVideoNote', **kwargs)
        
    def media(self, media, chat_id, **kwargs):
        kwargs['media'] = json.dumps(media)
        kwargs['chat_id'] = chat_id
        return self.method('sendMediaGroup', **kwargs)

    def delete(self, message_id, chat_id):
        kwargs = {'chat_id': chat_id, 'message_id': message_id}
        return self.method('deleteMessage', **kwargs)
        
    def editmessagetext(self, text, **kwargs):
        kwargs['text'] = text
        return self.method('editMessageText', **kwargs)
        
    def editreplymarkup(self, **kwargs):
        return self.method('editMessageReplyMarkup', **kwargs)
    
    def command(self, command_, types = ['message']):
        def reg(old):
            for type_ in types:
                if type_ in self.commands:
                    self.commands[type_]['commands'].append({'run': old, 'match': re.compile(command_)})
            return old
        return reg
        
    def message_checker(self, mess, type='message'):
        for com in self.commands[type]['commands']:
            if 'text' in mess:
                res = com['match'].match(mess['text'])
                if res: 
                    com['run'](Message(mess, self, type, res))
                    break
        free = self.commands[type]['free']
        if free:
            free(Message(mess, self, type, None))
    
    def message(self, command):
        def reg(old):
            if command is True:
                self.commands['message']['free'] = old
            else:
                self.commands['message']['commands'].append({'run': old, 'match': re.compile(command)})
            return old
        return reg
        
    def edited_message_checker(self, mess):
        self.message_checker(mess, 'edited_message')
    
    def edited_message(self, command):
        def reg(old):
            if command is True:
                self.commands['edited_message']['free'] = old
            else:
                self.commands['edited_message']['commands'].append({'run': old, 'match': re.compile(command)})
            return old
        return reg
    
    def channel_post_checker(self, mess):
        self.message_checker(mess, 'channel_post')
    
    def channel_post(self, command):
        def reg(old):
            if command is True:
                self.commands['channel_post']['free'] = old
            else:
                self.commands['channel_post']['commands'].append({'run': old, 'match': re.compile(command)})
            return old
        return reg
    
    def edited_channel_post_checker(self, mess):
        self.message_checker(mess, 'edited_channel_post')
    
    def edited_channel_post(self, command):
        def reg(old):
            if command is True:
                self.commands['edited_channel_post']['free'] = old
            else:
                self.commands['edited_channel_post']['commands'].append({'run': old, 'match': re.compile(command)})
            return old
        return reg
    
    def inline_query_checker(self, mess):
        for com in self.commands['inline_query']['commands']:
            res = com['match'].match(mess['query'])
            if res: 
                com['run'](InlineQuery(mess, self, res))
                break
    
    def inline_query(self, command):
        def reg(old):
            self.commands['inline_query']['commands'].append({'run': old, 'match': re.compile(command)})
            return old
        return reg
    
    def chosen_inline_result_checker(self, mess):
        for com in self.commands['chosen_inline_result']['commands']:
            res = com['match'].match(mess['result_id'])
            if res: 
                com['run'](ChosenInlineResult(mess, self, res))
                break
    
    def chosen_inline_result(self, command):
        def reg(old):
            self.commands['chosen_inline_result']['commands'].append({'run': old, 'match': re.compile(command)})
            return old
        return reg
      
    def callback_query_checker(self, mess):
        for com in self.commands['callback_query']['commands']:
            res = com['match'].match(mess['data']) if 'data' in mess else []
            if res: 
                com['run'](CallbackQuery(mess, self, res))
                break
            
    def callback_query(self, command):
        def reg(old):
            self.commands['callback_query']['commands'].append({'run': old, 'match': re.compile(command)})
            return old
        return reg
    
    def more(self, urls):
        async def fetch(url, session):
            async with session.get('https://api.telegram.org/bot{}/{}'.format(url.token, url.method), params=url.params) as response:
                return json.loads(await response.text())
        async def get():
            async with aiohttp.ClientSession() as session:
                return await asyncio.gather(*[asyncio.ensure_future(fetch(url, session)) for url in urls])
        return asyncio.new_event_loop().run_until_complete(get())
    
    def check_(self, mess):
        for comm in self.commands:
            if comm in mess:
                self.commands[comm]['checker'](mess[comm])
                break
            
    def check(self, mess):
        Thread(target=self.check_, args=[mess]).start()
    