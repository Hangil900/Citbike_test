'''

This module is 

'''

import CTMC
import LevelParsers
# from gurobipy import *

# from mpl_toolkits.mplot3d.axes3d import Axes3D
# import matplotlib.pyplot as plt


# imports specific to the plots in this example
import numpy as np
from matplotlib import cm
from mpl_toolkits.mplot3d.axes3d import get_test_data

def generateCTMC(cap, flowIn, flowOut):
    return CTMC.generateColumns(flowIn, flowOut, cap)

##
# This will load up the file where the flow rates are stored
##
def getFlowRates():
    line = open("flowRates.txt", "r").read()
    flowMap = eval(line)
    print flowMap.values()[0]
    return flowMap

##
# Generate curves from the flows
##
def generateStationCurves(fM, statMap, timesFlow=True, flowFactorIncrease=1):
    curveMap = {}
    for sid in fM.keys():
        if statMap.has_key(sid):
            a,b = generateCTMC(statMap[sid].cap, -fM[sid][1]*flowFactorIncrease, fM[sid][0]*flowFactorIncrease)
            for i in range(len(a)):
                if timesFlow:
                    a[i] = (a[i]*fM[sid][0]) + (b[i]*(-1*fM[sid][1]))
                else: a[i] += b[i]
            curveMap[sid] = a
    return curveMap

##
# This generates the line equations based on the cost vector
# we are assuming that the cost vector is piecewiselinear
##
def generateLines(costVector):
    lines = []
    for i in range(len(costVector)-1):
        slope = (costVector[i+1] - costVector[i])# We are dividing by 1
        yint = costVector[i] - slope*i
        lines.append( [ slope, yint ] )
    return lines

##
#
##
def solveModel(statMap, cM, numBikes=10000, iname="test.png"):
    
    model = Model("Bike Placement")

    statBikes = {}
    statCosts = {}
    cost = model.addVar(0,GRB.INFINITY, vtype=GRB.CONTINUOUS,
                                    name="costs")

    # Create the variables
    for sid, stat in statMap.items():
        statBikes[sid] = model.addVar(0, stat.cap, vtype=GRB.CONTINUOUS,
                                    name="stat_bikes_%d" % sid )
        statCosts[sid] = model.addVar(0,GRB.INFINITY, vtype=GRB.CONTINUOUS,
                                    name="stat_costs_%d" % sid )
    print "Variables created"
    model.update()
    
    # Add constraints
    #model.addConstr(quicksum(bikes for bikes in statBikes.values()) <= numBikes )
    print "Bike budget constraint"
    
    model.addConstr(quicksum(c for c in statCosts.values()) == cost)
    print "Const constriant"
    
    # Now for each station post the cost constraints
    for sid in statMap.keys():
        if cM.has_key(sid):
            for line in generateLines(cM[sid]):
                model.addConstr(statCosts[sid] >=
                            statBikes[sid]*float(line[0]) + float(line[1]))
    print "Cost constraints"

    model.setObjective(cost, GRB.MINIMIZE)
    print "Objective function posted"
    
    model.update()
    
    print model
    
    model.optimize()    
    
    sumBikes = 0
    
    print sumBikes
    
    sol = {}
        
    for sid, stat in statBikes.items():
        #print sid, statBikes[sid].x, statCosts[sid].x
        #print statBikes[sid].x, sumBikes
        sumBikes += statBikes[sid].x
        sol[sid] = statBikes[sid].x
        
    gmap = MapMaker.Map()
    for sid, stat in statMap.items():
        if cM.has_key(sid):
            pct = statBikes[sid].x/float(stat.cap)
            gmap.addCircle(MapMaker.Circle( stat.ords, pct = pct, text="%d"%sid ))
    print dir(gmap)
    open("test.html", "w").write(gmap.getFullHtml())    
    gmap.produceImage(iname)
        
    print "SumBikes: ", sumBikes, numBikes    
    
    #print sol    
        
    return sol

##
# This function will plot how the curves change as capacity varies
##
def showCapChange(statMap, fM, showSpecial=229):
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from mpl_toolkits.mplot3d import Axes3D

    if showSpecial is None: specFilter = lambda x: True
    else: specFilter = lambda x: x == showSpecial

    for sid in [x for x in statMap.keys() if fM.has_key(x) and specFilter(x)]:
        statMapNew = {sid:statMap[sid]}
        fMNew = {sid:fM[sid]}
        curves = []
        for extraCap in range(0,100):
            statMapNew[sid].cap = extraCap
            cM = generateStationCurves(fMNew, statMapNew,
                                       timesFlow=False, flowFactorIncrease=2)
            curves.append(cM[sid])
            
        plt.clf()
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        
        print len(curves)
        
        ax.set_xlabel("Number of bikes")
        ax.set_ylabel("Added capacity")
        ax.set_zlabel("E[time out]")
        
        index = 0
        for c in curves:
            plt.plot(range(len(c)), [index]*len(c), c) 
            index += 1
            
        # Now plot the hyperplanes
        
        if showSpecial is None:    
            plt.savefig("./3dCurves/%d.png" % sid)
        else:
            plt.show()
            
