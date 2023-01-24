import calendar
import datetime as dt
from datetime import datetime, timedelta

import pytz
import requests


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
