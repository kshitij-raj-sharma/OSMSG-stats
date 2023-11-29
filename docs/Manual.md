### Example Commands

- To extract stats of last_hour for whole_world Using Planet Replication with specific tags

```
osmsg --url "https://planet.openstreetmap.org/replication/minute" --format csv --tags building highway waterway amenity --name stats --all_tags --last_hour
```

In order to extract for specific country just add --country with country name as in [data/countries.csv](./data/countries.csv) for eg : For Nepal : `--country Nepal`

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

  Processing geofabrik country based osm change files are faster as they will have changes only for country and smaller in size , or you can pass --country parameter and pass id from data/countries.csv

```
osmsg --start_date "2022-01-01 00:00:00+00:00" --url "http://download.geofabrik.de/asia/nepal-updates" --username 'your osm username' --password 'user osm password' --tags 'building' 'highway' 'waterway' 'amenity'  --format csv
```

- To extract on-going mapathons statistics 

  Example of extract last 8 days of data for Turkey and Syria using hashtag smforst with geofabrik as source
  --summary will allow to divide and provide stats as summary sepearated by daily , You can use this to get both summary csv and user contribution csv ! 
```
osmsg --country turkey syria --username "OSM USERNAME" --password "OSM PASSWORD" --hashtags smforst --length highway --force --days 6 --tags building highway amenity waterway --all_tags --summary
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

3. For hashtag stats , planet changeset minute replication is by default for now (Found only this reliable source , couldn't find daily/monthly replication files) , Generating daily/weekly is feasible , To generate more than that you can supply multiple countries geofabrik urls so that script can go through only country changefiles as stated on example above for turkey and syria , similarly you can pass your countries url and generate monthly yearly etc or you can run osmsg one time for a year it will download and store osm files , and next time when you run it would avoid downloading and it can generate stats quicker

4. For Country stats , if you use the --country option : You can also pass country name id supported from data/countries.csv and it supports multiple countries at a time  if supplied , Name would be automatically translated to available geofabrik URL or You can pass your own URL eg :

```
osmsg --url "http://download.geofabrik.de/asia/nepal-updates" --username '${{ secrets.OSM_USERNAME }}' --password '${{ secrets.OSM_PASSWORD }}' --format csv --last_month --tags 'building' 'highway' 'waterway' 'amenity' --name last_month_stats  --all_tags
```
5. It is recommended use same dir for running osmsg because osmsg stores downloaded osm files to temp dir and it can be reused next time you run stats on same period , avoids downloading all again, for eg : I run some stats for #hashtag1 for last month , and i want to run again for #hashtag2 , osmsg will use same downloaded files and avoid downloading for second time if you use the same dir for running 

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