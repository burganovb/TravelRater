# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib
import urllib2
import sqlite3
import re


def wikisearch(word):
    url = 'https://en.wikipedia.org/wiki/w/index.php'
    values = {'search' : word,
            'title' : 'Special:Search',
            'go' : 'Go' }

    try:
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        the_page = response.read()
        soup = BeautifulSoup(the_page, "html.parser")
        return soup
    except urllib2.HTTPError:
        print "HTTPError searching wiki for ", word
        return None
    except:
        print "Unexpected searching wiki for ", word
        return None

def fetch_travel_data(city):
    """
    Scrape numbeo.com to find travel costs

    city is a list [city_key, city_name, country_name, url, BHI, HPI, BTCI, TCI, BDC, TDC]
    
    """
    url = city[3] + '&displayCurrency=USD'
    print url
    try:
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page.read(), "html.parser")
    except urllib2.HTTPError:
        print "HTTPError fetching travel data for ", city[1], ", ", city[2]
        return None
    except:
        print "Unexpected error fetching travel data!"
        return None

    travel_data = [city[0]]
    for td in soup.find_all('td'):
        try:
            x = str(td.string)
            found = x.find('Meal, Inexpensive Restaurant')
        except:
            continue
        
        #print found, 'found'
        if  found >= 0:
            for cell in td.parent.parent.find_all():
                try:
                    travel_data.append(float(cell.string.replace('$','').replace(',','').replace(' ','')))
                except:
                    continue
    return travel_data
        

def fetch_city_list(url):
    """
    Scrape to find cities at numbeo.com
    """
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page.read(), "html.parser")
    cities = []
    # city is a list [city_key, city_name, country_name, url, BHI, HPI, BTCI, TCI, BDC, TDC]
    for link in soup.find_all('a'):
        x = str(link.get('href'))

        if x.find('http://www.numbeo.com/travel-prices/city_result.jsp?country=') >= 0:
            text = str(link.string)
            textkey = text.replace(' ','').replace('-','').replace(',','')
            city_name_country = [s.strip() for s in text.split(',')]
            if len(city_name_country)==2:
                city = [textkey, city_name_country[0], city_name_country[1]]
            else:
                cityname = city_name_country[0] + ' ' + city_name_country[1]
                #cityname = cityname.replace(',',' ')
                city = [textkey, cityname, city_name_country[-1]]
            city.append(x)
            
            current_cell = link.parent
            for cell in current_cell.next_siblings:
                try:
                    city.append(float(str(cell.string)))
                except:
                    continue
            cities.append(city)
    
    return cities


