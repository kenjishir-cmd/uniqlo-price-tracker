import requests
import json
import os
from datetime import datetime

PRODUCTS = [
    {
        "id": "u0000000053625",
        "name": "UNIQLO 商品 053625",
    }
]

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
PRICE_FILE = "prices.json"

def get_product_info(product_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9",
        "Referer": "https://www.uniqlo.com/tw/",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
    }

    # 嘗試多個 API 端點
    urls = [
        f"https://www.uniqlo.com/tw/api/commerce/v5/zh_TW/products/{product_id}/combinations/prices?withStocks=true&country=TW&lang=zh_TW",
        f"https://www.uniqlo.com/tw/api/commerce/v5/zh_TW/products/{product_id}/price-groups/00?withPrices=true&withStocks=true&country=TW&lang=zh_TW",
        f"https://d.uniqlo.com/p/hmall/{product_id}/zh_TW/price/zh_TW",
    ]

    for url in urls:
        try:
            print(f"嘗試：{url}")
            r = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {r.status_code}")

            if r.status_code != 200:
                continue

            data = r.json()
            print(f"Response: {json.dumps(data)[:200]}")
            result = data.get("result", {})

            # 嘗試取價格
            price = None
            groups = result.get("groups", [])
            if groups:
                price_data = groups[0].get("priceGroup", [{}])[0].get("prices", {})
                price = price_data.get("base", {}).get("value") or price_data.get("promo", {}).get("value")

            if not price:
                # 備用解析方式
                price = result.get("price") or result.get("basePrice") or result.get("value")

            # 嘗試取圖片
            image_url = None
            images = result.get("images", {}).get("main", [])
            if images:
                image_url = images[0].get("url") or images[0].get("image")

            if price:
                return price, image_url

        except Exception as e:
            print(f"Error: {e}")
            continue

    return None, None

def send_telegram(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("No Telegram credentials")
        return
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={
            "chat_id": TG_CHAT_ID,
            "text": message,
        }
    )

def load_prices():
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_prices(prices):
    with open(PRICE_FILE, "w") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)

def main():
    saved = load_prices()
    updated = dict(saved)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📦 UNIQLO 每日價格報告\n🕘 {now}\n"]

    for product in PRODUCTS:
        pid = product["id"]
        name = product["name"]
        price, image_url = get_product_info(pid)
        prev_price = saved.get(pid, {}).get("price")

        if price is None:
            lines.append(f"❌ {name}：無法取得價格")
            continue

        if prev_price and price < prev_price:
            trend = f"📉 降價（之前 NT${prev_price}）"
        elif prev_price and price > prev_price:
            trend = f"📈 漲價（之前 NT${prev_price}）"
        else:
            trend = "➡️ 無變動"

        lines.append(f"👕 {name}")
        lines.append(f"💰 NT${price}　{trend}")
        if image_url:
            lines.append(f"🖼 圖片：{image_url}")
        lines.append(f"🔗 https://m.uniqlo.com/tw/product?pid={pid}")

        updated[pid] = {"price": price, "updated": now}

    send_telegram("\n".join(lines))
    save_prices(updated)
    print("完成！")

if __name__ == "__main__":
    main()
