import mysql.connector
import config, csv, pdb, os, time, pickle
import datetime as dt
import calendar

def get_station_fill(tripDF):
    """
    Takes as input a trips Data Frame, and adds the station fill level data.
    """
    cnx = mysql.connector.connect(**config.bikshare_db_config)
    cursor = cnx.cursor()

    q1 = "SELECT h.station_id, h.bikes_available, h.docks_available, h.time"
    q2 =  " FROM ("
    q3 = " SELECT station_id, MAX(time) time"
    q4 = " FROM status"
    q5 = " WHERE time <= '{0}' AND station_id = {1}"
    q6 = " GROUP BY station_id"
    q7= " ) q JOIN status h"
    q8 = " ON q.station_id = h.station_id"
    q9 = " AND q.time = h.time;"
    query = (q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8 + q9)

    tripDF['startlevel'] = 0
    tripDF['endlevel'] = 0
    error = 0
    for index, trip in tripDF.iterrows():
	startID = trip['startID']
	endID = trip['endID']
	startTime = trip['startDatetime']
	endTime = trip['endDatetime']
        
	startTime = startTime.strftime('%Y-%m-%d %H:%M:%S')
        endTime = endTime.strftime('%Y-%m-%d %H:%M:%S')
	queryForm = query.format(startTime, startID)
        try:
	    cursor.execute(queryForm)
	    res = cursor.fetchall()[0]
	    startLevel = str(res[1])
        except Exception as e:
            error += 1
            startLevel = -1

	queryForm = query.format(endTime, endID)
        try:
	    cursor.execute(queryForm)
	    res = cursor.fetchall()[0]
	    endLevel = str(res[1])
        except Exception as e:
            error += 1
            endLevel = -1
            
        tripDF.ix[index, 'startlevel'] = int(startLevel)
        tripDF.ix[index, 'endlevel'] = int(endLevel)
        
    print error
    pickle.dump(tripDF, open('../data_files/tripsDF.p', 'wb'))

def run():
    tripDF = pickle.load(open('../data_files/tripsDF.p', 'rb'))
    get_station_fill(tripDF)



    
def get_riders():
    # Get the incentivized members (Angels)
    if os.path.isfile(config.riders_pickle):
        # if the data was already generated then load it through pickle
        angels = pickle.load(open(config.riders_pickle, "rb"))
    else:
	# otherwise generate it and then dump it to a pickle file
	angels = set()
        tripsDF = pickle.load(open(config.tripDF_pickle, 'rb'))
        for rider in tripsDF['member number']:
            angels.add(rider)
        angels = list(angels)
	pickle.dump(angels, open(config.riders_pickle,"wb"))
    return angels

def get_stations():
    # Gets the incentivized stations
    if os.path.isfile(config.stations_pickle):
        Istations = pickle.load(open(config.stations_pickle, "rb"))
    else:
        tripsDF = pickle.load(open(config.tripDF_pickle, 'rb'))
        AM = set()
        PM = set()
        for i, status in enumerate(tripsDF['start status']):
            if status  < 0:
                AM.add(tripsDF['startID'].tolist()[i])

        for i, status in enumerate(tripsDF['end status']):
            if status > 0:
                PM.add(tripsDF['endID'].tolist()[i])
        pickle.dump(list(AM), open(config.AM_stations_p, 'wb'))
        pickle.dump(list(PM), open(config.PM_stations_p, 'wb'))

        Istations = list(set(list(AM) + list(PM)))
        pickle.dump(Istations, open(config.stations_pickle, 'wb'))
    return Istations
        

