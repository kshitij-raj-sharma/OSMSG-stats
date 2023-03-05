import argparse
import os
from collections import defaultdict

import humanize
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
import tweepy


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--tweet_last_week", action="store_true", default=False)
    parser.add_argument("--tweet_last_day", action="store_true", default=False)
    parser.add_argument("--tweet_last_month", action="store_true", default=False)
    parser.add_argument("--tweet_last_year", action="store_true", default=False)
    parser.add_argument("--tweet_global", action="store_true", default=False)
    parser.add_argument("--tweet_hotosm", action="store_true", default=False)
    parser.add_argument("--tweet_nepal", action="store_true", default=False)

    parser.add_argument(
        "--git",
        default=None,
        help="Github Commit id to include in tweet",
    )

    args = parser.parse_args()

    # Authenticate using your API keys and access tokens
    auth = tweepy.OAuthHandler(os.environ["API_KEY"], os.environ["API_KEY_SECRET"])
    auth.set_access_token(os.environ["ACCESS_TOKEN"], os.environ["ACCESS_TOKEN_SECRET"])

    api = tweepy.API(auth)

    files = os.listdir(os.getcwd())
    first_file = os.path.join(os.getcwd(), "top_users.png")

    csv = [f for f in files if f.endswith(".csv")]
    summary_text = ""
    thread_summary = ""
    csv_file = os.path.join(os.getcwd(), csv[0])
    filename = os.path.basename(csv_file)

    lstfile = filename.split("_")

    # read the .csv file and store it in a DataFrame
    df = pd.read_csv(csv_file)
    # if args.tweet_nepal:
    #     df = df.drop("countries", axis=1)
    # create_charts(df)
    # Compute sums of specified columns for the entire dataframe
    created_sum = df["nodes.create"] + df["ways.create"] + df["relations.create"]
    modified_sum = df["nodes.modify"] + df["ways.modify"] + df["relations.modify"]
    deleted_sum = df["nodes.delete"] + df["ways.delete"] + df["relations.delete"]

    # Get the attribute of first row
    summary_text = f"{len(df)} Users made {df['changesets'].sum()} changesets with {humanize.intword(df['map_changes'].sum())} map changes."
    thread_summary = f"{humanize.intword(created_sum.sum())} OSM Elements were Created,{humanize.intword(modified_sum.sum())} Modified & {humanize.intword(deleted_sum.sum())} Deleted . Including {humanize.intword(df['building.create'].sum())} buildings & {humanize.intword(df['highway.create'].sum())} highways created. {df.loc[0, 'name']} tops table with {humanize.intword(df.loc[0, 'map_changes'])} changes"

    with open(f"summary.md", "a", encoding="utf-8") as file:
        file.write("\n Charts : \n")
        file.write("![Alt text](./charts/osm_changes.png) \n")
        file.write("![Alt text](./charts/users_per_hashtag.png) \n")
        file.write("![Alt text](./charts/users_per_country.png) \n")
        file.write("![Alt text](./charts/tags.png) \n")

    print("Readme Created")

    try:
        api.verify_credentials()
        print("Authentication OK")
    except:
        print("Error during authentication")

    all_files = os.listdir(os.getcwd())
    media_ids = []

    chart_png_files = [
        f for f in all_files if f.endswith(".png") and not f.startswith("top_user")
    ]
    for chart in chart_png_files:
        file_path = os.path.join(os.getcwd(), chart)
        chart_media = api.media_upload(file_path)
        media_ids.append(chart_media.media_id)

    first_media = api.media_upload(first_file)

    if args.tweet_last_week:
        if args.tweet_hotosm:
            orginal_tweet = api.update_status(
                status=f"HOTOSM Contributors Last Week\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/hotosm/Weekly/stats.csv #weeklystats #gischat @hotosm #OpenStreetMap",
                media_ids=media_ids,
            )
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )

        if args.tweet_global:
            orginal_tweet = api.update_status(
                status=f"Global Contributors Last Week\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Weekly/stats.csv #weeklystats #gischat @OpenStreetMap #global",
                media_ids=media_ids,
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )

        if args.tweet_nepal:
            orginal_tweet = api.update_status(
                status=f"Nepal Contributors Last Week\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Weekly/stats.csv #weeklystats #gischat #OpenStreetMap #osmnepal",
                media_ids=media_ids,
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )

        print("twitted")
    if args.tweet_last_month:
        if args.tweet_global:
            orginal_tweet = api.update_status(
                status=f"Global Contributors Last Month\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Monthly/stats.csv #monthlystats #gischat @OpenStreetMap #global",
                media_ids=media_ids,
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )
        if args.tweet_hotosm:
            orginal_tweet = api.update_status(
                status=f"Hotosm Contributors Last Month\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/hotosm/Monthly/stats.csv #monthlystats #gischat @OpenStreetMap #global",
                media_ids=media_ids,
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )
        if args.tweet_nepal:
            orginal_tweet = api.update_status(
                status=f"Nepal Contributors This Month\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Monthly/stats.csv #monthlystats #gischat #OpenStreetMap #osmnepal",
                media_ids=media_ids,
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )
        print("twitted")

    if args.tweet_last_day:
        if args.tweet_hotosm:
            orginal_tweet = api.update_status(
                status=f"HOTOSM Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/hotosm/Daily/stats.csv #dailystats @hotosm #gischat #OpenStreetMap",
                media_ids=media_ids,
            )
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )

        if args.tweet_global:
            orginal_tweet = api.update_status(
                status=f"Global Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Daily/stats.csv #dailystats #gischat @OpenStreetMap #global",
                media_ids=media_ids,
            )
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )

        if args.tweet_nepal:
            orginal_tweet = api.update_status(
                status=f"Nepal Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Daily/stats.csv #dailystats #gischat #OpenStreetMap #osmnepal",
                media_ids=media_ids,
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )
    os.remove(
        first_file
    )  # we no longer need stats as it was copied on earlier github action


if __name__ == "__main__":
    main()
