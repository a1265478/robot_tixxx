from playwright.async_api import async_playwright, TimeoutError

import asyncio
import os
import kktix_setting
import random
from typing import Optional
import time
from random import uniform


class TicketBot:
    def __init__(self):
        self.browser = None
        self.page = None

        
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
            args=browser_args
        )
        
        context = await self.browser.new_context(
            viewport = kktix_setting.VIEWPORT,
            user_agent = kktix_setting.USER_AGENT,
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
                await self.page.wait_for_selector(kktix_setting.AREA_LOCATOR,timeout=100)
                
                # 獲取所有區域元素
                areas = await self.page.query_selector_all(kktix_setting.AREA_LOCATOR)
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
                    if any(excluded in area_text for excluded in kktix_setting.EXCLUDED_AREAS):
                        continue
                    is_sold_out = "已售完" in area_text or "已售" in area_text
                    if not is_sold_out:
                        available_areas.append((area_text, area))
                
                if not available_areas:
                    print("所有區域都已售完，準備重新整理...")
                    await self.page.reload()
                    continue
                
                # 按照優先順序尋找可用區域
                selected = False
                # 優先選擇偏好區域
                for preferred in kktix_setting.PREFERRED_AREAS:
                    for area_text, area in available_areas:
                        if preferred in area_text:
                            try:
                                await self.page.mouse.move(50,100)
                                element =  await area.query_selector('input[type="text"]')
                                await self.page.wait_for_timeout(200)
                                await element.fill(f'{kktix_setting.TICKET_NUMBER}')
                                # await area.click()
                                # print(f"成功選擇偏好區域: {area_text}")
                                selected = True
                                return True
                            except Exception as e:
                                print(f"點擊偏好區域 {area_text} 時發生錯誤: {str(e)}")
                                continue
                
                # 如果沒有偏好區域，選擇有位置並沒被排除的區域
                if not selected and not kktix_setting.ONLY_PREFERRED_AREAS:
                    for area_text, area in available_areas:
                        if not any(excluded in area_text for excluded in kktix_setting.EXCLUDED_AREAS):
                            try:
                                # input
                                await self.page.mouse.move(50,100)
                                element =  await area.query_selector('input[type="text"]')
                                await self.page.wait_for_timeout(200)
                                await element.fill(f'{kktix_setting.TICKET_NUMBER}')
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

    async def wait_for_clickable(self, selector: str ,text:str = None, timeout: int = 500) -> bool:
        """等待元素可點擊，有超時機制"""
        try:
            element = self.page.locator(selector,has_text= text)
            await element.wait_for(state='visible', timeout=timeout)
            return True
        except TimeoutError:
            return False
        
    async def login(self):
        """登入流程"""
        try:
            if await self.wait_for_clickable("#nav-user-display-id"):
                    return
            await self.page.goto(kktix_setting.LOGIN_URL, wait_until='domcontentloaded')
            await self.page.get_by_role("link", name="登入").click()
            await self.page.get_by_role("textbox", name="使用者名稱或 Email").click()
            await self.page.get_by_role("textbox", name="使用者名稱或 Email").fill(kktix_setting.ACCOUNT)
            await self.page.wait_for_timeout(500)
            await self.page.get_by_role("textbox", name="密碼").fill(kktix_setting.PASSWORD)
            await self.page.get_by_role("button", name="登入").click()
            while True:
                print("等待登入...")
                if await self.wait_for_clickable("#nav-user-display-id"):
                    break

            print("登入成功")

        except Exception as e:
            print(f"登入錯誤: {str(e)}")

    async def ready_to_buy(self):
        """準備購買流程"""
        try:
            while not await self.page.locator("button", has=self.page.locator("text='下一步'")).is_visible():
                print("尚未開賣...")
                await self.page.wait_for_timeout(1000)
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
            await self.page.goto(kktix_setting.SELL_URL, 
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
        
        
    async def buy_process(self):
        try:
            ready_to_fill = await self.wait_for_clickable(".contact-info")
            if ready_to_fill:
                pass
            print('BUY_PROCESS')
            
            await self.select_area()
            await self.page.get_by_role("checkbox", name="我已經閱讀並同意 服務條款 與 隱私權政策").check()
            await self.page.get_by_role("button", name="下一步").click()
        except Exception as e:
            pass

    async def run(self):
        """主要運行流程"""
        start_time = time.time()
        try:
            await self.init_browser()            
            await self.login()
            await self.navigate_to_sell_page()
            await self.ready_to_buy()
            await self.buy_process()
            await self.page.wait_for_timeout(100)
            while True:
                try:
                    is_searching = await self.page.get_by_role("button", name="查詢空位中，請勿重新讀取或關閉此頁").is_visible()
                    print(f'IS_SEARCHING:{is_searching}')
                    if is_searching:
                        continue
                    else:
                        ready_to_fill = await self.wait_for_clickable(".contact-info")
                        print(f'IS_READY_TO_FILL:{ready_to_fill}')
                        if ready_to_fill:
                            break
                        else:
                            await self.buy_process()
                            await self.page.wait_for_timeout(1000)
                            continue
                except Exception as e:
                    print(f"執行過程發生錯誤: {str(e)}")
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
                self.page.on("dialog", lambda dialog: print(f"發現對話框: {dialog.message}"))
                await self.page.pause()
                self.keep_running = asyncio.Event()  # 建立事件
                await self.keep_running.wait()
                

                
      
async def main():
    bot = TicketBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())