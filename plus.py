

from playwright.async_api import async_playwright, TimeoutError

import asyncio
import os
import plus_setting as setting
import random
from typing import Optional
import time
from random import uniform
import re
import script as S

class TicketBot:
    def __init__(self):
        self.browser = None
        self.page = None

        
    async def init_browser(self):
        """Initialize browser with optimized settings"""

        
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            channel='chrome',
            args=S.BROWSER_ARGS,
        )
        
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

        await context.add_init_script(S.SCRIPT)
       
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

    async def fetch_area(self) -> list :
        """獲取區域"""
        try:
            while True:            
                await self.page.wait_for_selector('div.seats-area')
                areas = await self.page.query_selector_all(setting.AREA_LOCATOR)
                print(f"總共 {len(areas)} 個區域")
                if not areas:
                    print("沒有找到任何區域，準備重新整理...")
                    await self.wait_for_click('.v-btn__content','更新票數')
                    continue
                available_areas = []
                for area in areas:                
                    # 獲取區域文本
                    area_text = await area.text_content()
                    # 檢查是否可選（不含"已售完"或其他不可選狀態）
                    if any(excluded in area_text for excluded in setting.EXCLUDED_AREAS):
                        continue
                    is_sold_out = "已售完" in area_text or "暫無票券" in area_text or "0\n" in area_text or "開賣時間" in area_text
                    if not is_sold_out:
                        available_areas.append((area_text, area))
                   

                if not available_areas:
                    print("所有區域都已售完，準備重新整理...")
                    await self.wait_for_click('.v-btn__content',text='更新票數')
                    continue
                print(available_areas)
                return available_areas

        except Exception as e:
            print(f"獲取區域時發生錯誤: {str(e)}")

    async def select_area(self):
        """選擇區域"""
        try:
            while True:
                available_areas = await self.fetch_area()
                print(f"找到 {len(available_areas)} 個可用區域")
                # 按照優先順序尋找可用區域
                selected = False
                # 優先選擇偏好區域
                for preferred in setting.PREFERRED_AREAS:
                    for area_text, area in available_areas:
                        if preferred in area_text:
                            try:
                                await self.page.mouse.move(50,100)
                                await area.click()
                                await self.page.wait_for_timeout(300)
                                element = self.page.locator("role=button", has_text=re.compile(r"^$")).nth(2)
                                if element:
                                    try:
                                        await element.click(click_count=setting.TICKET_NUMBER,timeout=300)
                                        selected = True
                                        return True
                                    except Exception as e:
                                        print(f"點擊偏好區域 {area_text} 時發生錯誤: {str(e)}")
                                        continue
                                else:
                                    print("賣完了")
                                    raise Exception("賣完了")
                                
                            except Exception as e:
                                print(f"點擊偏好區域 {area_text} 時發生錯誤: {str(e)}")
                                continue
                
                # 如果沒有偏好區域，選擇有位置並沒被排除的區域
                if not selected and not setting.ONLY_PREFERRED_AREAS:
                    for area_text, area in available_areas:
                        if not any(excluded in area_text for excluded in setting.EXCLUDED_AREAS):
                            try:
                                # input
                                await self.page.mouse.move(50,100)
                                await area.click()
                                await self.page.wait_for_timeout(300)
                                element = self.page.locator("role=button", has_text=re.compile(r"^$")).nth(2)
                                if element:
                                    await element.click(click_count=setting.TICKET_NUMBER)
                                    selected = True
                                    return True
                                else:
                                    print("賣完了")
                                    raise Exception("賣完了")
                                
                            except Exception as e:
                                print(f"點擊區域 {area_text} 時發生錯誤: {str(e)}")
                                continue
                
                # 如果沒有找到理想的區域，重新整理
                if not selected:
                    print("沒有找到理想的區域，準備重新整理...")
                    await self.wait_for_click('.v-btn__content',text='更新票數')
                
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
        
    async def wait_for_click(self, selector: str ,text:str = None, timeout: int = 500) -> bool:
        """等待元素可點擊，有超時機制"""
        try:
            element = self.page.locator(selector,has_text= text)
            await element.wait_for(state='visible', timeout=timeout)
            if element:
                await element.click()
            return True
        except TimeoutError:
            return False
        
    async def wait_for_role_clickable(self, role:str,text:str,auto_click :bool =True, timeout: int = 500) -> bool:
        """等待元素可點擊，有超時機制"""
        try:
            element = await self.page.get_by_role(role, name=text).wait_for(state='visible',timeout=timeout)
            if auto_click:
                await element.click()
            return True
        except TimeoutError:
            return False
        
    async def login(self):
        """登入流程"""
        try:
            if await self.wait_for_role_clickable('button','登出'):
                    return
            await self.page.goto(setting.LOGIN_URL, wait_until='domcontentloaded')
            await self.page.get_by_role("button", name="會員登入").click()
            await self.page.get_by_role("textbox", name="手機號碼 *").fill(setting.PHONE)
            await self.page.wait_for_timeout(100)
            await self.page.get_by_role("textbox", name="密碼").fill(setting.PASSWORD)
            await self.page.get_by_role("button", name="登入", exact=True).click()
            while True:
                print("等待登入...")
                if await self.wait_for_role_clickable('button','登出'):
                    break

            print("登入成功")

        except Exception as e:
            print(f"登入錯誤: {str(e)}")

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

        except Exception as e:
            print(f"初始導航和表單填寫錯誤: {str(e)}")
        
    async def buy_process(self):
        try:
            print('BUY_PROCESS')
            await self.select_area()
            await self.page.get_by_role("button", name="下一步").click()
        except Exception as e:
            return

    async def run(self):
        """主要運行流程"""
        start_time = time.time()
        try:
            await self.init_browser()            
            await self.login()
            await self.navigate_to_sell_page()
            await self.buy_process()
            while True:
                try:
                    is_searching = await self.page.locator('.v-overlay__content').first.is_visible()
                    print(f'IS_SEARCHING:{is_searching}')
                    if is_searching:
                        continue
                    await self.page.wait_for_timeout(500)
                    if 'confirmSeat' in self.page.url:
                        break
                    else:
                        await self.page.wait_for_timeout(uniform(100, 300))
                        await self.buy_process()
                    
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