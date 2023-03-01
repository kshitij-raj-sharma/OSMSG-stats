import calendar
import datetime as dt
import sys
from datetime import datetime, timedelta

import pytz
import requests
from osmium.replication.server import ReplicationServer


def in_local_timezone(date, timezone):
    tz = dt.timezone.utc
    if timezone == "Nepal":
        # Set the timezone to Nepal
        tz = pytz.timezone("Asia/Kathmandu")

    return date.astimezone(tz)


def strip_utc(date, timezone):
    tz = dt.timezone.utc
    given_dt = date
    if not isinstance(date, datetime):
        given_dt = dt.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=tz)

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


def get_prev_hour(timezone):
    now = datetime.now()

    # Get the previous hour's start time
    start_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)

    # Get the previous hour's end time
    end_time = start_time + timedelta(hours=1)

    tz = dt.timezone.utc
    if timezone == "Nepal":
        # Set the timezone to Nepal
        tz = pytz.timezone("Asia/Kathmandu")
    return start_time.astimezone(tz), end_time.astimezone(tz)


def previous_day(timezone):
    today = datetime.today()
    previous_day = today - timedelta(days=1)
    return strip_utc(previous_day.strftime("%Y-%m-%d"), timezone), strip_utc(
        today.strftime("%Y-%m-%d"), timezone
    )


def last_days_count(timezone, days):
    today = datetime.today()
    previous_day = today - timedelta(days=days)
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


def get_download_urls_changefiles(start_date, end_date, base_url, timezone):
    repl = ReplicationServer(base_url)

    # Gets sequence id using timestamp we get from osm api using pyosmium tool
    seq = repl.timestamp_to_sequence(start_date)
    # going one step back to cover all changes only if it is not already behind
    start_seq_time = seq_to_timestamp(repl.get_state_url(seq), timezone)
    if start_date > start_seq_time:
        if "minute" in base_url:
            seq = (
                seq + int((start_date - start_seq_time).total_seconds() / 60)
            ) - 60  # go 60 min earlier
        if "hour" in base_url:
            seq = (
                seq + int(((start_date - start_seq_time).total_seconds() / 60) / 60)
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
            last_seq += 1  # go 1 sequence later
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
