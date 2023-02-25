import argparse
import concurrent.futures
import datetime as dt
import gzip
import json
import os
import re
import shutil
import sys
import time
import humanize
from datetime import datetime

import dataframe_image as dfi
import geopandas as gpd
import osmium
import pandas as pd
import requests
from osmium.replication.server import ReplicationServer
from shapely.geometry import box
from tqdm import tqdm

from osmsg.utils import create_charts, create_profile_link, verify_me_osm,sum_tags

from .changefiles import (
    get_prev_hour,
    get_prev_year_dates,
    in_local_timezone,
    previous_day,
    previous_month,
    previous_week,
    seq_to_timestamp,
    strip_utc,
)
from .changesets import ChangesetToolKit

users_temp = {}
users = {}
hashtag_changesets = {}
countries_changesets = {}

# read the GeoJSON file
countries_df = gpd.read_file(
    "https://raw.githubusercontent.com/kshitijrajsharma/OSMSG/master/data/countries_un.geojson"
)


def collect_changefile_stats(user, uname, changeset, version, tags, osm_type):
    tags_to_collect = list(additional_tags) if additional_tags else None
    if version == 1:
        action = "create"
    if version > 1:
        action = "modify"
    if version == 0:
        action = "delete"
    if user in users:
        users[user]["name"] = uname
        users[user]["uid"] = user
        if changeset not in users_temp[user]["changesets"]:
            users_temp[user]["changesets"].append(changeset)
        users[user]["changesets"] = len(users_temp[user]["changesets"])
        if hashtags or changeset:
            try:
                for ch in hashtag_changesets[changeset]["countries"]:
                    if ch not in users[user]["countries"]:
                        users[user]["countries"].append(ch)
                for ch in hashtag_changesets[changeset]["hashtags"]:
                    if ch not in users[user]["hashtags"]:
                        users[user]["hashtags"].append(ch)
            except:
                pass

        users[user][osm_type][action] += 1
        if osm_type == "nodes" and tags:
            if action != "delete":
                users[user]["poi"][action] += 1
        if all_tags:
            if tags:
                for key, value in tags:
                    if action != "delete":  # we don't need deleted tags
                        if key in users[user][f"tags_{action}"]:
                            users[user][f"tags_{action}"][key] += 1
                        else:
                            users[user][f"tags_{action}"][key] = 1

        if tags_to_collect:
            if action != "delete":  # we don't need deleted tags
                for tag in tags_to_collect:
                    if tag in tags:
                        users[user][tag][action] += 1
        if country:
            if not hashtags:
                for ch in countries_changesets[changeset]:
                    if ch not in users[user]["hashtags"]:
                        users[user]["hashtags"].append(ch)


    else:
        users[user] = {
            "name": uname,
            "uid": user,
            "changesets": 0,
            "nodes": {"create": 0, "modify": 0, "delete": 0},
            "ways": {"create": 0, "modify": 0, "delete": 0},
            "relations": {"create": 0, "modify": 0, "delete": 0},
            "poi": {"create": 0, "modify": 0},  # nodes that has tags
        }
        if hashtags or changeset:
            users[user]["countries"] = []
            users[user]["hashtags"] = []

            try:
                users[user]["countries"] = hashtag_changesets[changeset]["countries"]
                users[user]["hashtags"] = hashtag_changesets[changeset]["hashtags"]
            except:
                pass

        if tags_to_collect:
            for tag in tags_to_collect:
                users[user][tag] = {"create": 0, "modify": 0}
        users_temp[user] = {"changesets": []}
        if changeset not in users_temp[user]["changesets"]:
            users_temp[user]["changesets"].append(changeset)
        users[user]["changesets"] = len(users_temp[user]["changesets"])
        users[user][osm_type][action] = 1
        if all_tags:
            users[user]["tags_create"] = {}
            users[user]["tags_modify"] = {}
            if tags:
                for tag, value in tags:
                    users[user][f"tags_{action}"][tag] = 1
        if tags_to_collect:
            for tag in tags_to_collect:
                if tag in tags:
                    users[user][tag][action] = 1
        if country:
            if not hashtags:
                users[user]["hashtags"] = countries_changesets[changeset]


