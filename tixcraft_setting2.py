# -*- coding: utf-8 -*-
"""
設定檔（不要把帳密寫死在程式碼庫；請用環境變數注入）
"""

import os

# 票頁（請填實際活動/場次頁）
SELL_URL = os.getenv("TIX_SELL_URL", "https://tixcraft.com/activity/detail/25_twice_c")

# 使用者代理與視窗大小（維持穩定，不要頻繁更換）
USER_AGENT = os.getenv(
    "TIX_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1280, "height": 900}
LOCALE = os.getenv("TIX_LOCALE", "zh-TW")

# 帳號（建議以環境變數注入）
ACCOUNT = os.getenv("TIX_ACCOUNT", "")
PASSWORD = os.getenv("TIX_PASSWORD", "")

# 想買的張數（依頁面下拉選單可選值而定）
TICKET_NUMBER = os.getenv("TIX_TICKET", "2")

# 區域偏好/排除（以逗號分隔）
EXCLUDED_AREAS = [x.strip() for x in os.getenv("TIX_EXCLUDE", "身障,愛心").split(",") if x.strip()]
PREFERRED_AREAS = [x.strip() for x in os.getenv("TIX_PREFERRED", "").split(",") if x.strip()]
ONLY_PREFERRED_AREAS = os.getenv("TIX_ONLY_PREF", "false").lower() == "true"

# 是否在流程中自動選區/選數量（預設 True；遇到驗證會停下等你手動）
AUTO_CHOOSE = os.getenv("TIX_AUTO_CHOOSE", "true").lower() == "true"

# 持久化使用者資料夾（保存 cookies/session）
USER_DATA_DIR = os.getenv("TIX_USER_DIR", ".pw-user")

# 頁面操作的預設 timeout（毫秒）
DEFAULT_TIMEOUT = int(os.getenv("TIX_TIMEOUT_MS", "15000"))

# 是否使用可見瀏覽器（建議 True 比較容易人工介入）
HEADLESS = os.getenv("TIX_HEADLESS", "false").lower() == "true"