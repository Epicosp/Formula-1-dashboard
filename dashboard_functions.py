import requests
import pandas as pd
import panel as pn
pn.extension('echarts', 'plotly')
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
    
    
'''Podium data'''
# Read from online data source
podium_data = pd.read_html('https://en.everybodywiki.com/List_of_Formula_One_podium_finishers')
podium_data = podium_data[3]


'''sunburst plots data'''
# read from master table csv
sunburst_data = pd.read_csv('data/master_table.csv')

'''mapbox data'''
master_circuits_cleaned = pd.read_csv('data/master_circuits_cleaned.csv')

'''data for driver country of origin'''
def driver_data():
    list_of_formula_one_drivers = pd.read_html('https://en.wikipedia.org/wiki/List_of_Formula_One_drivers')
    drivers_country = list_of_formula_one_drivers[2]
    
    
    #DATA SORTING AND CLEANING
    #sortby naationailtiy 
    country = drivers_country.groupby('Nationality')

    
    #refine data to just these columns 
    #just name and nationality for drivers in a table/df, renaming
    name_nationality = drivers_country[['Driver Name', 'Nationality']]
    name_nationality.rename(columns = {"Driver Name": "driver_name"}, inplace=True)

    
    #give numeric value for each driver (one diver equals 1 driver)
    name_nationality['count'] = 1
    name_nationality = name_nationality.drop('driver_name', 1) #droppping diver name colunm leaving us just with nationality and a driver unit(1 driver name = 1 driver)


    #cleaning data
    #Nationality splitting counts from nationality column with a function
    def update_data(value_, new_value):
        index = name_nationality[name_nationality['Nationality']==value_].index.values
        name_nationality.iloc[index, name_nationality.columns.get_loc('Nationality')] = new_value
        return index

    update_data(value_='Argentina[50]', new_value='Argentina')
    update_data(value_='Morocco[43]', new_value='Morocco')
    update_data(value_='Argentina[50]', new_value='Argentina')
    update_data(value_='East Germany, West Germany[f]', new_value='Germany')
    update_data(value_='East Germany', new_value='Germany')
    update_data(value_='West Germany', new_value='Germany')
    update_data(value_='Rhodesia and Nyasaland', new_value='Rhodesia')

    #dropping rows that have non relevant incorrect data
    #index_nationality = name_nationality[name_nationality['Nationality']=='Nationality'].index.values
    name_nationality = name_nationality.drop([name_nationality.index[865], name_nationality.index[505]])
    
    
    #VISUALISATION
    #sum all drivers (units) into their nationalities 
    name_nationality = name_nationality.apply(name_nationality.value_counts).fillna(0)
    name_nationality = name_nationality.sort_values('Nationality')
    name_nationality = name_nationality.drop('count', 1)
    name_nationality = name_nationality.drop(name_nationality.index[0])  #weird 1 in the countries column with a 0 for count, deleting
    
    return name_nationality

driver_data = driver_data()

'''Functions'''
def top_driver_points_gauge():
    url = 'http://ergast.com/api/f1/current/DriverStandings.json'
    data = requests.get(url).json()
    points = int(data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]['points'])
    gname = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]['Driver']['givenName']
    fname = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]['Driver']['familyName']
    max_points = 23 * 25
    gauge = pn.indicators.Gauge(name=f'Top points:\n{gname} {fname}', value=points, bounds=(0, max_points), colors=[(0.8,'white'),(1,'red')], format='{value}pts')
    return gauge

