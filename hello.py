from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://ticket-training.onrender.com/checking?seat=A4%E5%8D%80&price=6680&color=%2306002a")
    element = page.locator('.captcha-image')
    element.wait_for(state='visible')
    print('Image loaded')
    element.screenshot(path="captcha.png")
    page.wait_for_timeout(3000)
    captcha_text = pytesseract.image_to_string(Image.open("captcha.png"))
    print('Captcha text:', captcha_text.strip())
    
    
    page.get_by_placeholder("請輸入驗證碼").fill(captcha_text.strip())
    page.get_by_label("我已詳細閱讀且同意會員服務條款及節目資訊公告，並同意放棄契約審閱期，且授權貴公司可於條款中的範圍內，進行本人之個人資料蒐集、處理及利用。").check()
    page.get_by_role("button", name="確認張數").click()

    page.wait_for_timeout(30000)


# https://tixcraft.com/activity/detail/25_taeyeon
# https://ticket-training.onrender.com/