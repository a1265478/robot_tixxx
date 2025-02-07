from playwright.async_api import async_playwright, TimeoutError
import asyncio
import os
import setting
import random
from typing import Optional
import time
import logging
from random import uniform

class TicketBot:
    def __init__(self):
        self.browser = None
        self.page = None
        self.area_locator = setting.AREA_LOCATOR_TEST
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ticket_bot.log'),
                logging.StreamHandler()
            ]
        )
        
    async def init_browser(self):
        """Initialize browser with enhanced anti-detection measures"""
        playwright = await async_playwright().start()
        
        # Enhanced browser arguments for anti-detection
        self.browser = await playwright.chromium.launch(
            headless=False,
            channel='chrome',
            args=['--disable-dev-shm-usage', '--no-sandbox','--disable-blink-features=AutomationControlled']
        )
        
        context = await self.browser.new_context(
            viewport = setting.VIEWPORT,
            user_agent = setting.USER_AGENT,
            java_script_enabled=True,
        )

        # Enhanced context settings
        context = await self.browser.new_context(
            viewport=setting.VIEWPORT,
            user_agent=setting.USER_AGENT,
            java_script_enabled=True,
            locale='zh-TW',
            timezone_id='Asia/Taipei',
            geolocation={'latitude': 25.0330, 'longitude': 121.5654},
            permissions=['geolocation'],
            color_scheme='light',
            has_touch=True,
        )
        
        # Add custom scripts to mask automation
        # await context.add_init_script("""
        #     Object.defineProperty(navigator, 'webdriver', {get: () => false});
        #     Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        #     Object.defineProperty(navigator, 'languages', {get: () => ['zh-TW', 'zh', 'en-US', 'en']});
        # """)
        
        self.page = await context.new_page()
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

    async def retry_on_failure(self, func, max_retries=3, delay=1):
        """Retry mechanism for functions"""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise

    async def select_area_with_retry(self):
        """Enhanced area selection with retry logic for sold-out situations"""
        while True:
            try:
                success = await self.select_area()
                if success:
                    # 檢查是否有售完提示
                    dialog_text = await self.check_sold_out_dialog()
                    if dialog_text and "已售完" in dialog_text:
                        logging.info("區域已售完，重新選擇...")
                        await self.handle_sold_out()
                        continue
                    return True
                
                await asyncio.sleep(uniform(0.5, 1.0))
                
            except Exception as e:
                logging.error(f"選擇區域時發生錯誤: {str(e)}")
                await self.handle_error()

    async def check_sold_out_dialog(self):
        """Check for sold-out dialog"""
        try:
            dialog = await self.page.query_selector("div[role='dialog']")
            if dialog:
                return await dialog.text_content()
            return None
        except Exception:
            return None

    async def handle_sold_out(self):
        """Handle sold-out situation"""
        try:
            # 關閉提示對話框
            await self.page.click("button:has-text('確定')")
            
            # 返回區域選擇
            await self.page.goto(setting.SELL_URL, wait_until='domcontentloaded')
            
            # 隨機延遲
            await asyncio.sleep(uniform(0.5, 1.5))
            
            # 重新開始購票流程
            await self.navigate_and_fill_initial()
            
        except Exception as e:
            logging.error(f"處理售完情況時發生錯誤: {str(e)}")

    async def handle_error(self):
        """General error handling"""
        await asyncio.sleep(uniform(1, 2))
        await self.page.reload()

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
    async def login(self):
        """登入流程"""
        try:
            await self.page.goto(setting.LOGIN_URL, wait_until='domcontentloaded')
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
        
    async def wait_for_clickable(self, selector: str, timeout: int = 3000) -> bool:
        """等待元素可點擊，有超時機制"""
        try:
            element = self.page.locator(selector)
            await element.wait_for(state='visible', timeout=timeout)
            return True
        except TimeoutError:
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

    async def run(self):
        """Enhanced main running process with retry logic"""
        start_time = time.time()
        
        try:
            await self.init_browser()
            await self.retry_on_failure(self.login)
            
            while True:
                try:
                    await self.ready_to_buy()
                    await self.navigate_and_fill_initial()
                    await self.choose_ticket_count()
                    
                    # 等待驗證碼輸入
                    await self.handle_captcha_input()
                    
                    # 檢查是否出現售完提示
                    dialog_text = await self.check_sold_out_dialog()
                    if dialog_text and "已售完" in dialog_text:
                        logging.info("票券已售完，重試中...")
                        await self.handle_sold_out()
                        continue
                    
                    # 成功購票，跳出循環
                    break
                    
                except Exception as e:
                    logging.error(f"購票過程發生錯誤: {str(e)}")
                    await self.handle_error()
                    
        except Exception as e:
            logging.error(f"執行過程發生錯誤: {str(e)}")
        finally:
            if self.browser:
                end_time = time.time()
                logging.info(f"總耗時: {end_time - start_time} 秒")
                self.keep_running = asyncio.Event()
                await self.keep_running.wait()

    async def choose_ticket_count(self):
    # 選擇票數
        try:
            if await self.wait_for_clickable("select"):
                await self.page.locator('select').select_option(setting.TICKET_NUMBER)
                await self.page.get_by_label("我已詳細閱讀且同意").check()
                
        except Exception as e:
            print(f"選擇票數錯誤: {str(e)}")

    async def handle_captcha_input(self):
        """Enhanced captcha handling"""
        while True:
            try:
                captcha_text = await self.page.locator("input[placeholder='請輸入驗證碼']").input_value()
                if len(captcha_text) == 4 and captcha_text.isalnum():
                    # 添加隨機延遲模擬人工輸入
                    await asyncio.sleep(uniform(0.1, 0.3))
                    await self.page.locator("button:text('確認張數')").click()
                    break
                await asyncio.sleep(0.1)
            except Exception as e:
                logging.error(f"驗證碼處理錯誤: {str(e)}")
                raise



async def main():
    bot = TicketBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())