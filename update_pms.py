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

def fetch_from_twse(own_holdings):
    """從台灣證券交易所 (TWSE/TPEx) 官方 API 批次抓取即時/最新收盤股價"""
    prices = {}
    try:
        # 建立上市 (tse) 與 上櫃 (otc) 代碼組合
        ex_ch_list = []
        for info in own_holdings.values():
            code = info['ticker'].split('.')[0]
            ex_ch_list.append(f"tse_{code}.tw")
            ex_ch_list.append(f"otc_{code}.tw")
            
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={'|'.join(ex_ch_list)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            msg_array = data.get('msgArray', [])
            
            code_price_map = {}
            for item in msg_array:
                code = item.get('c')
                # 優先抓成交價 z，若未開盤/無成交則依序取昨收 y 或最佳賣價 a
                z_price = item.get('z', '-')
                y_price = item.get('y', '-')
                a_price = item.get('a', '_').split('_')[0]
                
                final_price = None
                for val in [z_price, y_price, a_price]:
                    if val and val != '-' and val != '':
                        try:
                            final_price = float(val)
                            break
                        except ValueError:
                            continue
                            
                if final_price and final_price > 0:
                    code_price_map[code] = round(final_price, 2)

            for name, info in own_holdings.items():
                code = info['ticker'].split('.')[0]
                if code in code_price_map:
                    prices[name] = code_price_map[code]
                    print(f"✅ [證交所官方API] 成功抓取 {name} ({code}): ${prices[name]}")
    except Exception as e:
        print(f"⚠️ 證交所 API 抓取失敗: {e}")
        
    return prices

def fetch_from_yahoo(own_holdings):
    """備用源：透過 Yahoo Finance API (帶 Session Cookie) 抓取股價"""
    prices = {}
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    })
    
    # 先請求首頁建立 Session Cookie
    try:
        session.get("https://fc.yahoo.com", timeout=5)
    except Exception:
        pass

    for name, info in own_holdings.items():
        ticker = info['ticker']
        for domain in ['query1.finance.yahoo.com', 'query2.finance.yahoo.com']:
            try:
                url = f"https://{domain}/v8/finance/chart/{ticker}?interval=1d&range=1d"
                res = session.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    price = data['chart']['result'][0]['meta']['regularMarketPrice']
                    prices[name] = round(float(price), 2)
                    print(f"✅ [Yahoo備用源] 成功抓取 {name} ({ticker}): ${prices[name]}")
                    break
            except Exception:
                continue

    return prices

def fetch_prices():
    """多源抓取最新股價 (優先證交所 API，備用 Yahoo API)"""
    prices = DEFAULT_PRICES.copy()
    print("開始抓取最新即時股價...")
    
    # 1. 第一優先：台灣證券交易所官方 API
    twse_prices = fetch_from_twse(OWN_HOLDINGS)
    prices.update(twse_prices)
    
    # 2. 第二備援：對於沒抓到的個股，嘗試 Yahoo
    missing = {k: v for k, v in OWN_HOLDINGS.items() if k not in twse_prices}
    if missing:
        print(f"🔄 共有 {len(missing)} 檔個股切換至 Yahoo 備用源: {list(missing.keys())}")
        yahoo_prices = fetch_from_yahoo(missing)
        prices.update(yahoo_prices)
        
    for name in OWN_HOLDINGS:
        if name not in twse_prices and name not in yahoo_prices:
            print(f"⚠️ 抓取 {name} 失敗，使用預設基準價: ${prices[name]}")
            
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

    # 1. 更新即時股價時間標籤
    html = re.sub(
        r'<strong>即時股價：</strong>.*?</span>',
        f'<strong>即時股價：</strong>{now_str}</span>',
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
