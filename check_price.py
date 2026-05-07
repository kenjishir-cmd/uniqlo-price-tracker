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
    url = f"https://www.uniqlo.com/tw/api/commerce/v5/zh_TW/products/{product_id}/price-groups/00"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9",
        "Referer": "https://www.uniqlo.com/tw/zh_TW/",
        "Origin": "https://www.uniqlo.com",
    }

    params = {
        "withPrices": "true",
        "withStocks": "true",
        "country": "TW",
        "lang": "zh_TW",
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")

        if r.status_code != 200:
            return None, None

        data = r.json()
        result = data.get("result", {})
        price = None
        groups = result.get("groups", [])

        if groups:
            price_data = groups[0].get("priceGroup", [{}])[0].get("prices", {})
            price = (
                price_data.get("promo", {}).get("value")
                or price_data.get("base", {}).get("value")
            )

        image_url = None
        images = result.get("images", {}).get("main", [])
        if images:
            image_url = images[0].get("url") or images[0].get("image")

        return price, image_url

    except Exception as e:
        print(f"Error: {e}")

    return None, None


def send_telegram(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Missing Telegram config")
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    print(r.text)


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

    lines = [f"📦 UNIQLO 每日價格報告", f"🕘 {now}", ""]

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
        lines.append(f"NT${price}　{trend}")
        if image_url:
            lines.append(f"🖼 {image_url}")
        lines.append(f"https://www.uniqlo.com/tw/zh_TW/product-detail.html?productCode={pid}")
        lines.append("")

        updated[pid] = {"price": price, "updated": now}

    message = "\n".join(lines)
    send_telegram(message)
    save_prices(updated)
    print("完成！")


if __name__ == "__main__":
    main()
