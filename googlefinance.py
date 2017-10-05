import requests
from datetime import datetime, timedelta
import pandas as pd

def addRsi(intervalDays, pridces):
  upPriceList = []
  downPriceList = []
  for i in range(1, len(pridces)):
    if(pridces[i-1] < pridces[i]):
      upPriceList.append(pridces[i])
      downPriceList.append(pridces[i-1])
    elif(pridces[i-1] > pridces[i]):
      downPriceList.append(pridces[i])
      upPriceList.append(pridces[i - 1])
    else:
      downPriceList.append(0)
      upPriceList.append(0)
#     if(len(upPriceList) + len(downPriceList) >= intervalDays):
#       upAverage = sum(upPriceList)/intervalDays
#       downAverage = sum(downPriceList)/intervalDays
#       rsi = upAverage/(upAverage + downAverage)
#       pridces.append(rsi)
#       #RSIを追加した後、次に備えて[0]要素を削除
#       del upPriceList[0]
#       del downPriceList[0]
#     else:
#       #上がった
#       if(pridces[keys[i-1]]['CLOSE'] < pridces[keys[i]]['CLOSE']):
#         upPriceList.append(pridces[i]['CLOSE'])
#       elif(pridces[keys[i-1]]['CLOSE'] > pridces[keys[i]]['CLOSE']):
#         downPriceList.append(pridces[i]['CLOSE'])
#       else:
#         pridces.append(0)


url = "https://www.google.com/finance/getprices"
code = 7203
lsat_date = datetime.now() #データの取得開始日
interval = 86400  #データの間隔(秒)。1日 = 86400秒
market = "TYO"  #取引所のコード　TYO=東京証券取引所
period =  "1Y" #データを取得する期間

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

# RSI追加
columns.append('RSI')
addRsi(5, pridces)


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


