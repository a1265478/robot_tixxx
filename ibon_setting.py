import os
# Description: Setting for ibon ticketing
USER_DATA_DIR = os.getenv("TIX_USER_DIR", ".pw-user3")
LOGIN_URL = 'https://ticket.ibon.com.tw/'
SELL_URL = 'https://ticket.ibon.com.tw/ActivityInfo/Details/39311'
# SELL_URL = 'https://orders.ibon.com.tw/application/UTK02/UTK0201_001.aspx?PERFORMANCE_ID=B086TCFK&GROUP_ID=10&PERFORMANCE_PRICE_AREA_ID=B086W46O'
# SELL_URL = 'https://orders.ibon.com.tw/application/UTK02/UTK0201_000.aspx?PERFORMANCE_ID=B07ZNUBI&PRODUCT_ID=B07ZKHEO&strItem=WEB%E7%B6%B2%E7%AB%99%E5%85%A5%E5%8F%A31&Token=MTE0LjQ1LjE5My4xNzh8MTc0MTQ0NDE3MzQxMHxtZVViVnd1aEhzWE1PcTMwd296RnFpZEZ4cjFYbFQ4ZC9KbXNYSjU4N3JnPQ=='
# SELL_URL = 'https://ticket.ibon.com.tw/ActivityInfo/Details/38834'
# Description: Account
ACCOUNT = 'tixket000@gmail.com'
PASSWORD = 'forgetP@ssw0rd'
NEED_INPUT = False
INPUT_VALUE = '123456'
INPUT_VALUE2 = '000'
# Description: Robot setting
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
VIEWPORT = {'width': 1440, 'height': 1080}
IMAGE_PATH = 'captcha.png'
# Description: Hope
TICKET_NUMBER = '1'
EXCLUDED_AREAS = ['身障', '愛心']
PREFERRED_AREAS = []
ONLY_PREFERRED_AREAS = False
PREFERRED_SESSION = 'Moon'
SOUND = 'assets/ding-dong.wav'
# # API Setting
HEADER = {
    'Accept':'application/json, text/plain, */*',
    'Accept-Encoding':'gzip, deflate, br',
    'Accept-Language':'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Origin':'https://ticket.ibon.com.tw',
    'Referer':'https://ticket.ibon.com.tw',
    'Content-length':'52',
    'Content-Type':'application/json',
    'Priority':'u=1, i',
    'Connection':'keep-alive',
    'Observe':'response',
    'Origin':'https://ticket.ibon.com.tw',
    'Sec-Ch-Ua':'"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'Sec-Ch-Ua-Mobile':'?0',
    'Sec-Ch-Ua-Platform':'"macOS"',
    'Sec-Fetch-Site':'same-origin',
    'Sec-Fetch-Dest':'empty',
    'Sec-Fetch-Mode':'cors',
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'Cookie':'_cfuvid=bW.9m5HxXysGiKPVilAg80q3_rjLzZUbw.EZY8TGRVI-1767173141474-0.0.1.1-604800000; _ga=GA1.1.107305656.1767173142; _qg_fts=1767173142; QGUserId=1934037451868603; bb_page-6ffdc6af531e40c38e786363_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJiYi11cWc3dFA3REFsaGFtdXRxWjctdFUiLCJwYWdlSWQiOiJwYWdlLTZmZmRjNmFmNTMxZTQwYzM4ZTc4NjM2MyIsImJvdElkIjoiYm90LVdZbnBHdFRmNCIsImlhdCI6MTc2NzE3MzE0MiwiaXNzIjoiYm90Ym9ubmllX3dlYmNoYXQifQ.hKcWLTbNDOWuBZn5fnd06CKLNWT_t1Kxw3qymbzsMoE; bb_page-6ffdc6af531e40c38e786363_uuid=bb-uqg7tP7DAlhamutqZ7-tU; _qg_cm=2; bb_binding_bb-uqg7tP7DAlhamutqZ7-tU_1934037451868603_v2=appier-12ae48c128e3a1b26753de5a4c7bec6d; _ga_0WBR78PRVP=GS2.1.s1767317089$o2$g0$t1767317089$j60$l0$h0; __cf_bm=fbHPcTfC3C3atTuvEPozwZLnYBhebH.ILRIkv0kIxk8-1767321048-1.0.1.1-HFUAVxUK5uHPkZ_OoADJiwb8DzQ.CEFZ4nk8yA9mnf.CXVU795ANr.xhXgyxHWSXfu055dxOR1mZWqB4YhgkOp15W1cUuIzBLufp6UyxxWI; lastUrl=%2FActivityInfo%2FDetails%2F39311'
  }

GAME_ID = 39311
GAMES_API = 'https://ticket.ibon.com.tw/api/ActivityInfo/GetGameInfoList'
AREA_API = 'https://qwareticket-asysimg.azureedge.net/QWARE_TICKET/images/Temp/{performance_id}/1_{performance_id}_live.map'