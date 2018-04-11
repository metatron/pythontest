import sys

"""
コマンドライン上で打てるように実装。
python3 get_minsellprice.py <<コインの値段>> <<コイン個数>> <<0.001コイン辺りの利益額>>

return: [1コイン辺りの最低売り金額, 買いの時との差, 売らなければいけないコイン個数] 
"""


def getMinSellPrice(buyPrice, coinAmount=0.001, minEarn=1.0, extraFreeList=[0.0, 0.0]):
    #買ったコインを円に変換
    actualBuyYenPrice = buyPrice * coinAmount
    #売り（円）を設定
    idealSellYenPrice = actualBuyYenPrice + minEarn
    #売りのコイン値に変換
    idealSellPrice = idealSellYenPrice /coinAmount

    diffPrice = idealSellPrice - buyPrice

    return [idealSellPrice, diffPrice, coinAmount]






if __name__ == '__main__':
    args = sys.argv
    buyPrice = args[1]
    coinAmount = 0.001
    minEarn = 1.0
    if len(args) > 2:
        coinAmount = args[2]

    if len(args) > 3:
        minEarn = args[3]

    sellprice = getMinSellPrice(float(buyPrice), float(coinAmount), float(minEarn))

    # sellprice = getMinSellPrice(1000000.0, 0.001, 1.0)
    print(sellprice)

