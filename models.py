import config, pdb, pickle
import datetime as dt
import sys, os
import numpy as np

ADD_BOTH_STATIONS = config.ADD_BOTH_STATIONS

# Returns flow rates for all stations.
def get_flow_rates():
    flow_rates = pickle.load(open(config.flow_rates_final, 'rb'))
    return flow_rates

# Returns the rider probability of being happened because of incentive.
def get_ride_prob(flow_rates, base_rates):
    day_p = {}
    for d in flow_rates:
        station_p = {}
        for s in flow_rates[d]:
            time_p = {}
            for t in flow_rates[d][s]:
                base_in = base_rates[s][t]['in']
                incent_in = flow_rates[d][s][t]['in']['incent']
                
                if incent_in == 0:
                    prob_in = 0
                else:
                    prob_in = ((float(incent_in) - base_in) / float(incent_in))
                    prob_in = min(1, max(prob_in, 0))

                base_out = base_rates[s][t]['out']
                incent_out = flow_rates[d][s][t]['out']['incent']
                
                if incent_out == 0:
                    prob_out = 0
                else:
                    prob_out = ((float(incent_out) - base_out) / float(incent_out))
                    prob_out = min(1, max(prob_out, 0))

                prob = {'in': prob_in, 'out': prob_out}
                time_p[t] = prob
            station_p[s] = time_p
        day_p[d] = station_p
    return day_p

# Sets all probability =1
def get_dummy_ride_prob(flow_rates, base_rates):
    day_p = {}
    for d in flow_rates:
        station_p = {}
        for s in flow_rates[d]:
            time_p = {}
            for t in flow_rates[d][s]:
                prob = {'in': 1.0, 'out': 1.0}
                time_p[t] = prob
            station_p[s] = time_p
        day_p[d] = station_p
    return day_p

# Returns start levels for stations on days at 6am.
def get_station_start_lvls():
    lvls = pickle.load(open(config.station_start_lvls, 'rb'))
    return lvls

# Returns all incentiv trip data frames.
def get_tripDF():
    tripDF = pickle.load(open(config.tripDF_pickle, 'rb'))
    return tripDF

def calc_static_score(dates, stations, tripDF, rates, rideProb, COST_PARAM):
    scores = {}
    total_impact = {}

    for cp in COST_PARAM:
        total_impact[cp] = 0
        scores[cp] = {}
        for d in dates:
            scores[cp][d] = {}
    
    for d in dates:
        startDay = dt.datetime.strptime(d, '%Y_%m_%d')
	endDay = startDay + dt.timedelta(days=1)
	dayTripDF = tripDF[(tripDF.startDatetime>=startDay) &
                                 (tripDF.endDatetime <= endDay)]
        station_scores = {}
        for s in stations:
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

            impact = 0
	    countIncentRides = 0

	    for _, data in startData.iterrows():
                if ADD_BOTH_STATIONS:
		    impact += ((data.startDeltaCC + data.endDeltaCC) *
                                (rideProb[d][s][data.startTimeIndex]['out']))
                else:
                    impact += ((data.startDeltaCC) *
                                (rideProb[d][s][data.startTimeIndex]['out']))
		countIncentRides += 1
	    for _, data in endData.iterrows():
                if ADD_BOTH_STATIONS:
		    impact += (( data.startDeltaCC + data.endDeltaCC ) *
                                (rideProb[d][s][data.endTimeIndex]['in']))
                else:
                    impact += ((data.endDeltaCC) *
                                (rideProb[d][s][data.endTimeIndex]['in']))
		countIncentRides += 1

	    impact *= -1
            for cp in COST_PARAM:
                cp_impact = impact - cp * countIncentRides
                total_impact[cp] += cp_impact
                scores[cp][d][s] = cp_impact

    return total_impact, scores