def checkPlanes(statMap, fM, showSpecial=229):
    
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from mpl_toolkits.mplot3d import Axes3D
    
    if showSpecial is None: specFilter = lambda x: True
    else: specFilter = lambda x: x == showSpecial

    SIZERANGE=20

    for sid in [x for x in statMap.keys() if fM.has_key(x) and specFilter(x)]:
        statMapNew = {sid:statMap[sid]}
        fMNew = {sid:fM[sid]}
        curves = []
        for extraCap in range(0,SIZERANGE*2):
            statMap[sid].cap = extraCap
            cM = generateStationCurves(fMNew, statMapNew,
                                       timesFlow=False, flowFactorIncrease=2)
            curves.append(cM[sid])
            
        # Now I need to rebase the planes
        # g(b,c) = f(b, b+c)
        
        g = [ [0]*SIZERANGE for i in range(SIZERANGE) ]
        
        for b in range(SIZERANGE):
            for c in range(SIZERANGE):
                g[b][c] = curves[b+c][b]
        
        plt.clf()
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        
        ax.set_xlabel("B")
        ax.set_ylabel("C")
        ax.set_zlabel("E[time out]")
        
        index = 0
        for b in g:
            plt.plot(range(len(b)), [index]*len(b), b) 
            index += 1
            
        count = 0    
                
        # Now plot the hyperplanes
        for b in range(SIZERANGE-1):
            for c in range(SIZERANGE-1):
                # Make some planes
                if count % 5 == 0:                
                    # Go up and to right
                    deltaU = - g[b][c] + g[b][c+1]
                    deltaR = - g[b][c] + g[b+1][c]
                    
                    plane = lambda x: (x[1]-c)*deltaU + (x[0]-b)*deltaR + g[b][c]
                    xx, yy = np.meshgrid(range(SIZERANGE), range(SIZERANGE))
                    
                    z = ( deltaR * (xx - b) + deltaU * (yy - c) + g[b][c])
                    
                    Gx, Gy = np.gradient(xx * yy)  # gradients with respect to x and y
                    G = (Gx ** 2 + Gy ** 2) ** .5  # gradient magnitude
                    N = G / G.max()  # normalize 0..1
                    
    
                    ax.plot_surface(xx, yy, z, rstride=1, cstride=1,
                           linewidth=0, antialiased=False, shade=False
                    )
                count += 1
        
        plt.savefig("test.png")
        
        if showSpecial is None:    
            plt.savefig("test.png" % sid)
        else:
            plt.show()
            
def optimizeBikeAndCapacityPlacement(statMap, fM):
    
    SIZERANGE=100
    numBikes = 11000
    numRacks = 11000 + 2461
    
    # Now create the model
    model = Model("Bike Placement")

    statBikes = {}
    statSpots = {}
    statCosts = {}
    cost = model.addVar(0,GRB.INFINITY, vtype=GRB.CONTINUOUS,
                                    name="costs")

    # Create the variables
    for sid, stat in statMap.items():
        statBikes[sid] = model.addVar(0, SIZERANGE, vtype=GRB.CONTINUOUS,
                                    name="stat_bikes_%d" % sid )
        statSpots[sid] = model.addVar(0, SIZERANGE, vtype=GRB.CONTINUOUS,
                                    name="stat_spots_%d" % sid )
        statCosts[sid] = model.addVar(0,GRB.INFINITY, vtype=GRB.CONTINUOUS,
                                    name="stat_costs_%d" % sid )
    print "Variables created"
    model.update()
    
    # Add constraints
    model.addConstr(quicksum(bikes for bikes in statBikes.values()) <= numBikes )
    print "Bike budget constraint"
    
    model.addConstr(quicksum(spots for spots in statSpots.values()) +
                    quicksum(bikes for bikes in statBikes.values()) <= numRacks )
    print "Rack budget constraint"
    
    model.addConstr(quicksum(c for c in statCosts.values()) == cost)
    print "Const constriant"
    
    # Now for each station post the cost constraints
    for sid in [x for x in statMap.keys() if fM.has_key(x)]:
        print sid
        statMapNew = {sid:statMap[sid]}
        fMNew = {sid:fM[sid]}
        curves = []
        for extraCap in range(0,SIZERANGE*2):
            statMap[sid].cap = extraCap
            cM = generateStationCurves(fMNew, statMapNew,
                                       timesFlow=False, flowFactorIncrease=2)
            curves.append(cM[sid])
        # Now I need to rebase the planes
        # g(b,c) = f(b, b+c)
        g = [ [0]*SIZERANGE for i in range(SIZERANGE) ]
        for b in range(SIZERANGE):
            for c in range(SIZERANGE):
                g[b][c] = curves[b+c][b]
        
        #if type(sid) == type(1):
        #    # Its an old one
        #    model.addConstr(statSpots[sid] + statBikes[sid] == statMap[sid].cap)
        
        # Now plot the hyperplanes
        for b in range(SIZERANGE-1):
            for c in range(SIZERANGE-1):            
                # Go up and to right to start
                deltaU = - g[b][c] + g[b][c+1]
                deltaR = - g[b][c] + g[b+1][c]
                
                model.addConstr(statCosts[sid] >=
                            (statBikes[sid]-b)*float(deltaR) +
                            (statSpots[sid]-c)*float(deltaU) + float(g[b][c]))
                
    print "Cost constraints"

    model.setObjective(cost, GRB.MINIMIZE)
    print "Objective function posted"
    
    model.update()
    
    print model
    
    model.optimize()    
            
    for sid in [x for x in statMap.keys() if fM.has_key(x)]:
        print sid, statMap[sid], statBikes[sid].x, statBikes[sid].x + statSpots[sid].x
        
