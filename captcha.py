import asyncio
from playwright.sync_api import sync_playwright

def google_lens_ocr(image_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 設定 headless=True 可隱藏瀏覽器
        page = browser.new_page()

        # 1. 打開 Google Lens
        page.goto("https://lens.google.com/")

        # 2. 上傳驗證碼圖片
        input_element = page.query_selector('input[type="file"]')
        input_element.set_input_files(image_path)
        page.locator("img[jsname='kSDGid']").wait_for(state='visible')
        page.locator("img[jsname='kSDGid']").click()        
        # page.wait_for_timeout(3000)
        # page.locator("#tsf c-wiz img").dblclick()
        # element.click()        
        # page.wait_for_timeout(1000)
        
        # page.pause()
        # 等待 Google Lens OCR 解析
        page.wait_for_selector("div[jsname='JdLDjd']", timeout=10000)

        # 3. 擷取 OCR 解析結果
        ocr_result = page.inner_text("div[jsname='JdLDjd']")  # 可能需要調整選擇器
        print("Google Lens OCR 解析結果:", ocr_result.strip())
        # page.pause()
        browser.close()
        

image_path = "captcha.png"
google_lens_ocr(image_path)
#https://www.google.com/webhp?hl=zh-TW&sa=X&ved=0ahUKEwi80MDRwquLAxWvdPUHHXJOADcQPAgI