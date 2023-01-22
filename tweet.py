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
    if csv:
        csv_file = os.path.join(os.getcwd(), csv[0])

        # read the .csv file and store it in a DataFrame
        df = pd.read_csv(csv_file)

        # Get the attribute of first row
        summary_text = f"User {df.loc[0, 'name']} tops table with {df.loc[0, 'map_changes']} followed by {df.loc[1, 'name']} with {df.loc[1, 'map_changes']} & {df.loc[2, 'name']} with {df.loc[2, 'map_changes']} map changes"

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
                status=f"Nepal Contributors This Week(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal/Weekly/weekly_nepal_stats.csv #weeklystats #OpenStreetMap #osmnepal",
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
                status=f"Nepal Contributors This Month(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal/Monthly/Monthly_nepal_stats.csv #monthlyystats #OpenStreetMap #osmnepal",
                media_ids=[media.media_id],
            )
        print("twitted")
    if args.tweet_last_day:
        if args.tweet_global:
            api.update_status(
                status=f"Global Contributors Last Day(UTC)\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Global/Daily/daily_global_stats.csv #dailystats #OpenStreetMap #global",
                media_ids=[media.media_id],
            )
        else:
            api.update_status(
                status=f"Nepal Contributors Last Day\n{lstfile[1]} - {lstfile[2][:-4]}\n{summary_text}\nFull Stats: https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal/Daily/daily_nepal_stats.csv #dailystats #OpenStreetMap #osmnepal",
                media_ids=[media.media_id],
            )
            print("twitted")


if __name__ == "__main__":
    main()
