class CallbackQuery:
    def __init__(self, type, data, args, bot):
        self.data = data
        self.args = args
        self.type = 'callback_query'
        self.bot = bot
        self.__session = None

    @property
    def session(self):
        if not self.__session:
            self.__session = self.bot.get_session(self)
        return self.__session
        
    def answer(self, **kwargs):
        kwargs['callback_query_id'] = self.data['id']
        return self.bot.method('answerCallbackQuery', **kwargs)
    