def calculate_stats(user, uname, changeset, version, tags, osm_type):
    if (hashtags and country) or hashtags:  # intersect with changesets
        if (
            len(hashtag_changesets) > 0
        ):  # make sure there are changesets to intersect if not meaning hashtag changeset not found no need to go for changefiles
            if country : 
                if changeset in hashtag_changesets.keys() and changeset in countries_changesets.keys():
                    collect_changefile_stats(user, uname, changeset, version, tags, osm_type)
            else: 
                if changeset in hashtag_changesets.keys(): 
                    collect_changefile_stats(
                    user, uname, changeset, version, tags, osm_type
                )
    elif country:
        if len(countries_changesets) > 0:
            if changeset in countries_changesets.keys():
                collect_changefile_stats(
                    user, uname, changeset, version, tags, osm_type
                )
    else:  # collect everything
        collect_changefile_stats(user, uname, changeset, version, tags, osm_type)


class ChangesetHandler(osmium.SimpleHandler):
    def __init__(self):
        super(ChangesetHandler, self).__init__()

    def changeset(self, c):
        run_hashtag_check_logic = False
        if changeset and not hashtags:
            if "comment" in c.tags:
                run_hashtag_check_logic = True
        if hashtags:
            if "comment" in c.tags:
                if exact_lookup:
                    hashtags_comment = re.findall(r"#[\w-]+", c.tags["comment"])
                    if any(
                        elem.lower() in map(str.lower, hashtags_comment)
                        for elem in hashtags
                    ):
                        run_hashtag_check_logic = True
                elif any(
                    elem.lower() in c.tags["comment"].lower() for elem in hashtags
                ):
                    run_hashtag_check_logic = True

        if run_hashtag_check_logic:
            if c.id not in hashtag_changesets.keys():
                hashtag_changesets[c.id] = {"hashtags": [], "countries": []}
                # get bbox
                bounds = str(c.bounds)
                if "invalid" not in bounds:
                    bbox_list = bounds.strip("()").split(" ")
                    minx, miny = bbox_list[0].split("/")
                    maxx, maxy = bbox_list[1].split("/")
                    bbox = box(float(minx), float(miny), float(maxx), float(maxy))
                    # Create a point for the centroid of the bounding box
                    centroid = bbox.centroid
                    intersected_rows = countries_df[countries_df.intersects(centroid)]
                    hashtags_comment = re.findall(r"#[\w-]+", c.tags["comment"])
                    for hash_tag in hashtags_comment:
                        if hash_tag not in hashtag_changesets[c.id]["hashtags"]:
                            hashtag_changesets[c.id]["hashtags"].append(hash_tag)
                    for i, row in intersected_rows.iterrows():
                        if row["name"] not in hashtag_changesets[c.id]["countries"]:
                                hashtag_changesets[c.id]["countries"].append(
                                    row["name"]
                                )

        if country:
            if c.bounds:
                bounds = str(c.bounds)
                if "invalid" not in bounds:
                    bbox_list = bounds.strip("()").split(" ")

                    minx, miny = bbox_list[0].split("/")
                    maxx, maxy = bbox_list[1].split("/")

                    bbox = box(float(minx), float(miny), float(maxx), float(maxy))
                    # Create a point for the centroid of the bounding box
                    centroid = bbox.centroid
                    intersected_rows = countries_df[
                        countries_df.intersects(centroid)
                    ]
                    for i, row in intersected_rows.iterrows():

                        if row["name"] == country:
                            if c.id not in countries_changesets.keys():
                                countries_changesets[c.id] = []
                            if "comment" in c.tags:
                                hashtags_comment = re.findall(
                                    r"#[\w-]+", c.tags["comment"]
                                )
                                for tag in hashtags_comment:
                                    if tag not in countries_changesets[c.id]:
                                        countries_changesets[c.id].append(tag)


