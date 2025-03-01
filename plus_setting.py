LOGIN_URL = 'https://ticketplus.com.tw/'
PHONE = '929155921'
ACCOUNT = 'tixket000'
PASSWORD = 'ohMyWhee1n'
SELL_URL = 'https://ticketplus.com.tw/order/a4f9ce1cad2e1d670a946d62dd62acee/c2e15e46c3ba58f87f4474f5f3edc4cd'
# SELL_URL = 'https://ticketplus.com.tw/order/aeda973d460ddf716e04112957161895/233c27bca7e2c83bae675c5c58fe4dfd'
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
# AREA_LOCATOR = '.v-expansion-panel'
AREA_LOCATOR = 'div.seats-area > div.v-expansion-panel'

VIEWPORT = {'width': 1600, 'height': 900}
TICKET_NUMBER = 1

EXCLUDED_AREAS = ['已售完','身心障礙','身障','愛心','剩餘0']
# PREFERRED_AREAS = ['A5區', 'A6區','A7區','A8區','A9區', 'A10區','A11區','A12區']
PREFERRED_AREAS = ['A']
ONLY_PREFERRED_AREAS = False

