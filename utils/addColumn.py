import numpy

def add_column(mat, data):
    maxNum = mat.shape[0]
    if maxNum != len(data):
        print("wrong data length! mat:{0}, data:{1}".format(maxNum, len(data)))
        exit(-1)

    newX=[]
    for i in range(mat.shape[0]):
        tmpX = mat[i,]
        tmpX = numpy.append(tmpX,data[i])
        newX.append(tmpX)

    return numpy.array(newX)


if __name__ == '__main__':

    x=numpy.arange(25).reshape(5,5)
    print(x)

    data = [1,2,3,4,5]
    print(add_column(x,data))
