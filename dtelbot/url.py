import asyncio
import aiohttp

class URL:
    def __init__(self, method, data, bot):
        self.params = data
        self.token = bot.token
        self.method = method
        self.proxy = bot.proxy
    
    async def fetch(self, session):
        if 'data' in self.params:
            file = self.params['data']
            del self.params['data']
            async with session.post('https://api.telegram.org/bot{}/{}'.format(self.token, self.method), params=self.params, data=file, proxy=self.proxy) as response:
                return await response.json()
        else:
            async with session.get('https://api.telegram.org/bot{}/{}'.format(self.token, self.method), params=self.params, proxy=self.proxy) as response:
                return await response.json()
    
    def send(self):
        async def get():
            try:
                async with aiohttp.ClientSession() as session:
                    return await self.fetch(session)
            except:
                return None
        return asyncio.new_event_loop().run_until_complete(get())