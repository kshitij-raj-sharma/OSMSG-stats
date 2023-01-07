import argparse
import calendar
import concurrent.futures
import datetime as dt
import gzip
import os
import shutil
import sys
import time

import dataframe_image as dfi
import osmium
import pandas as pd
import pytz
import requests
from osmium.replication.server import ReplicationServer

from osmsg.utils import verify_me_osm

users_temp = {}
users = {}

from datetime import datetime, timedelta


def strip_utc(date_str, timezone):
    tz = dt.timezone.utc
    if timezone == "Nepal":
        # Set the timezone to Nepal
        tz = pytz.timezone("Asia/Kathmandu")

    return dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)


def get_prev_year_dates(timezone):
    # Get today's date
    today = datetime.now()

    # Get the start and end date of the previous year
    prev_year_start = datetime(today.year - 1, 1, 1)
    prev_year_end = datetime(today.year - 1, 12, 31)

    return strip_utc(prev_year_start.strftime("%Y-%m-%d"), timezone), strip_utc(
        prev_year_end.strftime("%Y-%m-%d"), timezone
    )


def previous_month(timezone):
    today = datetime.now()
    month = today.month
    year = today.year
    if today.month == 1:
        month = 13
        year -= 1
    prev_month_start = datetime(year, month - 1, 1)
    prev_month_end = datetime(year, month - 1, calendar.monthrange(year, month - 1)[1])
    return strip_utc(prev_month_start.strftime("%Y-%m-%d"), timezone), strip_utc(
        prev_month_end.strftime("%Y-%m-%d"), timezone
    )


def previous_day(timezone):
    today = datetime.today()
    previous_day = today - timedelta(days=1)
    return strip_utc(previous_day.strftime("%Y-%m-%d"), timezone), strip_utc(
        today.strftime("%Y-%m-%d"), timezone
    )


def previous_week(timezone):
    today = datetime.today()
    start_date = today - timedelta(days=today.weekday() + 7)
    end_date = start_date + timedelta(days=6)
    return strip_utc(start_date.strftime("%Y-%m-%d"), timezone), strip_utc(
        end_date.strftime("%Y-%m-%d"), timezone
    )


def calculate_stats(user, uname, changeset, version, tags, osm_type):
    tags_to_collect = list(additional_tags) if additional_tags else None
    if version == 1:
        action = "create"
    elif version > 1:
        action = "modify"
    elif version == 0:
        action = "delete"
    if user in users:
        users[user]["name"] = uname
        users[user]["uid"] = user
        if changeset not in users_temp[user]["changesets"]:
            users_temp[user]["changesets"].append(changeset)
        users[user]["changesets"] = len(users_temp[user]["changesets"])
        users[user][osm_type][action] += 1
        if tags_to_collect:
            for tag in tags_to_collect:
                if tag in tags:
                    users[user][tag][action] += 1

    else:
        users[user] = {
            "name": uname,
            "uid": user,
            "changesets": 0,
            "nodes": {"create": 0, "modify": 0, "delete": 0},
            "ways": {"create": 0, "modify": 0, "delete": 0},
            "relations": {"create": 0, "modify": 0, "delete": 0},
        }
        if tags_to_collect:
            for tag in tags_to_collect:
                users[user][tag] = {"create": 0, "modify": 0, "delete": 0}
        users_temp[user] = {"changesets": []}
        if changeset not in users_temp[user]["changesets"]:
            users_temp[user]["changesets"].append(changeset)
        users[user]["changesets"] = len(users_temp[user]["changesets"])
        users[user][osm_type][action] = 1
        if tags_to_collect:
            for tag in tags_to_collect:
                if tag in tags:
                    users[user][tag][action] = 1


class ChangefileHandler(osmium.SimpleHandler):
    def __init__(self):
        super(ChangefileHandler, self).__init__()

    def node(self, n):

        calculate_stats(n.uid, n.user, n.changeset, n.version, n.tags, "nodes")

    def way(self, w):

        calculate_stats(w.uid, w.user, w.changeset, w.version, w.tags, "ways")

    def relation(self, r):

        calculate_stats(r.uid, r.user, r.changeset, r.version, r.tags, "relations")


