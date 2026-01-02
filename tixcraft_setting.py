import os

LOGIN_URL = 'https://tixcraft.com/'
# ACCOUNT = 'tixket000@gmail.com'
ACCOUNT = 'stanfordma90@gmail.com'
# PASSWORD = 'iLoveWhee'
PASSWORD = 'stanfordmaS05190'
CAPTCHA = 'captcha.txt'

# CAPTCHA = 'captcha.txt'

# 3/20
# SELL_URL = 'https://tixcraft.com/ticket/area/26_twice/21471'
# 3/22
# SELL_URL = 'https://tixcraft.com/ticket/area/26_twice/21455'
SELL_URL = 'https://tixcraft.com/ticket/area/26_twice/21471'

AREA_LOCATOR = 'div[class*="area-list"] li'
USER_AGENT = os.getenv(
    "TIX_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1280, "height": 900}
LOCALE = os.getenv("TIX_LOCALE", "zh-TW")
IMAGE_PATH = 'captcha.png'
GOOGLE_LENS_URL = 'https://lens.google.com/'
OCR_IMAGE_LOCATOR = "#TicketForm_verifyCode-image"
OCR_TEXT_LOCATOR = "div[jsname='JdLDjd']"
NEED_INPUT = False
MEMBER_NUMBER = '42843038'
# 803291
# 391112
TICKET_NUMBER = '2'
EXCLUDED_AREAS = ['身障','愛心','2樓','2800','3800','1800','5800','4800','6800']
PREFERRED_AREAS = ['8800']
ONLY_PREFERRED_AREAS = False
SOUND = 'assets/ding-dong.wav'
WEBHOOK = 'https://discord.com/api/webhooks/1379701632484376576/mJ7iLgg7Kjr0v5GTmqxQoJmgougR-5SMETpUuzQU_UM3hmkj9pQEe2xMovniSTn3d6fo'

USER_DATA_DIR = os.getenv("TIX_USER_DIR", ".pw-user")
USER_DATA_DIR2 = os.getenv("TIX_USER_DIR", ".pw-user2")
DAY_WORD = '2026/03/20 (五) 19:00'
# DAY_WORD = '2026/03/22 (日) 18:00'