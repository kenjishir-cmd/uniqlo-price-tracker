import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

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
    url = f"https://www.uniqlo.com/tw/products/{product_id}/00"
    price = None
    image_url = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            locale="zh-TW",
        )
        page = context.new_page()

        # 攔截 API 回應
        captured = {}
        def handle_response(response):
            if "price-groups" in response.url or "combinations/prices" in response.url:
                try:
                    data = response.json()
                    captured["price_data"] = data
                    print(f"攔截到 API：{response.url}")
                except:
                    pass
            if "products/" in response.url and "/00" in response.url:
                try:
                    data = response.json()
                    captured["product_data"] = data
                except:
                    pass

        page.on("response", handle_response)

        try:
            print(f"開啟頁面：{url}")
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            # 從攔截的 API 取價格
            if "price_data" in captured:
                result = captured["price_data"].get("result", {})
                groups = result.get("groups", [])
                if groups:
                    price_data = groups[0].get("priceGroup", [{}])[0].get("prices", {})
                    price = price_data.get("base", {}).get("value") or price_data.get("promo", {}).get("value")

            # 備用：直接從頁面 DOM 抓價格
            if not price:
                try:
                    price_el = page.locator(".price, [class*='price'], [class*='Price']").first
                    price_text = price_el.inner_text()
                    price = int("".join(filter(str.isdigit, price_text)))
                    print(f"DOM 取得價格：{price_text}")
                except:
                    pass

            # 取圖片
            try:
                img_el = page.locator("img[class*='product'], img[class*='main']").first
                image_url = img_el.get_attribute("src")
            except:
                pass

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

    return price, image_url

def send_telegram(message):
    import requests
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
