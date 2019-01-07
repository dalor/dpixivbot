import re
import json
import aiohttp
import asyncio

post_key_search = re.compile(r'name\=\"post_key\" value\=\"([a-z0-9]+)\"')
tt_search = re.compile(r'name\=\"tt\" value\=\"([a-z0-9]+)\"')
reccomend_sample_search = re.compile(r'illustRecommendSampleIllust \= \"([0-9\,]+)\"\;')
info_json_pattern = re.compile('\}\)\((\{token\:.+\})\)\;\<\/script\>')
info_fix_json = re.compile(r'([\,\{]) ?(\w+):')
find_data_items = re.compile(r'data\-items\=\"(\[.+\])\"')

class DPixivIllusts:
    def __init__(self, login, password, session=None, tt=None):
        self.login = login
        self.password = password
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36'}
        self.tt = tt
        self.cookies = {'PHPSESSID': session} if session else {} 
        self.auth()
    
    def get_session(self):
        return self.cookies['PHPSESSID'] if 'PHPSESSID' in self.cookies else None
    
    async def __fetch_get(self, url, session, params=None, ref=None):
        async with session.get(url, params=params, headers={'Referer': ref} if ref else None) as resp:
            return await resp.text()
            
    async def __fetch_get_with_id(self, url, id_, session, params=None, ref=None):
        async with session.get(url, params=params, headers={'Referer': ref} if ref else None) as resp:
            return {id_: (await resp.text())}
            
    async def __fetch_post(self, url, session, data):
        async with session.post(url, data=data) as resp:
            return await resp.text()
    
    async def __get(self, url, params=None, ref=None):
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            return await (self.__fetch_get(url, session, params, ref))
            
    async def __get_list_with_id_prepare(self, list_):
        new_list_ = {}
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            for resp in (await asyncio.gather(*[asyncio.ensure_future(self.__fetch_get_with_id(url, id_, session)) for id_, url in list_.items()])):
                new_list_.update(resp)
        return new_list_
    
    def __get_list_with_id(self, list_):
        return asyncio.new_event_loop().run_until_complete(self.__get_list_with_id_prepare(list_))   
         
    def get(self, url, params=None, ref=None):
        return asyncio.new_event_loop().run_until_complete(self.__get(url, params, ref))
    
    def auth(self): #Use to set up all cookies use again to reauth
        async def work_in_one_session():
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
                if not await self.__is_auth(session):
                    login_page = await (self.__fetch_get('https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index', session))
                    prepost_key = post_key_search.search(login_page)
                    login_params = {
                        'password': self.password,
                        'pixiv_id': self.login,
                        'captcha': '',
                        'g_recaptcha_response': '',
                        'post_key': prepost_key[1] if prepost_key else None,
                        'ref': 'wwwtop_accounts_index',
                        'return_to': 'https://www.pixiv.net/',
                        'source': 'pc'
                    }
                    await (self.__fetch_post('https://accounts.pixiv.net/api/login?lang=en', session, data=login_params))
                    await self.__set_tt(session)
                    clear_cookies = {cookie.key:cookie.value for cookie in session.cookie_jar if cookie.key == 'PHPSESSID'}
                    self.cookies = clear_cookies
                elif not self.tt:
                    await self.__set_tt(session)
        asyncio.new_event_loop().run_until_complete(work_in_one_session())
    
    async def __set_tt(self, session):
        prett = tt_search.search(await (self.__fetch_get('https://www.pixiv.net', session)))
        self.tt = prett[1] if prett else None
    
    async def __is_auth(self, session):
        get_result = await (self.__fetch_get('https://www.pixiv.net/rpc/index.php?mode=message_thread_unread_count', session))
        result = json.loads(get_result)
        if 'error' in result and not result['error']:
            return True
        else:
            return False
    
    def recommender(self, sample_illusts=None, count=100): #Return list of recommendations or None if error; sample_illusts - id or list ids; can be executed without parameters and show all recommendations
        rec_params = {
            'type': 'illust',
            'num_recommendations': count,
            'tt': self.tt
        }
        if not sample_illusts:
            rec_params.update({'mode': 'all', 'page': 'discovery'})
        else:
            rec_params.update({'sample_illusts': ','.join(sample_illusts) if type(sample_illusts) == list else sample_illusts})
        rec_resp = json.loads(self.get('http://www.pixiv.net/rpc/recommender.php', params=rec_params, ref='https://www.pixiv.net/discovery'))
        return [i for i in rec_resp['recommendations']] if 'recommendations' in rec_resp else None
    
    def similar(self, id, limit=10): 
        sim_resp = json.loads(self.get('https://www.pixiv.net/ajax/illust/{}/recommend/init?limit={}'.format(id, limit)))
        return [one['workId'] for one in sim_resp['body']['illusts']] if not sim_resp['error'] else None
    
    def load_ids_from_pages(self, url, parser, page, from_page, to_page, step_count):
        url = url + '?p={}'
        if page:
            return parser(self.get(url.format(page)))
        else:
            results = []
            if step_count > to_page: step_count = to_page
            pg = from_page
            end = False
            while not end and pg <= to_page:
                prepared = self.__get_list_with_id({i: url.format(i) for i in range(pg, step_count + pg)})
                prepared_items = sorted(prepared.items())
                for key, value in prepared_items:
                    parsed = parser(value)
                    if parsed:
                        results.extend(parser)
                    else:
                        end = True
                pg += step_count
            return results if results else None
    
    def bookmarks_parser(self, page):
        res_parse = reccomend_sample_search.search(page)
        return res_parse[1].split(',') if res_parse else None
            
    def bookmarks(self, page=None, from_page=1, to_page=1000000, step_count=10): #Get bookmarks of user
        url = 'https://www.pixiv.net/bookmark.php'
        return self.load_ids_from_pages(url, self.bookmarks_parser, page, from_page, to_page, step_count)
    
    def new_work_following_parser(self, page):
        res_parse = find_data_items.search(page)
        if res_parse:
            return [one['illustId'] for one in json.loads(res_parse[1].replace('&quot;', '"'))]

    def new_work_following(self, page=None, from_page=1, to_page=1000000, step_count=10):
        url = 'https://www.pixiv.net/bookmark_new_illust.php'
        return self.load_ids_from_pages(url, self.new_work_following_parser, page, from_page, to_page, step_count)
        
    def illust_list(self, illusts): #Returns list of descriptions of illusts; illusts - one id or list of ids
        list_params = {
            'exclude_muted_illusts': 1,
            'illust_ids': ','.join(illusts),
            'page': 'discover',
            'tt': self.tt
        }
        return json.loads(self.get('https://www.pixiv.net/rpc/illust_list.php', params=list_params, ref='https://www.pixiv.net/discovery'))
    
    def __parse_info(self, page):
        find_json = info_json_pattern.search(page)
        if find_json:
            result = json.loads(info_fix_json.sub(r'\1"\2":', find_json[1].replace(',}','}')))
            return result['preload']['illust'] if 'preload' in result and 'illust' in result['preload'] else None
    
    def info(self, id): #Return all info; get one id
        return self.__parse_info(self.get('https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(id)))
    
    def info_packs(self, illusts): #Return all info; get list of ids
        pages = self.__get_list_with_id({one: 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format(one) for one in illusts})
        return [self.__parse_info(pages[ilust]) for ilust in illusts]
        
    