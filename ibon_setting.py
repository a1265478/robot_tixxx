# Description: Setting for ibon ticketing
LOGIN_URL = 'https://ticket.ibon.com.tw/'
SELL_URL = 'https://ticket.ibon.com.tw/ActivityInfo/Details/38969'
# SELL_URL = 'https://orders.ibon.com.tw/application/UTK02/UTK0201_001.aspx?PERFORMANCE_ID=B086TCFK&GROUP_ID=10&PERFORMANCE_PRICE_AREA_ID=B086W46O'
# SELL_URL = 'https://orders.ibon.com.tw/application/UTK02/UTK0201_000.aspx?PERFORMANCE_ID=B07ZNUBI&PRODUCT_ID=B07ZKHEO&strItem=WEB%E7%B6%B2%E7%AB%99%E5%85%A5%E5%8F%A31&Token=MTE0LjQ1LjE5My4xNzh8MTc0MTQ0NDE3MzQxMHxtZVViVnd1aEhzWE1PcTMwd296RnFpZEZ4cjFYbFQ4ZC9KbXNYSjU4N3JnPQ=='
# SELL_URL = 'https://ticket.ibon.com.tw/ActivityInfo/Details/38834'
# Description: Account
ACCOUNT = 'tixket000@gmail.com'
PASSWORD = 'forgetP@ssw0rd'
COOKIE = {
    'name': 'ibonqware',
    'value': 'mem_id=19516896488999532918&mem_email=a1265478@gmail.com&huiwanTK=apFVLmgpZMXEJZFixos21ssbv2A1j5P/XDRWKU94aVlVICTYDWQFmGw5vacx1HWoDrtv63Y4D+y7eejrXw4+ZFQxlqWGGpgTvNuZAerrVQU=&ibonqwareverify=f74e512e1e8f2d491b3c&datatime=202503091843&checksum=477ac833b2b068f5223df900172484cb',
    'domain': '.ibon.com.tw',
    'path': '/',
    'httpOnly': True,
    'secure': True,
    'sameSite': 'Lax'
}
NEED_INPUT = False
INPUT_VALUE = '515721'
# Description: Robot setting
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
VIEWPORT = {'width': 1440, 'height': 1080}
IMAGE_PATH = 'captcha.png'
# Description: Hope
TICKET_NUMBER = '2'
EXCLUDED_AREAS = ['身障','搖滾','愛心','一般區','敬老']
PREFERRED_AREAS = ['超級搖滾區']
ONLY_PREFERRED_AREAS = True
PREFERRED_SESSION = '2025/07/05'

# # API Setting
HEADER = {
    'Host': 'ticketapi.ibon.com.tw',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': 'https://ticket.ibon.com.tw/',
    'Content-Type': 'application/json',
    'observe': 'response',
    'Content-Length': '52',
    'Origin': 'https://ticket.ibon.com.tw',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Cookie': 'lastUrl=%2FActivityInfo%2FDetails%2F38735; _ga_0WBR78PRVP=GS1.1.1741458906.1.1.1741458911.55.0.0; _ga=GA1.1.389044735.1741458906; .AspNetCore.Antiforgery.cdV5uW_Ejgc=CfDJ8ATQjvx_LrtIoAKQbYzApU0l0lUkt3YeFNC8rzNuqpCfQGYYSXnSkBRAyzZ9ydPblNPN8-_c6oeYRle7UkLAoOX4-IVs_gsGVvOowT8aiFid6Ae4RuDD-kUThbCTpYrpB7lE-6x-NLo7qI124tV_XDs; XSRF-TOKEN=CfDJ8ATQjvx_LrtIoAKQbYzApU2At5TGxPktDUqe59z0M2uHc5YaqyPE7GP4W1qbLUivh3NwvC8yQjRttHVo0_CE5mEZmzf9kShmtEoFZJ6O0rF5VCGtedf4IAE_ZTylF44jmfYz8uHHUpNQOwJ3HsZ9q_U',
    'X-XSRF-TOKEN': 'CfDJ8ATQjvx_LrtIoAKQbYzApU2At5TGxPktDUqe59z0M2uHc5YaqyPE7GP4W1qbLUivh3NwvC8yQjRttHVo0_CE5mEZmzf9kShmtEoFZJ6O0rF5VCGtedf4IAE_ZTylF44jmfYz8uHHUpNQOwJ3HsZ9q_U'
}

GAME_ID = 38969
GAMES_API = 'https://ticketapi.ibon.com.tw/api/ActivityInfo/GetGameInfoList'
AREA_API = 'https://qwareticket-asysimg.azureedge.net/QWARE_TICKET/images/Temp/{performance_id}/1_{performance_id}_live.map'