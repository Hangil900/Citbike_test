import pickle
import pdb
import config
import numpy as np
import datetime as dt

# Parses the flow count data to actually get flow rates.
# Returns the rates by looking at past 20 days to predict rates for today.
def get_rates():
    # Get the flows and active minutes.

    remove_weekends()
    
    flows_file = config.flow_rates_p.format(config.test_start.strftime("%Y_%m_%d"),
                                            config.test_end.strftime("%Y_%m_%d"))
    flows = pickle.load(open(flows_file, 'rb'))

    active_file = config.stations_active_min.format(
        config.test_start.strftime("%Y_%m_%d"),
        config.test_end.strftime("%Y_%m_%d"))
    active = pickle.load(open(active_file, 'rb'))

    """
    Builds flow rates, such that it goes: date, station, time, in/out, i_out, i_in,
    n_out, n_in
    """
    rates = [] # Flow counts
    mins = [] # Flow mins
    dates = [] # Dates in order processed
    stations = [] # Stations in order processed
    times = [] # Times in order processed

    dates = flows.keys()
    dates.sort()
    stations = flows[dates[0]].keys()
    stations.sort()
    times = flows[dates[0]][stations[0]]['incentivized'].keys()
    times.sort()
    
    for date in dates:
        day_flow = flows[date]
        day_active = active[date]
        date_rates = []
        date_mins = []

        for station in stations:
            s_flow = day_flow[station]
            s_active = day_active[station]
            station_rates = []
            station_mins = []

            for time in times:
                i_out = s_flow['incentivized'][time][0]
                i_in = s_flow['incentivized'][time][1]
                n_out = s_flow['non-incentivized'][time][0]
                n_in = s_flow['non-incentivized'][time][1]
                minutes = s_active[time]
                station_rates.append([i_out, i_in, n_out, n_in])
                station_mins.append([minutes])
            
            date_mins.append(station_mins)    
            date_rates.append(station_rates)
            
        rates.append(date_rates)
        mins.append(date_mins)

    rates = np.array(rates).astype('float')
    mins = np.array(mins).astype('float')

    # Get rates for a particular day by looking back 20 days.
    CSR = np.cumsum(rates, axis=0)
    CSR_lag = np.roll(CSR, 20, axis=0)
    CSR_20 = CSR - CSR_lag

    CSM = np.cumsum(mins, axis=0)
    CSM_lag = np.roll(CSM, 20 ,axis=0)
    CSM_20 = CSM - CSM_lag
    
    rates_20 = np.roll(CSR_20 / CSM_20, 1, axis=0)

    all_rates = {}
    for i, d in enumerate(dates):
        if i < 20:
            # These are the first 20 entries which we don't have data for.
            continue
        d_rates = {}
        for j,s in enumerate(stations):
            s_rates = {}
            for k,t in enumerate(times):
                i_out = rates_20[i][j][k][0]
                i_in = rates_20[i][j][k][1]
                n_out = rates_20[i][j][k][2]
                n_in = rates_20[i][j][k][3]

                inflow = {'incent': i_in, 'normal': n_in}
                outflow = {'incent': i_out, 'normal': n_out}
                s_rates[t] = {'in': inflow, 'out':outflow}

            d_rates[s] = s_rates
        all_rates[d] = d_rates
    
    pickle.dump(all_rates, open(config.flow_rates_final, 'wb'))
    __get_rates(all_rates)

"""
Helper function to look at baseline rates, and calculate what 
unincentivized angel flows are.
"""
def __get_rates(all_rates):
    f = config.flow_rates_p
    prev_file = f.format(config.base_start.strftime('%Y_%m_%d'),
                         config.base_end.strftime('%Y_%m_%d'))
    base_flows = pickle.load(open(prev_file, 'rb'))
    
    test_file = f.format(config.test_start.strftime('%Y_%m_%d'),
                         config.test_end.strftime("%Y_%m_%d"))
    test_flows = pickle.load(open(test_file, 'rb'))

    base_total = 0
    base_avg = {}
    for d in base_flows:
        for s in base_flows[d]:
            if s not in base_avg:
                base_avg[s] = {}
            for t in base_flows[d][s]['incentivized']:
                if t not in base_avg[s]:
                    base_avg[s][t] = {'in': 0.0, 'out':0.0}
                outflow = base_flows[d][s]['incentivized'][t][0]
                inflow =  base_flows[d][s]['incentivized'][t][1]
                
                base_avg[s][t]['in'] += inflow
                base_avg[s][t]['out'] += outflow
                
                base_total += inflow + outflow

    base_total /= float(len(base_flows))

    test_total = 0
    for d in test_flows:
        for s in test_flows[d]:
            for t in test_flows[d][s]['incentivized']:
                test_total += test_flows[d][s]['incentivized'][t][0]
                test_total += test_flows[d][s]['incentivized'][t][1]

    test_total /= float(len(test_flows))

    ratio = test_total/ base_total

    # Calculate the avg rate by dividing by num of minutes and days.
    # Multiply by ratio to keep it standardized.
    for s in base_avg:
        for t in base_avg[s]:
            base_avg[s][t]['in'] /= float(config.interval)
            base_avg[s][t]['in'] *= ratio
            base_avg[s][t]['in'] /= float(len(base_flows))
            
            base_avg[s][t]['out'] /= float(config.interval)
            base_avg[s][t]['out'] *= ratio
            base_avg[s][t]['out'] /= float(len(base_flows))
            
    pickle.dump(base_avg, open(config.base_rates_final, 'wb'))
    

def remove_weekends():
    f = config.flow_rates_p
    base_file = f.format(config.base_start.strftime('%Y_%m_%d'),
                         config.base_end.strftime('%Y_%m_%d'))
    base_flows = pickle.load(open(base_file, 'rb'))
    
    test_file = f.format(config.test_start.strftime('%Y_%m_%d'),
                         config.test_end.strftime("%Y_%m_%d"))
    test_flows = pickle.load(open(test_file, 'rb'))
    
    bdates = base_flows.keys()
    tdates = test_flows.keys()

    for d in bdates:
        date = dt.datetime.strptime(d, '%Y_%m_%d')
        if date.weekday() in [5, 6]:
            base_flows.pop(d)

    for d in tdates:
        date = dt.datetime.strptime(d, '%Y_%m_%d')
        if date.weekday() in [5, 6]:
            test_flows.pop(d)

    pickle.dump(base_flows, open(base_file, 'wb'))
    pickle.dump(test_flows, open(test_file, 'wb'))

    
    
get_rates()
