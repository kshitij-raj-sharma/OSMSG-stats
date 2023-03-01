# OpenStreetMap Stats Generator

On the Fly Commandline Stats Generator for OpenStreetMap User Contributions

I tweet stats Every day/week/month for Global/Region and #hotosm hashtag at https://twitter.com/stats_osm and store them [here](/stats/)

Monitored stats are available under `stats`, Currently Bot monitors OSM as whole , hotosm hashtag , Nepal Country : weekly,monthly and yearly stats are stored in github and twitter

### Installation

- Install [osmium](https://github.com/osmcode/pyosmium) lib on your machine

```
pip install osmium
```

- Install osmsg

```
pip install osmsg
```

### Usage:

```
osmsg [-h] [--start_date START_DATE] [--end_date END_DATE] [--username USERNAME]
             [--password PASSWORD] [--timezone {Nepal,UTC}] [--name NAME] [--country COUNTRY]
             [--tags TAGS [TAGS ...]] [--hashtags HASHTAGS [HASHTAGS ...]]
             [--length LENGTH [LENGTH ...]] [--force] [--rows ROWS] [--workers WORKERS]
             [--url URL [URL ...]] [--last_week] [--last_day] [--last_month] [--last_year]
             [--last_hour] [--days DAYS] [--charts] [--summary] [--exact_lookup] [--changeset]
             [--all_tags] [--temp] [--exclude_date_in_name]
             [--format {csv,json,excel,image,text} [{csv,json,excel,image,text} ...]]
             [--read_from_metadata READ_FROM_METADATA]
```

### Options:

```
  -h, --help            show this help message and exit
  --start_date START_DATE
                        Start date in the format YYYY-MM-DD HH:M:Sz eg: 2023-01-28 17:43:09+05:45
  --end_date END_DATE   End date in the format YYYY-MM-DD HH:M:Sz eg: 2023-01-28 17:43:09+05:45
  --username USERNAME   Your OSM Username : Only required for Geofabrik Internal Changefiles
  --password PASSWORD   Your OSM Password : Only required for Geofabrik Internal Changefiles
  --timezone {Nepal,UTC}
                        Your Timezone : Currently Supported Nepal, Default : UTC
  --name NAME           Output stat file name
  --country COUNTRY     Country name to extract (get name from data/un_countries) : Only viable until
                        day stats since changeset replication is available for minute, avoid using
                        for geofabrik url since geofabrik already gives country level changefiles
  --tags TAGS [TAGS ...]
                        Additional stats to collect : List of tags key
  --hashtags HASHTAGS [HASHTAGS ...]
                        Hashtags Statistics to Collect : List of hashtags , Limited until daily stats
                        for now , Only lookups if hashtag is contained on the string , not a exact
                        string lookup on beta
  --length LENGTH [LENGTH ...]
                        Calculate length of osm features , Only Supported for way created features ,
                        Pass list of tags key to calculate eg : --length highway waterway , Unit is
                        in Meters
  --force               Force for the Hashtag Replication fetch if it is greater than a day interval
  --rows ROWS           No. of top rows to extract , to extract top 100 , pass 100
  --workers WORKERS     No. of Parallel workers to assign : Default is no of cpu available , Be aware
                        to use this max no of workers may cause overuse of resources
  --url URL [URL ...]   Your public list of OSM Change Replication URL , 'minute,hour,day' option by
                        default will translate to planet replciation url. You can supply multiple
                        urls for geofabrik country updates , Url should not have trailing / at the
                        end
  --last_week           Extract stats for last week
  --last_day            Extract Stats for last day
  --last_month          Extract Stats for last Month
  --last_year           Extract stats for last year
  --last_hour           Extract stats for Last hour
  --days DAYS           N nof of last days to extract , for eg if 3 is supplied script will generate
                        stats for last 3 days
  --charts              Exports Summary Charts along with stats
  --summary             Produces Summary.md file with summary of Run and also a summary.csv which will have summary of stats per day
  --exact_lookup        Exact lookup for hashtags to match exact hashtag supllied , without this
                        hashtag search will search for the existence of text on hashtags and comments
  --changeset           Include hashtag and country informations on the stats. It forces script to
                        process changeset replciation , Careful to use this since changeset
                        replication is minutely
  --all_tags            Extract statistics of all of the unique tags and its count
  --temp                Deletes downloaded osm files from machine after processing is done , if you
                        want to run osmsg on same files again keep this option turn off
  --exclude_date_in_name
                        By default from and to date will be added to filename , You can skip this
                        behaviour with this option
  --format {csv,json,excel,image,text} [{csv,json,excel,image,text} ...]
                        Stats output format
  --read_from_metadata READ_FROM_METADATA
                        Location of metadata to pick start date from previous run's end_date ,
                        Generally used if you want to run bot on regular interval using cron/service
```

It is a Simple python script processes osm files live and produces stats on the fly

1. It can Generate Stats on Country Level for countries . Countries are available in [here](./data/countries_un.csv)
2. It can also take any other server replication changefile to extract stats (Tested with Geofabrik and Planet Replication)
3. Can Generate hashtag statistics
4. Supports multiple output formats , Visualize Automatic Stats Being Genarated [here](./stats/)
5. It can create summary charts automatically along with stats , Visualize them [here](./stats/Global/Daily/)
6. Can generate stats for any custom timestamp provided

```
{"name":"username","uid":uid,"changesets":1,"nodes.create":1071,"nodes.modify":2100,"nodes.delete":0,"ways.create":146,"ways.modify":69,"ways.delete":0,"relations.create":0,"relations.modify":1,"relations.delete":0,"building.create":138,"building.modify":11,"building.delete":0,"highway.create":5,"highway.modify":49,"highway.delete":0,"waterway.create":0,"waterway.modify":4,"waterway.delete":0,"amenity.create":0,"amenity.modify":3,"amenity.delete":0,"landuse.create":3,"landuse.modify":1,"landuse.delete":0,"natural.create":0,"natural.modify":3,"natural.delete":0,"total_map_changes":3387}
```

### Start Right Away :

- Extract Stat of last hour and visualize stats/charts
  
  By default replication is minute url.

```
osmsg --last_hour --charts --changeset
```

### More Example Commands

- To extract stats of last_hour for whole_world Using Planet Replication with specific tags

```
osmsg --url "https://planet.openstreetmap.org/replication/minute" --format csv --tags building highway waterway amenity --name stats --all_tags --last_hour
```

In order to extract for specific country just add --country with country name as in [data/countries_un.csv](./data/countries_un.csv) for eg : For Nepal : `--country Nepal`

- To extract stats for last day whole world with all the tags and specified stat :
  
  You can either pass url "https://planet.openstreetmap.org/replication/day" itself or if you want to use planet default replciation url you can simply pass as : minute , day & hour , script will get url itself  
```
osmsg  --url day --format csv --last_day --name stats --all_tags
```

If you wish to have tags with specific count for key you can include them as `--tags "building" "highway" ` & add --country to extract specific country , if you use geofabrik country updates you don't need to use --country option

- To extract specific country with Geofabrik URL (extracts stats for 15 days custom date range)

```
export OSM_USERNAME="yourusername"
export OSM_PASSWORD="yourpassword"

osmsg  --url "http://download.geofabrik.de/asia/nepal-updates" --format csv --start_date "2023-01-15 00:00:00+00:00" --end_date "2023-01-30 00:00:00+00:00" --name all_tags_stats --all_tags
```

- To get stat of country for year with geofabrik replication:

  Example of nepal for year of 2022

  Processing geofabrik country based osm change files are faster as they will have changes only for country and smaller in size

```
osmsg --start_date "2022-01-01 00:00:00+00:00" --url "http://download.geofabrik.de/asia/nepal-updates" --username 'your osm username' --password 'user osm password' --tags 'building' 'highway' 'waterway' 'amenity'  --format csv
```

- To extract on-going mapathons statistics 

  Example of extract last 8 days of data for Turkey and Syria using hashtag smforst with geofabrik as source
  --summary will allow to divide and provide stats as summary sepearated by daily , You can use this to get both summary csv and user contribution csv ! 
```
osmsg --url http://download.geofabrik.de/europe/turkey-updates https://download.geofabrik.de/asia/syria-updates --username "OSM USERNAME" --password "OSM PASSWORD" --hashtags smforst --length highway --force --days 6 --tags building highway amenity waterway --all_tags --summary
```

- Extract mapathon stats for hashtag only 
  
  You can use --length to get length of created features , supported for way features along with count
```
osmsg --url minute --hashtags mymapathonhashtag1 hashtag2 --length highway --force --tags building highway amenity waterway --all_tags --summary --start_date "2023-01-15 00:00:00+00:00" --end_date "2023-01-15 11:59:00+00:00"
```
Or you can simply say --last_day like this , can use hour replication to avoid processing too many files 

```
osmsg --url hour --hashtags mymapathonhashtag1 hashtag2 --length highway --force --tags building highway amenity waterway --all_tags --summary --last_day
```

Check more commands examples inside `stats/` `stats_metadata.json`

Now start generating stats with above sample commands

### TIPS & Tricks of using OSMSG:

OSMSG uses/supports sources , --url provided on argument will be used for osm changefiles and for changeset it is default of planet replication/minute ( used for hashtag and country )

1. To process weekly / monthly or yearly stats , Using minute replication might take forever on small machines , You can use daily replication files `/replication/day` to process faster and avoid network download issues for small minute fiels

2. If you are generating stats for rightnow / past 10min / past 1 hour using specific timeframe , stick with minutely (Sometimes to reflect changes you made on stats , Planet may take few minutes)

3. For hashtag stats , planet changeset minute replication is by default for now (Found only this reliable source , couldn't find daily/monthly replication files) , Generating daily/weekly is only feasible , To generate more than that you can supply multiple countries geofabrik urls so that script can go through only country changefiles as stated on example above for turkey and syria , similarly you can pass your countries url and generate monthly yearly etc 

4. For Country stats , if you use the --country option : It will use the planet minutely changeset replication to determine the location of the cahngeset bbox centroid , which means to process larger time frame it might take time , to avoid this Use Geofabrik internal changefiles based on country , OSMSG Supports processing of those hence you can directly supply geofabrik changefiles url for country and produce yearly/monthly stats eg :

```
osmsg --url "http://download.geofabrik.de/asia/nepal-updates" --username '${{ secrets.OSM_USERNAME }}' --password '${{ secrets.OSM_PASSWORD }}' --format csv --last_month --tags 'building' 'highway' 'waterway' 'amenity' --name last_month_stats  --all_tags
```

### Benchmarks :

Speed depends upon no of cores available on your CPU and your internet speed
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
