from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
from bs4 import BeautifulSoup
import numpy as np
import datetime
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ohlc
import stockstats as stss
import os
import scraping



class KabuComMainController():
    def __init__(self, stock=None, user="", password=""):
        self._driver = None
        if(stock != ""):
            self._driver = webdriver.Chrome(executable_path="../webdriver/chromedriver")
        self._delay = 3
        self._stock = stock
        self._user = user
        self._pass = password

        #買った時の単価
        self._stockBuyPrice = 0

        #売った際の差額（1株辺り）
        self._sellDiff = []

        # datetime, currentPrice, volume
        self._stockTicks = []

        crntDateTime = datetime.datetime.now().strftime("%Y%m%d")
        self._stockTickPath = "./stockTick_" + str(crntDateTime) + "_" + str(stock) + ".csv"
        self._stockStatusPath = "./stockStatus_" + str(crntDateTime) + "_" + str(stock) + ".csv"

        # datetime, open, high, low, close, volume of 1 min. dict.
        self._stockStats = {}

        #売買のシグナルを見つける
        self._signalFinder = scraping.SignalFinder.SignalFinder(self)


    """
        カブ.comにログインする。
    """
    def login(self):
        URL_LOGIN = "https://s10.kabu.co.jp/_mem_bin/members/login.asp?/members/"

        self._driver.get(URL_LOGIN)
        loginBtn = WebDriverWait(self._driver, self._delay).until(EC.element_to_be_clickable((By.ID, 'image1')))
        print("Login Page is ready!")

        #ログインプロセス
        element = self._driver.find_element_by_name("SsLogonUser").send_keys(self._user)
        self._driver.find_element_by_name("SsLogonPassword").send_keys(self._pass)
        self._driver.find_element_by_id('image1').click()


    """
        カブ.comのメンバーページにて株価及び出来高を取得。
    """
    def update(self, isTest = True):
        URL_STOCK = "https://s20.si1.kabu.co.jp/Members/Tradetool/investment_info/?trid=600&trric=" + str(self._stock) + ".T"

        self._driver.get(URL_STOCK)

        # mainbodyの中のpagecontentにアクセス。
        self._driver.switch_to.frame("mainbody")
        self._driver.switch_to.frame("pagecontent")

        isValidTime = True
        while(isValidTime):
            # chart1が表示されるまで待つ
            chartImg = WebDriverWait(self._driver, self._delay).until(EC.element_to_be_clickable((By.ID, 'chart1')))

            # qtbldというクラスを持つtdを見つける。
            # その中のtableのtdの4番目が株価
            stockPrice = self._driver.find_element_by_xpath('//*[@id="fullquotetbl"]/tbody/tr[3]/td/table/tbody/tr[1]/td[4]').get_attribute('innerHTML')
            stockPrice = str(stockPrice).replace(',', '')

            #出来高取得
            volumePrice = self._driver.find_element_by_xpath('//*[@id="fullquotetbl"]/tbody/tr[4]/td/div/table/tbody/tr[4]/td[2]').get_attribute('innerHTML')
            volumePrice = str(volumePrice).replace(',', '')

            # print("{}, {}".format(stockPrice,volumePrice))

            #更新ボタンが表示されるまで待つ
            updateImg = WebDriverWait(self._driver, self._delay).until(EC.element_to_be_clickable((By.XPATH, '//table[@id="fullquotetbl"]/tbody/tr[1]/td/div/table/tbody/tr[1]/td[10]/a/img')))

            #更新処理
            self._driver.find_element_by_xpath('//table[@id="fullquotetbl"]/tbody/tr[1]/td/div/table/tbody/tr[1]/td[10]/a/img').click()

            nowDateTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

            #更新ごとの状態を保存。datetime, stockprice, volume
            self._stockTicks.append([nowDateTime, stockPrice, volumePrice])

            #_stockStatsアップデート
            self._statusUpdate()

            print("date:{}, price:{}".format(nowDateTime,stockPrice))

            # 売買のシグナルを見つける
            self._signalFinder.update()
            self._signalFinder.buySignal()
            self._signalFinder.sellSignal()

            #出力
            self._writeStockTick()

            # 数秒待つ
            randWait = np.random.randint(3,6, dtype="int")
            time.sleep(int(randWait))

            isValidTime += 1
            if(isTest and isValidTime > 20):
                isValidTime = False

            nowTime = datetime.datetime.now().strftime("%H%M")
            if(isTest == False and (int(nowTime) > 1500)):
                isValidTime = False


    """
        ブラウザ削除
    """
    def close(self):
        self._driver.close()
        self._driver.quit()


    """
        各アップデートの値から1分事のopen、high, low, close, volumeを出し、self._stockStatsに格納。
        
        self._stockStats[日時分][open, high, low, close, volume]
        
        になる。
    """
    def _statusUpdate(self):
        #まだ1つしかレコードがない場合は全部現在の値段
        if len(self._stockTicks) == 1:
            tick = self._stockTicks[0]
            crntPrice = tick[1]
            crntDateTimeStr = str(tick[0])[0:12]
            self._stockStats[crntDateTimeStr] = [crntPrice, crntPrice, crntPrice, crntPrice, crntPrice]

            # close額設定の為保存しておく
            self._prevTick = tick
            return

        #一番最後の株価を取得
        tick = self._stockTicks[-1]
        # 分までを取得
        crntDateTimeStr = str(tick[0])[0:12]
        crntPrice = tick[1]

        #現在の時分キーが設定されてある場合、現在の株価と比較
        if crntDateTimeStr in self._stockStats:
            crntHigh = self._stockStats[crntDateTimeStr][1]
            crntLow = self._stockStats[crntDateTimeStr][2]
            if crntPrice > crntHigh:
                self._stockStats[crntDateTimeStr][1] = crntPrice

            if crntPrice < crntLow:
                self._stockStats[crntDateTimeStr][2] = crntPrice

        # 現在時分のキーが設定されてない場合は新しい時分
        else:
            #初めて追加
            self._stockStats[crntDateTimeStr] = [crntPrice, crntPrice, crntPrice, crntPrice, crntPrice]

            #前時分キーのclose値をアプデ
            if self._prevTick:
                prevDateTimeStr = str(self._prevTick[0])[0:12]
                prevClosePrice = self._prevTick[1]
                self._stockStats[prevDateTimeStr][3] = prevClosePrice

        #最終取引額追加
        self._stockStats[crntDateTimeStr][4] = tick[2]

        #close額設定の為保存しておく
        self._prevTick = tick


    """
        self._stockStatsからstockstatsフォーマットのデータにConvertする。
    """
    def convertToStockStats(self, paramlist=[]):
        statusListGraph = []
        statDateTimeList = self._stockStats.keys()
        for statDateTime in statDateTimeList:
            status = self._stockStats[statDateTime]
            statusListGraph.append([statDateTime,float(status[0]),float(status[1]),float(status[2]),float(status[3]),float(status[4])])


        # 保存されたCSVを読み込んでstockstatsフォーマットにする
        pandaDataFrame = pd.DataFrame(statusListGraph, columns=['date','open','high','low','close','volume'])
        stock = stss.StockDataFrame().retype(pandaDataFrame)

        if len(paramlist) > 0:
            for param in paramlist:
                stock.get(param)

        return stock


    """
        stockstatsフォーマットのデータを受け取ってグラフを描画する。
    """
    def makeGraph(self, stockStats):

        # plot graph
        fig = plt.figure(figsize=(10, 5))
        plt.title('Stock Graph', fontsize=10)
        plt.xlabel('x', fontsize=10)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)

        # グラフ用
        graphData = np.array(stockStats.as_matrix(columns=['open', 'high', 'low', 'close']), dtype='float')

        #一つ目
        ax1 = fig.add_subplot(1,1,1)

        open_ = graphData[:, 0]
        high_ = graphData[:, 1]
        low_ = graphData[:, 2]
        close_ = graphData[:, 3]
        candlestick2_ohlc(ax1, open_, high_, low_, close_, colorup="b", width=0.5, colordown="r")

        if (os.path.exists("../figures") != True):
            os.mkdir("../figures")

        plt.savefig("../figures/candle.jpg", format="jpg", dpi=80)

        # plt.show()


    def _writeStockTick(self):
        df = pd.DataFrame(self._stockTicks)
        df.to_csv(self._stockTickPath)


    def readStockTick(self):
        df = pd.read_csv(self._stockTickPath)
        tmpList = df.values.tolist()
        for tick in tmpList:
            tmpTick = tick[1:]
            tmpTick[0] = int(tmpTick[0])
            self._stockTicks.append(tmpTick)
            self._statusUpdate()

            # 売買のシグナルを見つける
            self._signalFinder.update()
            self._signalFinder.buySignal()
            self._signalFinder.sellSignal()

            # stockstatClass = self.convertToStockStats(['rsi_6', 'macd'])
            # alldata = stockstatClass.as_matrix(columns=['open', 'high', 'low', 'close', 'volume', 'macd', 'rsi_6'])
            # print(alldata[-1])
            # print()
            # time.sleep(1)


        # print(self._stockStats)


    def nisa_buy(self, price, isTest=True):
        URL_BUY = "https://s20.si1.kabu.co.jp/ap/pc/Nisa/Stock/Buy/Input?symbol="+str(self._stock)+"&exchange=1"
        self._driver.get(URL_BUY)

        #確認ボタンが表示されるまで待つ（これを待てば後はだいたい表示されてるはず）
        WebDriverWait(self._driver, self._delay).until(EC.element_to_be_clickable((By.XPATH, '/html/body/table[4]/tbody/tr[1]/td[1]/table/tbody/tr[2]/td/form/table[4]/tbody/tr/td[1]/table/tbody/tr[1]/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/input')))

        #株数Text
        self._driver.find_element_by_xpath('//*[@id="InputBuyModel_Quantity_Value"]').send_keys("100")

        #単価Text
        self._driver.find_element_by_xpath('//*[@id="InputBuyModel_Sashine_OrderPrice"]').send_keys(str(price))

        self._stockBuyPrice = price

        #確認画面へ繊維
        self._driver.find_element_by_xpath('/html/body/table[4]/tbody/tr[1]/td[1]/table/tbody/tr[2]/td/form/table[4]/tbody/tr/td[1]/table/tbody/tr[1]/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/input').click()



    def nisa_sell(self, price):
        URL_SELL = "https://s20.si1.kabu.co.jp/ap/PC/Nisa/Stock/Sell/Input?symbol="+str(self._stock)+"&exchange=TSE"
        self._driver.get(URL_SELL)

        #確認ボタン表示までまつ
        WebDriverWait(self._driver, self._delay).until(EC.element_to_be_clickable((By.XPATH, '/html/body/table[4]/tbody/tr[1]/td[1]/table/tbody/tr[2]/td/form/table[3]/tbody/tr/td[1]/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/input')))

        #株数Text
        self._driver.find_element_by_xpath('//*[@id="InputModel_Quantity_Value"]').send_keys("100")

        #指値チェックボックス
        self._driver.find_element_by_xpath('//*[@id="InputModel_WebOrderType_Value_SASHINE"]').click()

        #単価Text
        self._driver.find_element_by_xpath('//*[@id="InputModel_Sashine_OrderPrice"]').send_keys(str(price))

        self._sellDiff.append(price - self._stockBuyPrice)

        #確認画面へ繊維
        self._driver.find_element_by_xpath('/html/body/table[4]/tbody/tr[1]/td[1]/table/tbody/tr[2]/td/form/table[3]/tbody/tr/td[1]/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/input').click()





if __name__ == '__main__':
    #グリー
    STOCK = 3632

    #日産
    STOCK = 7201

    USER = ""
    PASSWORD = ""

    kabucom = KabuComMainController(STOCK, USER, PASSWORD)

    # kabucomにアクセスしてデータを取得
    try:
        kabucom.login()
        kabucom.update(isTest=False)
        print("listing Stock done!")
    except TimeoutException as ex:
        print("Loading took too much time! " + str(ex))

    #セーブしたcsvデータを読み込んでテクニカル指標を算出
    # kabucom.readStockTick()

    #buy処理
    # kabucom.login()
    # kabucom.nisa_sell(300)

    kabucom.close()



