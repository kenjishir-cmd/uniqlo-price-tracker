import requests
import json
import os
import re
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
    url = f"https://www.uniqlo.com/tw/zh_TW/product-detail.html?productCode={product_id}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9",
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {r.status_code}")

        # 從網頁 HTML 找價格
        match = re.search(r'"price":(\d+)', r.text)
        if match:
            price = int(match.group(1))
            print(f"Price: {price}")
            return price, None

        # 備用方式
        match = re.search(r'NT\$\s*(\d+)', r.text)
        if match:
            price = int(match.group(1))
            print(f"Price: {price}")
            return price, None

        print("Price not found in HTML")
        print(r.text[:1000])

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
        lines.append(f"https://www.uniqlo.com/tw/zh_TW/product-detail.html?productCode={pid}")
        lines.append("")

        updated[pid] = {"price": price, "updated": now}

    message = "\n".join(lines)
    send_telegram(message)
    save_prices(updated)
    print("完成！")


if __name__ == "__main__":
    main()
