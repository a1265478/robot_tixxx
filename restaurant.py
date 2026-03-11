import requests
import time
import datetime
import restaurant_setting as setting
from typing import Tuple, List, Dict

def parse_available_dates(payload: dict, weekdays_only: bool = False):
    """
    從 API response 裡解析出「可訂位」日期清單。
    可訂位條件：
      - isFull == False
      - isOffDay == False
    如果 weekdays_only=True，則只回傳週一～週五的日期。
    """
    result = payload.get("result", {})
    situation = result.get("situation", [])
    startDate = result.get("startDate")
    endDate = result.get("endDate")

    available = []
    for item in situation:
        is_full = bool(item.get("isFull", True))
        is_off = bool(item.get("isOffDay", False))
        date = item.get("date")
        if not date:
            continue

        if (not is_full) and (not is_off):
            if weekdays_only:
                d = datetime.datetime.strptime(date, "%Y-%m-%d").date()
                if d.weekday() < 5:  # 0=週一, 6=週日
                    available.append(date)
            else:
                available.append(date)

    return available, (startDate, endDate)

def send_discord(dates: List[str], window: Tuple[str, str]) -> None:
    startDate, endDate = window
    content = "🔔 Urban Paradise 有可訂位日期！"
    description = "\n".join(f"• {d} → [立即訂位]({setting.BOOKING_URL})" for d in dates)
    embed = {
        "title": "可訂位日期清單",
        "description": description or "（無）",
        "fields": [
            {"name": "查詢區間", "value": f"{startDate} ~ {endDate}", "inline": False},
            {"name": "說明", "value": "偵測到未滿的日期，手刀去訂位！", "inline": False},
        ],
    }
    resp = requests.post(setting.DISCORD_WEBHOOK, json={"content": content, "embeds": [embed]}, timeout=10)
    resp.raise_for_status()


def poll_api(api_url: str, weekdays_only: bool = True):
    while True:
        try:
            resp = requests.post(
                api_url,
                json={
                    "storeId": setting.STORE_ID,
                    "mealPeriod": setting.MEAL_PERIOD,
                    "peopleCount": setting.COUNT
                },
                timeout=1 
            )
            resp.raise_for_status()
            data = resp.json()

            dates, (startDate, endDate) = parse_available_dates(data, weekdays_only)
            if dates:
                print(f"✅ 發現可訂位日期：{dates} （區間 {startDate}~{endDate}）")
                send_discord(dates,(startDate, endDate))

            else:
                print(f"❌ 目前無空位 （查詢區間 {startDate}~{endDate}）")

        except Exception as e:
            print("⚠️ API 呼叫失敗：", e)

        time.sleep(3)  # 每 3 秒抓一次


if __name__ == "__main__":
    poll_api(setting.FETCH_API, weekdays_only=False)  # True=只抓平日，False=所有日期