def addcitiestodb(cities):
    conn = sqlite3.connect('travel_database')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS travelcostindex
        (citykey VARCHAR(100) PRIMARY KEY,
        city VARCHAR(100),
        country VARCHAR(100),
        travelurl VARCHAR(100),
        ibackphotel REAL,
        ihotel REAL,
        ibackptravel REAL,
        itravelpriceind REAL,
        backpcostperday REAL,
        travelcostperday REAL)''')
    for city in cities:
        print (city[0])
        c.execute('SELECT 1 FROM travelcostindex WHERE citykey=(?)', (city[0],))
        if len(c.fetchall()) > 0:
            print "Record for ", city[0], " exists!"
        else:
            print "Fetching data from www for ", city[0]
            print tuple(city)
            c.execute('INSERT INTO travelcostindex VALUES (?,?,?,?,?,?,?,?,?,?)', tuple(city))
            conn.commit()
    c.close()

def addtraveldatatodb(cities):
    conn = sqlite3.connect('travel_database')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS travelcostdetails
        (citykey VARCHAR(100) PRIMARY KEY,
        rmealcheap REAL,
        rmealmid REAL,
        rmealmcdonalds REAL,
        rdombeer REAL,
        rimportbeer REAL,
        rcoffee REAL,
        rcoke REAL,
        rwater REAL,
        tbus REAL,
        ttaxistart REAL,
        ttaximile REAL,
        ttaxihour REAL,
        tgas REAL,
        tcar REAL)''')
    
    for city in cities:
        print "Looking for travel cost data in ", city[1], ", ", city[2], "."
        
        # check if city is already in the table
        c.execute('SELECT 1 FROM travelcostdetails WHERE citykey=(?)', (city[0],))
        if len(c.fetchall()) > 0:
            print "Record for ", city[1], " exists!"
        else:
            print "Fetching city data from www for ", city[1], ", ", city[2]
            travel_data = fetch_travel_data(city)
            print travel_data
            if travel_data is not None:
                print "Inserting ", travel_data
                try:
                    c.execute('INSERT INTO travelcostdetails VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                              tuple(travel_data))
                    print "\t... was added!"
                except sqlite3.IntegrityError:
                    print "\t... was already in the table!"

            conn.commit()

    c.close()

def wikivcardfetch(soup):
    
    if soup.title.string.find('Search results')>=0:
        print '-------------ambiguous wiki seach results-----------------------------------------'
        print soup.title.string
        return [None, None, None]

    # scrape vcard
    vcard = soup.find(class_ = "infobox geography vcard")
    if vcard == None:
        vcard = soup.find(class_ = "infobox geography")
        if vcard == None:
            print "no vcard found"        
            return [None, None, None]
    
    #return vcard
    year_founded = None
    population = None
    img_url = None
    population_next = False
    img = vcard.find('img')
    print img.src
    
    for tr in vcard.find_all('tr'):
        if population_next:
            population_next = False
            for td in tr.find_all('td'):
                text = str(td).replace(',','')
                pop_match = re.search('[ >][0-9]{3,8}[< ]', text)
                try:
                    population = int(pop_match.group(0).replace(' ','').replace('>','').replace('<',''))
                except:
                    a=0
        try:
            if str(tr).find('Population')>=0:
                population_next = True
        except:
            a=0
        try:
            if str(tr).find('Founded')>=0 or str(tr).find('Settled')>=0 or str(tr).find('Established')>=0:
                text = str(tr)
                mBC = re.search('[ >][0-9]{1,4} BC', text)
                mAD = re.search('[ >][0-9]{1,4}<', text)
                if mBC != None:
                    try:
                        year_founded = -int(mBC.group(0).replace(' ','').replace('>','').replace('B','').replace('C',''))
                    except:
                        a=0
                elif mAD != None:
                    try:
                        year_founded = int(mAD.group(0).replace(' ','').replace('>','').replace('<',''))
                    except:
                        a=0
        except:
            a=0
    
    return year_founded, population, img_url

                                                                                                
def wikifetch(soup):
    
    if soup.title.string.find('Search results')>=0:
        print '-------------ambiguous wiki seach results-----------------------------------------'
        print soup.title.string
        return [0, 1900, 0, 0]

    # scrape history
    history = soup.find(id="History")
    history_score = 0
    year_founded = 1900
    try:
        history = history.parent
        for tag in history.next_siblings:
            try:
                if str(tag).find('h2')>=0:
                    #print 'next section', tag
                    break
            except:
                a=0
            #print tag
            if str(tag).find('<p>')>=0:
                text = str(tag)
                #print text
                history_score += len(text)
                m1 = re.search(' [1][0-9][0-9][0-9][ ,.]', text)
                m2 = re.search('[ 1][0-9][0-9][0-9] BC', text)
                if m2 != None:
                    try:
                        year_founded = -int(m2.group(0).replace(' ','').replace('B','').replace('C',''))
                    except:
                        a=0
                elif m1 != None:
                    try:
                        year_founded = min(year_founded, int(m1.group(0).replace(',','').replace('.','').strip()))
                    except:
                        a=0
    except:
        print 'Failed to get history'
    
    # scrape tourism
    tourism = soup.find(id="Tourism")
    tourism_score = 0
    
    try:
        tourism = tourism.parent
        for tag in tourism.next_siblings:
            try:
                if str(tag).find('h2')>=0:
                    #print 'next section'
                    break
            except:
                a=0
            if str(tag).find('<p>')>=0:
                text = str(tag)
                tourism_score += len(text)
    except:
        print 'Failed to get tourism data'
    
    # scrape culture
    culture = soup.find(id="Culture")
    if culture == None:
        culture = soup.find(id="Cityscape")
    culture_score = 0
    
    try:
        culture = culture.parent
        for tag in culture.next_siblings:
            try:
                if str(tag).find('h2')>=0:
                    #print 'next section'
                    break
            except:
                a=0
            if str(tag).find('<p>')>=0:
                text = str(tag)
                culture_score += len(text)
    except:
        print 'Failed to get culture data'
    
    return history_score, year_founded, tourism_score, culture_score
    
    
def wikiclimatefetch(soup):
    
    if soup.title.string.find('Search results')>=0:
        print '-------------ambiguous wiki seach results-----------------------------------------'
        print soup.title.string
        return [[], []]
    
    avg_high = []
    avg_low = []
    # scrape climate
    for th in soup.find_all('th'):
        if str(th).find('Average high')>=0:
            for cell in th.next_siblings:
                text = str(cell).replace("−","-")
                m1 = re.search('>-?[0-9]{1,2}(.[0-9])?<', text)
                m2 = re.search('(-?[0-9]{1,2}(.[0-9])?)', text)
                t1 = t2 = 50.
                try:
                    t1 = float(m1.group(0).replace('>','').replace('<',''))
                except:
                    a=0
                try:
                    t2 = float(m2.group(0).replace('(','').replace(')',''))
                except:
                    a=0
                if t1==50. and t2==50.:
                    t1 = 15.
                avg_high.append(min(t1,t2))

        elif str(th).find('Average low')>=0:
            for cell in th.next_siblings:
                text = str(cell).replace("−","-")
                m1 = re.search('>-?[0-9]{1,2}(.[0-9])?<', text)
                m2 = re.search('(-?[0-9]{1,2}(.[0-9])?)', text)
                t1 = t2 = 50.
                try:
                    t1 = float(m1.group(0).replace('>','').replace('<',''))
                except:
                    a=0
                try:
                    t2 = float(m2.group(0).replace('(','').replace(')',''))
                except:
                    a=0
                if t1==50. and t2==50.:
                    t1 = 20.
                avg_low.append(min(t1,t2))
    
    return [avg_high, avg_low]    
    
    
def add_wikidata_todb(cities):
    conn = sqlite3.connect('travel_database')
    c = conn.cursor()
    # citykey, year_founded, population, img_url, history_score, tourism_score, culture_score
    c.execute('''CREATE TABLE IF NOT EXISTS wikidata
        (citykey VARCHAR(100) PRIMARY KEY,
        year_founded REAL,
        population REAL,
        img_url VARCHAR(100),
        history_score REAL,
        tourism_score REAL,
        culture_score REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS climate
        (citykey VARCHAR(100) PRIMARY KEY,
        avhigh01 REAL,
        avhigh02 REAL,
        avhigh03 REAL,
        avhigh04 REAL,
        avhigh05 REAL,
        avhigh06 REAL,
        avhigh07 REAL,
        avhigh08 REAL,
        avhigh09 REAL,
        avhigh10 REAL,
        avhigh11 REAL,
        avhigh12 REAL,
        avlow01 REAL,
        avlow02 REAL,
        avlow03 REAL,
        avlow04 REAL,
        avlow05 REAL,
        avlow06 REAL,
        avlow07 REAL,
        avlow08 REAL,
        avlow09 REAL,
        avlow10 REAL,
        avlow11 REAL,
        avlow12 REAL)''')
    conn.commit()
    
    for city in cities:
        print "Reading wikipedia for ", city[1], ", ", city[2], "."
        city_country = city[1], ", ", city[2]
        soup = wikisearch(city_country)
        if soup==None:
            print "Couldn't fetch wiki data for ", city_country
            continue
        elif soup.title.string.find('Search results')>=0:
            soup = wikisearch(city[1])
            if soup == None:
                print "Couldn't fetch wiki data for ", city_country
                continue
        
        # fetch general info
        c.execute('SELECT 1 FROM wikidata WHERE citykey=(?)', (city[0],))
        if len(c.fetchall()) > 0:
            print "Record for ", city[1], " exists!"
        else:
            print "Fetching wiki for ", city[1], ", ", city[2]
            history, yearf, tourism, culture = wikifetch(soup)
            yearf1, population, img_url = wikivcardfetch(soup)
            if yearf==None:
                yearf = yearf1
            print "Inserting wiki data for ", city[1], ", ", city[2]
            try:
                c.execute('INSERT INTO wikidata VALUES (?,?,?,?,?,?,?)',
                          (city[0], yearf, population, img_url, history, tourism, culture))
                print "\t... was added!"
            except sqlite3.IntegrityError:
                print "\t... was already in the table!"
            conn.commit()
        # fetch climate
        c.execute('SELECT 1 FROM climate WHERE citykey=(?)', (city[0],))
        if len(c.fetchall()) > 0:
            print "Record for ", city[1], " exists!"
        else:
            print "Fetching climate for ", city[1], ", ", city[2]
            avghi, avglo = wikiclimatefetch(soup)
            if len(avghi)<12:
                print '...failed to get climate data', avghi, avglo
                continue
            print "Inserting climate data"
            try:
                c.execute('INSERT INTO climate VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                          tuple([city[0]] + avghi[0:12] + avglo[0:12]))
                print "\t... was added!"
            except sqlite3.IntegrityError:
                print "\t... was already in the table!"
            conn.commit()

    c.close()

    
def make_city_db():
    listurl = 'http://www.numbeo.com/travel-prices/rankings_current.jsp'
    cities = fetch_city_list(listurl)
    print len(cities), ' cities found'
    print cities[0]
    
    #scrape data
    addcitiestodb(cities)
    addtraveldatatodb(cities)
    add_wikidata_todb(cities)
    
    return cities

if __name__ == '__main__':
    print ''
    #make_city_db()
