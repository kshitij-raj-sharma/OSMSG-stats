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


def create_charts(df):
    ### osm changes block
    # Get the sum of all the create, modify, and delete values
    nodes_create = df["nodes.create"].sum()
    nodes_modify = df["nodes.modify"].sum()
    nodes_delete = df["nodes.delete"].sum()
    ways_create = df["ways.create"].sum()
    ways_modify = df["ways.modify"].sum()
    ways_delete = df["ways.delete"].sum()
    relations_create = df["relations.create"].sum()
    relations_modify = df["relations.modify"].sum()
    relations_delete = df["relations.delete"].sum()

    # Extract the start and end dates from the dataframe
    start_date = df["start_date"][0]
    end_date = df["end_date"][0]

    # Create the bar chart

    create = [nodes_create, ways_create, relations_create]

    modify = [nodes_modify, ways_modify, relations_modify]

    delete = [nodes_delete, ways_delete, relations_delete]

    bar_width = 0.25
    index = [1, 2, 3]

    sns.set(style="darkgrid")

    fig, ax = plt.subplots(figsize=(20, 20))

    create_bar = ax.bar(index, create, bar_width, label="Create", color="g")
    modify_bar = ax.bar(
        [i + bar_width for i in index], modify, bar_width, label="Modify", color="b"
    )
    delete_bar = ax.bar(
        [i + 2 * bar_width for i in index], delete, bar_width, label="Delete", color="r"
    )

    ax.set_xlabel("Elements")
    ax.set_ylabel("Count")
    ax.set_title(f"OSM Changes : From {start_date} to {end_date}")
    ax.set_xticks([i + bar_width for i in index])
    ax.set_xticklabels(["Nodes", "Ways", "Relations"])
    ax.legend()

    # Add count labels
    for i in range(len(create)):
        ax.text(
            index[i] - 0.1,
            create[i],
            humanize.intword(create[i]),
            ha="left",
            color="#2B1B17",
            va="bottom",
        )
        ax.text(
            index[i] + bar_width - 0.1,
            modify[i],
            humanize.intword(modify[i]),
            ha="left",
            color="#2B1B17",
            va="bottom",
        )
        ax.text(
            index[i] + 2 * bar_width - 0.1,
            delete[i],
            humanize.intword(delete[i]),
            ha="left",
            color="#2B1B17",
            va="bottom",
        )

    # ax.set_yscale("symlog")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ",")))

    plt.savefig("osm_changes.png", bbox_inches="tight")

    #### Countries block
    if "countries" in df.columns:

        # Split the countries column into multiple rows, one for each country
        split_df = (
            df["countries"]
            .str.split(",", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("countries")
        )

        # Create a new dataframe with the split countries data
        new_df = split_df.to_frame().join(df[["name"]]).reset_index(drop=True)

        # Group the data by country and count the number of users for each country
        grouped = (
            new_df.groupby("countries")["name"].count().sort_values(ascending=False)
        )

        # Show only the top 20 countries
        grouped = grouped.head(20)

        # Plot the data as a bar chart using seaborn
        sns.set(style="darkgrid")
        fig, ax = plt.subplots(figsize=(20, 20))
        ax = sns.barplot(x=grouped.index, y=grouped.values)

        font = fm.FontProperties(family="Arial", size=8)
        # Add the count labels to the bars
        for i, v in enumerate(grouped.values):
            ax.text(
                i, v + 0.05, str(v), color="#2B1B17", fontproperties=font, va="bottom"
            )

        ax.set(
            xlabel="Top 20 Countries Contributed",
            ylabel="User Count",
            title=f"Contributors per Country : from {start_date} to {end_date}",
        )
        plt.xticks(rotation=90, fontsize=12)

        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

        plt.savefig("users_per_country.png", bbox_inches="tight")

    ##### hashtag block
    if "hashtags" in df.columns:

        # Split the countries column into multiple rows, one for each country
        split_df = (
            df["hashtags"]
            .str.split(",", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("hashtags")
        )

        # Create a new dataframe with the split countries data
        new_df = split_df.to_frame().join(df[["name"]]).reset_index(drop=True)

        # Group the data by country and count the number of users for each country
        grouped = (
            new_df.groupby("hashtags")["name"].count().sort_values(ascending=False)
        )

        # Show only the top 20 countries
        grouped = grouped.head(20)

        # Plot the data as a bar chart using seaborn
        sns.set(style="darkgrid")
        fig, ax = plt.subplots(figsize=(20, 20))
        ax = sns.barplot(x=grouped.index, y=grouped.values)

        font = fm.FontProperties(family="Arial", size=8)
        # Add the count labels to the bars
        for i, v in enumerate(grouped.values):
            ax.text(
                i, v + 0.05, str(v), color="#2B1B17", fontproperties=font, va="bottom"
            )

        # Extract the start and end dates from the dataframe
        start_date = df["start_date"][0]
        end_date = df["end_date"][0]

        ax.set(
            xlabel="Top 20 Hashtags",
            ylabel="User Count",
            title=f"Contributors Per Hashtag : From {start_date} to {end_date}",
        )
        plt.xticks(rotation=90, fontsize=12)

        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

        plt.savefig("users_per_hashtag.png", bbox_inches="tight")

    if "tags_create" in df.columns and "tags_modify" in df.columns:
        ### tag block
        # count the total number of each tag type (create/modify)
        data = defaultdict(int)
        for i, row in df.iterrows():
            tags_create = eval(row["tags_create"])
            tags_modify = eval(row["tags_modify"])
            for k, v in tags_create.items():
                data[k + " (create)"] += v
            for k, v in tags_modify.items():
                data[k + " (modify)"] += v

        # sort the data by values and get the top 10
        top_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:10])

        # separate the "create" and "modify" values into two separate dictionaries
        create_data = {}
        modify_data = {}
        for k, v in top_data.items():
            if "create" in k:
                create_data[k.split(" (")[0]] = v
            else:
                modify_data[k.split(" (")[0]] = v

        # Set the style of the plot using seaborn
        sns.set(style="darkgrid")

        # Get all the unique keys
        keys = set(create_data.keys()).union(set(modify_data.keys()))

        # Initialize the bar width
        bar_width = 0.4

        # Initialize the x-axis position
        x_pos = np.arange(len(keys))

        # Create the figure and axis object
        fig, ax = plt.subplots(figsize=(15, 15))

        # Plot the create data
        bar1 = ax.bar(
            x_pos,
            [create_data.get(k, 0) for k in keys],
            bar_width,
            color="g",
            label="Create",
        )
        for i, bar in enumerate(bar1):
            height = bar.get_height()
            ax.annotate(
                f"{humanize.intword(height)}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha="center",
                color="#2B1B17",
                va="bottom",
            )

        # Plot the modify data
        bar2 = ax.bar(
            x_pos + bar_width,
            [modify_data.get(k, 0) for k in keys],
            bar_width,
            color="b",
            label="Modify",
        )
        for i, bar in enumerate(bar2):
            height = bar.get_height()
            ax.annotate(
                f"{humanize.intword(height)}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha="center",
                color="#2B1B17",
                va="bottom",
            )

        # Set the x-axis labels
        ax.set_xticks(x_pos + bar_width / 2)
        ax.set_xticklabels(keys, rotation=90, fontsize=12)

        # Set the axis labels and title
        ax.set(
            xlabel="Top 10 OSM Tags",
            ylabel="Count",
            title=f"Tags Creation/ Modification Distribution : From {start_date} to {end_date}",
        )

        # Add the legend
        ax.legend()

        # Format the y-axis with a log scale and comma separated values
        # ax.set_yscale("log")
        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
        plt.savefig("tags.png", bbox_inches="tight")


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
    png_files = [f for f in files if f.endswith(".png")]
    first_file = os.path.join(os.getcwd(), png_files[0])

    csv = [f for f in files if f.endswith(".csv")]
    summary_text = ""
    thread_summary = ""
    if csv:
        csv_file = os.path.join(os.getcwd(), csv[0])

        # read the .csv file and store it in a DataFrame
        df = pd.read_csv(csv_file)
        if args.tweet_nepal:
            df = df.drop("countries", axis=1)
        create_charts(df)
        # Compute sums of specified columns for the entire dataframe
        created_sum = df['nodes.create'] + df['ways.create'] + df['relations.create']
        modified_sum = df['nodes.modify'] + df['ways.modify'] + df['relations.modify']
        deleted_sum = df['nodes.delete'] + df['ways.delete'] + df['relations.delete']


        # Get the attribute of first row
        summary_text = f"{len(df)} Users made {df['changesets'].sum()} changesets with {humanize.intword(df['map_changes'].sum())} map changes."
        thread_summary = f"{humanize.intword(created_sum.sum())} OSM Elements were Created,{humanize.intword(modified_sum.sum())} Modified & {humanize.intword(deleted_sum.sum())} Deleted . Including {humanize.intword(df['building.create'].sum())} buildings & {humanize.intword(df['highway.create'].sum())} highways created. {df.loc[0, 'name']} tops table with {humanize.intword(df.loc[0, 'map_changes'])} changes"

        trending_countries = ""
        trending_hashtags = ""
        # Check if the 'hashtags' column exists in the dataframe
        if "hashtags" in df.columns:
            # Use value_counts on the result of str.split and then use head(3) to get the top three most frequent elements
            if args.tweet_hotosm:
                top_three = df["hashtags"].str.split(",").explode().dropna()
                top_three = (
                    top_three[top_three.str.contains("hotosm")].value_counts().head(3)
                )
            else:
                top_three = (
                    df["hashtags"]
                    .str.split(",")
                    .explode()
                    .dropna()
                    .value_counts()
                    .head(3)
                )

            # Format the output as a string
            trending_hashtags = f"Top three trending hashtags for those stats are {top_three.index[0]} : {top_three[0]}, {top_three.index[1]} : {top_three[1]} & {top_three.index[2]} : {top_three[2]}"
        if not args.tweet_nepal:
            if "countries" in df.columns:
                top_three = (
                    df["countries"].str.split(",").explode().value_counts().head(3)
                )
                trending_countries = f" & Top three countries based on no of users contributed are {top_three.index[0]} : {top_three[0]}, {top_three.index[1]} : {top_three[1]} & {top_three.index[2]} : {top_three[2]}"

    filename = os.path.basename(first_file)

    lstfile = filename.split("_")

    with open(f"meta.md", "w", encoding="utf-8") as file:
        file.write(f"### Last Update :\n\n")
        file.write(f"### Stats From {lstfile[1]} to {lstfile[2][:-4]}\n\n")
        file.write(f"{summary_text}\n")
        file.write(f"- {thread_summary}\n")
        file.write(f"- {trending_hashtags}\n")
        file.write(f"- {trending_countries}\n")
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
        f for f in all_files if f.endswith(".png") and not f.startswith("stats")
    ]
    for chart in chart_png_files:
        file_path = os.path.join(os.getcwd(), chart)
        chart_media = api.media_upload(file_path)
        media_ids.append(chart_media.media_id)
    first_media = api.media_upload(first_file)

    if args.tweet_last_week:
        if args.tweet_hotosm:
            orginal_tweet = api.update_status(
                status=f"HOTOSM Contributors Last Week\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/hotosm/Weekly/weekly_stats.csv #weeklystats #gischat @hotosm #OpenStreetMap",
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
                status=f"Global Contributors Last Week\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Weekly/weekly_global_stats.csv #weeklystats #gischat @OpenStreetMap #global",
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
                status=f"Nepal Contributors Last Week\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Weekly/weekly_nepal_stats.csv #weeklystats #gischat #OpenStreetMap #osmnepal",
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
                status=f"Global Contributors Last Month\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Monthly/Monthly_global_stats.csv #monthlystats #gischat @OpenStreetMap #global",
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
                status=f"Nepal Contributors This Month\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Monthly/Monthly_nepal_stats.csv #monthlystats #gischat #OpenStreetMap #osmnepal",
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
                status=f"HOTOSM Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/hotosm/Daily/daily_stats.csv #dailystats @hotosm #gischat #OpenStreetMap",
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
                status=f"Global Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Global/Daily/daily_global_stats.csv #dailystats #gischat @OpenStreetMap #global",
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
                status=f"Nepal Contributors Last Day\n{lstfile[1]} to {lstfile[2][:-4]}\n{summary_text}\nFull: https://github.com/kshitijrajsharma/OSMSG/blob/{args.git}/stats/Nepal/Daily/daily_nepal_stats.csv #dailystats #gischat #OpenStreetMap #osmnepal",
                media_ids=media_ids,
            )
            print(thread_summary)
            thread_tweet = api.update_status(
                status=thread_summary,
                in_reply_to_status_id=orginal_tweet.id,
                auto_populate_reply_metadata=True,
                media_ids=[first_media.media_id],
            )
    os.remove(first_file) # we no longer need stats as it was copied on earlier github action



if __name__ == "__main__":
    main()
