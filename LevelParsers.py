##
#
# This file stores the code to grab current station state from the web
#
##

import urllib2

##
# Parse the information from the O'Brien website
##
def parseOBCurrent(scheme="newyork"):
    url = "http://marlin.casa.ucl.ac.uk/~ollie/bikesapi/load.php?scheme=%s" % scheme
    res = urllib2.urlopen(url).read()
    lines = res.split("\n")[1:]
    load_map = {}
    stations = []
    for line in lines[:-1]:
        
        st = parseOBStation(line, load_map)
        if st is not None:
            stations.append(st)
        
    return stations, load_map

##
# Return a map of station id to station object
##
def parseOBCurrentIDMap(scheme="newyork"):
    stats, lm = parseOBCurrent(scheme)
    statMap = {}
    for stat in stats:
        statMap[stat.id] = stat
    return statMap

##
# Parse a station from a line
##
def parseOBStation(line, load_map):
    line = line.replace(", T", "")

    # Above is a special case for Chicago
    info = line.strip().split(",")
    s_id = int(info[0])
    addr = info[2].replace('"', '')
    lat_lng = ( float(info[3]), float(info[4]) )
    available = int(info[5])
    spaces = int(info[6])
    cap = available+spaces #int(info[10])
    
    if available == 0 and spaces == 0:
        return None
    
    st = Station(addr, cap, lat_lng, s_id)
    load_map[st.id] = (available, spaces)
    return st

##
# Object used to store basic station information
##
class Station(object):
    def __init__(self, address, cap = -1, ords = None, id=-1):
        self.address = address
        self.cap = cap
        self.ords = ords
        self.id = id

    def __str__(self, ):
        return self.address

##
# Example: used for testing
##
if __name__ == "__main__":
    stats, lm = parseOBCurrent("newyork")
    total = 0
    totalCap = 0
    for stat in stats:
        total += lm[stat.id][0]
        totalCap += stat.cap
        #print stat.cap, sum(lm[stat.id])
        #print stat, stat.id, lm[stat.id]
    print "Total:", total, totalCap
    