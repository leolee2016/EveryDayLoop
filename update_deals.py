import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

# 定義追蹤的 Google Flights 特惠連結
TARGET_URL = "https://www.google.com/travel/flights/deals?tfs=CBwQBhoaEgoyMDI2LTA4LTE3agwIAhIIL20vMGZ0a3gaGhIKMjAyNi0wOC0yMWIMCAISCC9tLzBmdGt4QAFIAXABggELCP___________wGYAQHaAQgKBDABSAEQAw&hl=zh-TW"

async def fetch_flight_deals():
    async with async_playwright() as p:
        # 啟動無頭瀏覽器 (Headless)
        browser = await p.chromium.launch(headless=True)
        # 設定模擬一般電腦瀏覽器的 User-Agent 避免被擋
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("正在前往 Google Flights 抓取最新特惠行情...")
        await page.goto(TARGET_URL, wait_until="networkidle")
        await page.wait_for_timeout(4000) # 等待動態頁面資料載入完成
        
        deals = []
        # 搜尋 Google Flights 特惠頁面的卡片元件
        cards = await page.query_selector_all('div[role="listitem"]')
        
        for idx, card in enumerate(cards):
            try:
                text = await card.inner_text()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                # 解析基本結構資訊
                if len(lines) >= 2:
                    deals.append({
                        "id": idx + 1,
                        "title": lines[0],
                        "price": lines[1] if ("$" in lines[1] or "NT" in lines[1]) else "點擊查看價格",
                        "details": " / ".join(lines[2:4]) if len(lines) >= 4 else "臺北出發特惠行程",
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
            except Exception as e:
                continue
                
        await browser.close()
        return deals

def generate_html(deals):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_template = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>臺北出發 - 每日最新機票特惠儀表板</title>
    <style>
        :root {{
            --primary: #1a73e8;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-main: #202124;
            --text-sub: #5f6368;
            --accent-green: #1e8e3e;
            --shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background-color: var(--bg-color); color: var(--text-main); padding: 24px; line-height: 1.5; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #1a73e8, #0d47a1); color: white; padding: 28px; border-radius: 16px; margin-bottom: 24px; box-shadow: var(--shadow); }}
        .header h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 8px; }}
        .update-time {{ font-size: 13px; opacity: 0.9; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }}
        .card {{ background: var(--card-bg); border-radius: 12px; padding: 20px; box-shadow: var(--shadow); border: 1px solid #e0e0e0; display: flex; flex-direction: column; justify-content: space-between; }}
        .title {{ font-size: 18px; font-weight: bold; color: var(--text-main); margin-bottom: 8px; }}
        .price {{ font-size: 22px; font-weight: 800; color: var(--accent-green); margin-bottom: 12px; }}
        .details {{ font-size: 13px; color: var(--text-sub); margin-bottom: 16px; line-height: 1.6; }}
        .btn {{ display: block; text-align: center; background: var(--primary); color: white; text-decoration: none; padding: 10px 0; border-radius: 8px; font-weight: 600; font-size: 14px; }}
        .btn:hover {{ background: #1557b0; }}
        .no-data {{ text-align: center; grid-column: 1 / -1; padding: 40px; background: white; border-radius: 12px; color: var(--text-sub); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ 臺北出發機票特惠（每日自動抓取更新）</h1>
            <div class="update-time">🕒 最後更新時間：{current_time} (CST)</div>
        </div>
        <div class="grid">
"""
    if not deals:
        html_template += """
            <div class="no-data">目前未抓取到即時特惠資料，請稍後重試，或點擊連結前往 Google Flights 查看。</div>
"""
    else:
        for deal in deals:
            html_template += f"""
            <div class="card">
                <div>
                    <div class="title">{deal.get('title', '特惠行程')}</div>
                    <div class="price">{deal.get('price', '點擊查看價格')}</div>
                    <div class="details">{deal.get('details', '')}</div>
                </div>
                <a href="{TARGET_URL}" target="_blank" class="btn">前往 Google Flights 預訂 ➔</a>
            </div>
"""
            
    html_template += """
        </div>
    </div>
</body>
</html>
"""
    # 將抓取結果寫入 index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("✅ 已成功自動生成/更新 index.html！")

if __name__ == "__main__":
    deals_data = asyncio.run(fetch_flight_deals())
    generate_html(deals_data)
