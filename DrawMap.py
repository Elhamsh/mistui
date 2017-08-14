__author__ = 'eshaaban'

import pandas as pd
import pygmaps
import numpy as np
import math
import General as gen
import simplekml

def _getcycle(lat, lng, radius, NumDot):
    cycle = []
    rad = radius #unit: meter
    d = (rad/1000.0)/6378.8;
    # d = (rad*10)/(4*10162.497770611415*0.9741419753696064);
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

def createInput(path_, case):
    Reports = pd.read_csv(path_+'Data/Checked_FinalReports.csv')
    Colors = ["#023FA5","#7D87B9","#BEC1D4","#D6BCC0","#BB7784","#FFFFFF", "#4A6FE3","#8595E1","#B5BBE3","#E6AFB9","#E07B91","#D33F6A",
              "#11C638","#8DD593","#C6DEC7","#EAD3C6","#F0B98D","#EF9708", "#0FCFC0","#9CDED6","#D5EAE7","#F3E1EB","#F6C4E1","#F79CD4"]

    Reports_Case=Reports[Reports['Case Num']==case].dropna(subset=['Loc N/lat', 'Loc W/lng'])
    i=Reports_Case.index[0]
    x,y=gen.convert_DMS_to_Decimal(Reports_Case['Loc N/lat'][i], Reports_Case['Loc W/lng'][i])
    mymap = pygmaps.maps(float(x), float(y), 9)
    mymap.addpoint(float(x), float(y), color='red', title=str(x)+', '+str(y))
    for i in Reports_Case.index[1:]:
        x,y=gen.convert_DMS_to_Decimal(Reports_Case['Loc N/lat'][i], Reports_Case['Loc W/lng'][i])
        mymap.addpoint(float(x), float(y), color='red', title=str(x)+', '+str(y))
    mymap.draw(path_+'Output/Inp_'+str(case)+'.html')

def createTest(path_, case):

    #Points = pd.read_csv('../Model/'+str(case)+'_2mul.csv')
    Points = pd.read_csv(path_+'Model/SelectedOnePointAtaTime_V1'+str(case)+'.csv')
    Colors = ["#023FA5","#7D87B9","#BEC1D4","#D6BCC0","#BB7784","#FFFFFF", "#4A6FE3","#8595E1","#B5BBE3","#E6AFB9","#E07B91","#D33F6A",
              "#11C638","#8DD593","#C6DEC7","#EAD3C6","#F0B98D","#EF9708", "#0FCFC0","#9CDED6","#D5EAE7","#F3E1EB","#F6C4E1","#F79CD4"]

    beta = 1

    GPS_Coor= Points['GPS'].values
    xx, yy = GPS_Coor[0].strip('()').split(', ')
    mymap = pygmaps.maps(float(xx), float(yy), 9)

    labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    i=0
    kml = simplekml.Kml()
    for p in GPS_Coor:
        xx, yy = p.strip('()').split(', ')
        mymap.addpointRegion(float(xx), float(yy), color="yellow", label=labels[i], title=str(xx)+', '+str(yy))
        kml.newpoint(name=labels[i], coords=[(float(yy), float(xx))])
        i+=1
        Dots=_getcycle(float(xx), float(yy), ((beta/2.)*np.sqrt(2))*1609.34, 8)
        path=[Dots[1], Dots[3], Dots[5], Dots[7], Dots[1]]
        ls = kml.newlinestring(coords=[(Dots[1][1], Dots[1][0]), (Dots[3][1], Dots[3][0]), (Dots[5][1], Dots[5][0]), (Dots[7][1], Dots[7][0]), (Dots[1][1], Dots[1][0])])
        ls.style.linestyle.width=10
        # kml.newlinestring(coords=[(Dots[3][1], Dots[3][0]), (Dots[5][1], Dots[5][0])])
        # kml.newlinestring(coords=[(Dots[5][1], Dots[5][0]), (Dots[7][1], Dots[7][0])])
        # kml.newlinestring(coords=[(Dots[7][1], Dots[7][0]), (Dots[1][1], Dots[1][0])])

        mymap.addpath(path, Colors[0])

    mymap.draw('Output/'+str(case)+'.html')
    kml.save('Output/'+str(case)+'.kml')
