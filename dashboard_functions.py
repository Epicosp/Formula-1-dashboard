import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import time
import datetime as dt
import hvplot.pandas


# read circuits, slice for nessecary data
circuits = pd.read_csv('data/circuits.csv')
circuits = circuits[['circuitId', 'name']].set_index('circuitId')

# read standings data, groupby unique identifiers for concat (sum wins for extra analysis)
standings = pd.read_csv('data/driver_standings.csv')
standings = standings.groupby(['raceId', 'driverId']).sum('wins')

# read pit_stops, groupby keys to get unique pit times for each driver during each race, sum to get total pit time.
pit_stops = pd.read_csv('data/pit_stops.csv')
pit_stops = pit_stops.groupby(['raceId', 'driverId']).sum().drop(columns=['stop', 'lap'])

# read races csv, for some reason this data contains columns with lots of null data and the column names are offset, 
# so the original csv was edited in excel to remove these columns.
races = pd.read_csv('data/races_edited.csv').set_index('raceId')

# concat pit_stops and standings by index, ensuring that raceId and driverId are the same
data = pd.concat([pit_stops, standings], join='inner', axis='columns')

# filter by total sum of pit time <500000 ms, removing outliers and excessivly long pit times.
data = data[data['milliseconds']<500000]

# remove multi indexing
data = data.reset_index()

# left merge data with races by raceId, and reset_index, slice to use only nessecary data.
data = data.merge(races, on='raceId' , how='left').reset_index()
data = data[['raceId', 'driverId', 'milliseconds', 'driverStandingsId', 'circuitId', 'position']]

# left merge data with circuits, by circuitId
data = data.merge(circuits, on='circuitId', how='left')


def time_to_next_race():
    # call api for current season
    url = 'http://ergast.com/api/f1/current.json'
    data = requests.get(url).json()
    
    #get today's date
    today = dt.date.today().isoformat()
    
    # get the date of the previous and next race
    for race in data['MRData']['RaceTable']['Races']:
        if dt.datetime.strptime(race['date'],'%Y-%m-%d').isoformat() < today:
            previous_race = dt.datetime.strptime(race['date'],'%Y-%m-%d').isoformat()
        else:
            next_race = dt.datetime.strptime(race['date'],'%Y-%m-%d').isoformat()
            break
            
    # convert dates to numbers
    previous_race = dt.datetime.fromisoformat(previous_race).timestamp()
    next_race = dt.datetime.fromisoformat(next_race).timestamp()
    now = dt.datetime.fromisoformat(today).timestamp()
    
    #calculate the percentage time till the next race from the previous race.
    pct_ttnr = round((((now-previous_race)/(next_race-previous_race)))*100, 2)
    
    return pct_ttnr

def pit_time_histogram():
    # multimodal data can be attributed to the modes of pit times ie: 1 stop for entire race vs 2 or 3 stops etc...
    histogram = data.hvplot.hist(y='milliseconds',bins = 200, height=500, width=900)
    return histogram

def pit_pos():
    # take the average pit time for top 20 positions and plot with trendline (data becomes thin after the top 20)
    avg_pt_for_position = data.groupby('position').mean().reset_index().head(20)
    scatter = px.scatter(avg_pt_for_position, x='position', y='milliseconds', trendline="ols")
    return scatter

def pit_pos_tracks():
    data_by_tracks = data.groupby(['name','position']).mean().reset_index()
    scatter = data_by_tracks.hvplot.scatter(x='position', y='milliseconds', groupby='name')
    return scatter

