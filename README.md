# osm_stats_analyzer
On the Fly Stats Generator , Inspired from [Insights](https://github.com/hotosm/insights)

1. Generates Stats on Country Level for countries Supported on http://download.geofabrik.de/ using boundary as visualized
2. Generates stats like this :
```
{"uid": {"name": "your osm username", "changesets": 13, "nodes": {"create": 426, "modify": 1579, "delete": 0}, "ways": {"create": 67, "modify": 99, "delete": 0}, "relations": {"create": 0, "modify": 0, "delete": 0}, "building": {"create": 5, "modify": 0, "delete": 0}, "highway": {"create": 0, "modify": 0, "delete": 0}}
```

Example command to Run : 

```
python app.py --start_date 2023-01-01 --url "http://download.geofabrik.de/asia/nepal-updates" --username 'kshitijraj sharma' --password 'Bishalraj1' --tags 'building' 'highway' 'waterway' 'amenity' --out all_tags_stats
```

Benchmarks : 
Speed depends upon no of cores available on your CPU .
Generally on Normal i5 machine To process a year of data for country like Nepal it takes approx 3min .