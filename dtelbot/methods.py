from .url import URL
import json

class Methods:
  def get_chat_id(self, chat_id):
    if chat_id is None:
      if hasattr(self, 'data'):
        result = self.data.get('chat')
        if result:
          chat_id = result.get('id')
          if chat_id:
            return chat_id
        raise ValueError('Can`t find `chat_id` parameter')
    else:
      return chat_id
      
  def get_message_id(self, message_id):
    if message_id is None:
      if hasattr(self, 'data'):
        message_id = self.data.get('message_id')
        if message_id:
          return message_id
        raise ValueError('Can`t find `message_id` parameter')
    else:
      return message_id
  
  def __check_file(self, kwargs, **file):
    if hasattr(next(iter(file.values())), 'read'):
      kwargs['data'] = file
    else:
      kwargs.update(file)
  
  def __check_kwargs(self, kwargs):
    reply_markup = kwargs.get('reply_markup')
    if reply_markup:
      kwargs['reply_markup'] = json.dumps(reply_markup)

  def method(self, method_, **kwargs):
    self.__check_kwargs(kwargs)
    return URL(method_, kwargs, self)
  
  def msg(self, text, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    kwargs['text'] = text
    return self.method('sendMessage', **kwargs)
    
  def photo(self, photo, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    self.__check_file(kwargs, photo=photo)
    return self.method('sendPhoto', **kwargs)
        
  def audio(self, audio, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    self.__check_file(kwargs, audio=audio)
    return self.method('sendAudio', **kwargs)
        
  def document(self, document, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    self.__check_file(kwargs, document=document)
    return self.method('sendDocument', **kwargs)
    
  def animation(self, animation, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    self.__check_file(kwargs, animation=animation)
    return self.method('sendAnimation', **kwargs)
        
  def video(self, video, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    self.__check_file(kwargs, video=video)
    return self.method('sendVideo', **kwargs)
        
  def voice(self, voice, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    self.__check_file(kwargs, voice=voice)
    return self.method('sendVoice', **kwargs)
      
  def video_note(self, video_note, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    self.__check_file(kwargs, video_note=video_note)
    return self.method('sendVideoNote', **kwargs)
        
  def sticker(self, sticker, chat_id=None, **kwargs):
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    self.__check_file(kwargs, sticker=sticker)
    return self.method('sendSticker', **kwargs)
        
  def media(self, media, chat_id=None, **kwargs):
    kwargs['media'] = json.dumps(media)
    kwargs['chat_id'] = self.get_chat_id(chat_id)
    return self.method('sendMediaGroup', **kwargs)

  def delete(self, chat_id=None, message_id=None):
    kwargs = {'chat_id': self.get_chat_id(chat_id), 'message_id': self.get_message_id(message_id)}
    return self.method('deleteMessage', **kwargs)
        
  def edittext(self, text, chat_id=None, message_id=None, auto=False, **kwargs):
    kwargs['text'] = text
    if auto:
      kwargs['chat_id'] = self.get_chat_id(chat_id)
      kwargs['message_id'] = self.get_message_id(message_id)
    return self.method('editMessageText', **kwargs)
    
  def editcaption(self, caption=None, chat_id=None, message_id=None, auto=False, **kwargs):
    kwargs['caption'] = '' if not caption else caption
    if auto:
      kwargs['chat_id'] = self.get_chat_id(chat_id)
      kwargs['message_id'] = self.get_message_id(message_id)
    return self.method('editMessageCaption', **kwargs)
        
  def editmedia(self, media, **kwargs):
    kwargs['media'] = json.dumps(media)
    return self.method('editMessageMedia', **kwargs)
    
  def editreplymarkup(self, **kwargs):
    return self.method('editMessageReplyMarkup', **kwargs)

  def getfile(self, file_id):
        return self.method('getFile', file_id=file_id)
        
  def fileurl(self, file_id):
    if type(file_id) is str:
      file_id = self.getfile(file_id).send()
      if type(file_id) is dict and file_id['ok']:
        return 'https://api.telegram.org/file/bot{}/{}'.format(self.token, file_id['result']['file_path'])
