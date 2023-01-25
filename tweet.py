import argparse
import json
import os

import pandas as pd
import tweepy


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--tweet_last_week", action="store_true", default=False)
    parser.add_argument("--tweet_last_day", action="store_true", default=False)
    parser.add_argument("--tweet_last_month", action="store_true", default=False)
    parser.add_argument("--tweet_last_year", action="store_true", default=False)
    parser.add_argument("--tweet_global", action="store_true", default=False)
    parser.add_argument("--tweet_hotosm", action="store_true", default=False)

    args = parser.parse_args()

    # Authenticate using your API keys and access tokens
    auth = tweepy.OAuthHandler(os.environ["API_KEY"], os.environ["API_KEY_SECRET"])
    auth.set_access_token(os.environ["ACCESS_TOKEN"], os.environ["ACCESS_TOKEN_SECRET"])

    api = tweepy.API(auth)

    files = os.listdir(os.getcwd())
    json_files = [f for f in files if f.endswith(".png")]
    first_file = os.path.join(os.getcwd(), json_files[0])

    csv = [f for f in files if f.endswith(".csv")]
    summary_text = ""
    thread_summary = ""
    if csv:
        csv_file = os.path.join(os.getcwd(), csv[0])

        # read the .csv file and store it in a DataFrame
        df = pd.read_csv(csv_file)

        # Get the attribute of first row
        summary_text = f"User {df.loc[0, 'name']} tops table with {df.loc[0, 'map_changes']} map changes, Followed by {df.loc[1, 'name']} - {df.loc[1, 'map_changes']} & {df.loc[2, 'name']} - {df.loc[2, 'map_changes']}"
        thread_summary = f"A total of {len(df)} users recorded with {df['changesets'].sum()} changesets and {df['map_changes'].sum()} map changes.They created {df['nodes.create'].sum()} Nodes , {df['ways.create'].sum()} Ways & {df['relations.create'].sum()} Relations. Out of which {df['building.create'].sum()} were building, {df['highway.create'].sum()} were highway, {df['waterway.create'].sum()} were waterway & {df['amenity.create'].sum()} were amenities. Users also modified {df['nodes.modify'].sum()} Nodes , {df['ways.modify'].sum()} Ways & {df['relations.modify'].sum()} Relations."
    filename = os.path.basename(first_file)

    lstfile = filename.split("_")

    try:
        api.verify_credentials()
        print("Authentication OK")
    except:
        print("Error during authentication")

    media = api.media_upload(first_file)

    if args.tweet_last_week:
        if args.tweet_global:
            api.update_status(
                status=f"Global Contributors Last Week(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Global/Weekly/weekly_global_stats.csv #weeklystats #OpenStreetMap #global",
                media_ids=[media.media_id],
            )

        else:
            api.update_status(
                status=f"Nepal Contributors Last Week(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal/Weekly/weekly_nepal_stats.csv #weeklystats #OpenStreetMap #osmnepal",
                media_ids=[media.media_id],
            )
        print("twitted")
    if args.tweet_last_month:
        if args.tweet_global:
            api.update_status(
                status=f"Global Contributors Last Month(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Global/Monthly/Monthly_global_stats.csv #monthlystats #OpenStreetMap #global",
                media_ids=[media.media_id],
            )

        else:
            api.update_status(
                status=f"Nepal Contributors This Month(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal/Monthly/Monthly_nepal_stats.csv #monthlystats #OpenStreetMap #osmnepal",
                media_ids=[media.media_id],
            )
        print("twitted")
    if args.tweet_hotosm:
        orginal_tweet = api.update_status(
            status=f"Hotosm Contributors Last Day(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Global/Daily/hotosm/daily_stats.csv #dailystats #hotosm #OpenStreetMap",
            media_ids=[media.media_id],
        )
        thread_tweet = api.update_status(
            status=thread_summary,
            in_reply_to_status_id=orginal_tweet.id,
        )

    if args.tweet_last_day:
        if args.tweet_global:
            orginal_tweet = api.update_status(
                status=f"Global Contributors Last Day(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Global/Daily/daily_global_stats.csv #dailystats #OpenStreetMap #global",
                media_ids=[media.media_id],
            )
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
            )
        else:
            orginal_tweet = api.update_status(
                status=f"Nepal Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal/Daily/daily_nepal_stats.csv #dailystats #OpenStreetMap #osmnepal",
                media_ids=[media.media_id],
            )
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
            )


if __name__ == "__main__":
    main()
