import datetime as dt

bikshare_db_config = {
  'user':'tracker_ro_user', 
  'password':'6W.v6/,HZR9mBGx',
  'host': 'tracker-ro.csqwfkioldwf.us-east-1.rds.amazonaws.com',
  'database':'bikeshare_nyc'
}

warehouse_db_config = {
  'user':'dm_nyc_mtv_bi', 
  'password':'t8IAGm5mREcdYiAnEb0b',
  'host': 'datamart.nyc.8d.com',
  'database':'nyc_datawarehouse_bss4'
}

# warehouse_db_config = {
#   'user':'datamart_mtvhq', 
#   'password':'31xHeaBuOvYF9JsPrBxO',
#   'host': 'datamart.nyc.8d.com',
#   'database':'nyc_datawarehouse_bss4'
# }

home = "/Users/hangil/Desktop/Citibike_new"

riders_file = "/Users/hangil/Desktop/Citibike_new/data_files/members_201610.csv"
riders_pickle = riders_file[:-3] + "p"

stations_file = "/Users/hangil/Desktop/Citibike_new/data_files/stations_201610.csv"
stations_pickle = stations_file[:-3] + "p"

AM_stations_p = "/Users/hangil/Desktop/Citibike_new/data_files/AM_stations.p"
PM_stations_p = "/Users/hangil/Desktop/Citibike_new/data_files/PM_stations.p"

# Curr stations to look at.
# -1 -> start station incent
# 1 -> end station incent
curr_Istations = AM_stations_p

tripDF_pickle = "/Users/hangil/Desktop/Citibike_new/data_files/tripsDF_full.p"

# We define positive flow to be outgoing, negative to be incoming.
flow_rates_final = home + '/data_files/flow_rates_final.p'
base_rates_final = home + '/data_files/base_rates_final.p'
flow_rates_p = home + "/data_files/flow_rates{0}_{1}.p"
stations_active_min = home + "/data_files/stations_active_{0}_{1}.p"

station_start_lvls = home + "/data_files/start_levels.p"
station_capacity = home + "/data_files/station_capacity.p"
station_fill_lvls = home + "/data_files/station_fill_lvls.p"

all_CC = home + "/costCurvePickle.p"
fluid_incentive_periods = home + "/data_files/fluid_incent_periods.p"
optimal_incentive_periods = home + '/data_files/optimal_incent_cp={0}.p'
static_incentive_periods = home + "/data_files/static_incent.p"
results_file = home + "/results.log"



# Whether to account for both stations deltaCC when calculating model scores.
ADD_BOTH_STATIONS = False

# Start and end minute index. (6am- 12pm)
start_min = 360
end_min= 720
interval = 30

# Test-Period
test_start = dt.date(2016, 10, 3)
test_end = dt.date(2016, 12, 14)

# Baseline Period
base_start = dt.date(2016, 4, 1)
base_end = dt.date(2016, 5, 13)
