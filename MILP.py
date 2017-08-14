import pandas as pd
import numpy as np
import General as gen
from coinor.pulp import *
import math

class MILP():
    def __init__(self, path, gridDim, theta):
        self.GridSize = 100
        self.path=path
        try:
            self.Reporter_Case = pd.read_csv(self.path+'Model/Beta.csv')
        except:
            self.Reporter_Case =''
        self.Date = ''
        self.theta=theta
        self.Beta = pd.DataFrame(columns=['Case Num', 'DRT', 'Dist(DRT, P)', 'Rep', 'Reported loc', 'Reporter Num'])
        self.ProbableDRT = pd.DataFrame(columns=['k', 'Name', 'Label', 'GPS', 'Prob of point', 'Prob of region', '# of points in region', 'Error', 'Closest GPS',	'Smallest Error'])
        self.gridDim = gridDim
        self.FinalReports = pd.read_csv(self.path+'Data/Checked_FinalReports.csv')
        self.Cases=pd.read_csv(self.path+'Data/FinalCases_V16.csv')
        if theta==0.5:
            self.varArea = 30
        elif theta==1:
            self.varArea = 60
        self.epsilon = 0.03
        self.Label = 'Prob'+str(self.epsilon)

    def Test(self,eps, wcc, TrainSet, Test):
        Label = 'Prob'+str(eps)
        if wcc=='W':
            #Train
            self._optimize_Blackbox_Test_Train_MILP_multipleBeta_AreaSize(TrainSet, Test)
            self._optimize_Blackbox_Test_Test_Grid_multipleBeta_AreaSize(Test)
            filename_pre =self.path+'Model/' + self.Date  + '/'
            self.Blackbox_Test_SelectOnePointAtaTime(.51*np.sqrt(2), Test)
        elif wcc=='WO':
            # optimization with no constraint on number of reporters:

            b=self._optimize_Blackbox_Test_Train_MILP_multipleBeta(TrainSet, Test, Label)
            b.to_csv(self.path+'Model/'+self.Date+'/trainedBeta_'+str(Test)+'.csv', index=False)
            self._optimize_Blackbox_Test_Test_Grid_multipleBeta('Model/'+self.Date+'/ProbBeta_', 'Model/'+self.Date, Test, Label)

    #8/11/2016
    def _optimize_Blackbox_Test_Train_MILP_multipleBeta_AreaSize(self, Train_set, Test_set):
        Reporters=self.FinalReports.dropna(subset=['Loc N/lat'])
        Reporters = Reporters[Reporters['Case Num']==Test_set]['Reporter Num']
        Reporters = list(Reporters)
        if 'LKP' in Reporters:
            Reporters.remove('LKP')
        Cond_prob = self._CalcConditionalReporterGivenRegion_all_beta(Train_set, Reporters)
        Cond_prob.to_csv(self.path+'Model/'+self.Date+'/ProbBeta_'+str(Test_set)+'.csv', index=False)
        self.Beta = pd.DataFrame(columns=['Case', 'Reporter', 'Beta'])

        OtherPoints = self._createGrid(Train_set)

        Beta = dict()
        Tmp = dict()
        for j in Reporters:
            Betat =  Cond_prob[np.logical_and(Cond_prob["Reporter Num"]==j,Cond_prob[self.Label]>0.5 )]#Cond_prob[Cond_prob["Reporter Num"]==j]
            Tmpt = self.Reporter_Case[list(np.logical_and(list(self.Reporter_Case["Case Num"].isin(Train_set)),list(self.Reporter_Case["Reporter Num"] == j)))]
            Tmpt = Tmpt[Tmpt['Dist(DRT, P)']<500]
            if len(Betat)>=1 and len(Tmpt)>=1:
                Beta[j] = Betat
                Tmp[j] = Tmpt

        for areaSize in range(1,self.varArea):
            area = min(areaSize, len(Beta))
            self.Beta = pd.DataFrame(columns=['Case', 'Reporter', 'Beta'])
            prob = LpProblem("MIST", LpMaximize)

            Xjb = LpVariable.dicts("Xjb", [(j,i) for j in Beta.keys()
                                                 for i in range((np.power(len(Beta[j]),2)+len(Beta[j]))/2)], 0, 1, LpBinary)
            for j in Beta.keys():
                prob += lpSum([Xjb[(j,b)] for b in range((np.power(len(Beta[j]),2)+len(Beta[j]))/2)]) <= 1

            prob += lpSum([Xjb[(j,b)] for j in Beta.keys() for b in range((np.power(len(Beta[j]),2)+len(Beta[j]))/2)])== area

            prob += lpSum([self._delta(Tmp[o].loc[c, "Rep"], Tmp[o].loc[c, "DRT"], b) * np.log(self._Calcprob(list(Beta[o][Beta[o]['Beta']==b][self.Label])[0])[0]) * \
                           Xjb[(o,(len(Beta[o]))*list(Beta[o]['Beta'].values).index(b)+list(Beta[o]['Beta'].values).index(b2)-sum(range(list(Beta[o]['Beta'].values).index(b)+1)))]+\
                            (1 - self._delta(Tmp[o].loc[c, "Rep"], Tmp[o].loc[c, "DRT"], b))* self._delta(Tmp[o].loc[c, "Rep"], Tmp[o].loc[c, "DRT"], b2)*\
                            np.log(self._Calcprob(list(Beta[o][Beta[o]['Beta']==b2][self.Label])[0]-list(Beta[o][Beta[o]['Beta']==b][self.Label])[0])[0]) * \
                           Xjb[(o,(len(Beta[o]))*list(Beta[o]['Beta'].values).index(b)+list(Beta[o]['Beta'].values).index(b2)-sum(range(list(Beta[o]['Beta'].values).index(b)+1)))]\
                            + (1 - self._delta(Tmp[o].loc[c, "Rep"], Tmp[o].loc[c, "DRT"], b2)) * np.log(self._Calcprob(list(Beta[o][Beta[o]['Beta']==b2][self.Label])[0])[1]) *\
                           Xjb[(o, (len(Beta[o]))*list(Beta[o]['Beta'].values).index(b)+list(Beta[o]['Beta'].values).index(b2)-sum(range(list(Beta[o]['Beta'].values).index(b)+1)))]
                          for o in Beta.keys()
                          for c in Tmp[o].index.values
                          for b in list(Beta[o]['Beta'])
                          for b2 in list(Beta[o]['Beta'])[list(Beta[o]['Beta']).index(b):]#list(Beta['Beta'])[list(Beta['Beta']).index(b):]

                          ])

            # print 'done'
            prob += lpSum([-(self._delta(Tmp[o].loc[c, "Rep"], poi, b) * np.log(self._Calcprob(list(Beta[o][Beta[o]['Beta']==b][self.Label])[0])[0]) *\
                            Xjb[(o,(len(Beta[o]))*list(Beta[o]['Beta'].values).index(b)+list(Beta[o]['Beta'].values).index(b2)-sum(range(list(Beta[o]['Beta'].values).index(b)+1)))]+\
                         (1 - self._delta(Tmp[o].loc[c, "Rep"], poi, b))*(self._delta(Tmp[o].loc[c, "Rep"], poi, b2))*\
                        np.log(self._Calcprob(list(Beta[o][Beta[o]['Beta']==b2][self.Label])[0]-list(Beta[o][Beta[o]['Beta']==b][self.Label])[0])[0]) *\
                            Xjb[(o,(len(Beta[o]))*list(Beta[o]['Beta'].values).index(b)+list(Beta[o]['Beta'].values).index(b2)-sum(range(list(Beta[o]['Beta'].values).index(b)+1)))]\
                         + (1 - self._delta(Tmp[o].loc[c, "Rep"], poi, b2)) * np.log(self._Calcprob(list(Beta[o][Beta[o]['Beta']==b2][self.Label])[0])[1]) *\
                            Xjb[(o,(len(Beta[o]))*list(Beta[o]['Beta'].values).index(b)+list(Beta[o]['Beta'].values).index(b2)-sum(range(list(Beta[o]['Beta'].values).index(b)+1)))]
                            )
                          for o in Beta.keys()
                          for c in Tmp[o].index.values
                          for b in list(Beta[o]['Beta'])
                          for b2 in list(Beta[o]['Beta'])[list(Beta[o]['Beta']).index(b):]#list(Beta['Beta'])[list(Beta['Beta']).index(b):]
                          for poi in OtherPoints[Tmp[o].loc[c, 'Case Num']]
                          ])
            prob.solve()
            print "Status:", LpStatus[prob.status]
            # Each of the variables is printed with it's resolved optimum value
            for v in prob.variables():
                Flag = True
                # print v.name, "=", v.varValue
                if v.varValue == 1:
                    # Case_Beta[j] = list(Beta['Beta'])[int(v.name.split('_')[1])]
                    index = (v.name.strip(')').split('(')[1])
                    j = index.split(',')[0].strip('\'')
                    index = int(index.split('_')[1])
                    it=0
                    lbound = len(Beta[j])
                    lbound = len(Beta[j]) - it
                    while index >= lbound and lbound > 0:
                        it+=1
                        index -= lbound
                        lbound = len(Beta[j]) - it
                    # print it, index
                    self.Beta = self.Beta.append({'Case': Test_set, 'Reporter': j, 'Beta': list(Beta[j]['Beta'])[it]}, ignore_index=True)
                    self.Beta = self.Beta.append({'Case': Test_set, 'Reporter': j, 'Beta': list(Beta[j]['Beta'])[it + index]}, ignore_index=True)

            self.Beta.to_csv(self.path+'Model/'+self.Date+'/trainedBeta_'+str(Test_set)+'_area_'+str(area)+'.csv', index=False)
            if area == len(Beta):
                break
        return self.Beta

    def _optimize_Blackbox_Test_Test_Grid_multipleBeta_AreaSize(self,Test):
        RepCount_dic = dict()
        Prob_Beta = pd.read_csv(self.path+'Model/'+self.Date+'/ProbBeta_'+str(Test)+'.csv', dtype={'Reporter Num': str}).drop_duplicates()
        loc = self.FinalReports[self.FinalReports['Case Num'] == Test]
        rep_id=dict()
        reported_xy = []
        for ii in loc['Reporter Num'].index:
            if str(loc['Loc N/lat'][ii])!= 'None' and str(loc['Loc N/lat'][ii])!= 'nan':
                a,b='',''
                if ',' not in loc['Loc N/lat'][ii]:
                    a,b = gen.convert_DMS_to_Decimal(loc['Loc N/lat'][ii], loc['Loc W/lng'][ii])
                else:
                    a,b = gen.convert_DMS_to_Decimal(loc['Loc N/lat'][ii].split(',')[0], loc['Loc W/lng'][ii].split(',')[0])
                rep_id[(float(a), float(b))] = loc['Reporter Num'][ii]
                reported_xy.append((float(a), float(b)))

        grid, clusters = self._createTestGrid(reported_xy)

        for area in range(1,self.varArea):
            print area
            try:
                # Selected_Beta = pd.read_csv(p2 + str(case) + '_area_' + str(area) + '.csv', dtype={'Reporter': str})
                Selected_Beta = pd.read_csv(self.path+'Model/'+self.Date+'/trainedBeta_' + str(Test) + '_area_' + str(area) + '.csv', dtype={'Reporter': str})
            except:
                continue

            Selected_Beta = Selected_Beta[Selected_Beta['Case'] == Test]

            # grid = self._grid_gen(avg_reported_x, avg_reported_y, self.GridSize)
            # DRT = self.Reporter_Case[self.Reporter_Case['Case Num']==Test]['DRT'].values[0]
            region_points = self._CalcArea_Blackbox_MultipleBeta(grid, Test, Selected_Beta, rep_id)
            PointToDraw_Dic = dict()
            NumberOfPointsinR = dict()
            sum_cond_prob = 0
            for d in region_points.keys():
                cond_prob = np.array([1.0])
                flag = False
                print d
                if d!='':
                    reps = d.strip(',').split(',')
                    for l in reps:
                        rep_beta=l.split(':')
                        print rep_beta
                        if '+' in rep_beta[1]:
                            tmpvalue = Prob_Beta[np.logical_and(Prob_Beta['Reporter Num'] == (rep_beta[0]), Prob_Beta['Beta'] == float(rep_beta[1]))][self.Label].values
                            if tmpvalue!=1:
                                cond_prob *= 1 - tmpvalue
                            else:
                                cond_prob *= .001
                        elif '-' in rep_beta[1]:
                            beta1, beta2 = rep_beta[1].split('-')
                            cond_prob *= (Prob_Beta[np.logical_and(Prob_Beta['Reporter Num'] == (rep_beta[0]), Prob_Beta['Beta'] == float(beta1))][self.Label].values[0]-
                                          Prob_Beta[np.logical_and(Prob_Beta['Reporter Num'] == (rep_beta[0]), Prob_Beta['Beta'] == float(beta2))][self.Label].values[0])
                        else:
                            tmpvalue = Prob_Beta[np.logical_and(Prob_Beta['Reporter Num'] == (rep_beta[0]), Prob_Beta['Beta'] == float(rep_beta[1]))][self.Label].values
                            if tmpvalue!=0:
                                cond_prob *= tmpvalue
                            else:
                                cond_prob *= .001
                        flag = True
                    if flag == True:
                        sum_cond_prob += cond_prob * len(region_points[d])
                        PointToDraw_Dic[d] = cond_prob
                        NumberOfPointsinR[d] = len(region_points[d])
            # self.ProbableDRT = self.ProbableDRT.append({'k':'DRT','Name':'DRT', 'Label': DRT_label, 'Prob of point':cond_prob},ignore_index=True)

            POINTS = pd.DataFrame(columns=['Name', 'Label', 'GPS', 'Prob of point', 'Prob of region', '# of points in region'])
            points = []
            point_label_dic =dict()
            for d in PointToDraw_Dic.keys(): #Point_label_prob_Dic.keys():
                for i in region_points[d]:
                    points.append(i)
                    point_label_dic[i]=d
                    # POINTS = POINTS.append(pd.DataFrame({'Name':[''], 'Label': [d], 'GPS':[i], 'Prob of point':[PointToDraw_Dic[d][0]], 'Prob of region':[PointToDraw_Dic[d]*NumberOfPointsinR[d]/sum_cond_prob], '# of points in region':[NumberOfPointsinR[d]]}))

            sorted_points, heu1, heu2 = self._Heuristics_Sorting(points, self.FinalReports, Test, 1+self.theta)#(0.51)*np.sqrt(2))
            indd=0
            for poi in sorted_points:
                POINTS = POINTS.append(pd.DataFrame({'Name':[''], 'Label': [point_label_dic[poi]], 'GPS':[poi], 'Prob of point':[PointToDraw_Dic[point_label_dic[poi]][0]],
                                                     'Heu1':[heu1[indd]], 'Heu2':[heu2[indd]],
                                                     'Prob of region':[PointToDraw_Dic[point_label_dic[poi]]*NumberOfPointsinR[point_label_dic[poi]]/sum_cond_prob], '# of points in region':[NumberOfPointsinR[point_label_dic[poi]]]}))
                indd+=1
            POINTS = POINTS.sort_values(['Prob of point','Heu2', 'Heu1'], ascending=False)

            POINTS.to_csv(self.path+'Model/'+self.Date+'/'+str(Test)+'area'+str(area)+'2mul.csv', index=False)

       
    def _CalcArea_MultipleBeta_Blackbox_Test(self, grid, case, Selected_Beta):
        region_points = dict()
        rep_locs = self.FinalReports[self.Reporter_Case['Case Num']==case]['Rep']
        rep_nums = self.Reporter_Case[self.Reporter_Case['Case Num']==case]['Reporter Num']
        for i in grid.keys():
            # print i
            for j in grid[i]:
                var = ''
                # if gen.dist(j[0], j[1], 37.4636043, -107.5339873)<=1:
                #      print 'reporter 109 in range', j

                for ii in rep_locs.index.values:
                    d = gen.dist(j[0], j[1], rep_locs[ii].split()[0], rep_locs[ii].split()[1])
                    betas = np.sort(Selected_Beta[Selected_Beta['Reporter']==(rep_nums[ii])]['Beta'])
                    var_tmp=''
                    if len(betas)>0:
                        if d<=betas[0]:
                            var_tmp = str(rep_nums[ii])+':'+str(betas[0])+','
                        elif d<= betas[1]:
                            var_tmp = str(rep_nums[ii])+':'+str(betas[1])+'-'+str(betas[0])+','
                        elif var_tmp=='' and len(betas)>0:
                            var_tmp=str(rep_nums[ii])+':+'+str(betas[1])+','

                        var+=var_tmp

                region_points.setdefault(var, []).append(j)
        return region_points

    def Blackbox_Test_SelectOnePointAtaTime(self,thre, Test):
        RepCount_dic = dict()
        Reporters = self.FinalReports[self.FinalReports['Case Num']==(Test)]
        for re in list(set(Reporters['Reporter Num'])):
            RepCount_dic[re]= list(Reporters['Reporter Num']).count(re)
        if 'LKP' in RepCount_dic:
            RepCount_dic['LKP'] = 0

        points = pd.DataFrame(columns=['# of points in region', 'GPS', 'Label', 'Name',	'Prob of point',
                                       'Prob of region', 'Dist'])
        areaFile=1

        for area in range(1,self.varArea):#(1, 17):
            Flag = False
            try:
                input = pd.read_csv(self.path+'Model/'+self.Date+'/'+str(int(Test))+ 'area' + str(area)+'2mul.csv')
                Flag = True
                areaFile = area
                for ind in range(len(input)):
                    if input.loc[ind, 'GPS'] not in list(points['GPS']):
                        points = points.append(input.loc[ind])
                        break
            except:
                if not Flag:
                    input = pd.read_csv(self.path+'Model/'+self.Date+'/'+str(int(Test))+ 'area' + str(areaFile)+'2mul.csv')
                    if len(input)>=len(points):
                        for ind in range(len(input)):
                            if input.loc[ind, 'GPS'] not in list(points['GPS']):
                                points = points.append(input.loc[ind])

        points.to_csv(self.path+'Model/'+self.Date+'/'+'SelectedOnePointAtaTime_V1'+str(Test)+'.csv', index=False)


    def _Heuristics_Sorting(self, Possible_GPS, HistoricalData_Reporters, Test_case, thre):
        Reps = HistoricalData_Reporters[np.logical_and(np.logical_and(HistoricalData_Reporters['Case Num']==Test_case,
                                                                        HistoricalData_Reporters['Loc N/lat']!=''),
                                                    list(np.invert(np.array(HistoricalData_Reporters['Loc N/lat']).astype(str) =='nan')))]
        RepCount_dic=dict()
        for re in list(Reps['Reporter Num']):
            RepCount_dic[re]= list(HistoricalData_Reporters['Reporter Num']).count(re)
        if 'LKP' in RepCount_dic:
            RepCount_dic['LKP'] = 0

        GPS_withinReps = dict()
        # rep_id=dict()
        rep_locs = []
        rep_nums=[]
        for ii in Reps['Reporter Num'].index:
            # if str(loc['Loc N/lat'][ii])!= 'None' and str(loc['Loc N/lat'][ii])!= 'nan':
            a,b='',''
            if ',' in Reps['Loc N/lat'][ii]:
                a,b = gen.convert_DMS_to_Decimal(Reps['Loc N/lat'][ii].split(',')[0], Reps['Loc W/lng'][ii].split(',')[0])
            else:
                a,b = gen.convert_DMS_to_Decimal(Reps['Loc N/lat'][ii], Reps['Loc W/lng'][ii])
            # rep_id[(float(a), float(b))] = Reps['Reporter Num'][ii]
            rep_locs.append((float(a), float(b)))
            rep_nums.append(Reps['Reporter Num'][ii])

        for gps in Possible_GPS:
            lat, lng = gps[0], gps[1]
            for reps in rep_locs:
                if gen.dist(lat, lng, reps[0], reps[1])<=thre:
                    GPS_withinReps.setdefault(gps, []).append(rep_nums[rep_locs.index(reps)])
        NumofReps = []
        SumofPrior = []
        points = []
        for item in Possible_GPS:
            if item in GPS_withinReps:
                NumofReps.append(len(GPS_withinReps[item]))
            else:
                NumofReps.append(0)
            v=0
            if item in GPS_withinReps:
                for rr in GPS_withinReps[item]:
                    v +=  RepCount_dic[rr]-1
            SumofPrior.append(v)
        from operator import itemgetter
        sorted_tuples = sorted(zip(Possible_GPS, NumofReps, SumofPrior), key=itemgetter(1,2), reverse=True)
        points, heu1, heu2 = list(zip(*sorted_tuples))
        return points, heu1, heu2


    #updated
    def _optimize_Blackbox_Test_Train_MILP_multipleBeta(self, Train_set, Test_set, Label):
        # inp = pd.read_csv('C:/Users/eshaaban/PycharmProjects/MIST/Oct_7/Nov_5/IntermediateOutputs/Checked_FinalReports.csv')
        Reporters=self.FinalReports.dropna(subset=['Loc N/lat'])
        Reporters = Reporters[Reporters['Case Num']==Test_set]['Reporter Num']
        Reporters = list(Reporters)
        if 'LKP' in Reporters:
            Reporters.remove('LKP')
        Cond_prob = self._CalcConditionalReporterGivenRegion_all_beta(Train_set, Reporters)
        Cond_prob.to_csv(self.path+'Model/'+self.Date+'/ProbBeta_'+str(Test_set)+'.csv', index=False)
        self.Beta = pd.DataFrame(columns=['Case', 'Reporter', 'Beta'])
        #random found locations
        OtherPoints =self._createGrid(Train_set)
        for j in Reporters:
            Tmp = self.Reporter_Case[list(np.logical_and(list(self.Reporter_Case["Case Num"].isin(Train_set)),list(self.Reporter_Case["Reporter Num"] == j)))]
            #print (j, len(Tmp))
            Tmp = Tmp[Tmp['Dist(DRT, P)']<500]
            #print (j, len(Tmp))
            Beta = Cond_prob[np.logical_and(Cond_prob["Reporter Num"]==j,Cond_prob[Label]>0.5 )]
            #print (j)

            if len(Beta)>=1 and len(Tmp)>=1:
                prob = LpProblem("MIST", LpMaximize)
                Xjb = LpVariable.dicts("Xjb", range((np.power(len(Beta),2)+len(Beta))/2), 0, 1, LpBinary)
                prob += lpSum([Xjb[b] for b in range((np.power(len(Beta),2)+len(Beta))/2)]) <= 1

                prob += lpSum([self._delta(Tmp.loc[c, "Rep"], Tmp.loc[c, "DRT"], b) * np.log(self._Calcprob(list(Beta[Beta['Beta']==b][Label])[0])[0]) * \
                               Xjb[(len(Beta))*list(Beta['Beta'].values).index(b)+list(Beta['Beta'].values).index(b2)-sum(range(list(Beta['Beta'].values).index(b)+1))]+\
                                (1 - self._delta(Tmp.loc[c, "Rep"], Tmp.loc[c, "DRT"], b))* self._delta(Tmp.loc[c, "Rep"], Tmp.loc[c, "DRT"], b2)*\
                                np.log(self._Calcprob(list(Beta[Beta['Beta']==b2][Label])[0]-list(Beta[Beta['Beta']==b][Label])[0])[0]) * \
                               Xjb[(len(Beta))*list(Beta['Beta'].values).index(b)+list(Beta['Beta'].values).index(b2)-sum(range(list(Beta['Beta'].values).index(b)+1))]\
                                + (1 - self._delta(Tmp.loc[c, "Rep"], Tmp.loc[c, "DRT"], b2)) * np.log(self._Calcprob(list(Beta[Beta['Beta']==b2][Label])[0])[1]) *\
                               Xjb[(len(Beta))*list(Beta['Beta'].values).index(b)+list(Beta['Beta'].values).index(b2)-sum(range(list(Beta['Beta'].values).index(b)+1))]
                              for c in Tmp.index.values
                              for b in list(Beta['Beta'])
                              for b2 in list(Beta['Beta'])[list(Beta['Beta']).index(b):]#list(Beta['Beta'])[list(Beta['Beta']).index(b):]

                              ])

                prob += lpSum([-(self._delta(Tmp.loc[c, "Rep"], poi, b) * np.log(self._Calcprob(list(Beta[Beta['Beta']==b][Label])[0])[0]) *\
                                Xjb[(len(Beta))*list(Beta['Beta'].values).index(b)+list(Beta['Beta'].values).index(b2)-sum(range(list(Beta['Beta'].values).index(b)+1))]+\
                             (1 - self._delta(Tmp.loc[c, "Rep"], poi, b))*(self._delta(Tmp.loc[c, "Rep"], poi, b2))*\
                            np.log(self._Calcprob(list(Beta[Beta['Beta']==b2][Label])[0]-list(Beta[Beta['Beta']==b][Label])[0])[0]) *\
                                Xjb[(len(Beta))*list(Beta['Beta'].values).index(b)+list(Beta['Beta'].values).index(b2)-sum(range(list(Beta['Beta'].values).index(b)+1))]\
                             + (1 - self._delta(Tmp.loc[c, "Rep"], poi, b2)) * np.log(self._Calcprob(list(Beta[Beta['Beta']==b2][Label])[0])[1]) *\
                                Xjb[(len(Beta))*list(Beta['Beta'].values).index(b)+list(Beta['Beta'].values).index(b2)-sum(range(list(Beta['Beta'].values).index(b)+1))]
                                )
                              for c in Tmp.index.values
                              for b in list(Beta['Beta'])
                              for b2 in list(Beta['Beta'])[list(Beta['Beta']).index(b):]#list(Beta['Beta'])[list(Beta['Beta']).index(b):]
                              for poi in OtherPoints[Tmp.loc[c, 'Case Num']]
                              ])
                # prob.writeLP("MISTProblem"+str(Train_set)+".lp")  # optional
                prob.solve()
                print ("Status:", LpStatus[prob.status])
                # Each of the variables is printed with it's resolved optimum value
                for v in prob.variables():
                    #Flag = True
                    #print (v.name, "=", v.varValue)
                    if v.varValue == 1:
                        # Case_Beta[j] = list(Beta['Beta'])[int(v.name.split('_')[1])]
                        index = int(v.name.split('_')[1])
                        it=0
                        #lbound = len(Beta)
                        lbound = len(Beta) - it
                        while index >= lbound and lbound > 0:
                            it+=1
                            index -= lbound
                            lbound = len(Beta) - it

                        print (it, index)
                        self.Beta = self.Beta.append({'Case': Test_set, 'Reporter': j, 'Beta': list(Beta['Beta'])[it]}, ignore_index=True)
                        self.Beta = self.Beta.append({'Case': Test_set, 'Reporter': j, 'Beta': list(Beta['Beta'])[it + index]}, ignore_index=True)
        return self.Beta

    def _optimize_Blackbox_Test_Test_Grid_multipleBeta(self, p1, p2,CC, Label):
        #Without constraint
        for case in [CC]:
            grid = []
            Prob_Beta = pd.read_csv(p1+str(case)+'.csv', dtype={'Reporter Num': str}).drop_duplicates()
            #print ('Case:', case)
            #find the grid

            loc = self.FinalReports[self.FinalReports['Case Num']==case]
            rep_id=dict()
            reported_xy = []
            for ii in loc['Reporter Num'].index:
                if str(loc['Loc N/lat'][ii])!= 'None' and str(loc['Loc N/lat'][ii])!= 'nan':
                    a,b='',''
                    if ',' not in loc['Loc N/lat'][ii]:
                        a,b = gen.convert_DMS_to_Decimal(loc['Loc N/lat'][ii], loc['Loc W/lng'][ii])
                    else:
                        a,b = gen.convert_DMS_to_Decimal(loc['Loc N/lat'][ii].split(',')[0], loc['Loc W/lng'][ii].split(',')[0])
                    rep_id[(float(a), float(b))] = loc['Reporter Num'][ii]
                    reported_xy.append((float(a), float(b)))

            grid, clusters = self._createTestGrid(reported_xy)

            Selected_Beta = pd.read_csv(p2 + '/trainedBeta_' +str(case) + '.csv', dtype={'Reporter': str})
            Selected_Beta = Selected_Beta[Selected_Beta['Case'] == case]

            region_points = self._CalcArea_Blackbox_MultipleBeta(grid, case, Selected_Beta, rep_id) ##########
            Point_label_prob_Dic = dict()
            NumberOfPointsinR = dict()
            sum_cond_prob = 0

            for d in region_points.keys():
                #print (d)
                cond_prob = np.array([1.0])
                flag = False
                #print (d)
                if d!='':
                    reps = d.strip(',').split(',')
                    for l in reps:
                        rep_beta=l.split(':')
                        #print (rep_beta)
                        if '+' in rep_beta[1]:# and float(rep_beta[1])!=2.5:
                            tmpvalue = Prob_Beta[np.logical_and(Prob_Beta['Reporter Num'] == (rep_beta[0]), Prob_Beta['Beta'] == float(rep_beta[1]))][Label].values
                            if tmpvalue!=1:
                                cond_prob *= 1 - tmpvalue
                            else:
                                cond_prob *= 0.001
                        elif '-' in rep_beta[1]:
                            beta1, beta2 = rep_beta[1].split('-')
                            cond_prob *= (Prob_Beta[np.logical_and(Prob_Beta['Reporter Num'] == (rep_beta[0]), Prob_Beta['Beta'] == float(beta1))][Label].values-\
                            Prob_Beta[np.logical_and(Prob_Beta['Reporter Num'] == (rep_beta[0]), Prob_Beta['Beta'] == float(beta2))][Label].values)
                        else:
                            tmpvalue = Prob_Beta[np.logical_and(Prob_Beta['Reporter Num'] == (rep_beta[0]), Prob_Beta['Beta'] == float(rep_beta[1]))][Label].values
                            if tmpvalue!=0:
                                cond_prob *= tmpvalue
                            else:
                                cond_prob *= 0.001
                        flag = True
                    if flag == True:
                        sum_cond_prob += cond_prob * len(region_points[d])
                        Point_label_prob_Dic[d] = cond_prob
                        NumberOfPointsinR[d] = len(region_points[d])

            POINTS = pd.DataFrame(columns=['Name', 'Label', 'GPS', 'Prob of point', 'Prob of region', '# of points in region'])
            points=[]
            point_label_dic=dict()
            for d in Point_label_prob_Dic.keys():
                for i in region_points[d]:
                    points.append(i)
                    point_label_dic[i]=d


            sorted_points, heu1, heu2 = self._Heuristics_Sorting(points, self.FinalReports, case, 1+self.theta)#########
            indd=0
            for poi in sorted_points:
                POINTS = POINTS.append(pd.DataFrame({'Name':[''], 'Label': [point_label_dic[poi]], 'GPS':[poi], 'Prob of point':[Point_label_prob_Dic[point_label_dic[poi]][0]],
                                                     'Heu1':[heu1[indd]], 'Heu2':[heu2[indd]],
                                                     'Prob of region':[Point_label_prob_Dic[point_label_dic[poi]]*NumberOfPointsinR[point_label_dic[poi]]/sum_cond_prob], '# of points in region':[NumberOfPointsinR[point_label_dic[poi]]]}))
                indd+=1
            POINTS = POINTS.sort_values(['Prob of point', 'Heu2','Heu1'], ascending=False)
            POINTS.to_csv(p2+'/'+str(case)+'_2mul.csv', index=False)

    def _CalcConditionalReporterGivenRegion_all_beta(self, Train_set, Reporters):
        #return betas for the reporters of test set
        Train_Beta = self.Reporter_Case[self.Reporter_Case['Case Num'].isin(Train_set)]
        ConProb = pd.DataFrame(columns=['Reporter Num', 'Beta', 'Support', 'Total cases', 'SE'])
        Train_Beta = Train_Beta.drop_duplicates(Train_Beta.columns)
        Train_Beta = Train_Beta[np.logical_and(Train_Beta['Rep']!='nan nan', Train_Beta['Rep']!='None None')]

        for r in list(Reporters):
            if str(r)!='nan':
                Tmp = Train_Beta[Train_Beta['Reporter Num']==r]
                Beta = set()
                for i in Tmp['Dist(DRT, P)'].values:
                    Beta.add(math.ceil(i*10)/10.)
                Beta = np.sort(list(Beta))
                Acc_Beta = filter(lambda x: x<500, Beta)
                if len(Acc_Beta)>0:
                    for b in list(Acc_Beta):
                        s =  (map(lambda x: x<=b,Tmp['Dist(DRT, P)']).count(True))
                        t = float(len(Tmp))

                        SE = ((len(Train_set)-t)/float(len(Train_set)))
                        p1 = s/t - 0.1*SE if s/t - 0.1*SE>0 else 0                        
                        p2 = s/t - 0.15*SE if s/t - 0.15*SE>0 else 0                       
                        p3 = s/t - .2*SE if s/t - .2*SE>0 else 0                       
                        p4 = s/t - 0.01*SE if s/t - 0.01*SE>0 else 0            
                        p5 = s/t - 0.05*SE if s/t - 0.05*SE>0 else 0
                        p6 = s/t - 0.03*SE if s/t - 0.03*SE>0 else 0
                        p7 = s/t - 0.4*SE if s/t - 0.4*SE>0 else 0

                        ConProb = ConProb.append(pd.DataFrame({'Reporter Num': [r], 'Beta':[b], 'Support': [s], 'Total cases': [t], 'SE': [SE] , 'Prob0.1': [p1],'Prob0.15': [p2],'Prob0.2': [p3],
                                                               'Prob0.01':[p4], 'Prob0': [s/t], 'Prob0.03': [p6], 'Prob0.4':[p7],
                                                               'Prob0.05': [p5],}))

        return ConProb

    #updated
    def _createGrid(self, Train_set):
        OtherPoints = dict()
        for c in Train_set:#Tmp.index.values:
            # print c
            drt = list(self.Reporter_Case[self.Reporter_Case['Case Num']==c]['DRT'])[0]
            # print c
            loc = self.Reporter_Case[self.Reporter_Case['Case Num'] == c]
            rep_id=dict()

            for ii in loc['Rep'].index:
                rep_id[(float(loc['Rep'][ii].split()[0]), float(loc['Rep'][ii].split()[1]))] = loc['Reporter Num'][ii]

            reported_xy = [(float(i.split()[0]), float(i.split()[1])) for i in loc['Rep'] if i != 'None None' or i != 'nan nan']

            clusters = self._clustering(reported_xy)
            A=[]
            for key in clusters.keys():
                # print A
                A = A + self._grid_gen_poly_noNearDRT(key, clusters[key], self.theta, drt)[key]
            OtherPoints[c]=A
        return OtherPoints

    #updated
    def _clustering(self, reported_xy):
        clusters = dict()
        for xy in reported_xy:
            clusters.setdefault(xy, []).append(xy)
            for yz in reported_xy:
                if xy != yz:
                    dd = gen.dist(xy[0], xy[1], yz[0], yz[1])
                    if dd <= 2*self.theta:
                        clusters.setdefault(xy, []).append(yz)


        for key1 in reported_xy:
            if key1 in clusters:
                # ind = reported_xy.index(key1)
                for key2 in reported_xy:
                    if key2 in clusters and key1!=key2:
                        # print key1, key2
                        if len(list(set(clusters[key1])|set(clusters[key2]))) < len(set(clusters[key1]))+ len(set(clusters[key2])):
                            clusters[key1] = list(set(clusters[key1])|set(clusters[key2]))
                            clusters.pop(key2)
        return clusters

    def _createTestGrid(self, reported_xy):
        grid=dict()
        clusters = self._clustering(reported_xy)
        for key in clusters.keys():
            try:
                grid.update(self._grid_gen_poly(key, clusters[key]))
            except:
                grid = self._grid_gen_poly(key, clusters[key])
        return grid, clusters

    def _grid_gen_poly_noNearDRT(self, key, points, beta,drt):
        #finds down left, and right up points, then calculate all points in between..
        drtx, drty = drt.split()[0], drt.split()[1]
        if len(points)==1 and beta<=self.gridDim*.5:
            if gen.dist(points[0][0], points[0][1], drtx,drty)>1:
                return {points[0]:points}
            else:
                return {points[0]:[]}
        gen_points = []
        output = []
        y_min = 200
        x_min = 200
        y_max = -200
        x_max = -200
        for p in points:
            if p[0] < x_min:
                x_min = p[0]
            if p[0] > x_max:
                x_max = p[0]
            if p[1] < y_min:
                y_min = p[1]
            if p[1] > y_max:
                y_max = p[1]


        Dots = self._getcycle(x_min, y_min, (beta-self.gridDim*.5)*1609.34, 4)

        x_l_d = Dots[2][0]
        y_l_d = Dots[1][1]
        x_u_r = Dots[0][0]
        y_u_r = Dots[3][1]

        a = max(min(x_l_d, x_u_r), -90)
        c = max(min(y_l_d, y_u_r), -180)

        Dots = self._getcycle(x_max, y_max, (beta-self.gridDim*.5)*1609.34, 4)

        x_l_d = Dots[2][0]
        y_l_d = Dots[1][1]
        x_u_r = Dots[0][0]
        y_u_r = Dots[3][1]

        b = min(max(x_l_d, x_u_r), 90)
        d = min(max(y_l_d, y_u_r), 180)
        # center of the squares are our points
        print ('a: ', a,'b:', b, 'c:', c,'d:', d)
        # add down left point to the array and output
        gen_points.append((a, c))
        drt_dist = gen.dist(a, c, drtx, drty)
        if drt_dist>1:
            for p in points:
                dist = gen.dist(p[0], p[1],a, c)
                if dist<=(beta+.01)*np.sqrt(2):
                    output.append((a,c))
                    break
        else:
            output.append((a,c))

        # output.append((a,c))
        curr = (a, c)
        while curr[1] < d:
            next = self._getRightPoint(a, curr[1], self.gridDim*1)[0]
            gen_points.append(next)
            drt_dist = gen.dist(next[0], next[1], drtx, drty)
            if drt_dist>1:
                for p in points:
                    dist = gen.dist(p[0], p[1], next[0], next[1])
                    if dist<=(beta+.01)*np.sqrt(2):
                        output.append(next)
                        break
            else:
                output.append(next)
            curr = next
        # output = gen_points
        # add points above the bottom row
        for i in gen_points:
            curr = i
            while curr[0] < b:
                next = self._getUpPoint(curr[0], i[1], self.gridDim*1)[0]
                drt_dist = gen.dist(next[0], next[1], drtx, drty)
                if drt_dist>1:
                    for p in points:
                        dist = gen.dist(p[0], p[1], next[0], next[1])
                        if dist<=(beta+.01)*np.sqrt(2):
                            output.append(next)
                            break
                else:
                    output.append(next)
                curr = next
        return {key:output}

    def _getcycle(self, lat, lng, radius, NumDot):
        cycle = []
        rad = radius #unit: meter
        d = (rad/1000.0)/6378.8;
        lat1 = (math.pi/180.0) * lat
        lng1 = (math.pi/180.0) * lng

        r = [x*(360/NumDot) for x in range(NumDot)]
        for a in r:
            tc = (math.pi/180.0)*a
            y = math.asin(math.sin(lat1)*math.cos(d)+math.cos(lat1)*math.sin(d)*math.cos(tc))
            dlng = math.atan2(math.sin(tc)*math.sin(d)*math.cos(lat1),math.cos(d)-math.sin(lat1)*math.sin(y))
            x = ((lng1-dlng+math.pi) % (2.0*math.pi)) - math.pi
            cycle.append((float(y*(180.0/math.pi)),float(x*(180.0/math.pi))))
        return cycle

    def _getRightPoint(self, lat, lng,radius):
        cycle = []
        rad = radius #unit: meter
        d = (rad*10)/(4*10162.497770611415*0.9741419753696064)
        lat1 = (math.pi/180.0) * lat
        lng1 = (math.pi/180.0) * lng

        r = [x*(360/1)-90 for x in range(1)]
        for a in r:
            tc = (math.pi/180.0)*a
            y = math.asin(math.sin(lat1)*math.cos(d)+math.cos(lat1)*math.sin(d)*math.cos(tc))
            dlng = math.atan2(math.sin(tc)*math.sin(d)*math.cos(lat1),math.cos(d)-math.sin(lat1)*math.sin(y))
            x = ((lng1-dlng+math.pi) % (2.0*math.pi)) - math.pi
            cycle.append((float(y*(180.0/math.pi)),float(x*(180.0/math.pi))))
        return cycle

    def _getUpPoint(self, lat, lng,radius):
        cycle = []
        rad = radius #unit: meter
        d = d = (rad*10)/(4*10162.497770611415*0.9741419753696064)
        lat1 = (math.pi/180.0) * lat
        lng1 = (math.pi/180.0) * lng

        r = [x*(360) for x in range(1)]
        for a in r:
            tc = (math.pi/180.0)*a
            y = math.asin(math.sin(lat1)*math.cos(d)+math.cos(lat1)*math.sin(d)*math.cos(tc))
            dlng = math.atan2(math.sin(tc)*math.sin(d)*math.cos(lat1),math.cos(d)-math.sin(lat1)*math.sin(y))
            x = ((lng1-dlng+math.pi) % (2.0*math.pi)) - math.pi
            cycle.append((float(y*(180.0/math.pi)),float(x*(180.0/math.pi))))
        return cycle

    def _delta(self, x,y, beta):
        if type(x) is tuple:
            p1lat, p1lng = x[0], x[1]
        else:
            p1lat, p1lng = x.split()
        if type(y) is tuple:
            p2lat, p2lng = y[0], y[1]
        else:
            p2lat, p2lng = y.split()
        if gen.dist(p1lat, p1lng, p2lat, p2lng) > beta:
            return 0
        else:
            return 1

    #updated
    def _Calcprob(self, x):
        # print x
        if x == 0:
            # happens when both betas are the same
            return 0.001, 1-0.001#0.00001, 0.00001
        elif x == 1:
            # print 'x==1 error'
            return 1-0.001, .001#0.00001, 0.00001
        else:
            return (x), (1-x)

    def _grid_gen_poly(self, key, points):
        beta=self.theta
        if len(points)==1 and beta<=self.gridDim*.5:
            return {points[0]:points}
        gen_points = []
        output = []
        y_min = 200
        x_min = 200
        y_max = -200
        x_max = -200
        for p in points:
            if p[0] < x_min:
                x_min = p[0]
            if p[0] > x_max:
                x_max = p[0]
            if p[1] < y_min:
                y_min = p[1]
            if p[1] > y_max:
                y_max = p[1]


        Dots = self._getcycle(x_min, y_min, (beta-self.gridDim*.5)*1609.34, 4)

        x_l_d = Dots[2][0]
        y_l_d = Dots[1][1]
        x_u_r = Dots[0][0]
        y_u_r = Dots[3][1]

        a = max(min(x_l_d, x_u_r), -90)
        c = max(min(y_l_d, y_u_r), -180)

        Dots = self._getcycle(x_max, y_max, (beta-self.gridDim*.5)*1609.34, 4)

        x_l_d = Dots[2][0]
        y_l_d = Dots[1][1]
        x_u_r = Dots[0][0]
        y_u_r = Dots[3][1]

        b = min(max(x_l_d, x_u_r), 90)
        d = min(max(y_l_d, y_u_r), 180)
        # center of the squares are our points
        #print 'a: ', a,'b:', b, 'c:', c,'d:', d
        gen_points.append((a, c))
        flag=False
        for p in points:
            dist = gen.dist(p[0], p[1], a, c)
            if dist<=(beta+.01)*np.sqrt(2):
                output.append((a,c))
                break
        # output.append((a,c))
        curr = (a, c)
        while curr[1] <= d:
            next = self._getRightPoint(a, curr[1], self.gridDim*1)[0]
            flag = False
            for p in points:
                dist = gen.dist(p[0], p[1], next[0], next[1])
                if dist<=(beta+.01)*np.sqrt(2):
                    gen_points.append(next)
                    output.append(next)
                    flag = True
                    break

            if flag == False:
                gen_points.append(next)

            curr = next
        # output = gen_points
        for i in gen_points:
            curr = i
            while curr[0] <= b:
                next = self._getUpPoint(curr[0], i[1], self.gridDim*1)[0]
                for p in points:
                    dist = gen.dist(p[0], p[1], next[0], next[1])
                    if dist<=(beta+.01)*np.sqrt(2):
                        output.append(next)
                        break
                curr = next
        return {key:output}

    def _CalcArea_Blackbox_MultipleBeta(self, grid, case, Selected_Beta, rep_id):
        region_points = dict()
        rep_locs = rep_id.keys()
        # rep_nums = self.Reporter_Case[self.Reporter_Case['Case Num']==case]['Reporter Num']
        for i in grid.keys():
            # print i
            for j in grid[i]:
                var = ''
                # if gen.dist(j[0], j[1], 37.4636043, -107.5339873)<=1:
                #      print 'reporter 109 in range', j
                for ii in rep_locs:
                    d = gen.dist(j[0], j[1], ii[0], ii[1])
                    betas = np.sort(Selected_Beta[Selected_Beta['Reporter']==(rep_id[ii])]['Beta'])
                    var_tmp=''
                    if len(betas)>0:
                        if d<=betas[0]:
                            var_tmp = str(rep_id[ii])+':'+str(betas[0])+','
                        elif d<= betas[1]:
                            var_tmp = str(rep_id[ii])+':'+str(betas[1])+'-'+str(betas[0])+','
                        elif var_tmp=='' and len(betas)>0:
                            var_tmp=str(rep_id[ii])+':+'+str(betas[1])+','

                        var+=var_tmp

                region_points.setdefault(var, []).append(j)
        return region_points

    def _Heuristics_Sorting(self, Possible_GPS, HistoricalData_Reporters, Test_case, thre):
        Reps = HistoricalData_Reporters[np.logical_and(np.logical_and(HistoricalData_Reporters['Case Num']==Test_case,
                                                                        HistoricalData_Reporters['Loc N/lat']!=''),
                                                    list(np.invert(np.array(HistoricalData_Reporters['Loc N/lat']).astype(str) =='nan')))]
        RepCount_dic=dict()
        for re in list(Reps['Reporter Num']):
            RepCount_dic[re]= list(HistoricalData_Reporters['Reporter Num']).count(re)
        if 'LKP' in RepCount_dic:
            RepCount_dic['LKP'] = 0

        GPS_withinReps = dict()
        # rep_id=dict()
        rep_locs = []
        rep_nums=[]
        for ii in Reps['Reporter Num'].index:
            # if str(loc['Loc N/lat'][ii])!= 'None' and str(loc['Loc N/lat'][ii])!= 'nan':
            a,b='',''
            if ',' in Reps['Loc N/lat'][ii]:
                a,b = gen.convert_DMS_to_Decimal(Reps['Loc N/lat'][ii].split(',')[0], Reps['Loc W/lng'][ii].split(',')[0])
            else:
                a,b = gen.convert_DMS_to_Decimal(Reps['Loc N/lat'][ii], Reps['Loc W/lng'][ii])
            # rep_id[(float(a), float(b))] = Reps['Reporter Num'][ii]
            rep_locs.append((float(a), float(b)))
            rep_nums.append(Reps['Reporter Num'][ii])

        for gps in Possible_GPS:
            lat, lng = gps[0], gps[1]
            for reps in rep_locs:
                if gen.dist(lat, lng, reps[0], reps[1])<=thre:
                    GPS_withinReps.setdefault(gps, []).append(rep_nums[rep_locs.index(reps)])
        NumofReps = []
        SumofPrior = []
        points = []
        for item in Possible_GPS:
            if item in GPS_withinReps:
                NumofReps.append(len(GPS_withinReps[item]))
            else:
                NumofReps.append(0)
            v=0
            if item in GPS_withinReps:
                for rr in GPS_withinReps[item]:
                    v +=  RepCount_dic[rr]-1
            SumofPrior.append(v)
        from operator import itemgetter
        sorted_tuples = sorted(zip(Possible_GPS, NumofReps, SumofPrior), key=itemgetter(1,2), reverse=True)
        points, heu1, heu2 = list(zip(*sorted_tuples))
        return points, heu1, heu2

    # calculate distance between reported location and found location
    def AtomRepDistDRT(self):#Last Scene lat
        # Number of cases each reporter have participated in and report gps
        C = self.Cases.dropna(subset=['Found lat', 'Found lng'])#, 'Last Scene lat', 'Last Scene lng'])
        Rep = self.FinalReports.dropna(subset=['Loc N/lat', 'Loc W/lng'])

        for c in C['Case Num'].index:
            R = Rep[Rep['Case Num'] == C['Case Num'][c]]
            print c,C['Case Num'][c]
            d = gen.dist(C.loc[c, 'Found lat'], C.loc[c, 'Found lng'], C.loc[c, 'Last Scene lat'], C.loc[c, 'Last Scene lng'])

            self.Beta = self.Beta.append(pd.DataFrame({'Case Num': [C['Case Num'][c]], 'Reporter Num': ['LKP'], 'Dist(DRT, P)': [d], 'Rep': [str(C.loc[c, 'Last Scene lat']) + ' ' + str(C.loc[c, 'Last Scene lng'])],
                                                       'DRT': [str(C['Found lat'][c]) + ' ' + str(C['Found lng'][c])]}))
            if len(R)>0:
                for r in R['Reporter Num'].index:
                    plat, plng = None, None
                    if ',' in R['Loc N/lat'][r]: # several locations reported by one reporter
                        la = R['Loc N/lat'][r].split(',')[0]
                        ln = R['Loc W/lng'][r].split(',')[0]
                    else:
                        la = R['Loc N/lat'][r]
                        ln = R['Loc W/lng'][r]
                    print 'la:',la,'ln:', ln
                    # print ite
                    try:
                        plat, plng = gen.convert_DMS_to_Decimal(la, ln)
                    except:
                        print 'connection lost!'

                    dist=0
                    if plat!=None and plng!=None:
                        d1=gen.dist(C.loc[c, 'Found lat'], C.loc[c, 'Found lng'], plat, plng)
                        d2=gen.dist(C.loc[c, 'Last Scene lat'], C.loc[c, 'Last Scene lng'], plat, plng)
                        if d1>200 and R['Loc W/lng'][r][0]!='-':
                            plat, plng = gen.convert_DMS_to_Decimal(R['Loc N/lat'][r], R['Loc W/lng'][r])
                            dist = gen.dist(C.loc[c, 'Found lat'], C.loc[c, 'Found lng'], plat, plng)
                        else:
                            dist = d1

                    self.Beta = self.Beta.append(pd.DataFrame({'Case Num': [C['Case Num'][c]], 'Reporter Num': [R['Reporter Num'][r]], 'Dist(DRT, P)': [dist],
                                                               'Reported loc': [R['Loc N/lat'][r] + ' ' + R['Loc W/lng'][r]],
                                                               'Rep':  [str(plat) + ' ' + str(plng)],
                                            'DRT': [str(C['Found lat'][c]) + ' ' + str(C['Found lng'][c])]}))
        self.Beta =  self.Beta[np.logical_and(self.Beta['Rep']!='nan nan', self.Beta['Rep']!='None None')]
        self.Beta.to_csv(self.path+'Model/Beta.csv', index=False)
        return self.Beta