def process_changefiles(url):
    # Check that the request was successful
    # Send a GET request to the URL

    url_splitted_list = url.split("/")
    temp_path = os.path.join(os.getcwd(), "temp/changefiles")
    file_path = os.path.join(
        temp_path,
        f"{url_splitted_list[-3]}_{url_splitted_list[-2]}_{url_splitted_list[-1]}",
    )
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    if not os.path.exists(file_path):
        # Read the cookies from the file

        if "geofabrik" in url:
            cookies_fmt = {}
            test = cookies.split("=")
            # name, value = line.strip().split("=")
            cookies_fmt[test[0]] = f'{test[1]}=="'
            print(f"Processing {url}")
            response = requests.get(url, cookies=cookies_fmt)
        else:
            response = requests.get(url)

        if not response.status_code == 200:
            sys.exit()

        file_data = response.content

        with open(file_path, "wb") as f:
            f.write(file_data)

    # Open the .osc.gz file in read-only mode
    print(file_path)
    handler = ChangefileHandler()
    with gzip.open(file_path, "rb") as f_in, open(file_path[:-3], "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    handler.apply_file(file_path[:-3])
    os.remove(file_path)
    os.remove(file_path[:-3])
    # Delete the changefiles folder
    os.chdir(os.getcwd())
    shutil.rmtree("temp")


def get_download_urls_changefiles(start_date, end_date, base_url):
    repl = ReplicationServer(base_url)

    # Gets sequence id using timestamp we get from osm api using pyosmium tool
    seq = repl.timestamp_to_sequence(start_date)

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
    last_ts = server_ts
    if end_date:
        end_date_seq = repl.timestamp_to_sequence(end_date)
        if end_date_seq:
            last_seq = end_date_seq
            last_ts = end_date

    print(
        f"You have supplied {start_date} : {seq} to {last_ts} : {last_seq} . Latest Server Fetched is : {server_seq} & {server_ts} on {base_url}"
    )

    if seq >= last_seq:
        print("Already up-to-date.")
        sys.exit()

    download_urls = []

    while seq < last_seq:
        seq_url = repl.get_diff_url(seq)
        if "geofabrik" in base_url:
            # use internal server
            seq_url = repl.get_diff_url(seq).replace(
                "download.geofabrik", "osm-internal.download.geofabrik"
            )
        download_urls.append(seq_url)
        seq += 1
    return download_urls, server_ts


def auth(username, password):
    print("Authenticating...")
    cookies = verify_me_osm(username, password)

    print("Authenticated !")
    return cookies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date", help="Start date in the format YYYY-MM-DD")
    parser.add_argument("--end_date", help="End date in the format YYYY-MM-DD")
    parser.add_argument("--username", required=True, help="Your OSM Username")
    parser.add_argument("--password", required=True, help="Your OSM Password")
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
        "--tags",
        nargs="+",
        type=str,
        help="Additional stats to collect : List of tags key",
    )

    parser.add_argument(
        "--rows",
        type=int,
        help="No fo top rows to extract , to extract top 100 , pass 100",
    )

    parser.add_argument(
        "--url", required=True, help="Your public Geofabrik Download URL "
    )
    parser.add_argument("--extract_last_week", action="store_true", default=False)
    parser.add_argument("--extract_last_day", action="store_true", default=False)
    parser.add_argument("--extract_last_month", action="store_true", default=False)
    parser.add_argument("--extract_last_year", action="store_true", default=False)

    parser.add_argument(
        "--format",
        choices=["csv", "json", "excel", "image"],
        default="json",
        help="Stats output format",
    )

    args = parser.parse_args()
    if args.start_date:
        start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").replace(
            tzinfo=dt.timezone.utc
        )

    if not args.start_date:
        if (
            args.extract_last_week
            or args.extract_last_day
            or args.extract_last_month
            or args.extract_last_year
        ):
            pass
        else:
            print("Supply start_date")
            sys.exit()

    if args.end_date:
        end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").replace(
            tzinfo=dt.timezone.utc
        )
    start_time = time.time()

    global additional_tags
    global cookies
    additional_tags = args.tags
    cookies = None
    if "geofabrik" in args.url:
        cookies = auth(args.username, args.password)
    print("Script Started")

    if args.extract_last_year:
        start_date, end_date = get_prev_year_dates(args.timezone)

    if args.extract_last_month:
        start_date, end_date = previous_month(args.timezone)

    if args.extract_last_day:
        start_date, end_date = previous_day(args.timezone)
    if args.extract_last_week:
        start_date, end_date = previous_week(args.timezone)
    print("Generating Download Urls")
    download_urls, server_ts = get_download_urls_changefiles(
        start_date, end_date, args.url
    )
    if server_ts < end_date:
        end_date = server_ts
    print("Download urls Generated")

    print("Starting Thread Processing")
    # Use the ThreadPoolExecutor to download the images in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Use `map` to apply the `download_image` function to each element in the `urls` list
        executor.map(process_changefiles, download_urls)
    if len(users) > 1:

        df = pd.json_normalize(list(users.values()))
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
        if args.format == "image":
            # Convert the DataFrame to an image
            dfi.export(df, f"{args.name}_{start_date}_{end_date}.png")

        if args.format == "json":
            # with open(f"{out_file_name}.json") as file:
            #     file.write(json.dumps(users))
            df.to_json(f"{args.name}_{start_date}_{end_date}.json", orient="records")
        if args.format == "csv":
            df.to_csv(f"{args.name}_{start_date}_{end_date}.csv", index=False)
        if args.format == "excel":
            df.to_excel(f"{args.name}_{start_date}_{end_date}.xlsx", index=False)
    else:
        sys.exit()

    end_time = time.time()
    elapsed_time = end_time - start_time

    # convert elapsed time to hr:min:sec format
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print(
        "Script Completd in hr:min:sec = {:0>2}:{:0>2}:{:05.2f}".format(
            int(hours), int(minutes), seconds
        )
    )


if __name__ == "__main__":
    main()
