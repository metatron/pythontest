import requests
from datetime import datetime, timedelta
import pandas as pd
import stockstats as stss


url = "https://finance.google.com/finance/getprices"
code = 3632
lsat_date = datetime.now() #データの取得開始日
interval = 86400  #データの間隔(秒)。1日 = 86400秒
market = "TYO"  #取引所のコード　TYO=東京証券取引所
period = "2Y" #データを取得する期間

# 日経平均
# code="NI225"
# market="INDEXNIKKEI"

# トヨタ
# code = 7203

# ヤマシンフィルター
# code = 6240



params = {
  'q': code,
  'i': interval,
  'x': market,
  'p': period,
  'ts': lsat_date.timestamp()
}

r = requests.get(url, params=params)

lines = r.text.splitlines()
columns = lines[4].split("=")[1].split(",")
pridces = lines[8:]

#レスポンスの１日目のタイムスタンプをdatetimeに
first_cols = pridces[0].split(",")
first_date = datetime.fromtimestamp(int(first_cols[0].lstrip('a')))
result = [[first_date.date(), first_cols[1], first_cols[2], first_cols[3], first_cols[4], first_cols[5]]]

for price in pridces[1:]:
  cols = price.split(",")
  date = first_date + timedelta(int(cols[0]))
  result.append([date.date(), cols[1], cols[2], cols[3], cols[4], cols[5]])

df = pd.DataFrame(result, columns = columns)
df.to_csv(str(code) + ".csv", index=False)

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv(str(code) + ".csv"))
print(stock['close'])