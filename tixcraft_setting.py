import os
CHROME_IP = 'http://localhost:9222'
LOGIN_URL = 'https://tixcraft.com/'
CAPTCHA = 'captcha.txt'

# CAPTCHA = 'captcha.txt'

# SELL_URL = 'https://tixcraft.com/ticket/area/26_itzy/22156'
SELL_URL = 'https://tixcraft.com/ticket/area/26_ive/22286'

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
MEMBER_NUMBER = '469656'
# 803291
# 391112
TICKET_NUMBER = '1'
EXCLUDED_AREAS = ['特1區','身障','愛心','2800','2300','黃3']
# EXCLUDED_AREAS = ['身障','愛心']
PREFERRED_AREAS = ['5800']
ONLY_PREFERRED_AREAS = False
SOUND = 'assets/ding-dong.wav'
WEBHOOK = 'https://discord.com/api/webhooks/1379701632484376576/mJ7iLgg7Kjr0v5GTmqxQoJmgougR-5SMETpUuzQU_UM3hmkj9pQEe2xMovniSTn3d6fo'

USER_DATA_DIR = os.getenv("TIX_USER_DIR", ".pw-user")
USER_DATA_DIR2 = os.getenv("TIX_USER_DIR", ".pw-user2")
DAY_WORD = '2026/09/11 (五) 19:00'
# DAY_WORD = '2026/03/22 (日) 18:00'

RELOAD_PROFILE = "peak"

RELOAD_PROFILES = {
    "peak": {
        "mu": 0.55, "sigma": 0.1,
        "min": 0.3, "max": 0.8,
        "hesitate_prob": 0.08,
        "hesitate_min": 0.8, "hesitate_max": 1.5,
    },
    "waiting": {
        "mu": 1.2, "sigma": 0.3,
        "min": 0.8, "max": 2.0,
        "hesitate_prob": 0.15,
        "hesitate_min": 2.0, "hesitate_max": 4.0,
    },
    "cautious": {
        "mu": 1.5, "sigma": 0.4,
        "min": 1.0, "max": 2.5,
        "hesitate_prob": 0.2,
        "hesitate_min": 3.0, "hesitate_max": 6.0,
    },
}