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

LINE_TOKEN = os.environ.get("LINE_TOKEN")
PRICE_FILE = "prices.json"

def get_product_info(product_id):
    url = f"https://www.uniqlo.com/tw/api/commerce/v5/zh_TW/products/{product_id}/price-groups/00"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "application/json",
        "Referer": "https://www.uniqlo.com/tw/",
    }
    params = {
        "withPrices": "true",
        "withStocks": "true",
        "country": "TW",
        "lang": "zh_TW",
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        data = r.json()
        result = data.get("result", {})

        price = None
        groups = result.get("groups", [])
        if groups:
            price_data = groups[0].get("priceGroup", [{}])[0].get("prices", {})
            price = price_data.get("base", {}).get("value") or price_data.get("promo", {}).get("value")

        image_url = None
        images = result.get("images", {}).get("main", [])
        if images:
            image_url = images[0].get("url") or images[0].get("image")

        return price, image_url

    except Exception as e:
        print(f"Error: {e}")
    return None, None

def send_line_notify(message):
    if not LINE_TOKEN:
        print("No LINE token")
        return
    requests.post(
        "https://notify-api.line.me/api/notify",
        headers={"Authorization": f"Bearer {LINE_TOKEN}"},
        data={"message": message}
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
    lines = [f"\n📦 UNIQLO 每日價格報告\n🕘 {now}\n"]

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
        lines.append(f"   NT${price}　{trend}")
        if image_url:
            lines.append(f"   🖼 圖片：{image_url}")
        lines.append(f"   🔗 https://m.uniqlo.com/tw/product?pid={pid}")

        updated[pid] = {"price": price, "updated": now}

    send_line_notify("\n".join(lines))
    save_prices(updated)
    print("完成！")

if __name__ == "__main__":
    main()
