import requests
from datetime import datetime, timedelta
import pandas as pd
import stockstats as stss
import pandas_datareader.data as DataReader # 米Yahoo Financeからデータを読み込めるようにする

import json
import oandapy


"""
Google Financeから株価取得。
"""
def google_finance():
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

  # 日産
  code = 7201

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



"""
為替取得

"""
def kawase():
  accountID = "101-001-7697895-001"
  access_token = "963a55950fcb62aa4d5e1bf4e1429552-967b143deb8692ad6c8e702260e1cd8e"

  oanda = oandapy.API(environment="practice", access_token=access_token)
  response = oanda.get_instruments(account_id=accountID)
  insts = response.get("instruments")
  # 見やすいようにpandasで
  df = pd.DataFrame(list(insts))
  print(df)

if __name__ == '__main__':
  # google_finance()
  kawase()