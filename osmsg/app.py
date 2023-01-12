import argparse
import calendar
import concurrent.futures
import datetime as dt
import gzip
import json
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


def in_local_timezone(date, timezone):
    tz = dt.timezone.utc
    if timezone == "Nepal":
        # Set the timezone to Nepal
        tz = pytz.timezone("Asia/Kathmandu")

    return date.astimezone(tz)


def strip_utc(date_str, timezone):
    tz = dt.timezone.utc
    given_dt = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)

    if timezone == "Nepal":
        # Set the timezone to Nepal
        tz = pytz.timezone("Asia/Kathmandu")

    return given_dt.astimezone(tz)


def get_prev_year_dates(timezone):
    # Get today's date
    today = datetime.utcnow()

    # Get the start and end date of the previous year
    prev_year_start = datetime(today.year - 1, 1, 1)
    prev_year_end = datetime(today.year - 1, 12, 31)

    return strip_utc(prev_year_start.strftime("%Y-%m-%d"), timezone), strip_utc(
        prev_year_end.strftime("%Y-%m-%d"), timezone
    )


def previous_month(timezone):
    today = datetime.utcnow()
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
        if n.timestamp >= start_date_utc and n.timestamp <= end_date_utc:

            calculate_stats(n.uid, n.user, n.changeset, n.version, n.tags, "nodes")

    def way(self, w):
        if w.timestamp >= start_date_utc and w.timestamp <= end_date_utc:
            calculate_stats(w.uid, w.user, w.changeset, w.version, w.tags, "ways")

    def relation(self, r):
        if r.timestamp >= start_date_utc and r.timestamp <= end_date_utc:
            calculate_stats(r.uid, r.user, r.changeset, r.version, r.tags, "relations")


def process_changefiles(url):
    # Check that the request was successful
    # Send a GET request to the URL
    print(f"Processing {url}")

    url_splitted_list = url.split("/")
    temp_path = os.path.join(os.getcwd(), "temp/changefiles")

    file_path = os.path.join(
        temp_path,
        f"{url_splitted_list[-3]}_{url_splitted_list[-2]}_{url_splitted_list[-1]}",
    )

    if not os.path.exists(file_path):
        # Read the cookies from the file

        if "geofabrik" in url:
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
    print(file_path)
    handler = ChangefileHandler()
    with gzip.open(file_path, "rb") as f_in, open(file_path[:-3], "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    handler.apply_file(file_path[:-3])


def get_download_urls_changefiles(start_date, end_date, base_url, timezone):
    repl = ReplicationServer(base_url)

    # Gets sequence id using timestamp we get from osm api using pyosmium tool
    seq = repl.timestamp_to_sequence(start_date)
    # going one step back to cover all changes
    seq = seq - 1
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
    last_ts = server_ts
    if end_date:
        end_date_seq = repl.timestamp_to_sequence(end_date)
        if end_date_seq:
            if end_date_seq < last_seq:
                # get one step ahead to cover all
                last_seq = end_date_seq + 1
            else:
                last_seq = end_date_seq
            last_ts = end_date

    print(
        f"You have supplied {start_date} : {seq} to {last_ts} : {last_seq} . Latest Server Fetched is : {server_seq} & {in_local_timezone(server_ts,timezone)} on {base_url}"
    )

    if seq >= last_seq:
        print("Already up-to-date.")
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


def seq_to_timestamp(url, timezone):
    response = requests.get(url)
    rtxt = response.text
    # find the index of the "timestamp=" substring
    timestamp_start = rtxt.find("timestamp=") + len("timestamp=")

    # find the index of the next newline character
    timestamp_end = rtxt.find("\n", timestamp_start)

    # extract the substring between the two indexes
    timestamp = rtxt[timestamp_start:timestamp_end]
    timestamp_obj = dt.datetime.strptime(timestamp, "%Y-%m-%dT%H\:%M\:%SZ")
    timestamp_obj = timestamp_obj.replace(tzinfo=dt.timezone.utc)
    tz = dt.timezone.utc
    if timezone == "Nepal":
        # Set the timezone to Nepal
        tz = pytz.timezone("Asia/Kathmandu")

    return timestamp_obj.astimezone(tz)


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
    parser.add_argument("--start_date", help="Start date in the format YYYY-MM-DD")
    parser.add_argument("--end_date", help="End date in the format YYYY-MM-DD")
    parser.add_argument("--username", required=True, help="Your OSM Username")
    parser.add_argument(
        "--password", required=True, help="Your OSM Password", default=argparse.SUPPRESS
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
        "--exclude_date_in_name",
        action="store_true",
        help="By default from and to date will be added to filename , You can skip this behaviour with this option",
        default=False,
    )

    parser.add_argument(
        "--format",
        nargs="+",
        choices=["csv", "json", "excel", "image", "text"],
        default="json",
        help="Stats output format",
    )
    parser.add_argument(
        "--read_from_metadata",
        help="Location of metadata to pick start date from previous run's end_date",
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

    print("Generating Download Urls")
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
            "Warning : End date data is not available at server, Changing to latest available date "
        )
        end_date = server_ts
        if start_date >= server_ts:
            print("Data is not available after start date ")
            sys.exit()
    global end_date_utc
    global start_date_utc

    start_date_utc = start_date
    end_date_utc = end_date
    print("Download urls Generated")

    print("Starting Thread Processing")
    temp_path = os.path.join(os.getcwd(), "temp/changefiles")
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    # Use the ThreadPoolExecutor to download the images in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Use `map` to apply the `download_image` function to each element in the `urls` list
        executor.map(process_changefiles, download_urls)
    os.chdir(os.getcwd())
    shutil.rmtree("temp")
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
        start_date = in_local_timezone(start_date, args.timezone)
        end_date = in_local_timezone(end_date, args.timezone)

        fname = f"{args.name}_{start_date}_{end_date}"
        if args.exclude_date_in_name:
            fname = args.name
        if "image" in args.format:
            # Convert the DataFrame to an image
            dfi.export(df, f"{fname}.png", max_cols=-1)

        if "json" in args.format:
            # with open(f"{out_file_name}.json") as file:
            #     file.write(json.dumps(users))
            df.to_json(f"{fname}.json", orient="records")
        if "csv" in args.format:
            df.to_csv(f"{fname}.csv", index=False)
        if "excel" in args.format:
            df.to_excel(f"{fname}.xlsx", index=False)
        if "text" in args.format:
            text_output = df.to_markdown(tablefmt="grid", index=False)
            with open(f"{fname}.txt", "w", encoding="utf-8") as file:
                file.write(
                    f"Top {args.rows} User Contributions From {start_date} to {end_date} . Planet Source File : {args.url}\n "
                )
                file.write(text_output)
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
