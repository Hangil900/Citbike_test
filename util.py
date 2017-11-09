import pickle
import config, os, pdb

def get_stations():
    # Gets the incentivized stations
    if os.path.isfile(config.stations_pickle):
        Istations = pickle.load(open(config.stations_pickle, "rb"))
    else:
        tripsDF = pickle.load(open(config.tripDF_pickle, 'rb'))

        AM = {}
        amTripDF = tripsDF[(tripsDF['startTimeIndex'] < 24) &
                           (tripsDF['startTimeIndex'] >= 12)]
        
        for i, status in enumerate(amTripDF['start status']):
            if status  < 0:
                station = amTripDF['startID'].tolist()[i]
                if station in AM and AM[station] != -1:
                    AM[station] = 0
                else:
                    AM[station] = -1

        for i, status in enumerate(amTripDF['end status']):
            if status > 0:
                station = amTripDF['endID'].tolist()[i]
                if station in AM and AM[station] != 1:
                    AM[station] = 0
                else:
                    AM[station] = 1

        PM = {}
        pmTripDF = tripsDF[(tripsDF['startTimeIndex'] >= 24) &
                           (tripsDF['startTimeIndex'] < 36)]
        
        for i, status in enumerate(pmTripDF['start status']):
            if status  < 0:
                station = pmTripDF['startID'].tolist()[i]
                if station in PM and PM[station] != -1:
                    PM[station] = 0
                else:
                    PM[station] = -1

        for i, status in enumerate(pmTripDF['end status']):
            if status > 0:
                station = pmTripDF['endID'].tolist()[i]
                if station in PM and PM[station] != 1:
                    PM[station] = 0
                else:
                    PM[station] = 1

        pickle.dump(AM, open(config.AM_stations_p, 'wb'))
        pickle.dump(PM, open(config.PM_stations_p, 'wb'))

        Istations = list(set(AM.keys() + PM.keys()))
        pickle.dump(Istations, open(config.stations_pickle, 'wb'))
    return Istations
