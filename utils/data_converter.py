import numpy

"""
予測で出た結果を1,0に判別
前日と比べて上がってたら1、そうでなければ0
"""
def convert_results_updown(predictionArray):
    res = []
    for i in range(0, len(predictionArray)):
        predT = predictionArray[i]
        # 初日は0.5以上か以下で判断
        if(i == 0):
            if(predT > 0.5):
                res.append([1])
            else:
                res.append([0])
            continue

        #2日以降は前日と比較
        predT_1 = predictionArray[i-1]

        if predT > predT_1:
            res.append([1])
        else:
            res.append([0])

    return numpy.array(res, dtype='float')



