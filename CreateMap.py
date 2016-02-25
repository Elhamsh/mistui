__author__ = 'eshaaban'

import pandas as pd
import pygmaps
import numpy as np

Colors = ["#023FA5","#7D87B9","#BEC1D4","#D6BCC0","#BB7784","#FFFFFF", "#4A6FE3","#8595E1","#B5BBE3","#E6AFB9","#E07B91","#D33F6A",
          "#11C638","#8DD593","#C6DEC7","#EAD3C6","#F0B98D","#EF9708", "#0FCFC0","#9CDED6","#D5EAE7","#F3E1EB","#F6C4E1","#F79CD4"]
Path='Jan24_beta.5'
BetaPath = 'Jan18'
beta = .5
FC_all = pd.read_csv('../Oct_7/PLS_DRT (version 1) (version 1).csv')
Reported_loc = pd.read_csv('../Oct_7/Nov_5/Beta_'+BetaPath+'.csv')
# FC =['49.1989187 -122.0500376']
# POINTS1 = ['49.0679195977 -122.649937089', '51.713831806 -122.180015028', '48.9027568033 -122.206182693', '51.2890467688 -122.873290334',
#           '48.9742410139 -122.86185821', '49.1819937072 -122.187899747', '49.0345652779 -122.547851734', '49.5170788638 -122.92769443',
#           '48.9956831066 -122.386658877', '49.0182829344 -122.655951742', '49.0715849019 -122.575838353', '49.0741973361 -122.809812742',
#           '49.031784662 -122.689133159', '49.0657136144 -122.545517637', '49.040065328 -122.568621883', '49.0691736404 -122.624583451',
#           '49.0419746524 -122.180995544', '49.0672620692 -122.63200302', '54.2107106044 -113.913589178', '49.1542699665 -122.999457129']
# POINTS2 = ['49.374718652 -123.094632466','49.5217518207 -122.378202381', '48.9702683741 -122.607053807', '49.2363987636 -123.033041992']
# Prob_POINTS2 = ['0.0625', '0.0625', '0.1875', '0.0625']


for c in [21.0]:#[258.0, 276.0, 21.0, 279.0, 280.0, 283.0, 287.0, 112.0, 166.0, 42.0, 53.0, 68.0, 211.0, 85.0, 218.0, 219.0, 231.0, 110.0, 240.0, 241.0, 248.0, 251.0, 253.0, 274.0]:
    FC = FC_all['drt'][np.where(np.array(FC_all['Case Num'])==c)[0][0]]
    Case_Beta = pd.read_csv('/trainedBeta_' + str(int(c)) + '.0.csv')
    # All_points = pd.read_csv('../Experiment Results/'+Path+'/grid' + str(c) + '_' + str(beta) + 'baseline__.csv')
    fx, fy = FC.split(" ")[0], FC.split(" ")[1]
    mymap = pygmaps.maps(float(fx), float(fy), 7)




    col=0
    Regions = pd.read_csv( '/_ProbableRegions' + str(int(c)) + '.csv')
    labels = list(set(Regions['Label']))
    for l in labels:
        xx, yy = list(Regions[Regions['Label']==l]['GPS'])[0].strip('()').split(', ')
        P = list(Regions[Regions['Label']==l]['Prob of point'])[0]
        print(l)
        k = min(Regions[Regions['Label']==l]['k'])
        print(P, k)
        mymap.addpointRegion(float(xx), float(yy), color="icon"+str(int(k+7)), title=str(P))

    for ind in Case_Beta.index:
        if ind/2==ind/2.:
            reporter_ID = Case_Beta.loc[ind]['Reporter']
            try:
                reporter_loc = Reported_loc[np.logical_and(Reported_loc['Case Num'] == c, Reported_loc['Reporter Num'] == reporter_ID)]['Rep'].values[0]
            except:
                reporter_loc = Reported_loc[np.logical_and(Reported_loc['Case Num'] == c, Reported_loc['Reporter Num'] == str(int(reporter_ID)))]['Rep'].values[0]
            x, y = reporter_loc.split()

            B = list(Case_Beta[Case_Beta['Reporter']==reporter_ID]['Beta'])
            print(B)
            mymap.addradpoint(float(x), float(y), B[0]*1609.34, color=Colors[col])
            mymap.addradpoint(float(x), float(y), B[1]*1609.34, color=Colors[col])
            if B[0]==2.5:
                mymap.addpoint(float(x), float(y), color="blue", title="R: " + str(reporter_ID))
            else:
                mymap.addpoint(float(x), float(y), color="green", title="R: " + str(reporter_ID))
            col += 1


    #
    # ind = 0
    # for i in POINTS1:
    #     mymap.addpoint(float(i.split(" ")[0]), float(i.split(" ")[1]), color="blue", title="P= " + "0")
    #     ind = 0
    # for i in POINTS2:
    #     mymap.addpoint(float(i.split(" ")[0]), float(i.split(" ")[1]), color="pink", title="P= " + str(Prob_POINTS2[ind]))
    #     ind += 1
    # for ind in range(len(Case_Beta)):
    #     x, y = Case_Beta["Rep"].values[ind].split(" ")[0], Case_Beta["Rep"].values[ind].split(" ")[1]
    #     if str(x)!="None" and str(y.strip())!="None":
    #         mymap.addpoint(float(x), float(y), color="green", title="R: " + str(Case_Beta["Reporter Num"][ind]))
    #         mymap.addradpoint(float(x), float(y), Case_Beta["Beta"][ind]*1609.34, color=Colors[23] if Case_Beta["Beta"][ind] == "LKP" or Case_Beta["Beta"][ind] == 'kaaren smoot' else Colors[int(Case_Beta["Beta"][ind])%24])
    #         print Case_Beta["Beta"][ind]
    #     ind +=1
    # mymap.addpoint(float(xx), float(yy), color="red", title="C: " + '0.0625')
    #
    # for xxx in list(All_points['GPS']):
    #     yyy = xxx.strip('()').split(',')
    #     mymap.addpoint(float(yyy[0]), float(yyy[1]), color="pink", title="")
    mymap.addpoint(float(fx), float(fy), color="red", title="FC")
    mymap.draw('/map_'+str(c)+'.html')