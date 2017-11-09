
import models, config, pickle
import numpy as np
import time
import pdb
import static_model

def compare_models(stations, rates):
    COSTS = [0.0, 0.01, 0.1, 0.2, 0.3, 0.4]
    
    start = time.time()
    tripDF = models.get_tripDF()

    base_rates = pickle.load(open(config.base_rates_final, 'rb'))
    
    rideProb = models.get_ride_prob(rates, base_rates)
    #rideProb = models.get_dummy_ride_prob(rates, base_rates)
    
    dates = rates.keys()
    dates.sort()

    stations = remove_inconsistent_stations(rates, stations)
    fluid_Iperiods = models.get_fluid_incentive_periods(rates, dates)
    sh_Iperiods = static_model.get_static_optimal_periods(dates, stations,
                                                          tripDF, COSTS)

    #sh_Iperiods = sh_Iperiods[0.01]
    dyn_CC_IP = models.get_dynamic_CC_IP(COSTS, rideProb)

    end = time.time()
    print "Initialization: {0}".format(end-start)

    f = open(config.results_file, 'a')
    f.write("\n-------------------------------------------------------")
    cp = 'COST'.ljust(10)
    s = 'Static'.ljust(10)
    fl = 'Fluid'.ljust(10)
    d = 'Dynamic'.ljust(10)
    sh = 'Optimized'.ljust(10)
    dCC = "DynamicCC".ljust(10)
    f.write('\n\n{0} {1} {2} {3} {4} {5}\n\n'.format(cp, s, fl, d, sh, dCC))

    
    start = time.time()
    dCC_total, dCC_scores, dCC_count = models.calc_dynamic_CC_score(dates,
                                                                    stations,
                                                                    tripDF, rates,
                                                                    dyn_CC_IP,
                                                                    rideProb,
                                                                    COSTS)
    end = time.time()
    print "dynamic_CC: {0}".format(end-start)
    
    start = time.time()
    stotal, static_scores = models.calc_static_score(dates, stations,
                                                     tripDF,
                                                     rates, rideProb, COSTS)

    end = time.time()
    print "Static: {0}".format(end-start)

    start = time.time()
    dtotal, dynamic_scores, dyn_count = models.calc_dynamic_score(dates,
                                                                  stations,
                                                                  tripDF,
                                                                  rates,
                                                                  rideProb, COSTS)
    end = time.time()
    print "Dynamic: {0}".format(end-start)
    
    start = time.time()
    ftotal, fluid_scores = models.calc_fluid_score(dates, stations, tripDF,
                                                   rates, rideProb,
                                                   fluid_Iperiods, COSTS)
    end = time.time()
    print "Fluid: {0}".format(end-start)

    shtotal, sh_scores = models.calc_static_hindsight_score(dates,
                                                            stations,
                                                            tripDF,
                                                            rates, rideProb,
                                                            sh_Iperiods, COSTS)

    for cp in COSTS:
        dyn = dtotal[cp]
        
        static = stotal[cp] / dyn
        fluid = ftotal[cp] / dyn
        sh = shtotal[cp] / dyn
        dCC = dCC_total[cp] / dyn
        dyn = dyn / dyn

       
        
        static = str(round(static, 3)).ljust(10)
        dyn = str(round(dyn, 3)).ljust(10)
        fluid = str(round(fluid, 3)).ljust(10)
        sh = str(round(sh, 3)).ljust(10)
        dCC = str(round(dCC, 3)).ljust(10)
        cp = str(cp).ljust(10)
        f.write('{0} {1} {2} {3} {4} {5}\n'.format(cp, static,
                                                   fluid, dyn, sh, dCC))

        
    f.write('\n\n')

    for cp in COSTS:

        static = stotal[cp] 
        fluid = ftotal[cp] 
        sh = shtotal[cp] 
        dCC = dCC_total[cp] 
        dyn = dtotal[cp]

        static = str(round(static, 3)).ljust(10)
        dyn = str(round(dyn, 3)).ljust(10)
        fluid = str(round(fluid, 3)).ljust(10)
        sh = str(round(sh, 3)).ljust(10)
        dCC = str(round(dCC, 3)).ljust(10)
        cp = str(cp).ljust(10)
        f.write('{0} {1} {2} {3} {4} {5}\n'.format(cp, static,
                                                   fluid, dyn, sh, dCC))

    f.write('\n\n')
    print dyn_count
    print dCC_count

    # Write per station score

    scores = [static_scores, fluid_scores, dynamic_scores, sh_scores, dCC_scores]
    new_scores = []
    for score in scores:
        new_score = {}
        for cp in COSTS:
            cp_score = {}
            for s in stations:
                station_score = 0
                for d in dates:
                    station_score += score[cp][d][s]
                cp_score[s] = station_score
            new_score[cp] = cp_score
        new_scores.append(new_score)

    f2 = open(config.per_station_results_file, 'a')
  
    for cp in COSTS:
        f2.write("\n-------------------------------------------------------")
        cps = 'COST'.ljust(10)
        s = 'Static'.ljust(10)
        fl = 'Fluid'.ljust(10)
        d = 'Dynamic'.ljust(10)
        sh = 'Optimized'.ljust(10)
        dCC = "DynamicCC".ljust(10)
        f2.write('\n\n{0} {1} {2} {3} {4} {5}\n\n'.format(cps, s, fl, d, sh, dCC))
        for s in stations:
            vals = []
            for score in new_scores:
                vals.append(score[cp][s])
            output = "{0}: {1}, {2}, {3}, {4}, {5}\n"
            output = output.format(s, int(vals[0]), int(vals[1]), int(vals[2]),
                                   int(vals[3]), int(vals[4]))
            f2.write(output)
            
    
    
