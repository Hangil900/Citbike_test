import config
import numpy as np
import datetime as dt
import os, pickle
"""
Returns static optimal IP when looking back in hindsight.
"""
def get_static_optimal_periods(dates, stations, tripDF, COSTS):
    f = config.static_incentive_periods
    if os.path.isfile(f):
        Iperiod = pickle.load(open(f, 'rb'))
        return Iperiod
    
    STATIC_LOOKBACK = 20
    Iperiod = {}
    for cp in COSTS:
        Iperiod[cp] = {}
        for d in dates:
            Iperiod[cp][d] = {}
        
    for d in dates:
        lookback_dates = get_lookback_dates(d, STATIC_LOOKBACK)
        for s in stations:
            print d, s
            opt_p = __get_static_optimal_period(lookback_dates, s, tripDF, COSTS)
            for cp in COSTS:
                Iperiod[cp][d][s] = opt_p[cp]

    pickle.dump(Iperiod, open(f, 'wb'))
    return Iperiod

"""
Given the dates to look at, and the station, returns the optimal IP
for a static model in hindsight of those dates.

Returns for each cost param, the optimal IP.
"""
def __get_static_optimal_period(dates, station, tripDF, COSTS):
    opt_p = {}
    opt_v = {}
    for i in xrange(config.start_min, config.end_min + 1, config.interval):
        for j in xrange(i + config.interval, config.end_min + 1, config.interval):
            trips = tripDF[(tripDF['startDatetime'] >= dates[-1]) &
                           (tripDF['endDatetime'] <= dates[0]) &
                           (tripDF['minuteIndex'] >= i) &
                           (tripDF['minuteIndex'] < j) ]

            startData = trips[(trips['startID'] == station) &
                              (trips['start status'] < 0)]
            endData = trips[(trips['endID'] == station) &
                            (trips['end status'] > 0)]

            
            impact = 0
	    countIncentRides = 0
            
            for _, data in startData.iterrows():
                if config.ADD_BOTH_STATIONS:
		    impact += (data.startDeltaCC + data.endDeltaCC) 

                else:
                    impact += (data.startDeltaCC)
		countIncentRides += 1
	    for _, data in endData.iterrows():
                if config.ADD_BOTH_STATIONS:
		    impact += ( data.startDeltaCC + data.endDeltaCC )
                else:
                    impact += (data.endDeltaCC)
		countIncentRides += 1

            impact *= -1
            for cp in COSTS:
                cp_impact = impact - cp * countIncentRides
                if cp in opt_v:
                    if opt_v[cp] < cp_impact:
                        opt_v[cp] = cp_impact
                        opt_p[cp] = [i,j]
                else:
                    opt_v[cp] = cp_impact
                    opt_p[cp] = [i,j]
    return opt_p
            
    
"""
Returns list of datetime dates of lookback dates excluding itself.
"""
def get_lookback_dates(date, lookback):
    if isinstance(date, str):
        date = dt.datetime.strptime(date, '%Y_%m_%d')
    dates = []
    while lookback >0 :
        while date.weekday() < 5:
            date = date - dt.timedelta(days = 1)
        dates.append(date)
        lookback -= 1
        date = date - dt.timedelta(days= 1)
    return dates
    

"""
Returns actual optimal period when looking at day's data.
"""
def get_optimal_periods(rates, dates, tripDF,rideProb, COST_PARAM):
    # Returns the optimal incentive periods for the static model.
    start, end = dates[0], dates[-1]
    f = config.optimal_incentive_periods.format(COST_PARAM)
    if os.path.isfile(f):
        Iperiods = pickle.load(open(f, 'rb'))
        return Iperiods

    Iperiods = {}
    for d in dates:
        today = dt.datetime.strptime(d, '%Y_%m_%d')
        tmrw = dt.timedelta(days = 1) + today

        dayTripDF = tripDF[(tripDF.startDatetime>=today) &
                           (tripDF.endDatetime <= tmrw)]
        Speriods = {}
        for s in rates[d]:
            opt_int = __get_optimal_period(dayTripDF, s, rideProb[d] ,COST_PARAM)
            Speriods[s] = opt_int
        Iperiods[d] = Speriods

    pickle.dump(Iperiods, open(f, 'wb'))
    return Iperiods

"""
Given the day's trip DF, and station s, returns optimal IP.
"""
def __get_optimal_period(dayTripDF, s, rideProb, COST_PARAM):
    start = config.start_min
    end = config.end_min
    startData = dayTripDF[(dayTripDF.minuteIndex>=start) &
                          (dayTripDF.minuteIndex < end) &
                          (dayTripDF['startID'] == s) &
                          (dayTripDF['start status'] < 0)]

    endData = dayTripDF[(dayTripDF.minuteIndex>=start) &
                        (dayTripDF.minuteIndex < end) &
                        (dayTripDF['endID'] == s) &
                        (dayTripDF['end status'] > 0)]

    num_int = (end - start) / config.interval

    scores = [0]* num_int

    for _, data in startData.iterrows():
        if config.ADD_BOTH_STATIONS:
	    impact = ((data.startDeltaCC + data.endDeltaCC) *
                       (rideProb[s][data.startTimeIndex]['out']))
        else:
            impact = ((data.startDeltaCC) *
                       (rideProb[s][data.startTimeIndex]['out']))
	impact *= -1
        impact -= COST_PARAM
        scores[data.startTimeIndex - 12] += impact
        
    for _, data in endData.iterrows():
        if config.ADD_BOTH_STATIONS:
	    impact = (( data.startDeltaCC + data.endDeltaCC ) *
                       (rideProb[s][data.endTimeIndex]['in']))
        else:
            impact = ((data.endDeltaCC) *
                       (rideProb[s][data.endTimeIndex]['in']))
        impact *= -1
        impact -= COST_PARAM
        scores[data.endTimeIndex - 12] += impact


    opt_int = (0,0)
    opt_val = 0
    curr = 0
    curr_start = 0

    for i in range(num_int):
        curr += scores[i]
        if curr > opt_val:
            opt_int = (curr_start, i+1)
            opt_val = curr
        if curr < 0:
            curr = 0
            curr_start = i+1

    return (opt_int[0] * config.interval + start ,
            opt_int[1] * config.interval + start)
    