def calc_dynamic_score(dates, stations, tripDF, rates, rideProb, COST_PARAM):
    scores = {}
    total_impact = {}
    total_count = np.zeros(shape=(len(COST_PARAM),))
    
    for cp in COST_PARAM:
        total_impact[cp] = 0
        scores[cp] = {}
        for d in dates:
            scores[cp][d] = {}
    
    for d in dates:
        startDay = dt.datetime.strptime(d, '%Y_%m_%d')
	endDay = startDay + dt.timedelta(days=1)
	dayTripDF = tripDF[(tripDF.startDatetime>=startDay) &
                                 (tripDF.endDatetime <= endDay)]
        station_scores = {}
        for s in stations:
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

            impact = np.zeros(shape=(len(COST_PARAM),))
	    countIncentRides = np.zeros(shape=(len(COST_PARAM),))
            cps = np.array(COST_PARAM)

	    for _, data in startData.iterrows():
                if ADD_BOTH_STATIONS:
		    curr_impact = ((data.startDeltaCC + data.endDeltaCC) *
                                    (rideProb[d][s][data.startTimeIndex]['out']))
                else:
                    curr_impact = ((data.startDeltaCC) *
                                   (rideProb[d][s][data.startTimeIndex]['out']))

                add_ride = ((curr_impact + cps) < 0).astype('int')
                impact += add_ride * curr_impact
                countIncentRides += add_ride
                    
	    for _, data in endData.iterrows():
                if ADD_BOTH_STATIONS:
		    curr_impact = (( data.startDeltaCC + data.endDeltaCC ) *
                                   (rideProb[d][s][data.endTimeIndex]['in']))
                else:
                    curr_impact = ((data.endDeltaCC) *
                                   (rideProb[d][s][data.endTimeIndex]['in']))

                add_ride = ((curr_impact + cps) < 0).astype('int')
                impact += add_ride * curr_impact
                countIncentRides += add_ride

	    impact *= -1

            for i, cp in enumerate(COST_PARAM):
                cp_impact = impact[i] - cp * countIncentRides[i]
                total_impact[cp] += cp_impact
                scores[cp][d][s] = cp_impact

            total_count += countIncentRides
            
    return total_impact, scores, total_count

def calc_fluid_score(dates, stations, tripDF, rates, rideProb,
                     Iperiods, COST_PARAM):
    scores = {}
    total_rides = {}
    total_impact = {}
    for cp in COST_PARAM:
        total_impact[cp] = 0
        scores[cp] = {}
        for d in dates:
            scores[cp][d] = {}
            
    for d in dates:
        startDay = dt.datetime.strptime(d, '%Y_%m_%d')
	endDay = startDay + dt.timedelta(days=1)
	dayTripDF = tripDF[(tripDF.startDatetime>=startDay) &
                                 (tripDF.endDatetime <= endDay)]
        station_scores = {}
        for s in stations:
            start = Iperiods[d][s][0]
            end = Iperiods[d][s][1]
            
            startData = dayTripDF[(dayTripDF.minuteIndex>=start) &
                                  (dayTripDF.minuteIndex < end) &
                                  (dayTripDF['startID'] == s) &
                                  (dayTripDF['start status'] < 0)]
            
	    endData = dayTripDF[(dayTripDF.minuteIndex>=start) &
                                (dayTripDF.minuteIndex < end) &
                                (dayTripDF['endID'] == s) &
                                (dayTripDF['end status'] > 0)]

            impact = 0
	    countIncentRides = 0
            
            for _, data in startData.iterrows():
                if ADD_BOTH_STATIONS:
		    impact += ((data.startDeltaCC + data.endDeltaCC) *
                                (rideProb[d][s][data.startTimeIndex]['out']))
                else:
                    impact += ((data.startDeltaCC) *
                                (rideProb[d][s][data.startTimeIndex]['out']))
		countIncentRides += 1
	    for _, data in endData.iterrows():
                if ADD_BOTH_STATIONS:
		    impact += (( data.startDeltaCC + data.endDeltaCC ) *
                                (rideProb[d][s][data.endTimeIndex]['in']))
                else:
                    impact += ((data.endDeltaCC) *
                                (rideProb[d][s][data.endTimeIndex]['in']))
		countIncentRides += 1

            impact *= -1
            for cp in COST_PARAM:
                cp_impact = impact - cp * countIncentRides
                total_impact[cp] += cp_impact
                scores[cp][d][s] = cp_impact

    return total_impact, scores

def calc_static_hindsight_score(dates, stations, tripDF, rates, rideProb,
                                all_Iperiods, COST_PARAM):
    scores = {}
    total_impact = {}
    for cp in COST_PARAM:
        total_impact[cp] = 0
        scores[cp] = {}
        for d in dates:
            scores[cp][d] = {}

    for cp in COST_PARAM:
        Iperiods = all_Iperiods[cp]
        for d in dates:
            startDay = dt.datetime.strptime(d, '%Y_%m_%d')
	    endDay = startDay + dt.timedelta(days=1)
	    dayTripDF = tripDF[(tripDF.startDatetime>=startDay) &
                               (tripDF.endDatetime <= endDay)]
            station_scores = {}
            for s in stations:
                start = Iperiods[d][s][0]
                end = Iperiods[d][s][1]
            
                startData = dayTripDF[(dayTripDF.minuteIndex>=start) &
                                      (dayTripDF.minuteIndex < end) &
                                      (dayTripDF['startID'] == s) &
                                      (dayTripDF['start status'] < 0)]
            
	        endData = dayTripDF[(dayTripDF.minuteIndex>=start) &
                                    (dayTripDF.minuteIndex < end) &
                                    (dayTripDF['endID'] == s) &
                                    (dayTripDF['end status'] > 0)]

                impact = 0
	        countIncentRides = 0
            
                for _, data in startData.iterrows():
                    if ADD_BOTH_STATIONS:
		        impact += ((data.startDeltaCC + data.endDeltaCC) *
                                   (rideProb[d][s][data.startTimeIndex]['out']))
                    else:
                        impact += ((data.startDeltaCC) *
                                   (rideProb[d][s][data.startTimeIndex]['out']))
		    countIncentRides += 1
	        for _, data in endData.iterrows():
                    if ADD_BOTH_STATIONS:
		        impact += (( data.startDeltaCC + data.endDeltaCC ) *
                                   (rideProb[d][s][data.endTimeIndex]['in']))
                    else:
                        impact += ((data.endDeltaCC) *
                                   (rideProb[d][s][data.endTimeIndex]['in']))
		    countIncentRides += 1

                impact *= -1
                cp_impact = impact - cp * countIncentRides
                total_impact[cp] += cp_impact
                scores[cp][d][s] = cp_impact
            
    return total_impact, scores

