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
        thread_summary = f"{len(df)} Users made {df['changesets'].sum()} changesets with {df['map_changes'].sum()} map changes. They created {df['nodes.create'].sum()} nodes , {df['ways.create'].sum()} ways & {df['relations.create'].sum()} relations, Including {df['building.create'].sum()} buildings, {df['highway.create'].sum()} highways, {df['waterway.create'].sum()} waterways & {df['amenity.create'].sum()} amenities. Users also modified {df['nodes.modify'].sum()} nodes, {df['ways.modify'].sum()} ways & {df['relations.modify'].sum()} relations"

        trending_countries = ""
        trending_hashtags = ""
        # Check if the 'hashtags' column exists in the dataframe
        if "hashtags" in df.columns:
            # Use value_counts on the result of str.split and then use head(3) to get the top three most frequent elements
            if args.tweet_hotosm:
                top_three = df["hashtags"].str.split(",").explode()
                top_three = (
                    top_three[top_three.str.contains("hotosm")].value_counts().head(3)
                )
            else:
                top_three = (
                    df["hashtags"].str.split(",").explode().value_counts().head(3)
                )

            # Format the output as a string
            trending_hashtags = f"Top three trending hashtags for those stats are {top_three.index[0]} : {top_three[0]}, {top_three.index[1]} : {top_three[1]} & {top_three.index[2]} : {top_three[2]}"
        if args.tweet_global:
            if "countries" in df.columns:
                top_three = (
                    df["countries"].str.split(",").explode().value_counts().head(3)
                )
                trending_countries = f" & Top three countries based on no of users contributed are {top_three.index[0]} : {top_three[0]}, {top_three.index[1]} : {top_three[1]} & {top_three.index[2]} : {top_three[2]}"

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
            orginal_tweet = api.update_status(
                status=f"Global Contributors Last Week\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Weekly/weekly_global_stats.csv #weeklystats #OpenStreetMap #global",
                media_ids=[media.media_id],
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
            )
        else:
            orginal_tweet = api.update_status(
                status=f"Nepal Contributors Last Week\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Weekly/weekly_nepal_stats.csv #weeklystats #OpenStreetMap #osmnepal",
                media_ids=[media.media_id],
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
            )
        print("twitted")
    if args.tweet_last_month:
        if args.tweet_global:
            orginal_tweet = api.update_status(
                status=f"Global Contributors Last Month\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Monthly/Monthly_global_stats.csv #monthlystats #OpenStreetMap #global",
                media_ids=[media.media_id],
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
            )
        else:
            orginal_tweet = api.update_status(
                status=f"Nepal Contributors This Month\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Monthly/Monthly_nepal_stats.csv #monthlystats #OpenStreetMap #osmnepal",
                media_ids=[media.media_id],
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
            )
        print("twitted")
    if args.tweet_hotosm:
        orginal_tweet = api.update_status(
            status=f"HOTOSM Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Daily/hotosm/daily_stats.csv #dailystats @hotosm #OpenStreetMap",
            media_ids=[media.media_id],
        )
        thread_tweet = api.update_status(
            status=thread_summary,
            in_reply_to_status_id=orginal_tweet.id,
            auto_populate_reply_metadata=True,
        )
        if trending_hashtags or trending_countries:
            thread_tweet_2 = api.update_status(
                status=trending_hashtags + trending_countries,
                in_reply_to_status_id=thread_tweet.id,
                auto_populate_reply_metadata=True,
            )

    if args.tweet_last_day:
        if args.tweet_global:
            orginal_tweet = api.update_status(
                status=f"Global Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Daily/daily_global_stats.csv #dailystats #OpenStreetMap #global",
                media_ids=[media.media_id],
            )
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
            )
            if trending_hashtags or trending_countries:
                thread_tweet_2 = api.update_status(
                    status=trending_hashtags + trending_countries,
                    in_reply_to_status_id=thread_tweet.id,
                    auto_populate_reply_metadata=True,
                )
        else:
            orginal_tweet = api.update_status(
                status=f"Nepal Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Daily/daily_nepal_stats.csv #dailystats #OpenStreetMap #osmnepal",
                media_ids=[media.media_id],
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
            )
            if trending_hashtags or trending_countries:
                thread_tweet_2 = api.update_status(
                    status=trending_hashtags + trending_countries,
                    in_reply_to_status_id=thread_tweet.id,
                    auto_populate_reply_metadata=True,
                )


if __name__ == "__main__":
    main()
