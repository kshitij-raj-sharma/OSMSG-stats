# OpenStreetMap Stats Generator

On the Fly Commandline Stats Generator for OpenStreetMap User Contributions

I tweet stats Every day/week/month for Global/Region and #hotosm hashtag at https://twitter.com/stats_osm and store them [here](/stats/)

Monitored stats are available under `stats`, Currently Bot monitors OSM as whole , hotosm hashtag , Nepal Country : weekly,monthly and yearly stats are stored in github and twitter

### Usage:
For installation & Local Setup follow [Installation](./docs/Installation.md)
```
osmsg [-h] [--start_date START_DATE] [--end_date END_DATE] [--username USERNAME]
             [--password PASSWORD] [--timezone {Nepal,UTC}] [--name NAME]
             [--country COUNTRY [COUNTRY ...]] [--tags TAGS [TAGS ...]]
             [--hashtags HASHTAGS [HASHTAGS ...]] [--length LENGTH [LENGTH ...]] [--force]
             [--field_mappers] [--meta] [--tm_stats] [--rows ROWS] [--users USERS [USERS ...]]
             [--workers WORKERS] [--url URL [URL ...]] [--last_week] [--last_day] [--last_month]
             [--last_year] [--last_hour] [--days DAYS] [--charts] [--summary] [--exact_lookup]
             [--changeset] [--all_tags] [--temp]
             [--format {csv,json,excel,image,text} [{csv,json,excel,image,text} ...]]
             [--read_from_metadata READ_FROM_METADATA] [--boundary BOUNDARY] [--update]
```

### Options:
Hit following command for listing out the option with their documentation
```
osmsg --help
```

### Features
It is a python package that processes osm files live and produces stats on the fly

1. It can Generate Stats on Country Level for countries based on geofabrik urls . Countries are available in [here](./data/countries.csv)
2. It can also take any other server replication changefile to extract stats (Tested with Geofabrik and Planet Replication)
3. Can Generate hashtag statistics
4. Supports multiple output formats , Visualize Automatic Stats Being Genarated [here](./stats/)
5. It can create summary charts automatically along with stats , Visualize them [here](./stats/Global/Daily/)
6. Can generate stats for any custom timestamp provided

```
{"name":"username","uid":uid,"changesets":1,"nodes.create":1071,"nodes.modify":2100,"nodes.delete":0,"ways.create":146,"ways.modify":69,"ways.delete":0,"relations.create":0,"relations.modify":1,"relations.delete":0,"building.create":138,"building.modify":11,"building.delete":0,"highway.create":5,"highway.modify":49,"highway.delete":0,"waterway.create":0,"waterway.modify":4,"waterway.delete":0,"amenity.create":0,"amenity.modify":3,"amenity.delete":0,"landuse.create":3,"landuse.modify":1,"landuse.delete":0,"natural.create":0,"natural.modify":3,"natural.delete":0,"total_map_changes":3387}
```

### Get Started :

- Extract Stat of last hour and visualize stats/charts
  
  By default replication is minute url.

```
osmsg --last_hour
```

- With Hashtags information

```
osmsg --last_hour --changeset
```

  
- Last week data with summary & all tags info and using day replication
```
osmsg --last_week --url day --summary --all_tags
```

For More , Follow [Manual](./docs/Manual.md)

### Contributing
Contributions are always welcome! Follow [Contributing Guidelines](./CONTRIBUTING.md) & Go through [Code of Conduct](./CODE_OF_CONDUCT.md)

### Version Control
Follow [Version Control Docs](./docs/Version_control.md)

### Request Stats Tracking on Github 
Follow [stats_request_docs](./docs/Request_Stats.md)
