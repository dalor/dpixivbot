class ChosenInlineResult:
    def __init__(self, type, data, args, bot):
        self.data = data
        self.args = args
        self.type = 'chosen_inline_result'
        self.bot = bot
        self.__session = None

    @property
    def session(self):
        if not self.__session:
            self.__session = self.bot.get_session(self)
        return self.__session