# Get inflow/outflow data for angels/non angels for incentivized stations
# for across periods of length periodLength
def getInflowOutflowAngels(stationID, startTime, endTime,
                           members, periodLength = 30):
	cnx = mysql.connector.connect(**config.warehouse_db_config)
	cursor = cnx.cursor()

	outFlowQuery = "SELECT FLOOR( (hourOfDayValue*60 + minuteOfHourValue) / {4}) AS timeIndex, count(*) FROM BikeRentalFact INNER JOIN DateDim ON BikeRentalFact.startDate_id = DateDim.id "
	outFlowQuery +=	"INNER JOIN TimeDim ON BikeRentalFact.startTime_id = TimeDim.id "
	outFlowQuery +=	"WHERE startStation_id = {0} AND "
	outFlowQuery += "member_memberNumber in ({1}) AND "
	outFlowQuery += "DateDim.dayOfWeekValue between 1 and 5 AND "
	outFlowQuery += "startTimeMs between {2} and {3} "
	outFlowQuery += "GROUP BY timeIndex;"
	
	queryForm = (outFlowQuery.format(stationID, members, startTime,
                                         endTime, periodLength))

	cursor.execute(queryForm)
	outRes = cursor.fetchall()

	inFlowQuery = "SELECT FLOOR( (hourOfDayValue*60 + minuteOfHourValue) / {4}) AS timeIndex, count(*) FROM BikeRentalFact INNER JOIN DateDim ON BikeRentalFact.startDate_id = DateDim.id "
	inFlowQuery +=	"INNER JOIN TimeDim ON BikeRentalFact.startTime_id = TimeDim.id "
	inFlowQuery +=	"WHERE endStation_id = {0} AND "
	inFlowQuery += "member_memberNumber in ({1}) AND "
	inFlowQuery += "DateDim.dayOfWeekValue between 1 and 5 AND "
	inFlowQuery += "startTimeMs between {2} and {3} "
	inFlowQuery += "GROUP BY timeIndex;"
	
	queryForm = (inFlowQuery.format(stationID, members, startTime, endTime, periodLength))

	cursor.execute(queryForm)
	inRes = cursor.fetchall()

	return outRes, inRes

#Get inflow/outflow data for angels/non angels for incentivized stations for across periods of length periodLength
def getInFlowOutFlowNonAngels(stationID, startTime, endTime, periodLength = 30):
	cnx = mysql.connector.connect(**config.warehouse_db_config)
	cursor = cnx.cursor()

	outFlowQuery = "SELECT FLOOR( (hourOfDayValue*60 + minuteOfHourValue) / {3}) AS timeIndex, count(*) FROM BikeRentalFact INNER JOIN DateDim ON BikeRentalFact.startDate_id = DateDim.id "
	outFlowQuery +=	"INNER JOIN TimeDim ON BikeRentalFact.startTime_id = TimeDim.id "
	outFlowQuery +=	"WHERE startStation_id = {0} AND "
	outFlowQuery += "DateDim.dayOfWeekValue between 1 and 5 AND "
	outFlowQuery += "startTimeMs between {1} and {2} "
	outFlowQuery += "GROUP BY timeIndex;"
	
	queryForm = (outFlowQuery.format(stationID, startTime, endTime,
                                         periodLength))

	cursor.execute(queryForm)
	outRes = cursor.fetchall()

	inFlowQuery = "SELECT FLOOR( (hourOfDayValue*60 + minuteOfHourValue) / {3}) AS timeIndex, count(*) FROM BikeRentalFact INNER JOIN DateDim ON BikeRentalFact.startDate_id = DateDim.id "
	inFlowQuery +=	"INNER JOIN TimeDim ON BikeRentalFact.startTime_id = TimeDim.id "
	inFlowQuery +=	"WHERE endStation_id = {0} AND "
	inFlowQuery += "DateDim.dayOfWeekValue between 1 and 5 AND "
	inFlowQuery += "startTimeMs between {1} and {2} "
	inFlowQuery += "GROUP BY timeIndex;"
	
	queryForm = (inFlowQuery.format(stationID, startTime, endTime,
                                        periodLength))

	cursor.execute(queryForm)
	inRes = cursor.fetchall()

	return outRes, inRes

def getStationFlows(stations, start_date, end_date, members, periodLength):
    
        curr_date = start_date
        memberSet = ",".join(["'" + x + "'" for x in members])
        all_flow = {}
        
        while curr_date <= end_date:
            print curr_date.strftime('%Y_%m_%d') + "\n\n"
            curr_file = config.flow_rates_p[:-6] + ".p"
            curr_file  = curr_file.format(curr_date.strftime('%Y_%m_%d'))

            if os.path.isfile(curr_file):
                # if the data was already generated then load it through pickle
                stationsFlowsTable  = pickle.load(open(curr_file, "rb"))
                all_flow[curr_date.strftime('%Y_%m_%d')] = stationsFlowsTable
                curr_date += dt.timedelta(days=1)
                continue
            
            stationsFlowTable = {}
            curr_end = dt.timedelta(days=1) + curr_date

            start = time.mktime(curr_date.timetuple()) * 1000
            end = time.mktime(curr_end.timetuple()) * 1000
        
	    for station in stations:
		print "Station %d" % station
		angelFlow = {}
		nonAngelFlow = {}
		for i in range((24*60 / periodLength)):
		    angelFlow[i] = [0,0]
		    nonAngelFlow[i] = [0,0]

		#Get Angels flow rates
		outRes, inRes = getInflowOutflowAngels(station, start,
                                                       end, memberSet,
                                                       periodLength)
		for (timeInd, flow) in outRes:
		    angelFlow[timeInd][0] += flow
		for (timeInd, flow) in inRes:
		    angelFlow[timeInd][1] += flow

                
		#Get non-Angel flow rates
		outRes, inRes = getInFlowOutFlowNonAngels(station, start,
                                                          end, periodLength)
		for (timeInd, flow) in outRes:
		    nonAngelFlow[timeInd][0] += flow
		for (timeInd, flow) in inRes:
		    nonAngelFlow[timeInd][1] += flow

		for timeInd in nonAngelFlow:
		    nonAngelFlow[timeInd][0] -= angelFlow[timeInd][0]
		    nonAngelFlow[timeInd][1] -= angelFlow[timeInd][1]
                
                
		stationFlow = {}
		stationFlow['incentivized'] = angelFlow
		stationFlow['non-incentivized'] = nonAngelFlow
		stationsFlowTable[station] = stationFlow
            all_flow[curr_date.strftime('%Y_%m_%d')] = stationsFlowTable
            pickle.dump(stationsFlowTable, open(curr_file, 'wb'))
            curr_date += dt.timedelta(days=1)

        filename = config.flow_rates_p
        filename = filename.format(start_date.strftime('%Y_%m_%d'),
                                   end_date.strftime('%Y_%m_%d'))
	pickle.dump(all_flow, open(filename, "wb"))

