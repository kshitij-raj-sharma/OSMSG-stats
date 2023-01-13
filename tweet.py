import argparse
import json
import os

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
                status=f"Top 100 Global Contributors Last Week (UTC Timezone)\n(From {lstfile[1]} to {lstfile[2][:-4]})\nCheck full stats on : https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Global/Weekly/weekly_global_stats.csv \n #dailystats #osm #openstreetmap #global",
                media_ids=[media.media_id],
            )

        else:
            api.update_status(
                status=f"Top 100 Nepal Contributors This week (UTC Timezone)\n(From {lstfile[1]} to {lstfile[2][:-4]})\nCheck full stats on : https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal/Weekly/weekly_nepal_stats.csv \n #weeklystats #osm #openstreetmap #osmnepal",
                media_ids=[media.media_id],
            )
        print("twitted")
    if args.tweet_last_day:
        if args.tweet_global:
            api.update_status(
                status=f"Top 100 Global Contributors Last Day (UTC Timezone)\n(From {lstfile[1]} to {lstfile[2][:-4]})\nCheck full stats on : https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Global/Daily/daily_global_stats.csv \n #dailystats #osm #openstreetmap #global",
                media_ids=[media.media_id],
            )
        else:
            api.update_status(
                status=f"Top 100 Nepal Contributors Last Day (Nepal Timezone)\n(From {lstfile[1]} to {lstfile[2][:-4]})\nCheck full stats on : https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal/Daily/daily_nepal_stats.csv \n #dailystats #osm #openstreetmap #osmnepal",
                media_ids=[media.media_id],
            )
            print("twitted")


if __name__ == "__main__":
    main()
