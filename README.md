# osm_stats_analyzer
On the Fly Stats Generator , Inspired from [Insights](https://github.com/hotosm/insights)

1. It can Generate Stats on Country Level for countries Supported on http://download.geofabrik.de/ using boundary as visualized 
2. It can also take any other server replication changefile to extract stats 
2. Generates stats like this :
```
{"name":"username","uid":uid,"changesets":1,"nodes.create":1071,"nodes.modify":2100,"nodes.delete":0,"ways.create":146,"ways.modify":69,"ways.delete":0,"relations.create":0,"relations.modify":1,"relations.delete":0,"building.create":138,"building.modify":11,"building.delete":0,"highway.create":5,"highway.modify":49,"highway.delete":0,"waterway.create":0,"waterway.modify":4,"waterway.delete":0,"amenity.create":0,"amenity.modify":3,"amenity.delete":0,"landuse.create":3,"landuse.modify":1,"landuse.delete":0,"natural.create":0,"natural.modify":3,"natural.delete":0,"total_map_changes":3387}
```

Example command to get stat of Nepal for 2022 to now : 

```
python app.py --start_date 2022-01-01 --url "http://download.geofabrik.de/asia/nepal-updates" --username 'your osm username' --password 'user osm password' --tags 'building' 'highway' 'waterway' 'amenity' --out all_tags_stats
```

Example command to get stat of a day for whole world :

```
python app.py --start_date 2023-01-01 --end_date 2023-01-02 --url "https://planet.openstreetmap.org/replication/day" --username 'your osm username' --password 'your password' --tags 'building' 'highway' 'waterway' 'amenity' 'landuse' 'natural' --name all_tags_stats --output csv
```

Benchmarks : 
Speed depends upon no of cores available on your CPU .
Generally on Normal i5 machine To process a year of data for country like Nepal it takes approx 3min .

Installation 

- Install osmium lib
- Clone the repo , install requirements and enjoy