class ChangefileHandler(osmium.SimpleHandler):
    def __init__(self):
        super(ChangefileHandler, self).__init__()

    def node(self, n):
        if n.timestamp >= start_date_utc and n.timestamp <= end_date_utc:
            version = n.version
            if n.deleted:
                version = 0
            calculate_stats(n.uid, n.user, n.changeset, version, n.tags, "nodes")

    def way(self, w):
        if w.timestamp >= start_date_utc and w.timestamp <= end_date_utc:
            version = w.version
            if w.deleted:
                version = 0
            calculate_stats(w.uid, w.user, w.changeset, version, w.tags, "ways")

    def relation(self, r):
        if r.timestamp >= start_date_utc and r.timestamp <= end_date_utc:
            version = r.version
            if r.deleted:
                version = 0
            calculate_stats(r.uid, r.user, r.changeset, version, r.tags, "relations")


def process_changefiles(url):
    # Check that the request was successful
    # Send a GET request to the URL
    if "minute" not in url:
        print(f"Processing {url}")

    url_splitted_list = url.split("/")
    temp_path = os.path.join(os.getcwd(), "temp/changefiles")

    file_path = os.path.join(
        temp_path,
        f"{url_splitted_list[-3]}_{url_splitted_list[-2]}_{url_splitted_list[-1]}",
    )

    if not os.path.exists(file_path):
        # Read the cookies from the file

        if "geofabrik" in url.lower():
            cookies_fmt = {}
            test = cookies.split("=")
            # name, value = line.strip().split("=")
            cookies_fmt[test[0]] = f'{test[1]}=="'
            response = requests.get(url, cookies=cookies_fmt)
        else:
            response = requests.get(url)

        if not response.status_code == 200:
            sys.exit()

        file_data = response.content

        with open(file_path, "wb") as f:
            f.write(file_data)

    # Open the .osc.gz file in read-only mode
    handler = ChangefileHandler()
    with gzip.open(file_path, "rb") as f_in, open(file_path[:-3], "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    handler.apply_file(file_path[:-3])


def process_changesets(url):
    # print(f"Processing {url}")
    url_splitted_list = url.split("/")
    temp_path = os.path.join(os.getcwd(), "temp/changesets")

    file_path = os.path.join(
        temp_path,
        f"{url_splitted_list[-3]}_{url_splitted_list[-2]}_{url_splitted_list[-1]}",
    )
    if not os.path.exists(file_path):

        response = requests.get(url)
        if not response.status_code == 200:
            sys.exit()

        file_data = response.content

        with open(file_path, "wb") as f:
            f.write(file_data)

    # Open the .osc.gz file in read-only mode

    handler = ChangesetHandler()
    with gzip.open(file_path, "rb") as f_in, open(file_path[:-3], "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    handler.apply_file(file_path[:-3])
    # print(f"Finished {url}")


def get_download_urls_changefiles(
    start_date, end_date, base_url, timezone, scan_early_seq=False
):
    repl = ReplicationServer(base_url)

    # Gets sequence id using timestamp we get from osm api using pyosmium tool
    seq = repl.timestamp_to_sequence(start_date)
    # going one step back to cover all changes only if it is not already behind
    start_seq_time = seq_to_timestamp(repl.get_state_url(seq), timezone)
    if scan_early_seq or (start_date - start_seq_time).days < 1:
        if "minute" in base_url:
            seq = (
                seq + int((start_date - start_seq_time).total_seconds() / 60)
            ) - 60  # go 60 min earlier
        elif "hour" in base_url:
            seq = (
                seq + int(((start_date - start_seq_time).total_seconds() / 60)/60)
            ) - 1  # go 1 hour earlier

    start_seq = seq
    start_seq_url = repl.get_state_url(start_seq)

    if seq is None:
        print(
            "Cannot reach the configured replication service '%s'.\n"
            "Does the URL point to a directory containing OSM update data?",
            base_url,
        )
        sys.exit()

    state_info = repl.get_state_info()  # gets current sequence / timestamp

    if state_info is None:
        # couldn't fetch state info from server
        sys.exit()

    server_seq, server_ts = state_info
    server_ts = server_ts.astimezone(dt.timezone.utc)
    last_seq = server_seq
    if end_date:
        end_date_seq = repl.timestamp_to_sequence(end_date)
        last_seq = end_date_seq
        if "minute" in base_url:
            last_seq = (
                last_seq
                + int(
                    (
                        seq_to_timestamp(repl.get_state_url(end_date_seq), timezone)
                        - end_date
                    ).total_seconds()
                    / 60
                )
            ) + 60  # go 1 hours later
        else:
            last_seq += 1 # go 1 sequence later
        if last_seq >= server_seq:
            last_seq = server_seq

    print(
        # f"You have supplied {start_date} : {seq} to {last_ts} : {last_seq} . Latest Server Fetched is : {server_seq} & {in_local_timezone(server_ts,timezone)} on {base_url}\n
        f"Processing Changefiles from {seq_to_timestamp(repl.get_state_url(seq), timezone)} to {seq_to_timestamp(repl.get_state_url(last_seq), timezone)}"
    )

    if seq >= last_seq:
        print("Changefile : Already up-to-date.")
        sys.exit()

    download_urls = []
    end_seq_url = repl.get_state_url(last_seq)

    while seq <= last_seq:
        seq_url = repl.get_diff_url(seq)
        if "geofabrik" in base_url:
            # use internal server
            seq_url = repl.get_diff_url(seq).replace(
                "download.geofabrik", "osm-internal.download.geofabrik"
            )
        download_urls.append(seq_url)
        seq = seq + 1
    return download_urls, server_ts, start_seq, last_seq, start_seq_url, end_seq_url


def auth(username, password):
    print("Authenticating...")
    try:
        cookies = verify_me_osm(username, password)
    except Exception as ex:
        raise ValueError("OSM Authentication Failed")

    print("Authenticated !")
    return cookies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start_date",
        help="Start date in the format YYYY-MM-DD HH:M:Sz eg: 2023-01-28 17:43:09+05:45",
    )
    parser.add_argument(
        "--end_date",
        help="End date in the format YYYY-MM-DD HH:M:Sz eg: 2023-01-28 17:43:09+05:45",
        default=dt.datetime.now(),
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Your OSM Username : Only required for Geofabrik Internal Changefiles",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Your OSM Password : Only required for Geofabrik Internal Changefiles",
    )
    parser.add_argument(
        "--timezone",
        default="UTC",
        choices=["Nepal", "UTC"],
        help="Your Timezone : Currently Supported Nepal, Default : UTC",
    )

    parser.add_argument(
        "--name",
        default="stats",
        help="Output stat file name",
    )
    parser.add_argument(
        "--country",
        default=None,
        help="Country name to extract (get name from data/un_countries) : Only viable until day stats since changeset replication is available for minute, avoid using for geofabrik url since geofabrik already gives country level changefiles",
    )

    parser.add_argument(
        "--tags",
        nargs="+",
        type=str,
        help="Additional stats to collect : List of tags key",
    )

    parser.add_argument(
        "--hashtags",
        nargs="+",
        type=str,
        help="Hashtags Statistics to Collect : List of hashtags , Limited until daily stats for now , Only lookups if hashtag is contained on the string , not a exact string lookup on beta",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force for the Hashtag Replication fetch if it is greater than a day interval",
        default=False,
    )

    parser.add_argument(
        "--rows",
        type=int,
        help="No. of top rows to extract , to extract top 100 , pass 100",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="No. of Parallel workers to assign : Default is no of cpu available , Be aware to use this max no of workers may cause overuse of resources",
    )

    parser.add_argument(
        "--url",
        default="https://planet.openstreetmap.org/replication/minute",
        help="Your public OSM Change Replication URL ",
    )

    parser.add_argument(
        "--last_week",
        action="store_true",
        help="Extract stats for last week",
        default=False,
    )
    parser.add_argument(
        "--last_day",
        action="store_true",
        help="Extract Stats for last day",
        default=False,
    )
    parser.add_argument(
        "--last_month",
        action="store_true",
        help="Extract Stats for last Month",
        default=False,
    )
    parser.add_argument(
        "--last_year",
        action="store_true",
        help="Extract stats for last year",
        default=False,
    )
    parser.add_argument(
        "--last_hour",
        action="store_true",
        help="Extract stats for Last hour",
        default=False,
    )
    parser.add_argument(
        "--charts",
        action="store_true",
        help="Exports Summary Charts along with stats",
        default=False,
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Produces Summary.md file with summary of Run",
        default=False,
    )
    parser.add_argument(
        "--exact_lookup",
        action="store_true",
        help="Exact lookup for hashtags to match exact hashtag supllied , without this hashtag search will search for the existence of text on hashtags and comments",
        default=False,
    )

    parser.add_argument(
        "--changeset",
        help="Include hashtag and country informations on the stats. It forces script to process changeset replciation , Careful to use this since changeset replication is minutely",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--all_tags",
        action="store_true",
        help="Extract statistics of all of the unique tags and its count",
        default=False,
    )

    parser.add_argument(
        "--exclude_date_in_name",
        action="store_true",
        help="By default from and to date will be added to filename , You can skip this behaviour with this option",
        default=False,
    )

    parser.add_argument(
        "--format",
        nargs="+",
        choices=["csv", "json", "excel", "image", "text"],
        default="csv",
        help="Stats output format",
    )
    parser.add_argument(
        "--read_from_metadata",
        help="Location of metadata to pick start date from previous run's end_date , Generally used if you want to run bot on regular interval using cron/service",
    )

    args = parser.parse_args()
    if args.start_date:
        start_date = strip_utc(
            dt.datetime.strptime(args.start_date, "%Y-%m-%d %H:%M:%S%z"), args.timezone
        )

    if not args.start_date:
        if (
            args.last_week
            or args.last_day
            or args.last_month
            or args.last_year
            or args.last_hour
        ):
            pass
        else:
            print("ERR: Supply start_date")
            sys.exit()

    if args.end_date:
        end_date = args.end_date
        if not isinstance(end_date, datetime):
            end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d %H:%M:%S%z")

        end_date = strip_utc(end_date, args.timezone)
    if args.country:
        if not countries_df["name"].isin([args.country]).any():
            print("Country doesn't exists : Refer to data/countries_un.csv name column")
            sys.exit()
    if args.changeset:
        if args.hashtags or args.country:
            assert (
                args.changeset
            ), "You can not use include changeset meta option along with hashtags/country"

    start_time = time.time()

    global additional_tags
    global cookies
    global all_tags
    global hashtags
    global country
    global changeset
    global exact_lookup

    all_tags = args.all_tags
    additional_tags = args.tags
    hashtags = args.hashtags
    country = args.country
    cookies = None
    changeset = args.changeset
    exact_lookup = args.exact_lookup

    if "geofabrik" in args.url.lower():
        if args.username is None:
            args.username = os.environ.get("OSM_USERNAME")
        if args.password is None:
            args.password = os.environ.get("OSM_PASSWORD")

        if not (args.username and args.password):
            assert (
                args.username and args.password
            ), "OSM username and password are required for geofabrik url"
        cookies = auth(args.username, args.password)
    print("Script Started")

    if args.last_hour:
        start_date, end_date = get_prev_hour(args.timezone)

    if args.last_year:
        start_date, end_date = get_prev_year_dates(args.timezone)

    if args.last_month:
        start_date, end_date = previous_month(args.timezone)

    if args.last_day:
        start_date, end_date = previous_day(args.timezone)
    if args.last_week:
        start_date, end_date = previous_week(args.timezone)

    if args.read_from_metadata:
        if os.path.exists(args.read_from_metadata):
            with open(args.read_from_metadata, "r") as openfile:
                # Reading from json file
                meta_json = json.load(openfile)
            if "end_date" in meta_json:
                start_date = datetime.strptime(
                    meta_json["end_date"], "%Y-%m-%d %H:%M:%S%z"
                )

                print(f"Start date changed to {start_date} after reading from metajson")
            else:
                print("no end_date in meta json")
        else:
            print("couldn't read start_date from metajson")
    if start_date == end_date:
        print("Err: Start date and end date are equal")
        sys.exit()

    if (end_date - start_date).days > 1:
        if args.hashtags or args.country:
            print(
                "Warning : Replication for Changeset is minutely , To process more than a day data it might take a while, Consider supplying geofabrik country replication url for countries. Use --force to ignore this warning"
            )
            if not args.force:
                sys.exit()
    print(f"Supplied start_date: {start_date} and end_date: {end_date}")

    if args.hashtags or args.country or args.changeset:

        Changeset = ChangesetToolKit()
        (
            changeset_download_urls,
            changeset_start_seq,
            changeset_end_seq,
        ) = Changeset.get_download_urls(start_date, end_date)
        print(
            f"Processing Changeset from {strip_utc(Changeset.sequence_to_timestamp(changeset_start_seq),args.timezone)} to {strip_utc(Changeset.sequence_to_timestamp(changeset_end_seq),args.timezone)}"
        )

        temp_path = os.path.join(os.getcwd(), "temp/changesets")
        print(os.path.exists(temp_path))
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        max_workers = os.cpu_count() if not args.workers else args.workers
        print(f"Using {max_workers} Threads")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Use `map` to apply the `download_image` function to each element in the `urls` list
            for _ in tqdm(
                executor.map(process_changesets, changeset_download_urls),
                total=len(changeset_download_urls),
                unit_scale=True,
                unit="changesets",
                leave=True,
            ):
                pass
            # executor.shutdown(wait=True)

        print("Changeset Processing Finished")
        end_seq_timestamp = Changeset.sequence_to_timestamp(changeset_end_seq)
        if end_date > end_seq_timestamp:
            end_date = strip_utc(end_seq_timestamp, args.timezone)

    print("Changefiles : Generating Download Urls")
    (
        download_urls,
        server_ts,
        start_seq,
        end_seq,
        start_seq_url,
        end_seq_url,
    ) = get_download_urls_changefiles(start_date, end_date, args.url, args.timezone)
    if server_ts < end_date:
        print(
            f"Warning : End date data is not available at server, Changing to latest available date {server_ts}"
        )
        end_date = server_ts
        if start_date >= server_ts:
            print("Err: Data is not available after start date ")
            sys.exit()
    global end_date_utc
    global start_date_utc

    start_date_utc = start_date.astimezone(dt.timezone.utc)
    end_date_utc = end_date.astimezone(dt.timezone.utc)
    print(f"Final UTC Date time to filter stats : {start_date_utc} to {end_date_utc}")
    temp_path = os.path.join(os.getcwd(), "temp/changefiles")
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    # Use the ThreadPoolExecutor to download the images in parallel
    max_workers = os.cpu_count() if not args.workers else args.workers
    print(f"Using {max_workers} Threads")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Use `map` to apply the `download_image` function to each element in the `urls` list
        # executor.map(process_changefiles, download_urls)
        for _ in tqdm(
            executor.map(process_changefiles, download_urls),
            total=len(download_urls),
            unit_scale=True,
            unit="changefiles",
            leave=True,
        ):
            pass

        # executor.shutdown(wait=True)
    print("Changefiles Processing Finished")
    os.chdir(os.getcwd())
    shutil.rmtree("temp")
    if len(users) >= 1:
        # print(users)
        if args.all_tags:
            for user in users:
                users[user]["tags_create"] = json.dumps(
                    dict(
                        sorted(
                            users[user]["tags_create"].items(),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                    )
                )
                users[user]["tags_modify"] = json.dumps(
                    dict(
                        sorted(
                            users[user]["tags_modify"].items(),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                    )
                )

        df = pd.json_normalize(list(users.values()))

        if hashtags or changeset:
            df["countries"] = df["countries"].apply(lambda x: ",".join(map(str, x)))

        df = df.assign(
            changes=df["nodes.create"]
            + df["nodes.modify"]
            + df["nodes.delete"]
            + df["ways.create"]
            + df["ways.modify"]
            + df["ways.delete"]
            + df["relations.create"]
            + df["relations.modify"]
            + df["relations.delete"]
        )
        df.insert(3, "map_changes", df["changes"], True)
        df = df.drop(columns=["changes"])
        df = df.sort_values("map_changes", ascending=False)
        df.insert(0, "rank", range(1, len(df) + 1), True)
        if args.rows:
            df = df.head(args.rows)
        print(df)
        if args.all_tags:
            # Get the column names of the DataFrame
            cols = df.columns.tolist()
            # Identify the column names that you want to move
            cols_to_move = ["tags_create", "tags_modify"]
            # Remove the columns to move from the list of column names
            cols = [col for col in cols if col not in cols_to_move]
            # Add the columns to move to the end of the list of column names
            cols = cols + cols_to_move
            # Reindex the DataFrame with the new order of column names
            df = df.reindex(columns=cols)

        if country or hashtags or changeset:
            df["hashtags"] = df["hashtags"].apply(lambda x: ",".join(map(str, x)))
            column_to_move = "hashtags"
            df = df.assign(**{column_to_move: df.pop(column_to_move)})

        start_date = in_local_timezone(start_date_utc, args.timezone)
        end_date = in_local_timezone(end_date_utc, args.timezone)

        fname = f"{args.name}_{start_date}_{end_date}"
        if args.exclude_date_in_name:
            fname = args.name
        if "image" in args.format:  ### image used for twitter tweet
            # Convert the DataFrame to an image
            df_img = df.head(25)
            # Compute sums of specified columns for the top 20 rows
            created = df_img[["nodes.create", "ways.create", "relations.create"]].sum(
                axis=1
            )
            modified = df_img[["nodes.modify", "ways.modify", "relations.modify"]].sum(
                axis=1
            )
            deleted = df_img[["nodes.delete", "ways.delete", "relations.delete"]].sum(
                axis=1
            )
            # Concatenate original DataFrame and sums DataFrame
            result_df = pd.concat(
                [
                    df_img,
                    created.rename("Created"),
                    modified.rename("Modified"),
                    deleted.rename("Deleted"),
                ],
                axis=1,
            )

            cols_to_export = [
                "rank",
                "name",
                "changesets",
                "map_changes",
                "Created",
                "Modified",
                "Deleted",
            ]  # Specify columns to export
            result_df = result_df.reset_index(drop=True)

            dfi.export(
                result_df[cols_to_export],
                "top_users.png",
                max_cols=-1,
                max_rows=-1,
            )

        if "json" in args.format:
            # with open(f"{out_file_name}.json") as file:
            #     file.write(json.dumps(users))
            df.to_json(f"{fname}.json", orient="records")
        if "csv" in args.format:
            # Add the start_date and end_date columns to the DataFrame
            csv_df = df
            csv_df["start_date"] = start_date_utc
            csv_df["end_date"] = end_date_utc

            # Create profile link column
            csv_df.insert(2, "profile", csv_df["name"].apply(create_profile_link))

            csv_df.to_csv(f"{fname}.csv", index=False)
        if "excel" in args.format:
            df.to_excel(f"{fname}.xlsx", index=False)        

        if "text" in args.format:
            text_output = df.to_markdown(tablefmt="grid", index=False)
            with open(f"{fname}.txt", "w", encoding="utf-8") as file:
                file.write(
                    f"User Contributions From {start_date} to {end_date} . Planet Source File : {args.url}\n "
                )
                file.write(text_output)
        

        if args.charts:
            if 'geofabrik' in args.url.lower():
                df.drop('countries', axis='columns')
            create_charts(df)
        
        if args.summary:
            created_sum = df['nodes.create'] + df['ways.create'] + df['relations.create']
            modified_sum = df['nodes.modify'] + df['ways.modify'] + df['relations.modify']
            deleted_sum = df['nodes.delete'] + df['ways.delete'] + df['relations.delete']


            # Get the attribute of first row
            summary_text = f"{humanize.intword(len(df))} Users made {humanize.intword(df['changesets'].sum())} changesets with {humanize.intword(df['map_changes'].sum())} map changes."
            thread_summary = f"{humanize.intword(created_sum.sum())} OSM Elements were Created, {humanize.intword(modified_sum.sum())} Modified & {humanize.intword(deleted_sum.sum())} Deleted."
            

            
            with open(f"summary.md", "w", encoding="utf-8") as file:
                file.write(f"### Last Update : Stats from {start_date_utc} to {end_date_utc} (UTC Timezone)\n\n")
                file.write(f"#### {summary_text}\n")
                file.write(f"#### {thread_summary}\n")
                top_users ="\nTop 5 Users are : \n"
                # set rank column as index
                df.set_index('rank', inplace=True)
                for i in range(1,6 if len(df)>6 else len(df)):
                    top_users += f"- {df.loc[i, 'name']} : {humanize.intword(df.loc[i, 'map_changes'])} Map Changes\n"
                file.write(top_users) 

                user_tags_summary="\nSummary of Supplied Tags\n"
                user_tag = 'poi'
                user_tags_summary+=f"- {user_tag} = Created: {humanize.intword(df[f'{user_tag}.create'].sum())}, Modified : {humanize.intword(df[f'{user_tag}.modify'].sum())}\n"

                if args.tags:
                    for user_tag in args.tags:
                        user_tags_summary+=f"- {user_tag} = Created: {humanize.intword(df[f'{user_tag}.create'].sum())}, Modified : {humanize.intword(df[f'{user_tag}.modify'].sum())}\n"
                file.write(f"{user_tags_summary}\n")

                if args.all_tags:
                    # Apply the sum_tags function to the tags column
                    tag_counts = sum_tags(df['tags_create'].tolist())

                    # Sort the resulting dictionary by values and take the top three entries
                    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    created_tags_summary = "\nTop 5 Created tags are :\n"
                    # Print the top tags and their counts
                    for tag, count in top_tags:
                        created_tags_summary+=f'- {tag}: {humanize.intword(count)}\n'
                    # Apply the sum_tags function to the tags column
                    tag_counts = sum_tags(df['tags_modify'].tolist())

                    # Sort the resulting dictionary by values and take the top three entries
                    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    modified_tags_summary = "\nTop 5 Modified tags are :\n"
                    # Print the top tags and their counts
                    for tag, count in top_tags:
                        modified_tags_summary+=f'- {tag}: {humanize.intword(count)}\n'
                    file.write(f"{created_tags_summary}\n")
                    file.write(f"{modified_tags_summary}\n")

                if "hashtags" in df.columns[df.astype(bool).any()]:
                    top_five = (
                        df["hashtags"]
                        .str.split(",")
                        .explode()
                        .dropna()
                        .value_counts()
                        .head(5)
                    )
                    trending_hashtags = f"\nTop 5 trending hashtags are:\n"
                    for i in range(0,len(top_five)):
                        if top_five.index[i].strip() !="":
                            trending_hashtags+=f"- {top_five.index[i]} : {top_five[i]} users\n"
                    file.write(f"{trending_hashtags}\n")

                if "countries" in df.columns[df.astype(bool).any()]:
                    top_five = (
                        df["countries"]
                        .str.split(",")
                        .explode()
                        .dropna()
                        .value_counts()
                        .head(5)
                    )
                    trending_countries = f"\nTop 5 trending Countries where user contributed are:\n"
                    for i in range(0,len(top_five)):
                        if top_five.index[i].strip() !="":
                            trending_countries+=f"- {top_five.index[i]} : {top_five[i]} users\n"
                    file.write(f"{trending_countries}\n")
        # Loop through the arguments
        for i in range(len(sys.argv)):
            # If the argument is '--password'
            if sys.argv[i] == "--password":
                # Replace the value with '***'
                sys.argv[i + 1] = "***"
        command = " ".join(sys.argv)
        start_repl_ts = seq_to_timestamp(start_seq_url, args.timezone)
        end_repl_ts = seq_to_timestamp(end_seq_url, args.timezone)

        with open(f"{args.name}_metadata.json", "w", encoding="utf-8") as file:
            file.write(
                json.dumps(
                    {
                        "command": str(command),
                        "source": str(args.url),
                        "start_date": str(start_date),
                        "start_seq": f"{start_seq} = {start_repl_ts}",
                        "end_date": str(end_date),
                        "end_seq": f"{end_seq} = {end_repl_ts}",
                    }
                )
            )
        print("Metadata Created")

    else:
        print("No data Found")
        sys.exit()

    end_time = time.time()
    elapsed_time = end_time - start_time

    # convert elapsed time to hr:min:sec format
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print(
        "Script Completed in hr:min:sec = {:0>2}:{:0>2}:{:05.2f}".format(
            int(hours), int(minutes), seconds
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print(ex)
        sys.exit()
