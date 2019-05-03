from .bot_core import BotCore

class Bot(BotCore):
  def __init__(self, token, proxy=None):
    super().__init__(token, proxy)
    self.oop = True
  
  def message(self, text, path=['text']):
    def reg(old):
      self.register(['message'], old, text, path)
      return old
    return reg
    
  def edited_message(self, text, path=['text']):
    def reg(self, old):
      self.register(['edited_message'], old, text, path)
      return old
    return reg
    
  def channel_post(self, text, path=['text']):
    def reg(self, old):
      self.register(['channel_post'], old, text, path)
      return old
    return reg
    
  def edited_channel_post(self, text, path=['text']):
    def reg(self, old):
      self.register(['edited_channel_post'], old, text, path)
      return old
    return reg

  def inline_query(self, text, path=['query']):
    def reg(self, old):
      self.register(['inline_query'], old, text, path)
      return old
    return reg

  def chosen_inline_result(self, text, path=['result_id']):
    def reg(self, old):
      self.register(['chosen_inline_result'], old, text, path)
      return old
    return reg

  def callback_query(self, text, path=['data']):
    def reg(old):
      self.register(['callback_query'], old, text, path)
      return old
    return reg
    