def calc_dynamic_CC_score(dates, stations, tripDF, rates,
                          ALL_IP, rideProb, COST_PARAM):
    scores = {}
    total_impact = {}
    total_count = {}
    
    for cp in COST_PARAM:
        total_count[cp] = 0
        total_impact[cp] = 0
        scores[cp] = {}
        for d in dates:
            scores[cp][d] = {}

    for cp in COST_PARAM:
        IP = ALL_IP[cp]
        for d in dates:
            startDay = dt.datetime.strptime(d, '%Y_%m_%d')
	    endDay = startDay + dt.timedelta(days=1)
	    dayTripDF = tripDF[(tripDF.startDatetime>=startDay) &
                               (tripDF.endDatetime < endDay)]
            station_scores = {}
            for s in stations:
                    starts = dayTripDF[(dayTripDF['startID'] == s) &
                                       (dayTripDF['start status'] < 0)]
            
	            ends = dayTripDF[(dayTripDF['endID'] == s) &
                                     (dayTripDF['end status'] > 0)]
                    impact = 0
                    countIncentRides = 0
                    for ind in IP[d][s]:
                        start = config.interval * ind
                        end = config.interval * (ind + 1)

                    
                        startData = starts[(starts.minuteIndex>=start) &
                                           (starts.minuteIndex < end)]
            
	                endData = ends[(ends.minuteIndex>=start) &
                                       (ends.minuteIndex < end)]

                    
                        for _, data in startData.iterrows():
                            if ADD_BOTH_STATIONS:
		                impact += ((data.startDeltaCC + data.endDeltaCC) *
                                           (rideProb[d][s][data.startTimeIndex]
                                            ['out']))
                            else:
                                impact += ((data.startDeltaCC) *
                                           (rideProb[d][s][data.startTimeIndex]
                                            ['out']))
		            countIncentRides += 1
	                for _, data in endData.iterrows():
                            if ADD_BOTH_STATIONS:
		                impact += (( data.startDeltaCC + data.endDeltaCC )
                                           * (rideProb[d][s][data.endTimeIndex]
                                              ['in']))
                            else:
                                impact += ((data.endDeltaCC) *
                                           (rideProb[d][s][data.endTimeIndex]
                                            ['in']))
		            countIncentRides += 1

                    impact *= -1
                    cp_impact = impact - cp * countIncentRides
                    total_impact[cp] += cp_impact
                    scores[cp][d][s] = cp_impact
                    total_count[cp] += countIncentRides
                    
    return total_impact, scores, total_count

def get_fluid_incentive_periods(rates, dates):
    # Returns the incentive periods for the fluid model.
    start, end = dates[0], dates[-1]
    f = config.fluid_incentive_periods.format(start, end)
    if os.path.isfile(f):
        Iperiods = pickle.load(open(f, 'rb'))
        return Iperiods
    
    lvls = get_station_start_lvls()
    capacity = pickle.load(open(config.station_capacity, 'rb'))
    base_rates = pickle.load(open(config.base_rates_final, 'rb'))
    CC = pickle.load(open(config.all_CC, 'rb'))
    Istations = pickle.load(open(config.curr_Istations, 'rb'))
    
    Iperiods = {}
    for d in dates:
        Speriods = {}
        for s in rates[d]:
            if capacity[d][s] == -1 or s not in Istations:
                Speriods[s] = (config.start_min, config.end_min)
                continue
            else:
                Speriods[s] = __get_fluid_incentive_period(rates[d][s],
                                                           base_rates[s],
                                                           CC,
                                                           capacity[d][s][0],
                                                           int(lvls[d][s]),
                                                           s,
                                                           int(Istations[s]))
        Iperiods[d] = Speriods

    pickle.dump(Iperiods, open(f, 'wb'))
    return Iperiods

