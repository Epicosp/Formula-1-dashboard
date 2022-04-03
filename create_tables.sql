drop table if exists drivers cascade;
drop table if exists races cascade;
drop table if exists pitStops cascade;
drop table if exists driverStandings cascade;

--create drivers table--
create table drivers(
	driverId int primary key,
	driverRef varchar(255),
	number varchar(10),
	code varchar(3),
	forename varchar(255),
	surname varchar(255),
	dob date,
	nationality varchar(255),
	url varchar(255)
);

--create races table--
create table races(
	raceId int primary key not null,
	year int,
	round int,
	curcuitId int,
	name varchar(255),
	date varchar(255),
	time varchar(255),
	url varchar(255),
	col1 varchar(255),
	col2 varchar(255),
	col3 varchar(255),
	col4 varchar(255),
	col5 varchar(255),
	col6 varchar(255),
	col7 varchar(255),
	col8 varchar(255),
	col9 varchar(255),
	col10 varchar(255)
);

--create pit stops table--
create table pitStops(
	raceId int,
	foreign key (raceId) references races (raceId),
	driverId int,
	foreign key (driverId) references drivers (driverId),
	stop int,
	lap	int,
	time time,
	duration varchar(255),
	milliseconds int
);

--create driver standings table--
create table driverStandings(
	driverStandingsId int primary key not null,
	raceId int,
	foreign key (raceId) references races (raceId),
	driverId int,
	foreign key (driverId) references drivers (driverId),
	points float,
	position int,
	positionText varchar(255),
	wins int
);

-- drop filler columns that were nessecay for import of data --
alter table races
drop column col1,
drop column col2,
drop column col3,
drop column col4,
drop column col5,
drop column col6,
drop column col7,
drop column col8,
drop column col9,
drop column col10;