def top_constructor_points_gauge():
    url = 'http://ergast.com/api/f1/current/ConstructorStandings.json'
    data = requests.get(url).json()
    points = int(data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings'][0]['points'])
    constructor = data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings'][0]['Constructor']['name']
    max_points = 23 * 25 + 23 * 18
    gauge = pn.indicators.Gauge(name=f'Top points:\n{constructor}', value=points, bounds=(0, max_points), colors=[(0.8,'white'),(1,'red')], format='{value}pts')
    return gauge

def time_to_next_race_gauge():
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
            next_race = dt.datetime.strptime(race['date'],'%Y-%m-%d')
            next_race_iso = next_race.isoformat()
            break
            
    # convert dates to numbers
    previous_race_val = dt.datetime.fromisoformat(previous_race).timestamp()
    next_race_val = dt.datetime.fromisoformat(next_race_iso).timestamp()
    now = dt.datetime.fromisoformat(today).timestamp()
    
    #calculate the percentage time till the next race from the previous race.
    pct_ttnr = round((((now-previous_race_val)/(next_race_val-previous_race_val)))*100, 2)
    
    gauge = pn.indicators.Gauge(name=f'Next Race', value=pct_ttnr, bounds=(0, 100), colors=[(0.8,'white'),(1,'red')], format=str(next_race.date()))
    
    return gauge

def pit_time_histogram():
    # multimodal data can be attributed to the modes of pit times ie: 1 stop for entire race vs 2 or 3 stops etc...
    histogram = pit_data.hvplot.hist(
        y='milliseconds',
        bins = 200,
        height=500,
        width=900
    )
    return histogram

def pit_pos():
    # take the average pit time for top 20 positions and plot with trendline (data becomes thin after the top 20)
    avg_pt_for_position = pit_data.groupby('position').mean().reset_index().head(20)
    scatter = px.scatter(
        avg_pt_for_position,
        x='position',
        y='milliseconds',
        trendline="ols",
        width = 1600,
        height = 500,
        
    )
    return scatter

def pit_pos_tracks():
    data_by_tracks = pit_data.groupby(['name','position']).filter(lambda x: len(x) > 5).groupby(['name','position']).mean().reset_index()
    scatter = data_by_tracks.hvplot.scatter(
        x='position',
        y='milliseconds',
        groupby='name',
        width = 900,
        height = 500,
        widget_location= 'top'
    )

    return scatter

def pit_improvements():
    improvements = pit_data.groupby('raceId').mean().reset_index()
    scatter = px.scatter(
        improvements,
        x='raceId',
        y='milliseconds',
        trendline="ols",
        width = 1600,
        height = 500,
        )
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

# Create function
def podium_country():
    # prepare podium data by country
    by_country = podium_data.loc[:,['Country','Podiums']].groupby('Country').sum().reset_index().sort_values('Podiums',ascending=True)
    by_country = by_country.sort_values(by = 'Podiums',ascending=False).nlargest(10,'Podiums')
    
    #plot podium data by country
    podium_finishes_country = px.bar(
        by_country,
        title='Top 10 F1 Podium Finishes by Country (1950 - 2018)',
        x='Podiums',
        orientation='h',
        y='Country',
        height = 500,
        color='Country').update_layout(showlegend=False)
    
    return podium_finishes_country

def podium_driver():
    # prepare podium data by driver data
    by_driver=podium_data.loc[:,['Driver','Podiums']].groupby('Driver').sum().reset_index().sort_values('Podiums',ascending=True)
    by_driver = by_driver.sort_values(by = 'Podiums',ascending=False).nlargest(20,'Podiums')
    
    #plot podium data by driver
    podium_finishes_driver = px.bar(
        by_driver,
        title='Top 20 F1 Podium Finishes by Driver (1950 - 2018)',
        x='Podiums',
        orientation='h',
        y='Driver',
        height = 500,
        color='Driver').update_layout(showlegend=False)
    
    return podium_finishes_driver

def constructor_sunburst():
    plot_constructor = px.sunburst(
        sunburst_data, path=['Year','City','Winning constructor'], 
        width=1000, 
        height=800, 
        color='Winning constructor', 
        hover_data=['Fastest lap','Pole position','Winning driver'],
        title='Winning Constructors by Year'
    )
    return plot_constructor

def driver_sunburst():
    plot_driver = px.sunburst(
        sunburst_data, 
        path=['Year','City','Fastest lap','Pole position','Winning driver'],
        width=1000, 
        height=800, 
        color='Winning driver', 
        hover_data=['Winning constructor'],
        color_discrete_map={'Lewis Hamilton':'black', 'Sebastian Vettel':'gold', 'Lewis Hamilton':'darkblue'},
        title='Winning Drivers by Year'
    )
    return plot_driver

# Create function
def world_circuit_map():
    '''World Map of F1 Circuits'''
    
    load_dotenv()
    map_box_api = os.getenv("mapbox")

    #Set the Mapbox API
    px.set_mapbox_access_token(map_box_api)
    
    #plot data to scatter mapbox
    plot =  px.scatter_mapbox(
        data_frame = master_circuits_cleaned,
        lat = 'Latitude',
        lon = 'Longitude',
        color = 'Name',
        mapbox_style = 'open-street-map',
        zoom = 1,
        size_max = 20,
        height = 800,
        width = 1450,
        hover_data = ['Last length used','Season(s)','N. races', 'Direction', 'Type'],
        title = 'F1 Circuit Locations Around the World'
    )
    return plot

def drivers_per_country():
    #plot bar chart
    fig,ax = plt.subplots(figsize=(12,10))
    
    driver_data.plot.bar(xlabel='Country', ylabel='Amount of Drivers', title='Drivers Per Country 1950-2022', figsize=(12,10), ax = ax)
    
    plt.close()
    
    return fig


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