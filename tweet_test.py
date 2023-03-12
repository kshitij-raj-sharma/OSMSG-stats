import argparse
import os

import humanize
import pandas as pd
import tweepy


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--name",
        default="stats",
        help="Output stat file name",
    )
    parser.add_argument(
        "--tweet",
        required=True,
        help="Main Stats Name to include in tweet",
    )

    parser.add_argument(
        "--git",
        default=None,
        help="Github Commit id to include in tweet",
    )

    args = parser.parse_args()

    if not args.git:
        args.git = "master"
    # Authenticate using your API keys and access tokens
    auth = tweepy.OAuthHandler(os.environ["API_KEY"], os.environ["API_KEY_SECRET"])
    auth.set_access_token(os.environ["ACCESS_TOKEN"], os.environ["ACCESS_TOKEN_SECRET"])

    api = tweepy.API(auth)

    summary_text = ""
    thread_summary = ""
    csv_file = os.path.join(os.getcwd(), f"{args.name}.csv")
    full_path = os.path.abspath(os.path.join(os.getcwd(), csv_file))
    base_dir = os.path.abspath(os.path.dirname(full_path))
    rel_csv_path = os.path.relpath(csv_file, os.getcwd())

    # read the .csv file and store it in a DataFrame
    df = pd.read_csv(csv_file)
    start_date = str(df.iloc[0]["start_date"])
    end_date = str(df.iloc[0]["end_date"])

    created_sum = df["nodes.create"] + df["ways.create"] + df["relations.create"]
    modified_sum = df["nodes.modify"] + df["ways.modify"] + df["relations.modify"]
    deleted_sum = df["nodes.delete"] + df["ways.delete"] + df["relations.delete"]

    # Get the attribute of first row
    summary_text = f"{len(df)} Users made {df['changesets'].sum()} changesets with {humanize.intword(df['map_changes'].sum())} map changes."
    thread_summary = f"{humanize.intword(created_sum.sum())} OSM Elements were Created,{humanize.intword(modified_sum.sum())} Modified & {humanize.intword(deleted_sum.sum())} Deleted . Including {humanize.intword(df['building.create'].sum())} buildings & {humanize.intword(df['highway.create'].sum())} highways created. {df.loc[0, 'name']} tops table with {humanize.intword(df.loc[0, 'map_changes'])} changes"

    try:
        api.verify_credentials()
        print("Authentication OK")
    except:
        print("Error during authentication")
    media_ids = []
    thread_media_ids = []

    chart_png_files = [f for f in os.listdir(base_dir) if f.endswith(".png")]
    for i, chart in enumerate(chart_png_files):
        file_path = os.path.join(base_dir, chart)
        chart_media = api.media_upload(file_path)
        if i < 4:
            media_ids.append(chart_media.media_id)
        else:
            thread_media_ids.append(chart_media.media_id)
    orginal_tweet = api.update_status(
        status=f"{args.tweet} Contributions\n{start_date} to {end_date}\n{summary_text}\nFullStats:https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/{rel_csv_path}  #gischat #OpenStreetMap",
        media_ids=media_ids,
    )
    if len(thread_media_ids) > 0:
        thread_tweet = api.update_status(
            status=thread_summary,
            in_reply_to_status_id=orginal_tweet.id,
            auto_populate_reply_metadata=True,
            media_ids=thread_media_ids,
        )


if __name__ == "__main__":
    main()
