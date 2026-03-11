import os
# Description: Setting for ibon ticketing
CHROME_IP = 'http://localhost:9222'
WEBHOOK = 'https://discord.com/api/webhooks/1379701632484376576/mJ7iLgg7Kjr0v5GTmqxQoJmgougR-5SMETpUuzQU_UM3hmkj9pQEe2xMovniSTn3d6fo'
USER_DATA_DIR = os.getenv("TIX_USER_DIR", ".pw-user3")
LOGIN_URL = 'https://ticket.ibon.com.tw/'
# SELL_URL='https://ticket.ibon.com.tw/ActivityInfo/Details/39311'
SELL_URL='https://orders.ibon.com.tw/application/UTK02/UTK0201_000.aspx?PERFORMANCE_ID=B0AHMRYG&PRODUCT_ID=B0AENC27&strItem=WEB%e7%b6%b2%e7%ab%99%e5%85%a5%e5%8f%a31'
NEED_INPUT = False
INPUT_VALUE = '123456'
INPUT_VALUE2 = '000'
# Description: Robot setting
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
VIEWPORT = {'width': 1440, 'height': 1080}
IMAGE_PATH = 'captcha.png'
# Description: Hope
TICKET_NUMBER = '1'
EXCLUDED_AREAS = ['身障', '愛心','視線遮蔽','視線','2980','3980','4980']
PREFERRED_AREAS = []
ONLY_PREFERRED_AREAS = False
PREFERRED_SESSION = 'Moon'
SOUND = 'assets/ding-dong.wav'
# # API Setting
GAME_ID = 39311
GAMES_API = '/api/ActivityInfo/GetGameInfoList'
AREA_API = 'https://qwareticket-asysimg.azureedge.net/QWARE_TICKET/images/Temp/{performance_id}/1_{performance_id}_live.map?v={uuid}'