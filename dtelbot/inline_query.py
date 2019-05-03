import json

class InlineQuery:
    def __init__(self, type, data, args, bot):
        self.data = data
        self.args = args
        self.type = 'inline_query'
        self.bot = bot
        self.__session = None

    @property
    def session(self):
        if not self.__session:
            self.__session = self.bot.get_session(self)
        return self.__session
        
    def answer(self, results, **kwargs):
        kwargs['inline_query_id'] = self.data['id']
        kwargs['results'] = json.dumps(results)
        return self.bot.method('answerInlineQuery', **kwargs)
