default_arguments = 'i([0-9]+) p([0-9]+) c([0-9]+) o([01]) b([01]) ([0-9]+)/([0-9]+) s([01])'

class Parameters:
    def __init__(self, pic_id=None, page=0, count=5, only_pics=0, by_one=0, ppic=0, mppic=1, show=0):
        self.pic_id = pic_id
        self.page = page
        self.count = count
        self.only_pics = only_pics
        self.by_one = by_one
        self.ppic = ppic
        self.mppic = mppic
        self.show = show
        
    def format(self):
        return 'i{} p{} c{} o{} b{} {}/{} s{}'.format(
            self.pic_id,
            self.page,
            self.count,
            self.only_pics,
            self.by_one,
            self.ppic,
            self.mppic,
            self.show
            )