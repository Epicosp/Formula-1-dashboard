import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import time
import datetime as dt
import hvplot.pandas
import seaborn as sns
import numpy as np
import matplotlib.style as style
style.use('fivethirtyeight')



'''Pit stop data'''
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
pit_data = pd.concat([pit_stops, standings], join='inner', axis='columns')

# filter by total sum of pit time <500000 ms, removing outliers and excessivly long pit times.
pit_data = pit_data[pit_data['milliseconds']<500000]

# remove multi indexing
pit_data = pit_data.reset_index()

# left merge data with races by raceId, and reset_index, slice to use only nessecary data.
pit_data = pit_data.merge(races, on='raceId' , how='left').reset_index()
pit_data = pit_data[['raceId', 'driverId', 'milliseconds', 'driverStandingsId', 'circuitId', 'position']]

# left merge data with circuits, by circuitId
pit_data = pit_data.merge(circuits, on='circuitId', how='left')


'''Budget data'''
# import data from csv
budget = pd.read_csv("data/Formula1_Budgets.csv")

# remove $ and change value type to float
for col in budget.columns[1:]:
    budget[col] = budget[col].str.replace('$', '', regex=True)
    budget[col] = budget[col].astype('float')

'''Functions'''
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
    histogram = pit_data.hvplot.hist(y='milliseconds',bins = 200, height=500, width=900)
    return histogram

def pit_pos():
    # take the average pit time for top 20 positions and plot with trendline (data becomes thin after the top 20)
    avg_pt_for_position = pit_data.groupby('position').mean().reset_index().head(20)
    scatter = px.scatter(avg_pt_for_position, x='position', y='milliseconds', trendline="ols")
    return scatter

def pit_pos_tracks():
    data_by_tracks = pit_data.groupby(['name','position']).mean().reset_index()
    scatter = data_by_tracks.hvplot.scatter(x='position', y='milliseconds', groupby='name')
    return scatter


def avg_budget_by_year():
    # get and format data
    plot_data = budget.set_index('Year')

    # init figure
    fig, ax = plt.subplots(figsize=(15,10))
    
    # plot total budget spend and format
    for col in plot_data.columns:
        plt.plot(plot_data[col], label=col)
    plt.legend()
    plt.title("Formula-1 Budget Spent from 2017 to 2021")
    
    # close fig to avoid showing when function is called
    plt.close()
    
    return fig

def avg_budget_by_year_bar():
    # get and format data
    bar = pd.melt(budget, id_vars='Year')
    bar = bar.groupby("Year").agg(average_budget_all =('value','mean'))
    
    fig, ax = plt.subplots(figsize=(15,10))
    
    sns.barplot(x = bar.index, y = bar["average_budget_all"])
    plt.title("Average budget spent by all the companies")
    plt.ylabel("Average Budget spent in $")
    
    plt.close()

    return fig

def budget_by_constructor():
    # get and format data
    const_bar = pd.melt(budget, id_vars='Year')
    
    # init figure
    fig, ax = plt.subplots(figsize=(15,10))
    
    
    # plot and format
    sns.barplot(x='Year', y='value', hue='variable', data=const_bar)
    plt.title("Formula-1 Budget Spent from 2017 to 2021")
    plt.xlabel("Year")
    plt.ylabel("Budget Spent in $")
    
    plt.close()
    
    return fig
    
def budget_stackplot():
    # get and format data
    stackplot = budget.set_index('Year')
    
    # init figure
    fig, ax = plt.subplots(figsize=(15,10))
    
    # plot
    plt.stackplot(
        stackplot.index,
        stackplot['Mercedes'],
        stackplot['Ferrari'],
        stackplot['RedBull'],
        stackplot['Mclaren'],
        stackplot['Alpine/Renault'],
        stackplot['Aston Martin/Racing Point/Force India'],
        stackplot['AlphaTauri/Toro Rossi'],
        stackplot['AlphaRomeo'],
        stackplot['Williams'],
        stackplot['Haas'],
        labels = list(stackplot.columns),
    )
    
    # formatting
    plt.legend()
    plt.ylabel("Total Budget Spent")
    plt.title("Formula1 Budget Overall")
    plt.xlabel("Year")
    
    plt.close()
    
    return fig
    