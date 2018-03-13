import sys

"""
コマンドライン上で打てるように実装。
python3 get_minsellprice.py <<コインの値段>> <<コイン個数>> <<0.001コイン辺りの利益額>>

return: [1コイン辺りの最低売り金額, 買いの時との差, 売らなければいけないコイン個数] 
"""


def getMinSellPrice(buyPrice, coinAmount=0.001, minEarn=1.0, extraFreeList=[0.0, 0.0]):
    minAmount = 0.001
    buyPrice = float(buyPrice)
    coinAmount = float(coinAmount)
    minEarn = float(minEarn)

    # 10万円以下手数料
    extraFee = extraFreeList[0]
    # 実際に払った金額
    actualBuyPrice = buyPrice * coinAmount

    # 50万以下だったら0.14%
    if (actualBuyPrice > 100000.0 and actualBuyPrice <= 500000.0):
        extraFee = extraFreeList[1]

    # 0.01あたりに直す
    ratio = minAmount / coinAmount

    # 0.001あたりの手数料（x2。買い＆売り）
    minExtraFee = actualBuyPrice * extraFee * ratio * 2

    # 0.001あたりの金額
    minActualBuyPrice = buyPrice * minAmount

    # 0.001あたりの最低売り価格 (minEarn*ratioをする事で「全部売ればminEarnになる」)
    possibleSellPrice = minActualBuyPrice + minExtraFee + (minEarn * ratio)

    # 1コインに置き換える
    coinSellPrice = possibleSellPrice / minAmount

    # 1コインあたりのdiff
    diffPrice = coinSellPrice - buyPrice

    return [coinSellPrice, diffPrice, coinAmount]






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

