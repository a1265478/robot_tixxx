import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

# 原始 cookies 來源檔案
SOURCE_COOKIE_FILE = "cookies.json"
TARGET_COOKIE_FILE = "playwright_cookies.json"

def convert_to_playwright_format():
    with open(SOURCE_COOKIE_FILE, "r") as f:
        raw_cookies = json.load(f)

    converted = []
    for c in raw_cookies:
        cookie = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"].lstrip("."),
            "path": c.get("path", "/"),
            "secure": c.get("secure", False),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": "Lax",  # 預設 fallback
        }

        # sameSite 正規化
        ss = c.get("sameSite", "").lower()
        if "strict" in ss:
            cookie["sameSite"] = "Strict"
        elif "none" in ss or "no" in ss:
            cookie["sameSite"] = "None"

        # 處理 expires
        if not c.get("session", False) and "expirationDate" in c:
            cookie["expires"] = int(float(c["expirationDate"]))

        converted.append(cookie)

    with open(TARGET_COOKIE_FILE, "w") as f:
        json.dump(converted, f, indent=2)

    print(f"✅ Cookies 轉換完成，儲存在 {TARGET_COOKIE_FILE}")


async def run_with_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # 載入轉換後的 cookies
        with open(TARGET_COOKIE_FILE, "r") as f:
            cookies = json.load(f)
            await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto("https://kktix.com", wait_until="networkidle")
        print("✅ 頁面標題:", await page.title())
        await asyncio.sleep(10)  # 給你時間確認登入狀態
        await browser.close()


if __name__ == "__main__":
    convert_to_playwright_format()
    asyncio.run(run_with_cookies())