def getStationInactiveMinutes(stationID, periodLength, startTime, endTime):
    cnx = mysql.connector.connect(**config.bikshare_db_config)
    cursor = cnx.cursor()

    inactiveQuery = "SELECT FLOOR((((UNIX_TIMESTAMP(time)) % (24*60*60)) / 60) / {3}) AS timeIndex, count(*) FROM status "
    inactiveQuery += "WHERE station_id = {0} AND "
    inactiveQuery += "( FLOOR(UNIX_TIMESTAMP(time) / (24*60*60) +4) % 7) between 1 and 5 AND "
    inactiveQuery += "UNIX_TIMESTAMP(time) between {1} and {2} AND"
    inactiveQuery += "(bikes_available = 0 OR docks_available = 0) "
    inactiveQuery += "GROUP BY timeIndex;"

    queryForm = (inactiveQuery.format(stationID, startTime, endTime, periodLength))
    cursor.execute(queryForm)
    inactiveRes = cursor.fetchall()
    return inactiveRes

def getStationActiveMinutes(stations, start_date , end_date, periodLength):
    all_active_min = {}
    curr_date = start_date
    while curr_date < end_date:
        print curr_date.strftime('%Y_%m_%d') + "\n\n"
        curr_file = config.stations_active_min[:-6] + ".p"
        curr_file = curr_file.format(curr_date.strftime('%Y_%m_%d'))
        if os.path.isfile(curr_file):
            # if the data was already generated then load it through pickle
            stationActiveMinTable  = pickle.load(open(curr_file, "rb"))
            all_active_min[curr_date.strftime('%Y_%m_%d')] = stationActiveMinTable
            curr_date += dt.timedelta(days=1)
            continue
        
        curr_end = curr_date + dt.timedelta(days=1)
	stationActiveMinTable = {}
	for station in stations:
            print station
	    stationTable = {}
	    for i in range((24*60 / periodLength)):
		#Total number of minutes
		stationTable[i] = periodLength

            startTime = calendar.timegm(curr_date.timetuple())
            endTime = calendar.timegm(curr_end.timetuple())
            
	    inactive = getStationInactiveMinutes(station, periodLength,
                                                 startTime, endTime)
	    for (timeInd, numMins) in inactive:
		stationTable[timeInd] -= numMins

	    stationActiveMinTable[station] = stationTable

        all_active_min[curr_date.strftime('%Y_%m_%d')] = stationActiveMinTable
        curr_date += dt.timedelta(days=1)
        pickle.dump(stationActiveMinTable, open(curr_file, 'wb'))

    filename = config.stations_active_min
    filename += filename.format(start_date.strftime('%Y_%m_%d'),
                                end_date.strftime('%Y_%m_%d'))
    pickle.dump(all_active_min, open(filename, "wb"))
    return stationActiveMinTable

