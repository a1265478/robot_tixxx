from playwright.async_api import async_playwright, TimeoutError
import asyncio
import aiohttp
import aiofiles
import tixcraft_setting
import random
import time
from random import uniform
from datetime import datetime


class TicketBot:
    def __init__(self):
        self.context = None
        self.browser = None
        self.page = None
        self.last_dialog_message = None
        self.isVerifying = False
        self.is_first_time = True
        
        self._last_reload_at: float = 0.0
        self._reload_profile: str = tixcraft_setting.RELOAD_PROFILE
        # --- Captcha cache ---
        self._captcha_cache: str = ""
        self._captcha_set_at: float = 0.0
        self.CAPTCHA_TTL: int = getattr(tixcraft_setting, "CAPTCHA_TTL", 3600)  # 秒，預設 1 小時

    # =========================================================
    # Browser init
    # =========================================================

    async def init_browser(self):
        """Initialize browser with optimized settings"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(tixcraft_setting.CHROME_IP)
        self.context = browser.contexts[0]
        self.page = self.context.pages[0]

        self.page.on("dialog", lambda dialog: asyncio.ensure_future(self._on_dialog(dialog)))
        await self.add_human_behavior()

    async def _on_dialog(self, dialog):
        try:
            print(datetime.now())
            print(f"[Dialog] type={dialog.type} message={dialog.message!r}")
            self.last_dialog_message = dialog.message 
            await dialog.accept()
        except Exception:
            print("Dialog error")

    async def add_human_behavior(self):
        """Add random delays and mouse movements to simulate human behavior"""

        async def _on_load():
            await asyncio.sleep(uniform(0.1, 0.3))

        async def _on_click():
            x = random.randint(0, 800)
            y = random.randint(0, 600)
            await self.page.mouse.move(x, y)

        # 用 ensure_future 讓 coroutine 真的被執行
        self.page.on("load", lambda: asyncio.ensure_future(_on_load()))
        self.page.on("click", lambda: asyncio.ensure_future(_on_click()))

    # =========================================================
    # Captcha cache
    # =========================================================

    def _is_cache_valid(self) -> bool:
        if not self._captcha_cache:
            return False
        if time.time() - self._captcha_set_at > self.CAPTCHA_TTL:
            print("[Captcha] Cache 已過期，需重新輸入")
            self._captcha_cache = ""
            return False
        return True

    def invalidate_captcha(self):
        """強制清除 cache（驗證失敗時呼叫）"""
        print("[Captcha] Cache 已清除")
        self._captcha_cache = ""
        self._captcha_set_at = 0.0
        # 同步清掉檔案，避免重啟後又載回舊的
        try:
            with open(tixcraft_setting.CAPTCHA, "w", encoding="utf-8") as f:
                f.write("")
        except FileNotFoundError:
            pass

    def _set_captcha_cache(self, code: str):
        self._captcha_cache = code
        self._captcha_set_at = time.time()

    async def get_captcha(self) -> str:
        """優先從記憶體 cache 拿，沒有再讀檔"""
        if self._is_cache_valid():
            return self._captcha_cache

        try:
            async with aiofiles.open(tixcraft_setting.CAPTCHA, "r", encoding="utf-8") as f:
                code = (await f.read()).strip().lower()
            if len(code) == 4 and code.isalnum():
                self._set_captcha_cache(code)
                print(f"[Captcha] 從檔案載入: {code}")
                return code
        except FileNotFoundError:
            pass

        return ""

    async def save_captcha(self, code: str):
        """更新記憶體 cache 並同步寫入檔案"""
        self._set_captcha_cache(code)
        async with aiofiles.open(tixcraft_setting.CAPTCHA, "w", encoding="utf-8") as f:
            await f.write(code)
        print(f"[Captcha] 已儲存: {code}")

    # =========================================================
    # Navigation
    # =========================================================

    async def navigate_to_sell_page(self):
        """導航到購票頁面"""
        try:
            print("導航到購票頁面...")
            await self.page.goto(tixcraft_setting.SELL_URL, wait_until='domcontentloaded')
        except Exception as e:
            print(f"導航錯誤: {str(e)}")

    async def setup_page(self):
        """設置瀏覽器頁面"""
        await self.page.evaluate("document.body.focus()")
        try:
            await self.page.get_by_role("button", name="全部拒絕").click()
        except Exception:
            pass

    # =========================================================
    # Buy flow
    # =========================================================

    async def ready_to_buy(self):
        """準備購買流程"""
        try:
            while not await self.wait_for_clickable("button:text('立即訂購')", timeout=100):
                print("尚未開賣...")
                await self.safe_reload()
                print("Reload")
        except Exception as e:
            print(f"準備購買錯誤: {str(e)}")

    async def click_buy_now(self):
        """點擊立即購買按鈕"""
        try:
            element = self.page.get_by_role("row", name=tixcraft_setting.DAY_WORD).get_by_role("button")
            await element.wait_for(state='visible', timeout=100)
            await element.click()
        except Exception as e:
            await self.safe_reload()
            print(f"點擊立即購買按鈕錯誤: {str(e)}")

    async def select_area(self):
        """選擇區域"""
        count = 0
        try:
            while True:
                now = datetime.now()
                # 奇偶分鐘的刷新視窗不同
                skip_until = 52 if now.minute % 2 == 0 else 48

                # 縮短輪詢間隔到 50ms，更快抓到視窗開口
                if 5 < now.second < skip_until:
                    await asyncio.sleep(0.05)
                    continue

                try:
                    await self.page.wait_for_selector(tixcraft_setting.AREA_LOCATOR, timeout=800)
                except TimeoutError:
                    await self.page.reload(wait_until='commit')
                    continue

                # 擬人滾動
                for i in range(2):
                    delta = -random.randint(100, 150) if i % 2 == 0 else random.randint(200, 300)
                    await self.page.mouse.wheel(0, delta)
                    await asyncio.sleep(random.uniform(0.1, 0.2))

                areas = await self.page.query_selector_all(tixcraft_setting.AREA_LOCATOR)
                count += 1

                if not areas:
                    print("沒有找到任何區域，準備重新整理...")
                    await self.safe_reload()
                    continue

                # 過濾：只做一次，排除已售完與 EXCLUDED_AREAS
                available_areas = []
                for area in areas:
                    area_text = await area.text_content()
                    if any(ex in area_text for ex in tixcraft_setting.EXCLUDED_AREAS):
                        continue
                    if "已售完" not in area_text and "已售" not in area_text:
                        available_areas.append((area_text, area))

                if not available_areas:
                    await self.safe_reload()
                    continue

                print(f"找到 {len(available_areas)} 個可購買區域")
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

                # 偏好區域都沒有，選第一個可用的
                if not selected:
                    for area_text, area in available_areas:
                        try:
                            await area.click()
                            print(f"成功選擇區域: {area_text}")
                            selected = True
                            return True
                        except Exception as e:
                            print(f"點擊區域 {area_text} 時發生錯誤: {str(e)}")
                            continue

                if not selected:
                    print("沒有找到可點擊區域，準備重新整理...")
                    await self.safe_reload()

        except Exception as e:
            is_locked = False
            try:
                page_content = await self.page.content()
                is_locked = "Your Browsing Activity" in page_content
            except Exception:
                is_locked = False  # 頁面本身就壞了，不用管

            # select_area 的 except 裡，被鎖了切 cautious
            if is_locked:
                print(f"第 {count} 次後被鎖了，等待解鎖...")
                await self.page.wait_for_timeout(random.randint(5000, 8000))
                self.set_reload_profile("cautious")  # ← 加這行
                count = 0
                
            
            else:
                print(f"select_area 錯誤: {str(e)}")
                await self.safe_reload()
            return False
        
    def set_reload_profile(self, profile: str):
        if profile in tixcraft_setting.RELOAD_PROFILES:
            print(f"[Reload] 切換模式: {self._reload_profile} → {profile}")
            self._reload_profile = profile
        else:
            print(f"[Reload] 未知 profile: {profile}")

    async def safe_reload(self):
        p = tixcraft_setting.RELOAD_PROFILES[self._reload_profile]
        elapsed = time.time() - self._last_reload_at

        base = random.gauss(p["mu"], p["sigma"])
        base = max(p["min"], min(base, p["max"]))

        if random.random() < p["hesitate_prob"]:
            base += random.uniform(p["hesitate_min"], p["hesitate_max"])

        wait = max(0.0, base - elapsed)
        if wait > 0:
            await asyncio.sleep(wait)

        await self.page.reload(wait_until='domcontentloaded')
        self._last_reload_at = time.time()
        
    

    async def enter_member_number(self):
        """輸入會員號碼"""
        if self.isVerifying:
            return
        self.isVerifying = True
        try:
            inputs = await self.page.query_selector_all('input[type="text"]')
            if len(inputs) > 1 and tixcraft_setting.NEED_INPUT:
                await inputs[1].fill(tixcraft_setting.MEMBER_NUMBER)
                await self.page.get_by_role("button", name="送出").click()
                self.page.on("dialog", lambda dialog: asyncio.ensure_future(dialog.accept()))
                await self.page.wait_for_timeout(random.randint(500, 900))
        except Exception as e:
            print(f"輸入會員號碼錯誤: {str(e)}")
        finally:
            # 確保 flag 一定會被釋放
            self.isVerifying = False

    async def choose_ticket_count(self):
        """選擇票數，不夠則選最大數"""
        try:
            if not await self.wait_for_clickable("select"):
                return
            select = self.page.locator('select').first
            options = await self.page.locator('select option').all_text_contents()
            if tixcraft_setting.TICKET_NUMBER in options:
                await select.select_option(tixcraft_setting.TICKET_NUMBER, timeout=600)
            else:
                max_option = max(options, key=lambda x: int(x))
                print(f"票數不足，改選最大數: {max_option}")
                await select.select_option(max_option, timeout=600)
        except Exception as e:
            await self.page.go_back()
            print(f"選擇票數錯誤: {str(e)}，返回上一頁")
            raise

    async def commit_to_buy(self):
        """確認購買（含驗證碼 cache 機制）"""
        try:
            await self.force_focus()
            await self.choose_ticket_count()
            await self.page.locator('#TicketForm_agree').check(timeout=1000)
            await self.page.get_by_placeholder("請輸入驗證碼").click(timeout=500)

            code = await self.get_captcha()
            captcha_input = self.page.locator("input[placeholder='請輸入驗證碼']")

            if len(code) == 4 and code.isalnum():
                # Cache 有值：自動填入，保留反爬蟲 delay
                await self.page.wait_for_timeout(random.randint(100, 200))
                await captcha_input.fill(code, timeout=500)

                filled = await captcha_input.input_value()
                if len(filled) == 4 and filled.isalnum():
                    await self.page.locator("button:text('確認張數')").click(timeout=1000)
                    await asyncio.sleep(0.3)  # 給 alert 時間出現

                    if self.last_dialog_message and "驗證碼" in self.last_dialog_message:
                        print(f"[Captcha] 驗證碼錯誤: {self.last_dialog_message}，清除 cache")
                        self.invalidate_captcha()
                        self.last_dialog_message = None
                else:
                    print(f"[Captcha] 填入異常: {filled!r}，清除 cache")
                    self.invalidate_captcha()
            else:
                # 第一次 / cache 過期：等使用者手動輸入
                print("[Captcha] 請在瀏覽器手動輸入驗證碼（輸入完 4 碼後自動送出）")
                while True:
                    filled = await captcha_input.input_value(timeout=500)
                    if len(filled) == 4 and filled.isalnum():
                        await self.save_captcha(filled)  # 存進 cache
                        await self.page.locator("button:text('確認張數')").click(timeout=1000)
                        break
                    await asyncio.sleep(0.1)

        except Exception as e:
            print(f"選張數確認購買錯誤: {str(e)}")

    async def check_is_success(self) -> bool:
        try:
            await self.page.wait_for_selector("div:has-text('訂單明細')", timeout=1000)
            await self.alert_discord('搶到票囉 🎉')
            return True
        except Exception:
            return False

    # =========================================================
    # Helpers
    # =========================================================

    async def wait_for_clickable(self, selector: str, timeout: int = 500) -> bool:
        """等待元素可見，有超時機制"""
        try:
            element = self.page.locator(selector).first
            await element.wait_for(state='visible', timeout=timeout)
            return True
        except TimeoutError:
            return False

    async def force_focus(self):
        try:
            await self.page.bring_to_front()
        except Exception:
            print("force_focus failed")

    async def check_and_handle_dialog(self) -> bool:
        """檢查並處理確認對話框"""
        try:
            dialog_button = self.page.locator("button:has-text('確定')")
            if await dialog_button.is_visible():
                await dialog_button.click()
                print("發現對話框並處理完成")
                return True
            return False
        except Exception as e:
            print(f"處理對話框時發生錯誤: {str(e)}")
            return False

    async def alert_discord(self, content: str):
        """非同步發送 Discord 通知"""
        message = {"content": content}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(tixcraft_setting.WEBHOOK, json=message) as resp:
                    if resp.status == 204:
                        print("Discord 通知已發送！")
                    else:
                        print(f"Discord 發送失敗，狀態碼：{resp.status}")
        except Exception as e:
            print(f"Discord 通知錯誤: {str(e)}")

    # =========================================================
    # Main run loop
    # =========================================================

    async def run(self):
        """主要運行流程"""
        start_time = time.time()
        try:
            await self.init_browser()
            await self.navigate_to_sell_page()

            while True:
                try:
                    url = self.page.url

                    if 'checkout' in url:
                        await self.alert_discord('搶到票囉 🎉')
                        await self.page.pause()
                        break
                    elif 'ticket/ticket' in url:
                        print(url)
                        await self.commit_to_buy()
                    elif 'area' in url:
                        self.set_reload_profile("peak")  # ← 加這行
                        result = await self.select_area()
                        if not result:
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                    elif 'verify' in url:
                        await self.enter_member_number()
                    elif 'order' in url:
                        print('Searching...')
                        self.invalidate_captcha()  # 每次進入訂單頁都清除 captcha cache，確保不會重複使用舊的驗證碼
                        await self.page.wait_for_timeout(random.randint(500, 1000))
                    elif 'detail' in url or 'game' in url:
                        self.set_reload_profile("waiting")  # ← 加這行
                        await self.navigate_to_sell_page()

                except Exception as e:
                    print(f"Loop 錯誤: {str(e)}")

                await asyncio.sleep(0.)

        except Exception as e:
            print(f"執行過程發生錯誤: {str(e)}")
        finally:
            end_time = time.time()
            print("搶票自動化流程結束")
            print(f"總耗時: {end_time - start_time:.2f} 秒")
            print("瀏覽器保持開啟中，請手動關閉...")
            await self.page.pause()
            keep_running = asyncio.Event()
            await keep_running.wait()


async def main():
    bot = TicketBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())