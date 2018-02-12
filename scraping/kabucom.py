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


class KabuComMainController():
    def __init__(self, stock, user, password):
        self._driver = webdriver.Chrome(executable_path="../webdriver/chromedriver")
        self._delay = 3
        self._stock = stock
        self._user = user
        self._pass = password

        # datetime, currentPrice, volume
        self._stockTicks = []

        crntDateTime = datetime.datetime.now().strftime("%Y%m%d")
        self._stockTickPath = "./stockTick_" + str(crntDateTime) + ".csv"

        # datetime, open, high, low, close, volume of 1 min. dict.
        self._stockStats = {}

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
            stockPrice = self._driver.find_element_by_xpath('//td[@class="qtbld"]/table/tbody/tr/td[4]').get_attribute('innerHTML')
            stockPrice = str(stockPrice).replace(',', '')
            print(stockPrice)

            #出来高取得
            volumePrice = self._driver.find_element_by_xpath('//*[@id="fullquotetbl"]/tbody/tr[4]/td/div/table/tbody/tr[4]/td[2]').get_attribute('innerHTML')
            volumePrice = str(volumePrice).replace(',', '')
            print(volumePrice)

            #更新ボタンが表示されるまで待つ
            updateImg = WebDriverWait(self._driver, self._delay).until(EC.element_to_be_clickable((By.XPATH, '//table[@id="fullquotetbl"]/tbody/tr[1]/td/div/table/tbody/tr[1]/td[10]/a/img')))

            #更新処理
            self._driver.find_element_by_xpath('//table[@id="fullquotetbl"]/tbody/tr[1]/td/div/table/tbody/tr[1]/td[10]/a/img').click()

            nowDateTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

            #更新ごとの状態を保存。datetime, stockprice, volume
            self._stockTicks.append([nowDateTime, stockPrice, volumePrice])

            #アップデート
            self._status()

            #出力
            self._writeStockTick()

            # 数秒待つ
            randWait = np.random.randint(3,6, dtype="int")
            time.sleep(int(randWait))

            isValidTime += 1
            if(isTest and isValidTime > 50):
                isValidTime = False


    def close(self):
        self._driver.close()
        self._driver.quit()


    """
        各アップデートの値から1分事のopen、high, low, close, volumeを出す。
    """
    def _status(self):
        if len(self._stockTicks) == 1:
            tick = self._stockTicks[0]
            crntPrice = tick[1]
            crntDateTimeStr = str(tick[0])[0:12]
            self._stockStats[crntDateTimeStr] = [crntPrice, crntPrice, crntPrice, crntPrice, crntPrice]
            return

        for i in range(len(self._stockTicks)-1):
            tick = self._stockTicks[i]
            #分までを取得
            crntDateTimeStr = str(tick[0])[0:12]
            crntPrice = tick[1]

            #存在する場合値を更新
            if crntDateTimeStr in self._stockStats:
                crntHigh = self._stockStats[crntDateTimeStr][1]
                crntLow = self._stockStats[crntDateTimeStr][2]
                if crntPrice > crntHigh:
                    self._stockStats[crntDateTimeStr][1] = crntHigh

                if crntPrice < crntLow:
                    self._stockStats[crntDateTimeStr][2] = crntLow

                self._stockStats[crntDateTimeStr][4] = tick[2]

            #初めて追加
            else:
                self._stockStats[crntDateTimeStr] = [crntPrice, crntPrice, crntPrice, crntPrice, crntPrice]

            if crntDateTimeStr != str(self._stockTicks[i+1][0])[0:12]:
                self._stockStats[crntDateTimeStr][4] = crntPrice

    def _writeStockTick(self):
        f = open(self._stockTickPath, 'w', newline='')
        writer = csv.writer(f, lineterminator="\r\n")
        writer.writerow(self._stockTicks)
        f.close()

def kabucom_nisa_buy(price, stock, delay=3):
    URL_BUY = "https://s20.si1.kabu.co.jp/ap/pc/Nisa/Stock/Buy/Input?symbol="+str(stock)+"&exchange=1"

def kabucom_nisa_sell(price, stock, dealy=3):
    URL_SELL = "https://s20.si1.kabu.co.jp/ap/PC/Nisa/Stock/Sell/Input?symbol="+str(stock)+"&exchange=TSE"




if __name__ == '__main__':
    #グリー
    STOCK = 3632

    #日産
    STOCK = 7201

    USER = ""
    PASSWORD = ""

    try:
        kabucom = KabuComMainController(STOCK, USER, PASSWORD)
        kabucom.login()
        kabucom.update()
        print("listing Stock done!")
        kabucom.close()
    except TimeoutException as ex:
        print("Loading took too much time! " + str(ex))



