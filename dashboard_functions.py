import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import time
import datetime as dt
import hvplot.pandas


# read circuits, slice for nessecary data
circuits = pd.read_csv('f1db_csv/circuits.csv')
circuits = circuits[['circuitId', 'name']].set_index('circuitId')

# read standings data, groupby unique identifiers for concat (sum wins for extra analysis)
standings = pd.read_csv('f1db_csv/driver_standings.csv')
standings = standings.groupby(['raceId', 'driverId']).sum('wins')

# read pit_stops, groupby keys to get unique pit times for each driver during each race, sum to get total pit time.
pit_stops = pd.read_csv('f1db_csv/pit_stops.csv')
pit_stops = pit_stops.groupby(['raceId', 'driverId']).sum().drop(columns=['stop', 'lap'])

# read races csv, for some reason this data contains columns with lots of null data and the column names are offset, 
# so the original csv was edited in excel to remove these columns.
races = pd.read_csv('f1db_csv/races_edited.csv').set_index('raceId')

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