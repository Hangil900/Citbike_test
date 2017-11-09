import pandas as pd
import datetime as dt
import pickle
import os
import numpy as np
import json, pdb, config

# directory where cost curves are stored
ccDirectory = "CCs/"

# format of cost curve files
ccFileFormat = "PainTime%d.txt"

# list of the names of all cost curve files
ccFiles = filter(lambda x: x.endswith(".txt"), os.listdir(ccDirectory))

# number of intervals in a given day (there is one file per interval)
nIntervalsPerDay = len(ccFiles)

# number of hours in an interval
nHoursPerInterval = 24./nIntervalsPerDay

######## get the cost curve data
if os.path.isfile("costCurvePickle.p"):
	# if the cost curve data was already generated then load it through pickle
	allCostCurves = pickle.load(open("costCurvePickle.p", "rb"))
else:
	# otherwise generate it and then dump it to a pickle file
	# allCostCurves[intervalIndex][stationID][bikeLevel] corresponds to the cost at
	# the bike value
	allCostCurves = [eval(open(ccDirectory+ccFileFormat%i, "rb").read()) 
		for i in range(nIntervalsPerDay)]

	pickle.dump(allCostCurves,open("costCurvePickle.p","wb"))

headerNames = [u'rental ID', u'member number', u'first_name', u'email',
               u'start_date', u'startDatetime', u'startID', u'start name',
               u'start status', u'end_date',  u'endDatetime', u'endID',
               u'end name', u'end status', u'trip score']

rawTripDF_file = "./data_files/tripsDF.p"
if os.path.isfile(rawTripDF_file):
    rawTripDF = pickle.load(open(rawTripDF_file))
else:
    # read raw trip data in from the csv file
    rawTripDF = pd.read_csv(
        "./data_files/trips_201610_2.csv", 
	parse_dates = [6,11],
	names=headerNames,
	skiprows=1,
        date_parser=lambda x:dt.datetime.fromtimestamp(long(x)/1.)
	).dropna(how="all")
    pickle.dump(rawTripDF, open('./data_files/tripsDF.p', 'wb'))

dataColumns = rawTripDF.columns

# a dictionary that lets you look up the column index from the header name
headerToIndex = {k:v for (v,k) in enumerate(rawTripDF.columns)}

# function for finding the time interval index in the day
# (for 30 minute intervals they range from 0 to 47)
getTimeIndex = lambda t: int((t.hour+(t.minute+(
    t.second+t.microsecond/1e6)/60.)/60.)/nHoursPerInterval)

getTimeMinute = lambda t: int((t.hour*60 + t.minute))

def parseEntry(row):
	"""
	This calculates for a given trip, the following difference:
	cost curve value after bike was taken out - cost curve value 
        before the bike was taken out
	# it also generates some useful data about the trips themselves
	"""
        row[headerToIndex['startlevel']] = int(row[headerToIndex['startlevel']])
        row[headerToIndex['endlevel']] = int(row[headerToIndex['endlevel']])
            
        datetime = row[headerToIndex["startDatetime"]]
	level = row[headerToIndex["startlevel"]]
	sID = row[headerToIndex["startID"]]
	timeIndex = getTimeIndex(datetime.time())
	badStartFlag = False

	if sID in allCostCurves[timeIndex]:
		levelBefore = max(1,level)

		badStartFlag = (level==0)

                CC = allCostCurves[timeIndex][sID]
                if levelBefore >= len(CC):
                    levelBefore = len(CC) - 1

                # because we take out a bike at the start location
		levelAfter = levelBefore-1
		ccBefore = allCostCurves[timeIndex][sID][levelBefore]
		ccAfter = allCostCurves[timeIndex][sID][levelAfter]

		startDeltaCC = ccAfter - ccBefore
	else:
		startDeltaCC = -2
	startTimeIndex = timeIndex

	datetime = row[headerToIndex["endDatetime"]]
	level = row[headerToIndex["endlevel"]]
	sID = row[headerToIndex["endID"]]
	timeIndex = getTimeIndex(datetime.time())
	badEndFlag = False


	if sID in allCostCurves[timeIndex]:
                largestIndex = len(allCostCurves[timeIndex][sID])
		
		# level before can be at most the number of entries in the cost curve - 2
		# because there is a zero and we must have at least one bike available to take out
		levelBefore = min(level,largestIndex-2)

		badEndFlag = (level==largestIndex-1)

		# because we put in a bike at the end location
		levelAfter = levelBefore+1

		ccBefore = allCostCurves[timeIndex][sID][levelBefore]
		ccAfter = allCostCurves[timeIndex][sID][levelAfter]

		endDeltaCC = ccAfter - ccBefore

	else:
		endDeltaCC = -2

	endTimeIndex = timeIndex

	minuteIndex = getTimeMinute(datetime.time())

	return pd.Series({'startDeltaCC':startDeltaCC,
                          'endDeltaCC':endDeltaCC,
                          'startTimeIndex':startTimeIndex,
                          'endTimeIndex':endTimeIndex,
                          'badStartFlag':badStartFlag,
                          'badEndFlag':badEndFlag,
                          'minuteIndex': minuteIndex})

if os.path.isfile(config.tripDF_pickle):
        deltaCCDF = pickle.load(open(config.tripDF_pickle, "rb"))
        pdb.set_trace()
else:
	deltaCCSeries = rawTripDF.apply(parseEntry,axis=1)
	deltaCCDF = pd.concat([rawTripDF, deltaCCSeries],axis=1)
	deltaCCDF = deltaCCDF[(deltaCCDF.startDeltaCC != -2) &
                              (deltaCCDF.endDeltaCC != -2)]
	deltaCCDF['totalDeltaCC'] = deltaCCDF.startDeltaCC + deltaCCDF.endDeltaCC
	# make requested plots
	# histogram of all cost curve improvements
	deltaCCDF.to_pickle(config.tripDF_pickle)
