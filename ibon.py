from playwright.async_api import async_playwright, TimeoutError
import requests
import urllib.parse
import asyncio
import re
import ibon_setting as setting
import script as S
import random
import pytesseract
import cv2
from typing import Optional
import time
from random import uniform
from bs4 import BeautifulSoup
import numpy as np
import ddddocr
from PIL import Image


class TicketBot:
    def __init__(self):
        self.browser = None
        self.page = None
        self.performance_id = None
        self.product_id = None
        self.sell_url = None
        
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
            args=browser_args
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
        # await context.add_cookies([setting.COOKIE])
        
        self.page = await context.new_page()
        await self.page.goto(setting.LOGIN_URL, wait_until='domcontentloaded')
        await self.page.pause()
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
            print("選擇區域...")
            response = requests.get(setting.AREA_API.format(performance_id = self.performance_id))
            response.encoding = response.apparent_encoding
            status_code = response.status_code
            if status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                # 找到所有的area標籤
                areas = soup.find_all('area')
                for area in areas:
                    # 獲取href屬性中的參數
                    href = area.get('href', '')
                    title = area.get('title', '')
                    ticket_info = {}
                    area_match = re.search(r'票區:([^票]+)票價：(\d+)\s+尚餘：(.+?)(?:"|\s*$)', title)
                    if area_match:
                        ticket_info['TicketArea'] = area_match.group(1).strip()
                        ticket_info['Price'] = area_match.group(2)
                        ticket_info['Remaining'] = area_match.group(3)
                        print(f"票區: {ticket_info['TicketArea']} 票價: {ticket_info['Price']} 尚餘: {ticket_info['Remaining']}")
                        # 如果是排除區域，則跳過
                        if any(excluded_area in ticket_info['TicketArea'] for excluded_area in setting.EXCLUDED_AREAS):
                            continue
                        if ticket_info['Remaining'] == '0':
                            continue
                        await self.page.evaluate(href)
                        return True
                
                print("沒有找到合適的票區，重新整理頁面")
                await self.page.reload()
                await asyncio.sleep(0.5)
            else:
                print(f"API 請求錯誤: {status_code}")
                raise Exception(f"API 請求錯誤: {status_code}")
        except Exception as e:
            print(f"選擇區域錯誤: {str(e)}")
            

    async def wait_for_clickable(self, selector: str, timeout: int = 500) -> bool:
        """等待元素可點擊，有超時機制"""
        try:
            element = self.page.locator(selector)
            await element.wait_for(state='visible', timeout=timeout)
            return True
        except TimeoutError:
            return False

    async def ready_to_buy(self):
        """準備購買流程"""
        try:
            while True:
                response = requests.post(
                    setting.GAMES_API,headers=setting.HEADER,
                    json={
                        "id":setting.GAME_ID,
                        "hasDeadline":True,
                        "SystemBrowseType":0
                    }
                )
                status_code = response.status_code
                if status_code == 200:
                    games = response.json()['Item']['GIHtmls']
                    game = games[0]
                    if game['Href'] is None:
                        print("沒有找到遊戲")
                        await asyncio.sleep(0.5)
                    else:
                        self.parser_game_info(game['Href'])
                        break
                else:
                    print(f"API 請求錯誤: {status_code}")
                    raise Exception(f"API 請求錯誤: {status_code}")
            
            await self.page.goto(self.sell_url,wait_until='domcontentloaded')  
            
        except Exception as e:
            print(f"準備購買錯誤: {str(e)}")
    def parser_game_info(self,url:str):
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 提取GoUrl參數值
        go_url = query_params.get('GoUrl', [''])[0]

        # 解碼URL編碼字符
        decoded_go_url = urllib.parse.unquote(go_url)

        # 再次解析GoUrl中的查詢參數
        go_url_parsed = urllib.parse.urlparse(decoded_go_url)
        go_url_params = urllib.parse.parse_qs(go_url_parsed.query)

        # 提取PERFORMANCE_ID和PRODUCT_ID
        performance_id = go_url_params.get('PERFORMANCE_ID', [''])[0]
        product_id = go_url_params.get('PRODUCT_ID', [''])[0]

        self.performance_id = performance_id
        self.product_id = product_id
        self.sell_url = go_url

        print(f"PERFORMANCE_ID: {performance_id}")
        print(f"PRODUCT_ID: {product_id}")


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
                if setting.TICKET_NUMBER in options:
                    await self.page.locator('select').select_option(setting.TICKET_NUMBER)
                else:
                    max_option = max(options, key=lambda x: int(x))
                    await self.page.locator('select').select_option(max_option)
                
        except Exception as e:
            print(f"選擇票數錯誤: {str(e)}")
        
    async def choose_ticket_count(self):
        """選擇票數"""
        try:
            is_sold_out = await self.page.get_by_text("已售完", exact=True).is_visible(timeout=500)
            if is_sold_out:
                print("已售完")
                await self.page.go_back()
                await self.select_area()
                return
            element = self.page.locator('#ctl00_ContentPlaceHolder1_DataGrid_ctl02_AMOUNT_DDL')
            await element.is_visible(timeout=500)
            await element.select_option(setting.TICKET_NUMBER)
                
        except Exception as e:
            await self.page.go_back()
            await self.select_area()
            print(f"選擇票數錯誤: {str(e)},返回上一頁重新選擇")
            raise Exception(f"選擇票數錯誤: {str(e)},返回上一頁重新選擇")


    async def enter_member_number(self):
        """輸入會員號碼"""
        try:
            await self.page.locator('#ctl00_ContentPlaceHolder1_Txt_id_name').fill(setting.INPUT_VALUE)
            await self.page.get_by_role("link", name="送出").click()
        except Exception as e:
            print(f"輸入會員號碼錯誤: {str(e)}")

    async def commit_to_buy(self):
        """確認購買"""
        try:
            await self.choose_ticket_count()
            await self.validate_captcha()
        except Exception as e:
            print(f"確認購買錯誤: {str(e)}")

    async def check_is_success(self):   
        try:
            await self.page.wait_for_selector("div:has-text('訂單明細')", timeout=1000)
            return True
        except Exception as e:
            print(f"確認購買錯誤: {str(e)}")
            return False
    
    async def validate_captcha(self):
        """驗證驗證碼"""
        try:
            element = self.page.get_by_text("驗證碼：(全為數字組成) 請勿多視窗操作，以免驗證碼未更新，購票失敗")
            await element.is_visible(timeout=500)
            box = await element.bounding_box()
            await self.page.screenshot(
                path=setting.IMAGE_PATH,
                clip={
                    "x": box["x"] + 180,
                    "y": box["y"],
                    "width": box["width"] - 350,
                    "height": box["height"] - 25
                }
            )
        
            ocr = ddddocr.DdddOcr()
            with open(setting.IMAGE_PATH, "rb") as f:
                image = f.read()
            result = ocr.classification(image)
            print(result)
            await self.page.locator("#ctl00_ContentPlaceHolder1_CHK").fill(result)
            await self.page.locator("#Next div").click()
        except Exception as e:
            print(f"驗證驗證碼錯誤: {str(e)}")

    async def run(self):
        """主要運行流程"""
        start_time = time.time()
        # 被踢出來要再回到搶票頁面
        try:
            await self.init_browser()
           
            # await self.ready_to_buy()
                        
            while True:
                try:
                    await self.page.wait_for_timeout(300)
                    is_selling = await self.page.get_by_text('購票方式').is_visible(timeout=500)
                    is_input = await self.wait_for_clickable('#ctl00_ContentPlaceHolder1_Txt_id_name')
                    is_submit = await self.page.get_by_text('請輸入購買張數').is_visible(timeout=500)
                    is_complete = await self.page.get_by_text("總計(付款金額)").is_visible(timeout=500)
                    if is_complete:
                        break
                    if is_input:
                        await self.enter_member_number()
                        continue
                    if is_selling:
                        print("找到購票頁面")
                        await self.select_area()
                        continue
                    if is_submit:
                        await self.commit_to_buy()
                        continue
                    
                    

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