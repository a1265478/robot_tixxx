import os
CHROME_IP = 'http://localhost:9222'
USER_DATA_DIR = os.getenv("TIX_USER_DIR", ".pw-user2")
USER_AGENT = os.getenv(
    "TIX_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1280, "height": 900}
LOCALE = os.getenv("TIX_LOCALE", "zh-TW")
IMAGE_PATH = 'captcha.png'
SELL_ICON = "icon_chair_sale_4"
EMPTY_ICON = "icon_chair_empty_4"

### 場次設定
SELL_URL = "https://ticket.com.tw/application/UTK02/UTK0201_00.aspx?PRODUCT_ID=P169BJ5V"
### 尚未開賣測試連結
SELL_URL2 = "https://ticket.com.tw/application/UTK02/UTK0201_00.aspx?PRODUCT_ID=P16YJKVE"
EXCLUDE_AREA = ['遮蔽', '身障','身障']
PREFERRED_AREA = []
COUNT = 2