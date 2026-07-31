import os
import re
import datetime
import requests

1. 個股資料與成本設定

OWN_HOLDINGS = {
'主動統一升級50': {'shares': 3000, 'cost': 28799, 'ticker': '00981.TW'},
'主動凱基台灣':   {'shares': 2000, 'cost': 17786, 'ticker': '00982.TW'},
'元大台灣50':     {'shares': 1924, 'cost': 187048, 'ticker': '0050.TW'},
'凱基台灣TOP50':  {'shares': 3000, 'cost': 42757, 'ticker': '00921.TW'},
'主動統一台股增長':{'shares': 5000, 'cost': 136703, 'ticker': '00983.TW'},
'台積電':         {'shares': 60,   'cost': 141823, 'ticker': '2330.TW'},
'王品':           {'shares': 10,   'cost': 2476,   'ticker': '2727.TW'}
}

PLEDGED_HOLDINGS = {
'元大台灣50':     {'shares': 6000,  'cost': 509910},
'主動凱基台灣':   {'shares': 5000,  'cost': 48398},
'主動統一升級50': {'shares': 24000, 'cost': 251295},
'主動統一台股增長':{'shares': 13000, 'cost': 389989},
'凱基台灣TOP50':  {'shares': 35000, 'cost': 450223}
}

LOAN_PRINCIPAL = 643968  # 已借款本金

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
prices = DEFAULT_PRICES.copy()
headers = {'User-Agent': 'Mozilla/5.0'}
for name, info in OWN_HOLDINGS.items():
try:
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{info['ticker']}"
res = requests.get(url, headers=headers, timeout=5)
if res.status_code == 200:
p = res.json()['chart']['result'][0]['meta']['regularMarketPrice']
prices[name] = round(p, 2)
except Exception as e:
print(f"抓取 {name} 股價失敗，維持原價: {e}")
return prices

def update_html(prices):
now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 更新時間標籤
html = re.sub(r'<strong>Google資料：</strong>.*?</span>', f'<strong>Google資料：</strong>{now_str}</span>', html)

# 重新計算數值
pledged_market_val = sum(PLEDGED_HOLDINGS[k]['shares'] * prices[k] for k in PLEDGED_HOLDINGS)
maint_ratio = (pledged_market_val / LOAN_PRINCIPAL) * 100

# 更新質押維持率
html = re.sub(r'<strong>\d+\.\d+%</strong><small>質押 83,000 股</small>', f'<strong>{maint_ratio:.2f}%</strong><small>質押 83,000 股</small>', html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
    
print(f"[{now_str}] 網頁更新完成！質押維持率: {maint_ratio:.2f}%")


if name == 'main':
prices = fetch_prices()
update_html(prices)
