# OpenStreetMap Stats Generator

On the Fly Commandline Stats Generator for OpenStreetMap User Contributions

I tweet stats Every day/week/month for Global/Region and #hotosm hashtag at https://twitter.com/stats_osm and store them [here](/stats/)

Monitored Country's stats are available under `stats`, For now Monitored countries are : `Nepal` , weekly,monthly and yearly stats are stored in github and twitter for sure

### Installation

- Install [osmium](https://github.com/osmcode/pyosmium) lib on your machine

```
pip install osmium
```

- Instal osmsg

```
pip install osmsg
```

### Usage:

```
osmsg [-h] [--start_date START_DATE] [--end_date END_DATE] [--username USERNAME] [--password PASSWORD] [--timezone {Nepal,UTC}]
             [--name NAME] [--country COUNTRY] [--tags TAGS [TAGS ...]] [--hashtags HASHTAGS [HASHTAGS ...]] [--force] [--rows ROWS]
             [--workers WORKERS] [--url URL] [--extract_last_week] [--extract_last_day] [--extract_last_month] [--extract_last_year]
             [--extract_last_hour] [--wild_tags] [--exclude_date_in_name] [--format {csv,json,excel,image,text} [{csv,json,excel,image,text} ...]]
             [--read_from_metadata READ_FROM_METADATA]
```

### Options:

```
  -h, --help            show this help message and exit
  --start_date START_DATE
                        Start date in the format YYYY-MM-DD HH:M:Sz eg: 2023-01-28 17:43:09+05:45
  --end_date END_DATE   End date in the format YYYY-MM-DD HH:M:Sz eg:2023-01-28 17:43:09+05:45
  --username USERNAME   Your OSM Username : Only required for Geofabrik Internal Changefiles
  --password PASSWORD   Your OSM Password : Only required for Geofabrik Internal Changefiles
  --timezone {Nepal,UTC}
                        Your Timezone : Currently Supported Nepal, Default : UTC
  --name NAME           Output stat file name
  --country COUNTRY     Country name to extract (get name from data/un_countries) : Only viable until day stats since changeset replication is
                        available for minute, avoid using for geofabrik url since geofabrik already gives country level changefiles
  --tags TAGS [TAGS ...]
                        Additional stats to collect : List of tags key
  --hashtags HASHTAGS [HASHTAGS ...]
                        Hashtags Statstics to Collect : List of hashtags , Limited until daily stats for now
  --force               Force for the Hashtag Replication fetch if it is greater than a day interval
  --rows ROWS           No. of top rows to extract , to extract top 100 , pass 100
  --workers WORKERS     No. of Parallel workers to assign : Default is no of cpu available , Be aware to use this max no of workers may cause
                        overuse of resources
  --url URL             Your public OSM Change Replication URL
  --extract_last_week
  --extract_last_day
  --extract_last_month
  --extract_last_year
  --extract_last_hour
  --wild_tags           Extract statistics of all of the unique tags and its count
  --exclude_date_in_name
                        By default from and to date will be added to filename , You can skip this behaviour with this option
  --format {csv,json,excel,image,text} [{csv,json,excel,image,text} ...]
                        Stats output format
  --read_from_metadata READ_FROM_METADATA
                        Location of metadata to pick start date from previous run's end_date , Generally used if you want to run bot on regular
                        interval using cron/service
```

It is a Simple python script processes osm files live and produces stats on the fly

1. It can Generate Stats on Country Level for countries . Countries are available in [here](./data/countries_un.csv)
2. It can also take any other server replication changefile to extract stats (Tested with Geofabrik and Planet Replication)
3. Can Generate hashtag statistics
4. Generates stats like this : or Visualize those as csv [here](./stats/)

```
{"name":"username","uid":uid,"changesets":1,"nodes.create":1071,"nodes.modify":2100,"nodes.delete":0,"ways.create":146,"ways.modify":69,"ways.delete":0,"relations.create":0,"relations.modify":1,"relations.delete":0,"building.create":138,"building.modify":11,"building.delete":0,"highway.create":5,"highway.modify":49,"highway.delete":0,"waterway.create":0,"waterway.modify":4,"waterway.delete":0,"amenity.create":0,"amenity.modify":3,"amenity.delete":0,"landuse.create":3,"landuse.modify":1,"landuse.delete":0,"natural.create":0,"natural.modify":3,"natural.delete":0,"total_map_changes":3387}
```

### Example Commands

- To extract stats of last_hour for whole_world Using Planet Replication

```
osmsg --url "https://planet.openstreetmap.org/replication/minute" --format csv --tags building highway waterway amenity --name stats --wild_tags --extract_last_hour  --name nepal_stats
```

In order to extract for specific country just add --country with country name as in [data/countries_un.csv](./data/countries_un.csv) for eg : For Nepal : `--country Nepal`

- To extract stats for last day whole world :

```
osmsg  --url "https://planet.openstreetmap.org/replication/day" --format csv --extract_last_day --tags 'building' 'highway' 'waterway' 'amenity' --name stats --wild_tags
```

add --country to extract specific country

- To extract specific country with Geofabrik URL (extracts stats for 15 days custom date range)

```
export OSM_USERNAME="yourusername"
export OSM_PASSWORD="yourpassword"

osmsg  --url "http://download.geofabrik.de/asia/nepal-updates" --format csv --start_date "2023-01-15 00:00:00+00:00" --end_date "2023-01-30 00:00:00+00:00" --tags 'building' 'highway' 'waterway' 'amenity' --name stats --wild_tags
```

- To get stat of Nepal for 2022 to now with geofabrik replication:

  Processing geofabrik country based osm change files are faster as they will have changes only for country and smaller in size

```
osmsg --start_date 2022-01-01 --url "http://download.geofabrik.de/asia/nepal-updates" --username 'your osm username' --password 'user osm password' --tags 'building' 'highway' 'waterway' 'amenity' --name all_tags_stats --format csv
```

Check more commands examples inside `stats/` `stats_metadata.json`

Now start generating stats with above sample commands

### TIPS & Tricks of using OSMSG:

OSMSG uses/supports sources , --url provided on argument will be used for osm changefiles and for changeset it is default of planet replication/minute ( used for hashtag and country )

1. To process weekly / monthly or yearly stats , Using minute replication might take forever on small machines , You can use daily replication files `/replication/day` to process faster and avoid network download issues for small minute fiels

2. If you are generating stats for rightnow / past 10min / past 1 hour using specific timeframe , stick with minutely (Sometimes to reflect changes you made on stats , Planet may take few minutes)

3. For hashtag stats , planet changeset minute replication is by default for now (Found only this reliable source , couldn't find daily/monthly replication files) , Generating daily/weekly is only feasible

4. For Country stats , if you use the --country option : It will use the planet minutely changeset replication to determine the location of the cahngeset bbox centroid , which means to process larger time frame it might take time , to avoid this Use Geofabrik internal changefiles based on country , OSMSG Supports processing of those hence you can directly supply geofabrik changefiles url for country and produce yearly/monthly stats eg :

```
osmsg --url "http://download.geofabrik.de/asia/nepal-updates" --username '${{ secrets.OSM_USERNAME }}' --password '${{ secrets.OSM_PASSWORD }}' --format csv --extract_last_month --tags 'building' 'highway' 'waterway' 'amenity' --name last_month_stats  --wild_tags
```

### Benchmarks :

Speed depends upon no of cores available on your CPU .
Generally on Normal i5 machine To process a year of data for country like Nepal it takes approx 3min .

### OSM LOGIN info

OSM Username and Password are not Mandatory , They are only required if you want to use geofabrik internal changefiles , There are two options you can either pass your username password on command line or export those in your env variable and script will pick it from there so that you don't need to pass your username and password to command itself like this.

```
export OSM_USERNAME="yourusername"
export OSM_PASSWORD="yourpassword"
```

Now use command as it is without username and password , OSM Login is enabled from Geofabrik [itself](https://github.com/geofabrik/sendfile_osm_oauth_protector) So OSMSG Doesn't uses any third party tool/methododology for the authentication

##### Note :

This project is under active development hence you may notice bugs or incomplete functions , Feel free to file issue or Contribute . Happy Coding ! Happy Mapping
