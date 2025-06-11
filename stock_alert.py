import re
import json
import requests

def check_stock(event_url):
    # 取得網頁原始碼
    try:
        
        session = requests.Session()
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome',
        #     'Accept-Language': 'zh-TW,zh;q=0.9',
        #     'Cache-Control': 'no-cache',
        #     'Cookie':"XSRF-TOKEN=IdT06sM41u984l8MzlZ9qLD40k4F3K0%2FZYzrBBWKYVLLH%2F%2Be%2FOSkT1yXAlP6eGQgepn33JPY7knARq8TvY0O4Q%3D%3D; __cfwaitingroom=ChhVUnVDWlkwWmVpWTNrV2lNbnVFT1lnPT0SkAJnVjlicEhtQWJPUjJjVnZLOGcvKzIvaFg1VktSM25YNStYK09zLzBsVVFsVmJVWVg0aHRWNGhSVXZRS3lKaTdzc3RaU0U1bXhYbThwODBlK3dsVTBQdCtoL05MaldqcTlnNTFXckdjb3VjaURESGVhRSt3WDN0MG5SU3RIQmpBZXpJNUhWWitvdStiQzAxb2NMSHlmNDNJVFhKQVgrR3M0b2djb2VvdE82aUE1MFFrU1RlcUNjWlZ2Sk1JbTdGd2QzdE1FeDdBbXVidDY2cnBvWk9kUWlDNlFBTzh2ejRvYVFNRUliUDZrUm1KTEtWKzZRbXV0MlpBb2xKL3RFZTNiOWYzNWpLalN2SGpLWW14cg%3D%3D; _cfuvid=LqWmg6P2p6lICilGN_beYFh70wtRK1ZEWmqQC65OAyU-1748941003075-0.0.1.1-604800000; kktix_session_token_v2=d0f51f785fdac69cfc1f71d6e70baf6b"
        # }

        # session.cookies.set('__cfwaitingroom', "ChhVUnVDWlkwWmVpWTNrV2lNbnVFT1lnPT0SkAJnVjlicEhtQWJPUjJjVnZLOGcvKzIvaFg1VktSM25YNStYK09zLzBsVVFsVmJVWVg0aHRWNGhSVXZRS3lKaTdzc3RaU0U1bXhYbThwODBlK3dsVTBQdCtoL05MaldqcTlnNTFXckdjb3VjaURESGVhRSt3WDN0MG5SU3RIQmpBZXpJNUhWWitvdStiQzAxb2NMSHlmNDNJVFhKQVgrR3M0b2djb2VvdE82aUE1MFFrU1RlcUNjWlZ2Sk1JbTdGd2QzdE1FeDdBbXVidDY2cnBvWk9kUWlDNlFBTzh2ejRvYVFNRUliUDZrUm1KTEtWKzZRbXV0MlpBb2xKL3RFZTNiOWYzNWpLalN2SGpLWW14cg%3D%3D")
        # session.cookies.set('locale', 'zh-TW')
        # session.cookies.set('_cfuvid', 'LqWmg6P2p6lICilGN_beYFh70wtRK1ZEWmqQC65OAyU-1748941003075-0.0.1.1-604800000')
        # session.cookies.set('kktix_session_token_v2', 'd0f51f785fdac69cfc1f71d6e70baf6b')
        # session.cookies.set('XSRF-TOKEN', 'IdT06sM41u984l8MzlZ9qLD40k4F3K0%2FZYzrBBWKYVLLH%2F%2Be%2FOSkT1yXAlP6eGQgepn33JPY7knARq8TvY0O4Q%3D%3D')
        # 第一次請求：伺服器回 Set-Cookie
        resp1 = session.get(event_url,timeout=10)
        print(f"第一次請求狀態碼: {resp1.status_code}")
        # resp1.raise_for_status()
        print(resp1.headers)
        # 第二次請求：Session 內已有 cookie，自動夾帶
        # session.headers.update(resp1.headers)
        resp2 = session.get(event_url, timeout=10)
        print("Status 2:", resp2.status_code)
        print("實際送出的 Cookie:", session.cookies.get_dict())
        resp2.raise_for_status()
        html = resp2.text

        # 用正則擷取 window.inventory = { ... };
        m = re.search(r'window\.inventory\s*=\s*(\{.*?\})\s*;\s*</script>', html, re.S)
        if not m:
            raise ValueError("無法在 HTML 中找到 window.inventory")

        inventory_json = m.group(1)

        # 解析 JSON
        data = json.loads(inventory_json)
        status = data['inventory']['registerStatus']
        # 也可以檢查剩餘數量：data['inventory']['eventInventory']

        if status == 'IN_STOCK':
            return True
        elif status in ('SOLD_OUT', 'OUT_OF_STOCK'):
            return False
        else:
            # 其他狀態（COMING_SOON、REGISTRATION_CLOSED…）
            return False
    except requests.RequestException as e:
        print(f"網路請求錯誤: {e}")
        return False

if __name__ == '__main__':
    # url_in_stock = 'https://kktix.com/events/alanwalkermacau2025/registrations/new'  # 有庫存的範例頁面  [oai_citation:0‡kktix.html](file-service://file-6ZScU12u1HeoR82kjKGfDH)
    url_sold_out  = 'https://kktix.com/events/h3148869/registrations/new'  # 已售完的範例頁面  [oai_citation:1‡kktix_sold_out.html](file-service://file-XyH5kEkvrkVqSckECdbGfv)

    # print('有庫存？', check_stock(url_in_stock))   # True
    print('有庫存？', check_stock(url_sold_out))    # False