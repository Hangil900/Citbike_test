import os
import config

def get_result_difference():
    f2 = open('results_analysis.txt', 'wb')
    f2.write("COST, Dynamic, Dyn_CC, Diff")
    with open(config.results_file, 'rb') as f:
        lines = f.readlines()
        for line in lines:
            lineA = line.split()
            if len(lineA) == 6:
                try:
                    cost = float(lineA[0])
                    dyn = float(lineA[3])
                    dyn_cc = float(lineA[-1])
                    s = "{0}, {1}, {2}, {3}\n".format(cost, dyn,
                                                    dyn_cc, dyn - dyn_cc)
                    f2.write(s)
                except Exception as e:
                    f2.write("\n")

get_result_difference()
    
            

                    
                        
