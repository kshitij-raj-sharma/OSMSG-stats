# OpenStreetMap Stats Generator

On the Fly Commandline Stats Generator for OpenStreetMap User Contributions

I tweet stats Every day/week/month for Global/Region and #hotosm hashtag at https://twitter.com/stats_osm and store them [here](/stats/)

Monitored Country's stats are available under `stats`, For now Monitored countries are : `Nepal` , weekly,monthly and yearly stats are stored in github and twitter for sure

usage:

```
osmsg [-h] [--start_date START_DATE] [--end_date END_DATE] [--username USERNAME]
             [--password PASSWORD] [--timezone {Nepal,UTC}] [--name NAME]
             [--tags TAGS [TAGS ...]] [--hashtags HASHTAGS [HASHTAGS ...]] [--force]
             [--rows ROWS] --url URL [--extract_last_week] [--extract_last_day]
             [--extract_last_month] [--extract_last_year] [--extract_last_hour]
             [--wild_tags] [--exclude_date_in_name]
             [--format {csv,json,excel,image,text} [{csv,json,excel,image,text} ...]]
             [--read_from_metadata READ_FROM_METADATA]
```

options:

```
  -h, --help            show this help message and exit
  --start_date START_DATE
                        Start date in the format YYYY-MM-DD
  --end_date END_DATE   End date in the format YYYY-MM-DD
  --username USERNAME   Your OSM Username : Only required for Geofabrik Internal
                        Changefiles
  --password PASSWORD   Your OSM Password : Only required for Geofabrik Internal
                        Changefiles
  --timezone {Nepal,UTC}
                        Your Timezone : Currently Supported Nepal, Default : UTC
  --name NAME           Output stat file name
  --tags TAGS [TAGS ...]
                        Additional stats to collect : List of tags key
  --hashtags HASHTAGS [HASHTAGS ...]
                        Hashtags Statstics to Collect : List of hashtags , Limited until
                        daily stats for now
  --force               Force for the Hashtag Replication fetch if it is greater than a day
                        interval
  --rows ROWS           No fo top rows to extract , to extract top 100 , pass 100
  --url URL             Your public Geofabrik Download URL
  --extract_last_week
  --extract_last_day
  --extract_last_month
  --extract_last_year
  --extract_last_hour
  --wild_tags           Extract statistics of all of the unique tags and its count
  --exclude_date_in_name
                        By default from and to date will be added to filename , You can
                        skip this behaviour with this option
  --format {csv,json,excel,image,text} [{csv,json,excel,image,text} ...]
                        Stats output format
  --read_from_metadata READ_FROM_METADATA
                        Location of metadata to pick start date from previous run's
                        end_date , Generally used if you want to run bot on regular
                        interval using cron/service
```

It is a Simple python script processes osm files live and produces stats with use of databases

1. It can Generate Stats on Country Level for countries Supported on http://download.geofabrik.de/ using boundary as visualized
2. It can also take any other server replication changefile to extract stats
3. Generates stats like this :

```
{"name":"username","uid":uid,"changesets":1,"nodes.create":1071,"nodes.modify":2100,"nodes.delete":0,"ways.create":146,"ways.modify":69,"ways.delete":0,"relations.create":0,"relations.modify":1,"relations.delete":0,"building.create":138,"building.modify":11,"building.delete":0,"highway.create":5,"highway.modify":49,"highway.delete":0,"waterway.create":0,"waterway.modify":4,"waterway.delete":0,"amenity.create":0,"amenity.modify":3,"amenity.delete":0,"landuse.create":3,"landuse.modify":1,"landuse.delete":0,"natural.create":0,"natural.modify":3,"natural.delete":0,"total_map_changes":3387}
```

Example command to get stat of Nepal for 2022 to now :

```
osmsg --start_date 2022-01-01 --url "http://download.geofabrik.de/asia/nepal-updates" --username 'your osm username' --password 'user osm password' --tags 'building' 'highway' 'waterway' 'amenity' --name all_tags_stats --format csv
```

Example command to get stat of a day for whole world :

```
osmsg --start_date 2023-01-01 --end_date 2023-01-02 --url "https://planet.openstreetmap.org/replication/day" --username 'your osm username' --password 'your password' --tags 'building' 'highway' 'waterway' 'amenity' 'landuse' 'natural' --name all_tags_stats --format csv
```

Check more commands examples inside `stats/` `stats_metadata.json`

Benchmarks :
Speed depends upon no of cores available on your CPU .
Generally on Normal i5 machine To process a year of data for country like Nepal it takes approx 3min .

Installation

- Install [osmium](https://github.com/osmcode/pyosmium) lib
- Instal osmsg

```
pip install osmsg
```

### OSM LOGIN info

OSM Username and Password are not Mandatory , They are only required if you want to use geofabrik internal changefiles , There are two options you can either pass your username password on command line or export those in your env variable and script will pick it from there so that you don't need to pass your username and password to command itself like this.

```
export OSM_USERNAME="yourusername"
export OSM_PASSWORD="yourpassword"
```

Now use command as it is without username and password , OSM Login is enabled from Geofabrik [itself](https://github.com/geofabrik/sendfile_osm_oauth_protector) So OSMSG Doesn't uses any third party tool/methododology for the authentication

##### Note :

This project is under active development hence you may notice bugs or incomplete functions , Feel free to file issue or Contribute . Happy Coding ! Happy Mapping
