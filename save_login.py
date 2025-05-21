import asyncio
import json

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

async def save_login_session():
    async with async_playwright() as p:
        with open("cookies.json", "r") as f:
            raw_cookies = json.load(f)
            cookies = normalize_cookies(raw_cookies)
        browser = await p.chromium.launch(headless=False)  # Headful 模式才看得到登入畫面
        context = await browser.new_context()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            viewport={"width": 1280, "height": 800}
        )
        await context.add_cookies(cookies)
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()
        
        await page.goto("https://kktix.com",wait_until="networkidle")
        await stealth_async(page)
        await page.mouse.move(100, 100)
        await page.wait_for_timeout(500)
        await page.mouse.click(100, 100)
        await page.keyboard.press("PageDown")
        print("請手動登入或通過 Cloudflare 驗證，完成後按 Enter...")
        input()

        print("✅ 登入狀態已儲存為 auth.json")
        await browser.close()
def normalize_cookies(cookies):
    valid_same_site = {"Strict", "Lax", "None"}
    for cookie in cookies:
        ss = str(cookie.get("sameSite", "")).strip().lower()

        # 修正常見錯誤值
        if ss not in valid_same_site:
            if ss in ["no_restriction", "unspecified"]:
                cookie["sameSite"] = "None"  # 這是最寬鬆的選擇
            elif ss == "lax":  # 正確
                cookie["sameSite"] = "Lax"
            elif ss == "strict":
                cookie["sameSite"] = "Strict"
            else:
                cookie["sameSite"] = "Lax"  # 預設安全值

    return cookies

asyncio.run(save_login_session())