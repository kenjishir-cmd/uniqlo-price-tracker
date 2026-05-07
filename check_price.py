import requests
import json
import os
from datetime import datetime

PRODUCTS = [
    {
        "id": "u0000000483832",
        "name": "男裝 輕型連帽外套 483832",
    }
]

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
PRICE_FILE = "prices.json"


def get_product_info(product_id):
    short_id = product_id.replace("u0000000", "")

    url = "https://www.uniqlo.com/tw/api/commerce/v5/zh_TW/products"

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept": "application/json",
        "Referer": "https://www.uniqlo.com/tw/",
    }

    params = {
        "q": short_id,
        "count": "1",
        "offset": "0",
        "lang": "zh_TW",
        "country": "TW",
        "withPrices": "true",
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")

        if r.status_code == 200:
            data = r.json()
            items = data.get("result", {}).get("items", [])
            if items:
                prices = items[0].get("prices", {})
                price = (
                    prices.get("promo", {}).get("value")
                    or prices.get("base", {}).get("value")
                )
                return price, None

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
        price, _ = get_product_info(pid)
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
        lines.append(f"https://m.uniqlo.com/tw/product?pid={pid}")
        lines.append("")
        updated[pid] = {"price": price, "updated": now}

    message = "\n".join(lines)
    send_telegram(message)
    save_prices(updated)
    print("完成！")


if __name__ == "__main__":
    main()
