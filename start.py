from playwright.async_api import async_playwright, TimeoutError

import asyncio
import os
import setting
import random
from typing import Optional
import easyocr
import time

class TicketBot:
    def __init__(self):
        self.browser = None
        self.page = None
        # self.ocr_browser = None
        # self.ocr = None
        self.area_locator = setting.AREA_LOCATOR_TEST
        
    async def init_browser(self):
        """Initialize browser with optimized settings"""
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            channel='chrome',
            args=['--disable-dev-shm-usage', '--no-sandbox','--disable-blink-features=AutomationControlled']
        )
        # self.ocrBrowser = await playwright.chromium.launch(headless=True)
        context = await self.browser.new_context(
            viewport = setting.VIEWPORT,
            user_agent = setting.USER_AGENT,
            java_script_enabled=True,
        )
       
        self.page = await context.new_page()
        # await stealth_async(self.page)
        # self.ocr = await self.ocrBrowser.new_page()

        # 修改資源攔截策略，允許驗證碼圖片加載
        # await self.page.route("**/*", lambda route: self.handle_route(route))

    async def handle_route(self, route):
        """智能處理資源請求"""
        request = route.request
        resource_type = request.resource_type
        url = request.url

        # 允許驗證碼相關的請求
        if 'captcha' in url.lower():
            await route.continue_()
            return

        # 根據資源類型選擇性攔截
        if resource_type in ['image', 'font', 'media']:
            # 允許驗證碼圖片相關的請求
            if '.png' in url and 'captcha' in url:
                await route.continue_()
            else:
                await route.abort()
        elif resource_type == 'stylesheet':
            # 只允許必要的 CSS
            if 'essential' in url or 'main' in url:
                await route.continue_()
            else:
                await route.abort()
        elif resource_type == 'script':
            # 只允許必要的 JS
            if 'essential' in url or 'main' in url or 'captcha' in url:
                await route.continue_()
            else:
                await route.abort()
        else:
            # 允許其他必要請求
            await route.continue_()

    async def select_area(self):
        """選擇區域"""
        try:
            while True:
                # 等待區域選項出現
                await self.page.wait_for_selector(setting.AREA_LOCATOR)
                
                # 獲取所有區域元素
                areas = await self.page.query_selector_all(setting.AREA_LOCATOR)
                print(f"找到 {len(areas)} 個區域")
                # 檢查是否有任何區域可選
                if not areas:
                    print("沒有找到任何區域，準備重新整理...")
                    await self.page.reload()
                    continue
                
                # 獲取所有區域的文本和狀態
                available_areas = []
                for area in areas:
                    # 獲取區域文本
                    area_text = await area.text_content()
                    # 檢查是否可選（不含"已售完"或其他不可選狀態）
                    is_sold_out = "已售完" in area_text or "已售" in area_text
                    if not is_sold_out:
                        available_areas.append((area_text, area))
                
                if not available_areas:
                    print("所有區域都已售完，準備重新整理...")
                    await self.page.pause()
                    await self.page.reload()
                    continue
                
                # 按照優先順序尋找可用區域
                selected = False
                # 優先選擇偏好區域
                for preferred in setting.PREFERRED_AREAS:
                    for area_text, area in available_areas:
                        if preferred in area_text and not any(excluded in area_text for excluded in setting.EXCLUDED_AREAS):
                            try:
                                await area.click()
                                print(f"成功選擇偏好區域: {area_text}")
                                selected = True
                                return True
                            except Exception as e:
                                print(f"點擊偏好區域 {area_text} 時發生錯誤: {str(e)}")
                                continue
                
                # 如果沒有偏好區域，選擇有位置並沒被排除的區域
                if not selected:
                    for area_text, area in available_areas:
                        if not any(excluded in area_text for excluded in setting.EXCLUDED_AREAS):
                            try:
                                await area.click()
                                print(f"成功選擇區域: {area_text}")
                                selected = True
                                return True
                            except Exception as e:
                                print(f"點擊區域 {area_text} 時發生錯誤: {str(e)}")
                                continue
                
                # 如果沒有找到理想的區域，重新整理
                if not selected:
                    print("沒有找到理想的區域，準備重新整理...")
                    await self.page.pause()
                    await self.page.reload()
                
                # 可選擇添加短暫延遲以防止過於頻繁的重新整理
                await asyncio.sleep(0.5)
                await self.page.pause()

                
        except Exception as e:
            print(f"選擇區域時發生錯誤: {str(e)}")
            return False

    async def wait_for_clickable(self, selector: str, timeout: int = 3000) -> bool:
        """等待元素可點擊，有超時機制"""
        try:
            element = self.page.locator(selector)
            await element.wait_for(state='visible', timeout=timeout)
            return True
        except TimeoutError:
            return False
        
    async def login(self):
        """登入流程"""
        try:
            await self.page.goto(setting.LOGIN_URL, wait_until='domcontentloaded')
            await self.page.evaluate("document.body.focus()")
            await self.page.locator("#bs-navbar").get_by_role("link", name="會員登入").click()
            await self.page.locator("#loginGoogle").click()
            await self.page.get_by_label("電子郵件地址或電話號碼").click()
            await self.page.get_by_label("電子郵件地址或電話號碼").fill(setting.ACCOUNT)
            await self.page.get_by_label("電子郵件地址或電話號碼").press("Enter")
            await self.page.get_by_label("輸入您的密碼").fill(setting.PASSWORD)
            await self.page.get_by_label("輸入您的密碼").press("Enter")
            await self.page.locator("#user-name").is_visible()
            await self.page.goto(setting.SELL_URL, 
                               wait_until='domcontentloaded')
            print("登入成功")
            

        except Exception as e:
            print(f"登入錯誤: {str(e)}")

    async def ready_to_buy(self):
        """準備購買流程"""
        try:
            while not await self.wait_for_clickable("button:text('立即訂購')"):
                await self.page.wait_for_timeout(100)
                await self.page.reload()            
        except Exception as e:
            print(f"準備購買錯誤: {str(e)}")
   
    async def navigate_and_fill_initial(self):
        """執行初始導航和表單填寫，使用最小等待時間"""
        try:
            print("導航到購票頁面...")
            await self.page.goto(setting.SELL_URL, 
                               wait_until='domcontentloaded')
            await self.page.evaluate("document.body.focus()")
            
            
            # 倒數輸入框
            # if await self.wait_for_clickable("[placeholder='請輸入倒數秒數']"):
            #     await self.page.get_by_placeholder("請輸入倒數秒數").fill("1")
            #     await self.page.get_by_role("button", name="開始倒數計時").click()
            
            # 立即購票按鈕
            # if await self.wait_for_clickable("button:text('立即購票')"):
            #     await self.page.locator('button:text("立即購票")').click()
            
            # 立即訂購按鈕
            if await self.wait_for_clickable("button:text('立即訂購')"):
                await self.page.locator('button:text("立即訂購")').click()
            # await self.page.get_by_role("row", name="/03/29 (六) ~ 2025/03/30 (日) 大港人優先購專區 高雄駁二藝術特區 立即訂購 選購一空").get_by_role("button").click() 
   
            
            # 身分證輸入
            # 排除第一個 input，選擇第二個 input
            inputs = await self.page.query_selector_all('input[type="text"]')
            if len(inputs) > 1 and setting.NEED_INPUT:
                await inputs[1].fill(setting.MEMBER_NUMBER)
                self.page.on("dialog", lambda dialog: dialog.accept())
                await self.page.get_by_role("button", name="送出").click()

             
            # 選擇區域
            success = await self.select_area()
            if not success:
                raise Exception("無法選擇合適的區域")

        except Exception as e:
            print(f"初始導航和表單填寫錯誤: {str(e)}")

    async def check_and_handle_dialog(self, timeout: int = 1000) -> bool:
        """
        檢查是否有彈出對話框並處理
        return: True 如果有對話框並處理了, False 如果沒有對話框
        """
        try:
            # 等待對話框出現，但如果沒有也不報錯
            dialog_button = self.page.locator("button:has-text('確定')")
            is_visible = await dialog_button.is_visible()
            
            if is_visible:
                # 找到對話框，點擊確認按鈕
                await dialog_button.click()
                print("發現對話框並處理完成")
                return True
            
            return False
        except Exception as e:
            print(f"處理對話框時發生錯誤: {str(e)}")
            return False
        
    async def complete_booking(self, captcha_text: str):
        """完成訂票流程"""
        try:
            # 同時執行驗證碼填寫和勾選同意
            print("填寫驗證碼並確認張數...")
            await self.page.get_by_placeholder("請輸入驗證碼").fill(captcha_text)

            if await self.wait_for_clickable("button:text('確認張數')"):
                await self.page.locator('button:text("確認張數")').click()
            
            # if await self.check_and_handle_dialog():
            #     raise Exception("訂票失敗")
            print('送訂單')
            await self.page.pause()

        except Exception as e:
            print(f"完成訂票錯誤: {str(e)}")

    def recognize_captcha(self)-> Optional[str]:
        """識別驗證碼"""
        reader = easyocr.Reader(['en']) 
        result = reader.readtext(setting.IMAGE_PATH,allowlist='abcdefghijklmnopqrstuvwxyz')

        # 解析結果
        captcha_text = "".join([res[1] for res in result])  # 取出 OCR 識別的文字
        print("EasyOCR 辨識結果:", captcha_text)
        if not captcha_text.isalpha() or len(captcha_text) != 4:
            return None
        
        return captcha_text.strip()


    async def captcha_screenshot(self):
        """處理驗證碼識別，確保圖片完全加載"""
        try:
            # 等待驗證碼圖片出現
            await self.page.wait_for_selector("#TicketForm_verifyCode-image", state="visible", timeout=5000)

            # 等待 naturalWidth > 0
            await self.page.wait_for_function(
                "() => document.querySelector('#TicketForm_verifyCode-image')?.naturalWidth > 0"
            )

            # 等待 complete 屬性
            await self.page.wait_for_function(
                "() => document.querySelector('#TicketForm_verifyCode-image')?.complete === true"
            )

            # **強制重繪**
            # await self.page.evaluate("document.querySelector('#TicketForm_verifyCode-image').getBoundingClientRect()")

            # 截圖
            await self.page.evaluate("document.querySelector('#TicketForm_verifyCode-image').style.opacity = '1'")
            await self.page.evaluate("document.querySelector('#TicketForm_verifyCode-image').style.display = 'block'")
            await self.page.evaluate("""
                let img = document.querySelector('#TicketForm_verifyCode-image');
                img.style.zIndex = '9999';
            """)
            # 確保圖片元素完全可見
            await self.page.wait_for_timeout(300)
            # img_src = await self.page.evaluate("document.querySelector('#TicketForm_verifyCode-image').src")
            # print("驗證碼圖片網址：", img_src)
            # await page.screenshot(path="captcha.png")
            # response = requests.get(img_src)
            # with open(setting.IMAGE_PATH, "wb") as f:
            #     f.write(response.content)
            image_element = self.page.locator('#TicketForm_verifyCode-image')
            await image_element.screenshot(path=setting.IMAGE_PATH)
        except Exception as e:
            print(f"驗證碼處理錯誤: {str(e)}")
            return None
        
    async def choose_ticket_count(self):
        # 選擇票數
        try:
            if await self.wait_for_clickable("select"):
                await self.page.locator('select').select_option(setting.TICKET_NUMBER)
                await self.page.get_by_label("我已詳細閱讀且同意").check()
                
        except Exception as e:
            print(f"選擇票數錯誤: {str(e)}")

    async def run(self):
        """主要運行流程"""
        start_time = time.time()

        try:
            await self.init_browser()            
            # await self.ocr.goto(setting.GOOGLE_LENS_URL)
            await self.login()
            await self.page.goto(setting.SELL_URL, 
                               wait_until='domcontentloaded')
            await self.page.evaluate("document.body.focus()")  # 移除焦點
            await self.page.mouse.click(10, 10)  # 點擊讓焦點回到頁面
            await self.page.keyboard.press("Escape")
            await self.page.get_by_role("button", name="全部拒絕").click()

            await self.ready_to_buy()
            await self.navigate_and_fill_initial()
            
            # retry_count = 0
            # max_retries = 10
            
            # while retry_count < max_retries:
            #     try:
            #         # 重試計數
            #         print(f"第 {retry_count + 1} 次嘗試...")
                    

            #         # await self.captcha_screenshot()
            #         # captcha_text = self.recognize_captcha()
            #         # if captcha_text:
            #         #     await self.complete_booking(captcha_text)
            #         #     break
            #     except Exception:
            #         retry_count += 1
            #         await asyncio.sleep(0.5)
            await self.choose_ticket_count()
            await self.page.wait_for_timeout(500)
            await self.page.evaluate("document.body.focus()")
            await self.page.mouse.click(10, 10)
            await self.page.keyboard.press("Escape")
            await self.page.get_by_placeholder("請輸入驗證碼").dblclick()
            while True:
                captcha_text = await self.page.locator("input[placeholder='請輸入驗證碼']").input_value()
                if len(captcha_text) == 4 and captcha_text.isalnum():
                    await self.page.locator("button:text('確認張數')").click()
                    break
                await asyncio.sleep(0.1)

            
            
        except Exception as e:
            print(f"執行過程發生錯誤: {str(e)}")
        finally:
            if self.browser:
                end_time = time.time()
                print("搶票自動化流程結束")
                print("搶票流程完成，瀏覽器保持開啟中，請手動關閉...")
                print(f"總耗時: {end_time - start_time} 秒")
                self.keep_running = asyncio.Event()  # 建立事件
                await self.keep_running.wait()
                
      
async def main():
    bot = TicketBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())