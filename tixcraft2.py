# -*- coding: utf-8 -*-
"""
拓元票務輔助（合規、人為介入版）
- 不做暴力刷新、不繞過驗證
- 幫你完成：登入、導頁、等待、選區/張數（可關閉）
- 碰到驗證/風控時會停在頁面讓你手動處理
"""

import asyncio
from pathlib import Path
from typing import Tuple

from playwright.async_api import async_playwright, Page, BrowserContext, Playwright, TimeoutError as PWTimeout

import tixcraft_setting2 as C
import random


# ---------------------------
# 啟動與基礎
# ---------------------------
async def launch() -> Tuple[Playwright, BrowserContext, Page]:
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=C.USER_DATA_DIR,
        headless=False,
        channel="chrome",
        viewport=C.VIEWPORT,
        user_agent=C.USER_AGENT,
        locale=C.LOCALE,
        args=[
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-automation',
            '--disable-infobars',
            '--disable-blink-features',
            '--disable-blink-features=AutomationControlled',
            f'--window-size={random.randint(1050, 1200)},{random.randint(800, 900)}',
            '--disable-gpu',
        ],
    )
    page = await context.new_page()
    page.set_default_timeout(C.DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(C.DEFAULT_TIMEOUT + 5000)
    return pw, context, page


# ---------------------------
# 登入（必要時）
# ---------------------------
async def ensure_login(page: Page) -> None:
    # 若首頁已登入可見「會員中心/訂單查詢」等字樣就略過
    await page.goto("https://tixcraft.com/", wait_until="domcontentloaded")
    try:
        if await page.get_by_text("會員中心", exact=False).first.is_visible():
            return
    except PWTimeout:
        pass
    except Exception:
        pass

    # 進登入頁（實際 selector 視拓元調整；以下是示意）
    # 有些活動會強制導去 /login，小心彈窗或 iframe
    try:
        # 首頁右上角登入按鈕（若有）
        btns = page.get_by_role("link", name="登入").or_(page.get_by_text("登入"))
        await btns.first.click(timeout=5000)
    except Exception:
        # 直接嘗試到會員登入頁
        await page.goto("https://tixcraft.com/login", wait_until="domcontentloaded")

    # 填帳密（視實際 DOM 微調）
    try:
        await page.fill('input[type="email"], input[name="email"]', C.ACCOUNT)
        await page.fill('input[type="password"], input[name="password"]', C.PASSWORD)
        # 送出
        await page.click('button[type="submit"], button:has-text("登入")')
        # 等登入完成（檢查登入後元素）
        await page.wait_for_selector("text=會員中心", timeout=20000)
    except Exception:
        # 若出現驗證碼/二步驟：停下等你手動（可在這裡 page.pause()）
        print("登入需要人工操作（可能有驗證碼/簡訊）。請手動完成後繼續。")
        await page.pause()


# ---------------------------
# 等待開賣／進入購買
# ---------------------------
async def wait_for_purchase_button(page: Page) -> None:
    """等待『立即訂購』或等同文案的按鈕可點擊。不要暴力刷新。"""
    await page.goto(C.SELL_URL, wait_until="domcontentloaded")
    keywords = ["立即訂購", "馬上訂購", "前往購買", "購票"]  # 頁面文案可能不同
    while True:
        try:
            for k in keywords:
                btn = page.get_by_role("button", name=k).or_(page.get_by_text(k)).first
                if await btn.is_visible():
                    # 有些情況需要先滾動讓按鈕可點
                    await btn.scroll_into_view_if_needed()
                    await btn.click()
                    await page.wait_for_load_state("domcontentloaded")
                    return
        except Exception:
            pass

        # 若頁面未開賣，等一段時間再輕量刷新（不要過於頻繁）
        print("尚未開放購買，稍候再試……")
        await page.wait_for_timeout(1200)
        try:
            await page.reload(wait_until="domcontentloaded")
        except Exception:
            await page.wait_for_timeout(1000)


# ---------------------------
# 選區（可關閉）
# ---------------------------
async def choose_area_if_needed(page: Page) -> bool:
    if not C.AUTO_CHOOSE:
        return True

    # 依活動頁 DOM 調整；以下採通用策略：找含「區」或看起來像場區列表的 li/button
    possible_lists = [
        'ul[class*="area"], div[class*="area"] li, .zone-list li, .area-list li',
        'button:has-text("區"), a:has-text("區")'
    ]
    for selector in possible_lists:
        items = page.locator(selector)
        count = await items.count()
        if count == 0:
            continue

        for i in range(count):
            el = items.nth(i)
            try:
                text = (await el.inner_text()).strip()
            except Exception:
                continue

            # 排除不想要的區
            if any(x and x in text for x in C.EXCLUDED_AREAS):
                continue

            # 若有偏好，只挑偏好；若 ONLY_PREFERRED_AREAS=False，則偏好優先、否則接受其他
            if C.PREFERRED_AREAS:
                preferred_hit = any(p in text for p in C.PREFERRED_AREAS)
                if C.ONLY_PREFERRED_AREAS and not preferred_hit:
                    continue
                # 偏好命中就先嘗試
                if preferred_hit:
                    try:
                        await el.click(timeout=1500)
                        await page.wait_for_load_state("domcontentloaded")
                        return True
                    except Exception:
                        continue

        # 沒挑中偏好，嘗試第一個可點的（非排除）
        for i in range(count):
            el = items.nth(i)
            try:
                text = (await el.inner_text()).strip()
                if any(x and x in text for x in C.EXCLUDED_AREAS):
                    continue
                await el.click(timeout=1500)
                await page.wait_for_load_state("domcontentloaded")
                return True
            except Exception:
                continue

    # 找不到可點的場區
    return False


# ---------------------------
# 選數量（可關閉）
# ---------------------------
async def choose_ticket_qty_if_needed(page: Page) -> bool:
    if not C.AUTO_CHOOSE:
        return True

    # 常見：select 下拉可選張數；不同活動可能不同 name/id
    candidates = [
        'select[name*="TicketForm"], select#ticket-amount, select[name*="qty"], select[name*="quantity"]',
        'select'
    ]
    for sel in candidates:
        select = page.locator(sel).first
        try:
            if await select.count() > 0:
                await select.select_option(C.TICKET_NUMBER)
                break
        except Exception:
            continue
    else:
        # 沒找到 select，可能是按鈕式加減；改成人工處理
        print("找不到票數下拉，請手動選擇票數後按下一步。")
        await page.pause()
        return True

    # 下一步/確認
    for btn_sel in ["button:has-text('下一步')", "button:has-text('確認')", "button[type=submit]"]:
        try:
            await page.click(btn_sel, timeout=1500)
            await page.wait_for_load_state("domcontentloaded")
            return True
        except Exception:
            pass

    return False


# ---------------------------
# 驗證/風控處理：停下請你手動
# ---------------------------
async def stop_if_captcha(page: Page) -> None:
    # 依實際頁面調整偵測條件；看到驗證就停下
    suspects = [
        "iframe[src*='captcha']",
        "img[alt*='驗證']", "img#TicketForm_verifyCode-image",
        "input[name*='captcha']", "input[id*='captcha']",
        "text=請輸入驗證碼", "text=驗證碼"
    ]
    for s in suspects:
        try:
            if await page.locator(s).first.is_visible():
                print("偵測到驗證/風控，請人工完成後再繼續。")
                await page.pause()
                return
        except Exception:
            pass


# ---------------------------
# 主流程
# ---------------------------
async def main():
    pw, ctx, page = await launch()
    try:
        await ensure_login(page)
        await wait_for_purchase_button(page)
        await stop_if_captcha(page)

        ok = await choose_area_if_needed(page)
        if not ok:
            print("沒有可選的場區（或皆被排除）。請手動選擇。")
            await page.pause()

        await stop_if_captcha(page)

        ok = await choose_ticket_qty_if_needed(page)
        if not ok:
            print("選票或下一步失敗，請手動處理。")
            await page.pause()

        print("已完成基本流程，接下來請你在頁面上確認購票與付款。")
        await page.pause()  # 讓你人工收尾
    finally:
        # 保留瀏覽器以利你手動完成；若要自動關閉請取消註解
        # await ctx.close()
        # await pw.stop()
        pass


if __name__ == "__main__":
    asyncio.run(main())