def tech_improvement_data():
    # Create parameterized url
    dicAUS = {}
    dicMON = {}
    dicItaly = {}
    for i in range(2009,2020):
        #had to do alot of if statements here because not all races happen at the same round every year, so i had to do a bit of research
        if i == 2010:
            request_urlAUS = (f"http://ergast.com/api/f1/{i}/2/qualifying.json")
        else:
            request_urlAUS = (f"http://ergast.com/api/f1/{i}/1/qualifying.json")
        request_urlMON = (f"http://ergast.com/api/f1/{i}/6/qualifying.json")
        if i == 2014 or i == 2017 or i == 2012 or i == 2011 or i == 2009:
            request_urlItaly = (f"http://ergast.com/api/f1/{i}/13/qualifying.json")
        elif i == 2015 or i == 2013:
            request_urlItaly = (f"http://ergast.com/api/f1/{i}/12/qualifying.json")
        else:
            request_urlItaly = (f"http://ergast.com/api/f1/{i}/14/qualifying.json")

    # Submit request and format output
        response_dataAUS = requests.get(request_urlAUS).json()
        response_dataMON = requests.get(request_urlMON).json()
        response_dataItaly = requests.get(request_urlItaly).json()


    # Select fact
        qualiDataAUS = response_dataAUS["MRData"]["RaceTable"]["Races"][0]["QualifyingResults"][0]['Q3']
        dicAUS[f'{i}'] = (qualiDataAUS)
        qualiDataMON = response_dataMON["MRData"]["RaceTable"]["Races"][0]["QualifyingResults"][0]['Q3']
        dicMON[f'{i}'] = (qualiDataMON)
        qualiDataItaly = response_dataItaly["MRData"]["RaceTable"]["Races"][0]["QualifyingResults"][0]['Q3']
        dicItaly[f'{i}'] = (qualiDataItaly)

    dicAll = {}
    for i in range(2009,2020):
        dicAll[f"{i}"] = [dicAUS[f"{i}"],dicMON[f"{i}"],dicItaly[f"{i}"]]
    #print(dicAll)

    dfAll = pd.DataFrame.from_dict(dicAll, orient='index')
    dfAll.columns = ['Australia','Monoco','Monza']

    def time_to_seconds(time_str):
        return float(time_str.replace("1:",""))
    dfAll['Australia Seconds'] = dfAll['Australia'].apply(time_to_seconds) + 60
    dfAll['Monoco Seconds'] = dfAll['Monoco'].apply(time_to_seconds) + 60
    dfAll['Monza Seconds'] = dfAll['Monza'].apply(time_to_seconds) + 60

    dfAll.index.name = 'year'
    f1_seconds = dfAll.drop(['Australia', 'Monoco', 'Monza'], axis=1).copy()
    f1_seconds = f1_seconds.reset_index().copy()
    f1_seconds['Albert Park Pct Change'] = f1_seconds['Australia Seconds'].pct_change()
    f1_seconds['Monoco Pct Change'] = f1_seconds['Monoco Seconds'].pct_change()
    f1_seconds['Monza Pct Change'] = f1_seconds['Monza Seconds'].pct_change()
    f1_pct_change = f1_seconds.drop(['Australia Seconds', 'Monoco Seconds','Monza Seconds'], axis=1).copy()
    f1_pct_change = f1_pct_change.dropna()
    f1_pct_change.loc[8, 'Monza Pct Change'] = -0.019614 
    f1_pct_change.loc[5, 'Albert Park Pct Change'] = 0.019247
    f1_pct_change['mean'] = f1_pct_change.mean(axis=1)
    f1_quali = f1_seconds.copy()
    f1_quali.loc[5, 'Australia Seconds'] = 90.934
    f1_quali.loc[8, 'Monza Seconds'] = 83.221
    tech_data = {}
    tech_data['f1_seconds'] =f1_seconds
    tech_data['f1_pct_change'] = f1_pct_change
    tech_data['f1_quali'] = f1_quali
    return tech_data



def tech_imp_scatterPlot(f1_quali):
    figMonoco = px.scatter(f1_quali, x="year", y="Monoco Seconds", trendline="lowess",title = "Monoco Grand Prix - High Down Force Track - Qualifying times")
    #figMonoco.show()
    figAus = px.scatter(f1_quali, x="year", y="Australia Seconds", trendline="lowess", title = "Australian Grand Prix - High Speed/High Down Force Track Qualifying times") #, trendline_scope="overall")
    #figAus.show()
    figMonz = px.scatter(f1_quali, x="year", y="Monza Seconds", trendline="lowess", title = "Italian Grand Prix - High Speed Track Qualifying times")
    #figMonz.show()
    tech_imp = [figMonoco,figAus,figMonz]
    return tech_imp
    
    
    
def tech_pct_scatterPlot(f1_pct_change):
    fig_pct_changeAus = px.scatter(f1_pct_change, x="year", y="mean",trendline="lowess", title = "Average Percentage Change in track time")#, color='country')
    return fig_pct_changeAus

if __name__ == "__main__":
    tech_data = tech_improvement_data()
    tech_pct_scatterPlot(tech_data)
    tech_pct_scatterPlot.show()