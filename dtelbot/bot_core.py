import re
import asyncio
import aiohttp

from .methods import Methods
from .checker import Checker

from .message import Message
from .inline_query import InlineQuery
from .callback_query import CallbackQuery
from .choosen_inline_result import ChosenInlineResult

class BotCore(Methods):
  def __init__(self, token, proxy=None):
    self.token = token
    self.proxy = proxy
    self.commands = {
      'message': [],
      'edited_message': [], 
      'channel_post': [],
      'edited_channel_post': [],
      'inline_query': [],
      'chosen_inline_result': [],
      'callback_query': []
    }
    self.return_types = {
      'message': Message,
      'edited_message': Message, 
      'channel_post': Message,
      'edited_channel_post': Message,
      'inline_query': InlineQuery,
      'chosen_inline_result': ChosenInlineResult,
      'callback_query': CallbackQuery
    }
    self.sessions = {}
    self.oop = False
  
  def get_session(self, a):
    user = a.data.get('from')
    if user:
      user_id = user.get('id')
      if user_id:
        session = self.sessions.get(user_id)
        if not session:
          session = {}
          self.sessions[user_id] = session
        return session

  def setwebhook(self, url, **kwargs):
    kwargs['url'] = url
    return self.method('setWebhook', **kwargs)
    
  def deletewebhook(self):
    return self.method('deleteWebhook')
    
  def getwebhookinfo(self):
    return self.method('getWebhookInfo')
  
  def register(self, types, function, text, path):
    for type_ in types:
      if type_ in self.commands:
        self.commands[type_].append({
          'run': function,
          'match': re.compile(text) if type(text) == str else text,
          'path': path,
          'return': self.return_types[type_]
        })
  
  def more(self, urls):
    async def get():
      async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[asyncio.ensure_future(url.fetch(session)) for url in urls])
    return asyncio.new_event_loop().run_until_complete(get())

  def check(self, message):
    Checker(self, message).start()
    
  def polling(self):
    async def poll():
      offset = 0
      async with aiohttp.ClientSession() as session:
        while True:
          response = await self.method('getUpdates', offset=offset).fetch(session)
          if response['ok']:
            results = response['result']
            if results:
              for resp in results:
                if resp['update_id'] >= offset:
                  self.check(resp)
              offset = results[0]['update_id'] + 1
    asyncio.get_event_loop().run_until_complete(poll())