"""
Given the stations rates, base_rates, capacity, starting lvl, and incentive
period indexes, Cost Curve and station ID calculates the following:

Number of unhappy customers when incentivizing stated periods.
"""
def __get_fluid_interval_score(rates, base_rates, capacity,
                               lvl, i, j, CC, sID, status):
    unhappy = 0
    for k in xrange(config.start_min, config.end_min, config.interval):
        timeInd = k / config.interval
        flow = rates[timeInd]['in']['normal'] - rates[timeInd]['out']['normal']

        if k >=i and k <j:
            # This is an incentive period.
            if status == -1:
                flow += rates[timeInd]['in']['incent']
                flow -= max(rates[timeInd]['out']['incent'], 1. / config.interval)
            else:
                flow += max(rates[timeInd]['in']['incent'], 1. / config.interval)
                flow -= rates[timeInd]['out']['incent']

        else:
            # We make the assumption that incentivization always results
            # in better flow.
            if status == -1:
                flow += rates[timeInd]['in']['incent']
                flow -= min(rates[timeInd]['out']['incent'],
                            base_rates[timeInd]['out'])
            else:
                flow += min(rates[timeInd]['in']['incent'],
                            base_rates[timeInd]['in'])
                flow -= rates[timeInd]['out']['incent']

        # Times by number of minutes
        flow *= config.interval

        # If flow is over capacity, add overflow to unhappy and cap lvl at cap.
        if flow + lvl > capacity:
            unhappy += flow + lvl - capacity
            lvl = capacity
        elif flow + lvl < 0:
            unhappy += abs(flow + lvl)
            lvl = 0
        else:
            lvl = flow + lvl

    # Hack for stations we don't care about.
    # Add the CC at the very end of the day.
    if sID in CC[timeInd+1]:
        lvl = min(max(int(lvl), 0), len(CC[timeInd+1][sID]) - 1)
        unhappy += CC[timeInd+1][sID][lvl]
    else:
        unhappy += 0
    return unhappy
        
"""
Returns optimal incentive period for a particular station on a day.
"""
def __get_fluid_incentive_period(rates, base_rate, CC, capacity, lvl, sID, status):
    optimal = sys.maxint
    opt_int = None
    for i in xrange(config.start_min, config.end_min, config.interval):
        for j in xrange(i+ config.interval, config.end_min + 1, config.interval):

            unhappy = __get_fluid_interval_score(rates, base_rate,
                                                 capacity, lvl, i,
                                                 j, CC, sID, status)

            if unhappy < optimal:
                opt_int = (i, j)
                optimal = unhappy

    return opt_int
    
"""
Returns the incentive periods for a dynamic CC based incentive program,
which at every 30 min interval, looks at current fill lvl and if an incentivized
ride helps, it incentivizes the entire period.
"""
def get_dynamic_CC_IP(COSTS, rideProb):

    if os.path.isfile(config.dynamic_CC_IP):
        IP = pickle.load(open(config.dynamic_CC_IP, 'rb'))
        return IP

    CC = pickle.load(open(config.all_CC, 'rb'))
    rates = get_flow_rates()

    # Get station fill levels
    station_fill_lvls = pickle.load(open(config.station_fill_lvls, 'rb'))
    dates = rates.keys()
    dates.sort()
    stations = pickle.load(open(config.common_stations, 'rb'))
    Istations = pickle.load(open(config.curr_Istations, 'rb'))
    
    IP = {}
    for cost in COSTS:
        cost_IP = {}
        for d in dates:
            day_IP = {}
            for s in stations:
                fill_lvls = station_fill_lvls[d][s]
                station_IP = []
                for i in xrange(config.start_min, config.end_min, config.interval):
                    timeInd = i / config.interval
                    lvl = min(max(fill_lvls[timeInd], 0), len(CC[timeInd][s]) -1)
                    incent = Istations[s]

                    if incent == -1:
                        # Start incentivization so next lvl is lvl -1.
                        next_lvl = min(max(lvl -1, 0), len(CC[timeInd][s]) - 1)
                        deltaCC = CC[timeInd][s][next_lvl] - CC[timeInd][s][lvl]

                        # Multiply by ride probability.
                        deltaCC *= rideProb[d][s][timeInd]['out']
                    else:
                        next_lvl = min(max(lvl + 1, 0), len(CC[timeInd][s]) - 1)
                        deltaCC = CC[timeInd][s][next_lvl] - CC[timeInd][s][lvl]

                        # Multiply by ride probability.
                        deltaCC *= rideProb[d][s][timeInd]['in']

                    if -1 * deltaCC >= cost :
                        station_IP.append(timeInd)
                day_IP[s] = station_IP
            cost_IP[d] = day_IP
        IP[cost] = cost_IP
        

    pickle.dump(IP, open(config.dynamic_CC_IP, 'wb'))
    return IP
        
