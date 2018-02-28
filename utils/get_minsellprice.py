import sys

"""
コマンドライン上で打てるように実装。
python3 get_minsellprice.py <<コインの値段>> <<コイン個数>> <<利益額>>
"""
def getMinSellPrice(buyPrice, coinAmount=0.001, minEarn=1.0):
    minAmount = 0.001
    
    #10万円以下手数料
    extraFee = 0.0015
    #実際に払った金額
    actualBuyPrice = float(buyPrice) * float(coinAmount)

    #50万以下だったら0.14%
    if(actualBuyPrice > 100000.0 and actualBuyPrice <= 500000.0):
        extraFee = 0.0014

    #手数料金額（買った時＋売った時の手数料になるが面倒なのでとりあえず2倍）
    payingFee = actualBuyPrice * extraFee * 2

    #実際に買った際の最低額(0.001コインの値段）
    minBuyPrice = actualBuyPrice * minAmount/float(coinAmount)

    actualSellPrice = minBuyPrice + payingFee + minEarn
    #1コインに置き換え
    sellPrice = actualSellPrice/minAmount
    #diff
    print("DIFFFFF: " + str(minBuyPrice))
    diffprice = sellPrice - float(minBuyPrice)/minAmount

    return [sellPrice, diffprice, coinAmount]


if __name__ == '__main__':
    # args = sys.argv
    # buyPrice = args[1]
    # coinAmount = 0.001
    # minEarn = 1.0
    # if len(args) > 2:
    #     coinAmount = args[2]
    #
    # if len(args) > 3:
    #     minEarn = args[3]
    #
    # sellprice = getMinSellPrice(float(buyPrice), float(coinAmount), float(minEarn))

    sellprice = getMinSellPrice(1000000.0, 0.002, 1)
    print(sellprice)

