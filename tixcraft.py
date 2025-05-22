from playwright.async_api import async_playwright, TimeoutError
import asyncio
import tixcraft_setting
import random
import time
from random import uniform
import script as S


class TicketBot:
    def __init__(self):
        self.browser = None
        self.page = None
        self.last_dialog_message = None

        
    async def init_browser(self):
        """Initialize browser with optimized settings"""

        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            channel='chrome',
            args=S.BROWSER_ARGS,
        )
        # self.ocrBrowser = await playwright.chromium.launch(headless=True)
        context = await self.browser.new_context(
            viewport = tixcraft_setting.VIEWPORT,
            user_agent = tixcraft_setting.USER_AGENT,
            java_script_enabled=True,
            locale='zh-TW',
            timezone_id='Asia/Taipei',
            geolocation={'latitude': 25.0330, 'longitude': 121.5654},
            permissions=['geolocation'],
            color_scheme='light',
            has_touch=True,
        )

        await context.add_init_script(S.SCRIPT)
       
        self.page = await context.new_page()
        self.page.on("dialog", lambda dialog: self._on_dialog(dialog))
        await self.add_human_behavior()

    async def _on_dialog(self, dialog):
        # 拿到訊息並存起來
        self.last_dialog_message = dialog.message
        print(f"[Dialog] type={dialog.type} message={dialog.message!r}")
        # 接著決定要 accept 還是 dismiss
        # alert、confirm 預設都 accept；prompt 可以傳入 text
        await dialog.accept()

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
                await self.page.wait_for_selector(tixcraft_setting.AREA_LOCATOR)
                
                # 獲取所有區域元素
                areas = await self.page.query_selector_all(tixcraft_setting.AREA_LOCATOR)
                print(f"找到 {len(areas)} 個區域")
                # 檢查是否有任何區域可選
                if not areas:
                    print("沒有找到任何區域，準備重新整理...")
                    await self.page.wait_for_timeout(random.randint(500, 1000))
                    await self.page.reload()
                    continue
                
                # 獲取所有區域的文本和狀態
                available_areas = []
                for area in areas:
                    # 獲取區域文本
                    area_text = await area.text_content()
                    # 檢查是否可選（不含"已售完"或其他不可選狀態）
                    if any(excluded in area_text for excluded in tixcraft_setting.EXCLUDED_AREAS):
                        continue
                    is_sold_out = "已售完" in area_text or "已售" in area_text
                    if not is_sold_out:
                        available_areas.append((area_text, area))
                
                if not available_areas:
                    print("所有區域都已售完，準備重新整理...")
                    await self.page.wait_for_timeout(random.randint(500, 1000))
                    await self.page.reload()
                    continue
                
                # 按照優先順序尋找可用區域
                selected = False
                # 優先選擇偏好區域
                for preferred in tixcraft_setting.PREFERRED_AREAS:
                    for area_text, area in available_areas:
                        if preferred in area_text:
                            try:
                                await area.click()
                                print(f"成功選擇偏好區域: {area_text}")
                                selected = True
                                return True
                            except Exception as e:
                                print(f"點擊偏好區域 {area_text} 時發生錯誤: {str(e)}")
                                continue
                
                # 如果沒有偏好區域，選擇有位置並沒被排除的區域
                if not selected and not tixcraft_setting.ONLY_PREFERRED_AREAS:
                    for area_text, area in available_areas:
                        if not any(excluded in area_text for excluded in tixcraft_setting.EXCLUDED_AREAS):
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
                    await self.page.wait_for_timeout(random.randint(500, 1000))
                    await self.page.reload()
                
                # 可選擇添加短暫延遲以防止過於頻繁的重新整理
                await asyncio.sleep(random.randint(0.5, 1))
                
        except Exception as e:
            print(f"選擇區域時發生錯誤: {str(e)}")
            return False

    async def wait_for_clickable(self, selector: str, timeout: int = 500) -> bool:
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
            await self.page.goto(tixcraft_setting.LOGIN_URL, wait_until='domcontentloaded')
            await self.page.locator("#bs-navbar").get_by_role("link", name="會員登入").click()
            await self.page.locator("#loginGoogle").click()
            await self.page.get_by_label("電子郵件地址或電話號碼").fill(tixcraft_setting.ACCOUNT)
            await self.page.wait_for_timeout(500)
            await self.page.get_by_label("電子郵件地址或電話號碼").press("Enter")
            await self.page.get_by_label("輸入您的密碼").fill(tixcraft_setting.PASSWORD)
            await self.page.get_by_label("輸入您的密碼").press("Enter")
            while True:
                print("等待登入...")
                if await self.wait_for_clickable(".user-name"):
                    break

            await self.page.goto(tixcraft_setting.SELL_URL, 
                               wait_until='domcontentloaded')
            print("登入成功")

        except Exception as e:
            print(f"登入錯誤: {str(e)}")

    async def ready_to_buy(self):
        """準備購買流程"""
        try:
            
            # element = await self.page.get_by_role("row", name="2025/06/29 (日) 18:00 2025").get_by_role("button")
            
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
            await self.page.get_by_role("button", name="立即訂購").click(timeout=100)
            # element = self.page.get_by_role("row", name="2025/06/29 (日) 18:00 2025").get_by_role("button")
            # element = await self.wait_for_clickable("button:text('立即訂購')",timeout=100)
            # await element.wait_for(state='visible', timeout=100)
            # await element.click()
            # if await self.wait_for_clickable("button:text('立即訂購')"):
            #     await self.page.locator('button:text("立即訂購")').click()
        except Exception as e:
            print(f"點擊立即購買按鈕錯誤: {str(e)}")
   
    async def navigate_to_sell_page(self):
        """執行初始導航和表單填寫，使用最小等待時間"""
        try:
            print("導航到購票頁面...")
            await self.page.goto(tixcraft_setting.SELL_URL, 
                               wait_until='domcontentloaded')
            await self.page.evaluate("document.body.focus()")

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


    async def try_to_choose_max_ticket(self):
        """選擇票數若不夠就選擇最大數"""
        try:
            if await self.wait_for_clickable("select"):
                options = await self.page.locator('select option').all_text_contents()
                if tixcraft_setting.TICKET_NUMBER in options:
                    await self.page.locator('select').select_option(tixcraft_setting.TICKET_NUMBER)
                else:
                    max_option = max(options, key=lambda x: int(x))
                    await self.page.locator('select').select_option(max_option)
                
        except Exception as e:
            print(f"選擇票數錯誤: {str(e)}")
        
    async def choose_ticket_count(self):
        """選擇票數"""
        try:
            if await self.wait_for_clickable("select"):
                await self.page.locator('select').select_option(tixcraft_setting.TICKET_NUMBER)
                
        except Exception as e:
            await self.page.go_back()
            print(f"選擇票數錯誤: {str(e)},返回上一頁重新選擇")
            raise Exception(f"選擇票數錯誤: {str(e)},返回上一頁重新選擇")


    async def enter_member_number(self):
        """輸入會員號碼"""
        try:
            inputs = await self.page.query_selector_all('input[type="text"]')
            if len(inputs) > 1 and tixcraft_setting.NEED_INPUT:
                await inputs[1].fill(tixcraft_setting.MEMBER_NUMBER)
                self.page.on("dialog", lambda dialog: dialog.accept())
                await self.page.get_by_role("button", name="送出").click()
        except Exception as e:
            print(f"輸入會員號碼錯誤: {str(e)}")

    async def commit_to_buy(self):
        """確認購買"""
        try:
            await self.choose_ticket_count()
            await self.page.locator('#TicketForm_agree').check(timeout=500)
            await self.page.get_by_placeholder("請輸入驗證碼").click(timeout=500)
            code = None
            try:
                with open("captcha.txt", "r", encoding="utf-8") as f:
                    code = f.read().strip().lower()
            except FileNotFoundError:
                raise RuntimeError("找不到 captcha.txt，請先建立並輸入驗證碼")
            if len(code) == 4:
                captcha_text = await self.page.locator("input[placeholder='請輸入驗證碼']").fill(code,timeout=500)
            while True:
                if await self.wait_for_clickable("input[placeholder='請輸入驗證碼']"):
                    captcha_text = await self.page.locator("input[placeholder='請輸入驗證碼']").input_value(timeout=500)
                    if len(captcha_text) == 4 and captcha_text.isalnum():
                        await self.page.locator("button:text('確認張數')").click(timeout=500)
                        break
                    await asyncio.sleep(0.1)
                else: 
                    break
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
        await self.page.evaluate("document.body.focus()") 
        try:
            await self.page.get_by_role("button", name="全部拒絕").click()
        except:
            pass

    async def run(self):
        """主要運行流程"""
        start_time = time.time()
        # 被踢出來要再回到搶票頁面
        try:
            await self.init_browser()  
            await self.login()
            await self.page.goto(tixcraft_setting.SELL_URL, 
                               wait_until='domcontentloaded')
            await self.setup_page()
            # await self.ready_to_buy()
            await self.navigate_to_sell_page()

            while True: 
                try:
                    if 'game' in self.page.url:
                        await self.click_buy_now()
                    if 'verify' in self.page.url:
                        await self.enter_member_number()
                    if 'area' in self.page.url:
                        await self.select_area()
                    if 'ticket/ticket' in self.page.url:
                        await self.commit_to_buy()
                    if 'order' in self.page.url:
                        await self.page.wait_for_timeout(random.randint(500, 1000))
                    if 'checkout' in self.page.url:
                        break
                    
                except Exception as e:
                    continue

                await asyncio.sleep(0.1)
   
        except Exception as e:
            print(f"執行過程發生錯誤: {str(e)}")
        finally:
            if self.browser:
                end_time = time.time()
                print("搶票自動化流程結束")
                print("搶票流程完成，瀏覽器保持開啟中，請手動關閉...")
                print(f"總耗時: {end_time - start_time} 秒")
                self.page.on("dialog", lambda dialog: print(f"發現對話框: {dialog.message}"))
                await self.page.pause()
                self.keep_running = asyncio.Event()  # 建立事件
                await self.keep_running.wait()
                
      
async def main():
    bot = TicketBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())