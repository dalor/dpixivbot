from dpixiv import DPixivIllusts

class User(DPixivIllusts):
    def __init__(self, session=None, chat_id=None, last_id=None, count=None, only_pics=None, by_one=None):
        super().__init__(session=session)
        self.chat_id = chat_id
        self.last_id = last_id if last_id else 0
        self.count = count if count else 5
        self.only_pics = only_pics if only_pics else 0
        self.by_one = by_one if by_one else 0