def getStartLevelOnDate(dt, stations):
	cnx = mysql.connector.connect(**config.bikshare_db_config)
	cursor = cnx.cursor()

	#q1 = "SELECT h.station_id, h.bikes_available, h.time"
	#q2 =  " FROM ("
	#q3 = " SELECT station_id, MAX(time) time"
	#q4 = " FROM status"
	#q5 = " WHERE time <= '{0}' AND station_id = {1}"
	#q6 = " GROUP BY station_id"
	#q7= " ) q JOIN status h"
	#q8 = " ON q.station_id = h.station_id"
	#q9 = " AND q.time = h.time;"
	#query = (q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8 + q9)

        query = "SELECT bikes_available FROM status WHERE time <= '{0}'"
        query += "AND station_id = {1} ORDER BY time desc LIMIT 1;"
        
	startLevels = {}
	startTime = dt.strftime('%Y-%m-%d %H:%M:%S')

	for station in stations:
	    queryForm = query.format(startTime, station)
	    cursor.execute(queryForm)
	    try:
		res = cursor.fetchall()[0]
		startLevel = int(res[0])
		startLevels[station] = startLevel
		print station, startLevel
	    except Exception as e:
		startLevels[station] = -1

	return startLevels

def getStartLevels(stations, start, end):
    currDay = start
    startLevels = {}
    while currDay <= end:
	SL = getStartLevelOnDate(currDay, stations)
	startLevels[currDay.strftime('%Y_%m_%d')] = SL
	currDay += dt.timedelta(days=1)

    pickle.dump(startLevels, open(config.station_start_lvls, "wb"))

"""
Gets station fill levels throughout the day for AM period.
"""
def getFillLevelOnDate(today, stations):
	cnx = mysql.connector.connect(**config.bikshare_db_config)
	cursor = cnx.cursor()

        query = "SELECT bikes_available FROM status WHERE time <= '{0}'"
        query += "AND station_id = {1} ORDER BY time desc LIMIT 1;"
        
	fillLevels = {}

	for station in stations:
            print station
            stationLvls = {}
            curr_dt = today
            for i in range(12, 24):
                startTime = curr_dt.strftime('%Y-%m-%d %H:%M:%S')
	        queryForm = query.format(startTime, station)
	        cursor.execute(queryForm)
	        try:
		    res = cursor.fetchall()[0]
		    startLevel = int(res[0])
		    stationLvls[i] = startLevel
	        except Exception as e:
		    stationLvls[i] = -1
                curr_dt += dt.timedelta(minutes= 30)

            fillLevels[station] = stationLvls

	return fillLevels

"""
Gets fill levels for every 30 min time interval on a particular day for AM.
"""
def getFillLevels(stations, start, end):
    currDay = start
    fillLevels = {}
    while currDay <= end:
        print currDay
	SL = getFillLevelOnDate(currDay, stations)
	fillLevels[currDay.strftime('%Y_%m_%d')] = SL
	currDay += dt.timedelta(days=1)
    pickle.dump(fillLevels, open(config.station_fill_lvls, "wb"))

def get_station_docks(stations, startDate, endDate):
    cnx = mysql.connector.connect(**config.bikshare_db_config)
    cursor = cnx.cursor()
    docks = {}
    currDay = startDate
    while currDay <= endDate:
        date_str = currDay.strftime('%Y-%m-%d')
        next_date = (currDay + dt.timedelta(days=1))
        next_date_str = next_date.strftime('%Y-%m-%d')
        query = "SELECT (bikes_available + docks_available) FROM status"
        query += " WHERE station_id = {0} and time between "
        query += "'{1}' and '{2}' LIMIT 1;"
        station_docks = {}
        for station in stations:
            queryForm = query.format(station, date_str, next_date_str)
            cursor.execute(queryForm)
	    try:
		res = cursor.fetchall()[0]
                station_docks[station] = res
	    except Exception as e:
                station_docks[station] = -1
                print date_str, station
        key = currDay.strftime('%Y_%m_%d') 
        docks[key] = station_docks
        currDay = next_date
    pickle.dump(docks, open(config.station_capacity, 'wb'))


# RUN
periodLength = 30
startDate = dt.datetime(2016, 10, 3, 6, 0, 0)
endDate = dt.datetime(2016, 12, 14, 6, 0, 0)
rates = pickle.load(open(config.flow_rates_final, 'rb'))
Istations = rates[rates.keys()[0]].keys()
#Istations = pickle.load(open(config.stations_pickle, "rb"))
#angels = get_riders()

# Get station inflow/outflows
#getStationFlows(Istations, startDate, endDate, angels, periodLength)

##### Get number of active mins for each station
#getStationActiveMinutes(Istations, startDate , endDate, periodLength)

# Get station start levels
#getStartLevels(Istations, startDate, endDate)

# Get station fill levels for AM period.
getFillLevels(Istations, startDate, endDate)

# Get station capacity levels
#get_station_docks(Istations, startDate, endDate)