def plotG(fM, sid):
    # Now for each station post the cost constraints
    
    SIZERANGE=20
    SIZERANGE += 1
    
    statMap = LevelParsers.parseOBCurrentIDMap()
    
    statMapNew = {sid:statMap[sid]}
    fMNew = {sid:fM[sid]}
    curves = []
    for extraCap in range(0,SIZERANGE*2):
        statMap[sid].cap = extraCap
        cM = generateStationCurves(fMNew, statMapNew,
                                   timesFlow=True, flowFactorIncrease=1)
        curves.append(cM[sid])
    # Now I need to rebase the planes
    # g(b,c) = f(b, b+c)
    g = [ [0]*SIZERANGE for i in range(SIZERANGE) ]
    for b in range(SIZERANGE):
        for c in range(SIZERANGE):
            g[b][c] = curves[b+c][b]
            
        
    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(1, 1, 1, projection='3d')
    
    
    Xs = np.arange(0, SIZERANGE, 1)
    Ys = np.arange(0, SIZERANGE, 1)
    X, Y = np.meshgrid(Xs, Ys)
    
    print X
    print Y
    
    
    p = ax.plot_wireframe(X, Y, g)
    
    ax.set_xlabel("i")
    ax.set_ylabel("j")
    ax.set_zlabel("g(i,j)")
    
    plt.show()

##
# TESTING:
# This function takes in a curveMap and plots it
# as well as the constraints that will be posted
# to the MIP. It is used to ensure things are convex.
##
def statBikes(curve, fName = None):
    import numpy as np
    import matplotlib.pyplot as plt

    plt.clf()

    def graph(formula, x_range):  
        x = np.array(x_range)  
        y = formula(x)  # <- note now we're calling the function 'formula' with x
        plt.plot(x, y)
        
    vec = curve
    plt.plot(range(len(vec)), vec,  linewidth=5.0)
    for line in generateLines(vec):
        graph(lambda x: x*line[0] + line[1], range(len(vec)))
    plt.ylim(0, 50)
    
    plt.title("Cost curve of CTMC for a station")
    plt.xlabel("Number of bikes")
    plt.ylabel("Cost")
    
    if fName is None:
        plt.show()
    else:
        plt.savefig(fName)
        
def plotPlanes(valueLattice, fName=None):
    pass
        
if __name__ == "__main__":
    
    # fM = getFlowRates()
    # statMap = LevelParsers.parseOBCurrentIDMap()
    
    # optimizeBikeAndCapacityPlacement(statMap, fM)
    
    #plotG(fM, 164)
    
    
    
    statMap = LevelParsers.parseOBCurrentIDMap()
    cM = generateStationCurves(fM, statMap, timesFlow=True, flowFactorIncrease=1)
    
    #solveModel(statMap, cM, numBikes=2000, iname="CTMC_2k_bikes.png")
    #solveModel(statMap, cM, numBikes=4000, iname="CTMC_4k_bikes.png")
    #solveModel(statMap, cM, numBikes=6000, iname="CTMC_6k_bikes.png")
    
    #print cM.values()[0]
    #statBikes(cM.values()[0])
    
    #solveModel(statMap, cM)
    #showCapChange(statMap, fM)
    
    #checkPlanes(statMap, fM, showSpecial=229)
    #optimizeBikeAndCapacityPlacement(statMap, fM)
    