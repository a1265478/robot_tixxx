from playwright.async_api import async_playwright, TimeoutError

import asyncio
import os
import setting
import random
from typing import Optional
import time
from random import uniform

class TicketBot:
    def __init__(self):
        self.browser = None
        self.page = None
        # self.ocr_browser = None
        # self.ocr = None
        
    async def init_browser(self):
        """Initialize browser with optimized settings"""

        browser_args = [ 
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-automation',
            '--disable-infobars',
            '--disable-blink-features',
            '--disable-blink-features=AutomationControlled',
            f'--window-size={random.randint(1050, 1200)},{random.randint(800, 900)}',
            '--disable-gpu',
        ]
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            channel='chrome',
            # args=['--disable-dev-shm-usage', '--no-sandbox','--disable-blink-features=AutomationControlled']
            args=browser_args
        )
        # self.ocrBrowser = await playwright.chromium.launch(headless=True)
        context = await self.browser.new_context(
            viewport = setting.VIEWPORT,
            user_agent = setting.USER_AGENT,
            java_script_enabled=True,
            locale='zh-TW',
            timezone_id='Asia/Taipei',
            geolocation={'latitude': 25.0330, 'longitude': 121.5654},
            permissions=['geolocation'],
            color_scheme='light',
            has_touch=True,
        )

        await context.add_init_script("""
            
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [{
                        0: {type: "application/x-google-chrome-pdf"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        name: "Chrome PDF Plugin"
                    }];
                }
            });
            
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-TW', 'zh', 'en-US', 'en']
            });
            
            
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type) {
                const context = originalGetContext.apply(this, arguments);
                if (type === '2d') {
                    const originalFillText = context.fillText;
                    context.fillText = function() {
                        arguments[0] = arguments[0] + ' ';
                        return originalFillText.apply(this, arguments);
                    }
                }
                return context;
            };
        """)
       
        self.page = await context.new_page()
        
        # await stealth_async(self.page)
        # self.ocr = await self.ocrBrowser.new_page()

        # 修改資源攔截策略，允許驗證碼圖片加載
        # await self.page.route("**/*", lambda route: self.handle_route(route))
        await self.add_human_behavior()

    async def add_human_behavior(self):
        """Add random delays and mouse movements to simulate human behavior"""
        async def random_delay():
            await asyncio.sleep(uniform(0.1, 0.3))
            
        async def random_mouse_movement():
            x = random.randint(0, 800)
            y = random.randint(0, 600)
            await self.page.mouse.move(x, y)
            
        self.page.on("load", lambda: random_delay())
        self.page.on("click", lambda: random_mouse_movement())

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
                    # area_status = await area.get_attribute("class")
                    remaining_tickets = await area.get_attribute("data-remaining-tickets")
                    is_hot = "熱賣中" in area_text
                    is_sold_out = "已售完" in area_text or "已售" in area_text
                    if not is_sold_out and (is_hot or (remaining_tickets and int(remaining_tickets) > 2)):
                        available_areas.append((area_text, area))
                    # if not is_sold_out:
                    #     available_areas.append((area_text, area))
                
                if not available_areas:
                    print("所有區域都已售完，準備重新整理...")

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
                if not selected and not setting.ONLY_PREFERRED_AREAS:
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
                    await self.page.reload()
                
                # 可選擇添加短暫延遲以防止過於頻繁的重新整理
                await asyncio.sleep(0.5)
                
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
            await self.page.locator("#bs-navbar").get_by_role("link", name="會員登入").click()
            await self.page.locator("#loginGoogle").click()
            await self.page.get_by_label("電子郵件地址或電話號碼").fill(setting.ACCOUNT)
            await self.page.wait_for_timeout(500)
            await self.page.get_by_label("電子郵件地址或電話號碼").press("Enter")
            await self.page.get_by_label("輸入您的密碼").fill(setting.PASSWORD)
            await self.page.get_by_label("輸入您的密碼").press("Enter")
            while True:
                print("等待登入...")
                if await self.wait_for_clickable(".user-name"):
                    break

            await self.page.goto(setting.SELL_URL, 
                               wait_until='domcontentloaded')
            print("登入成功")

        except Exception as e:
            print(f"登入錯誤: {str(e)}")

    async def ready_to_buy(self):
        """準備購買流程"""
        try:
            while not await self.wait_for_clickable("button:text('立即訂購')",timeout=100):
                print("尚未開賣...")
                await self.page.wait_for_timeout(100)
                await self.page.reload()            
                print("Reload")

        except Exception as e:
            print(f"準備購買錯誤: {str(e)}")

    async def click_buy_now(self):
        """點擊立即購買按鈕"""
        try:
            if await self.wait_for_clickable("button:text('立即訂購')"):
                await self.page.locator('button:text("立即訂購")').click()
        except Exception as e:
            print(f"點擊立即購買按鈕錯誤: {str(e)}")
   
    async def navigate_to_sell_page(self):
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
            # if await self.wait_for_clickable("button:text('立即訂購')"):
            #     await self.page.locator('button:text("立即訂購")').click()
   
            
            # 身分證輸入
            # 排除第一個 input，選擇第二個 input
            # inputs = await self.page.query_selector_all('input[type="text"]')
            # if len(inputs) > 1 and setting.NEED_INPUT:
            #     await inputs[1].fill(setting.MEMBER_NUMBER)
            #     self.page.on("dialog", lambda dialog: dialog.accept())
            #     await self.page.get_by_role("button", name="送出").click()
            # await self.enter_member_number()

             
            # 選擇區域
            # success = await self.select_area()
            # if not success:
                # raise Exception("無法選擇合適的區域")

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
            
            print('送訂單')
            await self.page.pause()

        except Exception as e:
            print(f"完成訂票錯誤: {str(e)}")
        
    async def choose_ticket_count(self):
        # 選擇票數
        try:
            if await self.wait_for_clickable("select"):
                await self.page.locator('select').select_option(setting.TICKET_NUMBER)
                await self.page.get_by_label("我已詳細閱讀且同意").check()
                
        except Exception as e:
            print(f"選擇票數錯誤: {str(e)}")

    async def enter_member_number(self):
        """輸入會員號碼"""
        try:
            inputs = await self.page.query_selector_all('input[type="text"]')
            if len(inputs) > 1 and setting.NEED_INPUT:
                await inputs[1].fill(setting.MEMBER_NUMBER)
                self.page.on("dialog", lambda dialog: dialog.accept())
                await self.page.get_by_role("button", name="送出").click()
        except Exception as e:
            print(f"輸入會員號碼錯誤: {str(e)}")

    async def commit_to_buy(self):
        """確認購買"""
        try:
            await self.choose_ticket_count()
            await self.page.get_by_placeholder("請輸入驗證碼").click()
            while True:
                captcha_text = await self.page.locator("input[placeholder='請輸入驗證碼']").input_value()
                if len(captcha_text) == 4 and captcha_text.isalnum():
                    await self.page.locator("button:text('確認張數')").click()
                    break
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"確認購買錯誤: {str(e)}")

    async def check_is_success(self):   
        try:
            await self.page.wait_for_selector("div:has-text('訂單明細')", timeout=1000)
            return True
        except Exception as e:
            print(f"確認購買錯誤: {str(e)}")
            return False
        
    async def setup_page(self):
        """設置瀏覽器頁面"""
        await self.page.evaluate("document.body.focus()")  # 移除焦點
        await self.page.mouse.click(10, 10)  # 點擊讓焦點回到頁面
        await self.page.keyboard.press("Escape")
        try:
            await self.page.get_by_role("button", name="全部拒絕").click()
        except:
            pass

    async def run(self):
        """主要運行流程"""
        start_time = time.time()

        try:
            await self.init_browser()            
            await self.login()
            await self.page.goto(setting.SELL_URL, 
                               wait_until='domcontentloaded')
            await self.setup_page()
            await self.ready_to_buy()
            await self.navigate_to_sell_page()

            while True: 
                try:
                    if self.page.url == setting.SELL_URL:
                        await self.click_buy_now()
                    if 'verify' in self.page.url:
                        await self.enter_member_number()
                    if 'area' in self.page.url:
                        await self.select_area()
                    if 'ticket/ticket' in self.page.url:
                        await self.commit_to_buy()
                    if 'order' in self.page.url:
                        await self.page.wait_for_timeout(1000)
                    if 'checkout' in self.page.url:
                        break
                    
                except Exception as e:
                    continue

                await asyncio.sleep(0.1)
            # 選擇區域
            # success = await self.select_area()
            # if not success:
            #     raise Exception("無法選擇合適的區域")
            # break
            
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
            # await self.choose_ticket_count()
            # await self.page.wait_for_timeout(500)
            # await self.page.evaluate("document.body.focus()")
            # await self.page.mouse.click(10, 10)
            # await self.page.keyboard.press("Escape")
            # await self.page.get_by_placeholder("請輸入驗證碼").dblclick()
            # while True:
            #     captcha_text = await self.page.locator("input[placeholder='請輸入驗證碼']").input_value()
            #     if len(captcha_text) == 4 and captcha_text.isalnum():
            #         await self.page.locator("button:text('確認張數')").click()
            #         break
            #     await asyncio.sleep(0.1)

            
            
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