"""
Removes all stations which we don't have info on,
or stations where the rates changed too drastically from test and train period.
"""    
def remove_inconsistent_stations(rates, stations):
    base_rates = pickle.load(open(config.base_rates_final, 'rb'))
    avg_rates = {}
    base_total = {}
    for d in rates.keys()[0:1]:
        for s in rates[d]:
            avg_rates[s] = 0.0
            base_total[s] = 0.0

    for d in rates:
        for s in rates[d]:
            for t in rates[d][s]:
                avg_rates[s] += rates[d][s][t]['in']['incent']
                avg_rates[s] += rates[d][s][t]['out']['incent']
                base_total[s] += base_rates[s][t]['in']
                base_total[s] += base_rates[s][t]['out']

    num_days = len(rates)
    bad_stations = []
    for s in stations:
        if s not in avg_rates:
            bad_stations.append(s)
        """
        else:
            rTotal = avg_rates[s]
            bTotal = base_total[s] * num_days
            if bTotal == 0:
                bad_stations.append(s)
            else:
                ratio = abs(rTotal - bTotal) / float(bTotal)
                if ratio > 2.0:
                    bad_stations.append(s)
        """
    
        
    goodStations = []
    for s in stations:
        if s not in bad_stations:
            goodStations.append(s)

    print "Removed {0} stations out of {1}\n".format(len(bad_stations),
                                                   len(stations))
    return goodStations

def run():

    rates = models.get_flow_rates()
    dates = rates.keys()
    dates.sort()

    EV = [438, 326, 237, 236, 439, 428, 432,
          301, 393, 433, 445, 394, 317, 403, 150, 302]

    FiDi = [279, 306, 376, 195, 264, 360, 304, 260,
            534, 259, 427, 315, 337, 415, 319, 387]

    rate_stations = rates[dates[0]].keys()
    common_stations = pickle.load(open(config.common_stations, 'rb'))

    all_stations = list(common_stations) 
    EV.sort()
    FiDi.sort()
    all_stations.sort()
    
    #station_lst = [all_stations, EV, FiDi]
    station_lst = [all_stations]

    for sts in station_lst:
        compare_models(sts, rates)

run()
