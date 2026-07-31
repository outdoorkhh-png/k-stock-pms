import os
import re
import datetime
import requests

# 1. 自有個股持股與成本設定 (券商口徑)
OWN_HOLDINGS = {
    '主動統一升級50': {'shares': 3000, 'cost': 28799, 'ticker': '00981.TW'},
    '主動凱基台灣':   {'shares': 2000, 'cost': 17786, 'ticker': '00982.TW'},
    '元大台灣50':     {'shares': 1924, 'cost': 187048, 'ticker': '0050.TW'},
    '凱基台灣TOP50':  {'shares': 3000, 'cost': 42757, 'ticker': '00921.TW'},
    '主動統一台股增長':{'shares': 5000, 'cost': 136703, 'ticker': '00983.TW'},
    '台積電':         {'shares': 60,   'cost': 141823, 'ticker': '2330.TW'},
    '王品':           {'shares': 10,   'cost': 2476,   'ticker': '2727.TW'}
}

# 2. 質押股票與股數 (KPMS 口徑)
PLEDGED_HOLDINGS = {
    '元大台灣50':     {'shares': 6000,  'cost': 509910},
    '主動凱基台灣':   {'shares': 5000,  'cost': 48398},
    '主動統一升級50': {'shares': 24000, 'cost': 251295},
    '主動統一台股增長':{'shares': 13000, 'cost': 389989},
    '凱基台灣TOP50':  {'shares': 35000, 'cost': 450223}
}

LOAN_PRINCIPAL = 643968  # 質押已借款總本金

# 預設基準股價
DEFAULT_PRICES = {
    '元大台灣50': 102.85,
    '主動凱基台灣': 8.48,
    '主動統一升級50': 9.25,
    '主動統一台股增長': 26.13,
    '凱基台灣TOP50': 14.65,
    '台積電': 2425.00,
    '王品': 234.50
}

def fetch_prices():
    """透過 Yahoo Finance API 抓取最新即時股價"""
    prices = DEFAULT_PRICES.copy()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    print("開始抓取最新即時股價...")
    for name, info in OWN_HOLDINGS.items():
        ticker = info['ticker']
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d"
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                prices[name] = round(float(price), 2)
                print(f"✅ 成功抓取 {name} ({ticker}): ${prices[name]}")
            else:
                print(f"⚠️ 抓取 {name} 失敗 (HTTP {res.status_code})，使用預設價 ${prices[name]}")
        except Exception as e:
            print(f"⚠️ 抓取 {name} 異常: {e}，使用預設價 ${prices[name]}")
            
    return prices

def update_html(prices):
    """將最新股價、計算數據與更新時間寫入 index.html"""
    tz_tw = datetime.timezone(datetime.timedelta(hours=8))
    now_str = datetime.datetime.now(tz_tw).strftime("%Y-%m-%d %H:%M")
    
    filename = 'index.html'
    if not os.path.exists(filename):
        print(f"❌ 找不到 {filename}")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. 更新資料時間標籤
    html = re.sub(
        r'<strong>Google資料：</strong>.*?</span>',
        f'<strong>Google資料：</strong>{now_str}</span>',
        html
    )
    
    # 2. 計算質押總市值與維持率
    pledged_market_val = sum(PLEDGED_HOLDINGS[k]['shares'] * prices.get(k, DEFAULT_PRICES[k]) for k in PLEDGED_HOLDINGS)
    maint_ratio = (pledged_market_val / LOAN_PRINCIPAL) * 100 if LOAN_PRINCIPAL > 0 else 0
    
    # 3. 更新質押維持率數值
    html = re.sub(
        r'<strong>\d+\.\d+%</strong><small>質押 83,000 股</small>',
        f'<strong>{maint_ratio:.2f}%</strong><small>質押 83,000 股</small>',
        html
    )

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"🎉 [{now_str}] index.html 更新完成！最新質押維持率：{maint_ratio:.2f}%")

if __name__ == '__main__':
    try:
        prices = fetch_prices()
        update_html(prices)
    except Exception as err:
        print(f"腳本執行捕獲例外: {err}")
