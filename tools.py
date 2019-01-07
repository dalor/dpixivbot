import asyncio
import aiohttp

class Tools:
    async def __fetch_get(self, url, session, params=None, ref=None):
        async with session.get(url, params=params, headers={'Referer': ref} if ref else None) as resp:
            return await resp.text()

    async def __fetch_post(self, url, session, data, ref=None):
        async with session.post(url, data=data, headers={'Referer': ref} if ref else None) as resp:
            return await resp.text()

    def get(self, url, params=None, ref=None):
        async def __get(url, params=None, ref=None):
            async with aiohttp.ClientSession() as session:
                return await (self.__fetch_get(url, session, params, ref))
        return asyncio.new_event_loop().run_until_complete(__get(url, params, ref))

    def post(self, url, data=None, ref=None):
        async def __get(url, data=None, ref=None):
            async with aiohttp.ClientSession() as session:
                return await (self.__fetch_post(url, session, data, ref))
        return asyncio.new_event_loop().run_until_complete(__get(url, data, ref))
        
    def min_split(self, list_, count):
        new_list = [list_[sp-count:sp] for sp in range(count, len(list_)+1, count)]
        if len(list_) % count: new_list.append(list_[-(len(list_) % count):])
        return new_list