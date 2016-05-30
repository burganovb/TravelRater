import sqlite3
import re
import math

def get_data_from_table(table_name='travelcostindex', what='*', condition='', value=None):
    conn = sqlite3.connect('travel_database')
    c = conn.cursor()
    if value==None:
        c.execute('SELECT ' + what + ' FROM ' + table_name + condition)
    else:
        c.execute('SELECT ' + what + ' FROM ' + table_name + condition, value)
    result = [a for a in c.fetchall()]
    c.close()
    return result    

def rank_destinations(budget, priorities, month):
    
    mindhi = {'Jan':1, 'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
    mindlo = {'Jan':13, 'Feb':14,'Mar':15,'Apr':16,'May':17,'Jun':18,'Jul':19,'Aug':20,'Sep':21,'Oct':22,'Nov':23,'Dec':24}
    
    maxdaily = budget['MaxCostPerDay']
    
    whistory = priorities['History']
    wculture = priorities['Culture']
    wTemp = priorities['Temperature']
    wPop = priorities['Size']
    
    rank=[]
    tci = get_data_from_table('travelcostindex')
    for k in xrange(len(tci)):
        if 0.5*(tci[k][8]+tci[k][9])>maxdaily:
            continue
        citykey = tci[k][0]
        city_country = tci[k][1] + ', ' + tci[k][2]
        
        tcd = get_data_from_table('travelcostdetails', '*', ' WHERE citykey=(?)', (citykey,))
        wiki = get_data_from_table('wikidata', '*', ' WHERE citykey=(?)', (citykey,))
        climate = get_data_from_table('climate', '*', ' WHERE citykey=(?)', (citykey,))
        
        gas = tcd[0][13]
        taxi = tcd[0][10]+3*tcd[0][11]+0.5*tcd[0][12]
        mealcheap = tcd[0][1]
        mealmid = tcd[0][2]
        #print tcd
        #print wiki
        #print climate
        T_lo = -15.
        T_hi = 25.        
        try:
            #print wiki[0][2]
            population = int(wiki[0][2])
        except:
            population = 100000
        try:
            #print wiki[0][4]
            history = 100.*(wiki[0][4]+14345)/40000
        except:
            history = 0
        try:
            #print wiki[0][6], wiki[0][5]
            culture =  100.*(wiki[0][6]+wiki[0][5]+15000)/60000
        except:
            culture = 0
        try:
            #print wiki[0][1]
            year_founded = int(wiki[0][1])
        except:
            year_founded = 1900
        try:
            if climate[0][17]!=20.:
                T_lo = climate[0][mindlo[month]]
                T_hi = climate[0][mindlo[month]]
                #print 'Temperatures in ', month, ': ', T_lo, ' - ', T_hi, ' C'
        except:
            a=0
        score = 1.5*whistory/10.*history + 3*wculture/10.*culture 
        score+= 300*math.exp(-(wTemp-T_lo)*(wTemp-T_hi)/(T_hi-T_lo)**2)/(T_hi-T_lo)**0.5
        score+= -int(2*(math.log(1.0*wPop)-math.log(1.0*population))**2)
        score+= 80.*math.exp(-(maxdaily-0.5*tci[k][8]-0.5*tci[k][8])**2)
        rank.append([score, citykey, city_country])
    sorted_rank = sorted(rank, reverse=True)
    #print sorted_rank
    #return 0
    for k in xrange(min(5,len(sorted_rank))):
        print k+1, ')', sorted_rank[k][2], ' - total score ', sorted_rank[k][0]
    for k in xrange(min(5,len(sorted_rank))):
        city_lookup_bykey(sorted_rank[k][1], month, mindlo[month], mindhi[month])
    '''
    cond=True
    while cond name in sorted_rank2:
        if counter>=10:
            break
        else:
            print counter, ')', name
    counter = 0
    for key in sorted_rank1:
        if counter>=4:
            break
        else:
            city_lookup_bykey(citykey, month, mindlo[month], mindhi[month])
            print ''
               '''
                               
def city_lookup(city_name):
    tci = get_data_from_table('travelcostindex', '*', ' WHERE city=(?)', (city_name,))
    for k in xrange(len(tci)):
        citykey = tci[k][0]
        tcd = get_data_from_table('travelcostdetails', '*', ' WHERE citykey=(?)', (citykey,))
        wiki = get_data_from_table('wikidata', '*', ' WHERE citykey=(?)', (citykey,))
        climate = get_data_from_table('climate', '*', ' WHERE citykey=(?)', (citykey,))
        
        print tci[k][1], ', ', tci[k][2]
        print 'Backpacker\'s cost per day ', tci[k][8]
        print 'Business traveller\'s cost per day ', tci[k][9]
        try:
            a = int(wiki[k][2])
            print 'Population: ', a
        except:
            a = 0
        try:
            #a =  math.log(wiki[0][4]+1)
            a = 100.*(wiki[k][4]+14345)/40000
            print 'History score: ', int(a)
        except:
            a = 0
        try:
            #a =  math.log(wiki[0][6]+1)
            a =  100.*(wiki[k][6]+wiki[k][5]+15000)/60000
            print 'Culture score: ', int(a)
        except:
            a = 0
        try:
            a = int(wiki[k][1])
            print 'Year founded: ', a
        except:
            a = 0
        try:
            if climate[k][17]!=20.:
                print 'Temperatures in May ', climate[0][17], ' - ', climate[0][5], ' C'
        except:
            a = 0

def city_lookup_bykey(citykey, month, indlo, indhi):
    tci = get_data_from_table('travelcostindex', '*', ' WHERE citykey=(?)', (citykey,))
    for k in xrange(len(tci)):
        tcd = get_data_from_table('travelcostdetails', '*', ' WHERE citykey=(?)', (citykey,))
        wiki = get_data_from_table('wikidata', '*', ' WHERE citykey=(?)', (citykey,))
        climate = get_data_from_table('climate', '*', ' WHERE citykey=(?)', (citykey,))
        
        print ''
        print '***'
        print ''
        print tci[k][1], ', ', tci[k][2]
        print 'Backpacker\'s cost per day ', tci[k][8]
        print 'Business traveller\'s cost per day ', tci[k][9]
        try:
            a = int(wiki[k][2])
            print 'Population: ', a
        except:
            a = 0
        try:
            #a =  math.log(wiki[0][4]+1)
            a = 100.*(wiki[k][4]+14345)/40000
            print 'History score: ', int(a)
        except:
            a = 0
        try:
            #a =  math.log(wiki[0][6]+1)
            a =  100.*(wiki[k][6]+wiki[k][5]+15000)/60000
            print 'Culture score: ', int(a)
        except:
            a = 0
        try:
            a = int(wiki[k][1])
            print 'Year founded: ', a
        except:
            a = 0
        try:
            if climate[k][indlo]!=20.:
                print 'Temperatures in ', month, climate[0][indlo], ' - ', climate[0][indhi], ' C'
        except:
            a = 0

def analyze_scores():
    #data = get_data_from_table('wikidata')
    data = get_data_from_table('travelcostdetails')
    gas = [a[13] for a in data]
    taxi = [a[10]+3*a[11]+0.5*a[12] for a in data]
    mealcheap = [a[1] for a in data]
    mealmid = [a[2] for a in data]
    
    print min(gas), max(gas)
    print min(taxi), max(taxi)
    print min(mealcheap), max(mealcheap)
    print min(mealmid), max(mealmid)
'''
0.02 13.84
1.36 84.89
0.76 28.52
3.99 125.5
'''


if __name__ == '__main__':

    print ''
