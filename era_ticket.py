from playwright.async_api import async_playwright, TimeoutError,expect
import asyncio
import era_setting as setting
import random
import time
from random import uniform
import script as S
import ddddocr

from datetime import datetime
import re
from typing import List, Dict

class TicketBot:
    def __init__(self):
        self.context = None
        self.browser = None
        self.page = None
        self.last_dialog_message = None
        self.isVerifying = False

        
    async def init_browser(self):
        """Initialize browser with optimized settings"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(setting.CHROME_IP)
        self.context = browser.contexts[0]
        self.page = self.context.pages[0]
       
        self.page.on("dialog", lambda dialog: self._on_dialog(dialog))
        await self.add_human_behavior()
        # user_data_dir = setting.USER_DATA_DIR
        # self.page = await playwright.chromium.launch_persistent_context(
        #     user_data_dir,
        #     headless=False,
        #     channel='chrome',
        #     args=S.BROWSER_ARGS,
        #     viewport=setting.VIEWPORT,
        #     user_agent=setting.USER_AGENT,
        #     java_script_enabled=True,
        #     locale='zh-TW',
        #     timezone_id='Asia/Taipei',
        #     geolocation={'latitude': 25.0330, 'longitude': 121.5654},
        #     permissions=['geolocation'],
        #     color_scheme='light',
        #     has_touch=True,
        # )
       
        # await self.page.add_init_script(S.SCRIPT)
        # self.page = await self.page.new_page()
        # self.page.set_default_timeout(15000)
        # self.page.set_default_navigation_timeout(15000+ 5000)
        # self.page.on("dialog", lambda dialog: self._on_dialog(dialog))
        # await self.add_human_behavior()

    async def _on_dialog(self, dialog):
        # 拿到訊息並存起來
        try:
            print(f"[Dialog] type={dialog.type} message={dialog.message!r}")
            
            await dialog.accept()
        except:
            print("Dialog error")

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

    async def is_open_now(self):
        """是否開賣，如果尚未開賣重新整理再確認是否開賣"""
        try:
            element = self.page.locator("button:text('立即訂購')")
            is_on_sale = await element.is_visible(timeout=100)
            if is_on_sale:
                await element.click()
            else:
                await asyncio.sleep(uniform(0.1, 0.2))
                await self.page.reload()
        except Exception as e:
            print(f"開賣檢查發生錯誤: {str(e)}")

    async def get_available_areas(self) -> List[Dict]:
        """
        取得篩選後的區域列表
        """
        try:

            # 獲取所有區域元素
            areas_locator = self.page.locator("ul.area-list")
            
            # # 強制等待至少一個區域出現，避免抓到空清單 (測試穩定性的關鍵)
            # await areas_locator.first.wait_for(state="visible", timeout=500)
            
            count = await areas_locator.count()
            final_list = []

            for i in range(count):
           
                target = areas_locator.nth(i)
                area_name = (await target.text_content()).strip()
                if any(key in area_name for key in setting.EXCLUDE_AREA):
                    continue
                if "完售" in area_name or "不開放" in area_name or "Sold out" in area_name:
                    continue

                area_id = target.evaluate("el => el.parentElement.id")
                
                final_list.append({
                    "index": i,
                    "id": area_id,
                    "name": area_name,
                    "locator": target # 保留 locator 方便後續直接點擊
                })
                
            return final_list
        except Exception as e:
            print(f"選擇區域發生錯誤:{str(e)}")

    async def select_areas(self):
        """
        根據優先順序選擇最理想的區域並點擊
        """
        while True:
            try:
                available = await self.get_available_areas()
                
                if not available:
                    print("❌ 沒有符合篩選條件的可用區域")
                    await self.page.reload()
                    continue

                # 根據優先順序關鍵字尋找第一個匹配的
                for pref in setting.PREFERRED_AREA:
                    for area in available:
                        if pref in area["name"]:
                            print(f"✅ 找到優先區域: {area['name']}，準備進入...")
                            await area["locator"].click()
                            return True
                
                # 如果優先標籤都沒中，就點擊剩餘可選的第一個
                print(f"⚠️ 未找到優先區域，自動選擇剩餘首選: {available[0]['name']}")
                await available[0]["locator"].click()
                return True
            except Exception as e:
                print(f"選擇區域發生錯誤:{str(e)}")
                await self.page.reload()
                return False

 

    async def can_select_seat(self) -> bool:
        """是否可以選座位"""
        return await self.page.get_by_text('請先選擇【票別】').is_visible(timeout=100)
        
    async def select_seat(self):
        """選擇座位"""
        try:
            target = self.page.locator(".ticketType .buttonGroup button").filter(has_not_text=re.compile(r"身心障礙|身障|陪同者")).first
            await target.click()
            await self.pick_seats()
        except Exception as e:
            print(f"選擇座位發生錯誤: ${str(e)}")
            await self.page.reload()

    async def get_all_available_seats(self):
        """解析所有可選座位，並提取排數與號碼"""
        seats = []
        # 定位所有具備點擊功能的 td
        locators = await self.page.locator("#TBL td[style*='cursor: pointer']").all()
        
        for loc in locators:
            style = await loc.get_attribute("style") or ""
            title = await loc.get_attribute("title") or ""
            
            # 必須是空位且非售出
            if setting.EMPTY_ICON in style and setting.SELL_ICON not in style:
                # 使用正則解析 title，假設格式為 "2樓2A區-1排-15號"
                match = re.search(r"(\d+)排-(\d+)號", title)
                if match:
                    row = int(match.group(1))
                    col = int(match.group(2))
                    seats.append({
                        "row": row, 
                        "col": col, 
                        "locator": loc, 
                        "title": title
                    })
        return seats

    async def pick_seats(self):
        available = await self.get_all_available_seats()
        if len(available) < setting.COUNT:
            print(f"❌ 剩餘座位不足，僅剩 {len(available)} 個")
            return False

        selected_locators = []

        # --- 策略 1: 尋找連號 ---
        # 先按排、號排序
        available.sort(key=lambda x: (x['row'], x['col']))
        
        for i in range(len(available) - setting.COUNT + 1):
            window = available[i : i + setting.COUNT]
            # 檢查是否同排且號碼連續
            is_consecutive = all(
                window[j]['row'] == window[0]['row'] and 
                window[j]['col'] == window[0]['col'] + j 
                for j in range(setting.COUNT)
            )
            
            if is_consecutive:
                print(f"✅ 找到連號座位: {[s['title'] for s in window]}")
                selected_locators = [s['locator'] for s in window]
                break

        # --- 策略 2: 若無連號，隨機補齊 ---
        if not selected_locators:
            print("⚠️ 未找到連號，改為隨機選位...")
            random_seats = random.sample(available, setting.COUNT)
            selected_locators = [s['locator'] for s in random_seats]

        # --- 執行點擊 ---
        for loc in selected_locators:
            await loc.click()
            # 嚴厲提示：點擊座位後通常會有 AJAX 請求，建議加微小延遲
            await self.page.wait_for_timeout(200) 
        
        return True

    async def select_count(self):
        """電腦選位，只選擇張數"""
        try:
            ticket_rows = self.page.locator("#tablePriceTypeList tbody tr").filter(has=self.page.locator("td[data-th='內容']"))
            target_row = ticket_rows.filter(
                has_not_text=re.compile(r"身心障礙|身障|陪同者", re.IGNORECASE)
            ).first
            await expect(target_row).to_be_visible(timeout=500)
            count_field = target_row.locator("#ctl00_ContentPlaceHolder1_PriceTypeList_ctl00_AMOUNT")
            await count_field.fill(str(setting.COUNT),timeout=500)
          
        except Exception as e:
            print(f"選擇張數發生錯誤: ${str(e)}")
            await self.page.reload()

    async def ocr(self):
        """ocr辨識並加入購物車"""
        try:
            element = self.page.locator('#chk_pic')
            await element.is_visible(timeout=800)
            await element.screenshot(path=setting.IMAGE_PATH)
            ocr = ddddocr.DdddOcr()
            with open(setting.IMAGE_PATH, "rb") as f:
                image = f.read()
            result = ocr.classification(image)
            print(result.upper())
            await self.page.locator("#ctl00_ContentPlaceHolder1_CHK").first.fill(result.upper(),timeout=500)
            await self.page.get_by_role('button',name='購物車').click(timeout=500)
            
            await self.page.pause()
        except Exception as e:
            print(f"OCR辨識失敗: ${str(e)}")
            await self.page.reload()

    async def get_step(self) -> int:
        """判斷現在是第幾步驟"""     
        try:  
            active_step_locator = self.page.locator(".bs-wizard-step.active")
            step_id = await active_step_locator.get_attribute("id")
            if not step_id:
                raise ValueError("找不到活動步驟的 ID 屬性")
            match = re.search(r'\d+', step_id)
            if match:
                return int(match.group())
        
        except Exception as e:
            raise ValueError(f"無法從 ID '{step_id}' 中解析步驟數字")
    
    async def wait_for_clickable(self, selector: str, timeout: int = 500) -> bool:
        """等待元素可點擊，有超時機制"""
        try:
            element = self.page.locator(selector).first
            await element.wait_for(state='visible', timeout=timeout)
            return True
        except TimeoutError:
            return False
        
    async def to_buy(self):
        try:
            unselected_area = await self.page.locator("ul.area-list").first.is_visible(timeout=200)
            if unselected_area:
                 await self.select_areas()
           
            can_select_seat = await self.can_select_seat()
            if can_select_seat:
                await self.select_seat()
            else:
                await self.select_count()
            await self.page.wait_for_timeout(300)
            await self.ocr()
            await asyncio.sleep(uniform(0.1, 0.2))
        except Exception as e:
            print(str(e))


    async def run(self):
        """主要運行流程"""
        start_time = time.time()
        try:
            await self.init_browser()  
            await self.page.goto(setting.SELL_URL, 
                               wait_until='domcontentloaded')
            # await self.page.pause()
            # await self.page.goto(setting.SELL_URL, 
            #                    wait_until='domcontentloaded')
            while True: 
                try:
                    current_step = await self.get_step()
                    if current_step == 1:
                        await self.is_open_now()
                        continue
                    if current_step == 2:
                        await self.to_buy()
                        continue
                    if current_step == 3:
                        await self.page.pause()
                        break
                    if current_step == 4:
                        await self.page.pause()
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
                # self.page.on("dialog", lambda dialog: print(f"發現對話框: {dialog.message}"))
                await self.page.pause()
                self.keep_running = asyncio.Event()  # 建立事件
                await self.keep_running.wait()
                
      
async def main():
    bot = TicketBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())