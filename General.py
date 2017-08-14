from geopy.distance import great_circle

def convert_DMS_to_Decimal(lat, lng):
    x=''
    y=''
    if ',' in lat:
        lat=lat.split(',')[0]
    if ',' in lng:
        lng=lng.split(',')[0]
    ll = len(lat.split())
    if ll == 3:
        Dlt, Mlt, Slt = lat.split()
        x = float(float(Dlt)+float(Mlt)/60.+float(Slt)/3600.)
    elif ll == 2:
        Dlt, Mlt= lat.split()
        x = float(float(Dlt)+float(Mlt)/60.)
    else:
        x = float(lat)

    ll = len(lng.split())
    if ll == 3:
        Dln, Mln, Sln = lng.split()
        if '-' in Dln:
            Dln = Dln.strip('-')
            y = -1*float(float(Dln)+float(Mln)/60.+float(Sln)/3600.)
        else:
            y = float(float(Dln)+float(Mln)/60.+float(Sln)/3600.)
    elif ll == 2:
        Dln, Mln= lng.split()
        if '-' in Dln:
            Dln = Dln.strip('-')
            y = -1*float(float(Dln)+float(Mln)/60.)
        else:
            y = float(float(Dln)+float(Mln)/60.)
    else:
        y = float(lng)

    return x, y

def dist(p1lat, p1lng, p2lat, p2lng):
    return great_circle((p1lat,p1lng), (p2lat,p2lng)).miles