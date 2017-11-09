'''

This module will compute the expected time 

'''

import numpy
import scipy.linalg
from scipy import sparse
from numpy.linalg import solve

import time, random

##
# Generate the rate matrix
# TODO: Check the outFlow,inFLow placing
##
def createRateMatrix(inRate, outRate, capacity):
    mat = numpy.zeros( (capacity+1, capacity+1) )
    # Put the entries in
    for i in range(capacity+1):
        if i > 0:
            mat[i][i] -= inRate
            mat[i-1][i] = outRate
        if i < capacity:
            mat[i][i] -= outRate
            mat[i+1][i] = inRate
    return mat

def matrixExponential(rMat, t):
    Pt = scipy.linalg.expm(rMat*t)
    return Pt

'''
From Jeff
Given Q...
> [QQ, R, P] = qr(Q)
> pi = QQ(:, 3)'
> pi = (1.0 / sum(pi)) * pi
''' 
def findStatDistribution(rMat):
    q,p = scipy.linalg.qr(rMat)
    pi = q[:,-1].transpose()
    pi = (1.0/sum(pi)) * pi
    return pi

def computeZk(A, pi, k, cap):
    e = numpy.ones((cap+1, 1))
    ek = numpy.zeros((cap+1, 1))
    ek[k] = 1
    rhs = pi[k]*e - ek
    res = scipy.linalg.lstsq(A, rhs)[0]
    b = pi.transpose().dot(res)
    for i in range(cap+1):
        res[i] = res[i] - b
    return res
    
def computeMk(pi, k, t, Pt, zk, cap):
    e = numpy.ones((cap+1, 1))
    I = numpy.identity(cap+1)
    mk = pi[k]*t*e + (I - Pt).dot(zk)
    return mk


'''
Example rate matrix from wikipedia
'''
def exampleWiki():
    mat = numpy.array( [
            [-0.025, 0.02, 0.005],
            [0.3, -0.5, 0.2],
            [0.02, 0.4, -0.42],
        ] )
    return mat

def generateColumns(flowIn, flowOut, cap, t=60*3):
    A = createRateMatrix(flowIn,flowOut, cap)
    Pt = matrixExponential(A, t)
    pi = findStatDistribution(A)
    
    z0 = computeZk(A, pi, 0, cap)
    m0 = computeMk(pi, 0, t, Pt, z0, cap)
    
    zCap = computeZk(A, pi, cap, cap)
    mCap = computeMk(pi, cap, t, Pt, zCap, cap)

    return [a[0] for a in m0], [b[0] for b in mCap]

def runTimesVaryC():
    # Vary cap first
    
    random.seed(20)
    
    t = 180
    times = []
    for cap in range(1,201):
        sclocks = []
        for seed in range(10):
            
            fIn = random.random()
            fOut = random.random()
            
            clock = time.time()
            computeRow(t, cap, fIn, fOut)
            clock = time.time() - clock
            sclocks.append(clock)
        
        times.append(sum(sclocks)/10.0)
        print t, cap, times[-1]
    
    import matplotlib.pyplot as plt
    plt.title("Running time (seconds) of CTMC Computation")
    plt.xlabel("Station Capacity")
    plt.ylabel("Computation Time (seconds)")
    plt.plot(range(1,201), times)
    plt.savefig("CTMC_Runtime_VaryC.png")
    
def runTimesVaryRate():
    # Vary cap first
    
    random.seed(20)
    
    cap = 50
    t = 180
    
    times = []
    for rateMul in range(1,20):
        sclocks = []
        for seed in range(10):
            
            fIn = random.random()*rateMul
            fOut = random.random()*rateMul
            
            clock = time.time()
            computeRow(t, cap, fIn, fOut)
            clock = time.time() - clock
            sclocks.append(clock)
        
        times.append(sum(sclocks)/10.0)
        print t, cap, times[-1]
    
    import matplotlib.pyplot as plt
    plt.title("Running time (seconds) of CTMC Computation")
    plt.xlabel("Size of the time horizon")
    plt.ylabel("Computation Time (seconds)")
    plt.plot(range(1,20), times)
    plt.savefig("CTMC_Runtime_VaryT.png")

def computeRow(t, cap, fIn, fOut):
    A = createRateMatrix(fIn,fOut, cap)
    Pt = matrixExponential(A, t)
    pi = findStatDistribution(A)
    M = []
    for k in range(cap+1):
        zk = computeZk(A, pi, k, cap)
        mk = computeMk(pi, k, t, Pt, zk, cap)
        M.append(map(lambda x: round(x, 3), mk.transpose()[0]))
    


if __name__ == "__main__":
    
    runTimesVaryRate()
    
    
    '''
    cap = 30
    t = 5
    
    
    
    A = createRateMatrix(5,5, cap)
    Pt = matrixExponential(A, t)
    pi = findStatDistribution(A)
    M = []
    for k in range(cap+1):
        zk = computeZk(A, pi, k, cap)
        mk = computeMk(pi, k, t, Pt, zk, cap)
        M.append(map(lambda x: round(x, 3), mk.transpose()[0]))
    print "\n".join(map(str, zip(*M)))
    
    print " Pi[0]*t: ", pi[0]*t
    
    import matplotlib.pyplot as plt
    plt.plot(range(cap+1), M[0])
    plt.plot(range(cap+1), M[-1])
    plt.ylim(0, t)
    plt.show()
    '''
    