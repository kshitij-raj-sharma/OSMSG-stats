# This file is part of OSMSG (https://github.com/kshitijrajsharma/OSMSG).
# MIT License

# Copyright (c) 2023 Kshitij Raj Sharma

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import ast
import gzip
import json
import os
import re
import shutil
import urllib.parse
from collections import defaultdict

import geopandas as gpd
import humanize
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from requests.adapters import HTTPAdapter
from shapely.geometry import MultiPolygon, Polygon, box

# number of times to retry
retry_count = 5
session = requests.Session()
retries = HTTPAdapter(max_retries=retry_count)
session.mount("https://", retries)
session.mount("http://", retries)


def get_editors_name_strapped(editor):
    try:
        pattern = r"([a-zA-Z\s]+)"
        editor_name = re.findall(pattern, editor)
        # convert to lowercase and print editor name
        editor = editor_name[0].lower().strip()
        return editor

    except:
        return editor.strip()


def create_charts(df, fname):
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
    created_charts = []
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

    plt.savefig(f"{fname}_osm_changes.png", bbox_inches="tight")
    created_charts.append(f"{fname}_osm_changes.png")

    #### Countries block
    if "countries" in df.columns[df.astype(bool).any()]:
        # Split the countries column into multiple rows
        split_df = (
            df["countries"]
            .astype(str)
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

        font = fm.FontProperties(size=8)
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

        plt.savefig(f"{fname}_users_per_country.png", bbox_inches="tight")
        created_charts.append(f"{fname}_users_per_country.png")

    ##### hashtag block
    if "hashtags" in df.columns[df.astype(bool).any()]:
        # Split the hashtags column into multiple rows, one for each hashtag
        split_df = (
            df["hashtags"]
            .str.split(",", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("hashtags")
            .dropna()
            .loc[lambda x: x.str.strip().astype(bool)]
        )

        # Create a new dataframe with the split countries data
        new_df = split_df.to_frame().join(df[["name"]]).reset_index(drop=True)

        # Group the data by hashtags and count the number of users for each hashtag
        grouped = (
            new_df.groupby("hashtags")["name"].count().sort_values(ascending=False)
        )

        # Show only the top 20 countries
        grouped = grouped.head(20)

        # Plot the data as a bar chart using seaborn
        sns.set(style="darkgrid")
        fig, ax = plt.subplots(figsize=(20, 20))
        ax = sns.barplot(x=grouped.index, y=grouped.values)

        font = fm.FontProperties(size=12)
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

        plt.savefig(f"{fname}_users_per_hashtag.png", bbox_inches="tight")
        created_charts.append(f"{fname}_users_per_hashtag.png")

    # if "editors" in df.columns[df.astype(bool).any()]:
    #     split_df = (
    #         df["editors"]
    #         .str.split(",", expand=True)
    #         .stack()
    #         .reset_index(level=1, drop=True)
    #         .rename("editors")
    #         .dropna()
    #         .loc[lambda x: x.str.strip().astype(bool)]
    #     )

    #     new_df = split_df.to_frame().join(df[["name"]]).reset_index(drop=True)
    #     # Group the data by editors and count the number of users for each editor
    #     grouped_editors = (
    #         new_df.groupby("editors")["name"].count().sort_values(ascending=False)
    #     )

    #     # Determine the number of categories to show in the pie chart
    #     num_categories = min(len(grouped_editors), 8)

    #     # Select the top categories and group the rest as "others"
    #     top_editors = grouped_editors.head(num_categories)
    #     other_editors_count = grouped_editors.iloc[num_categories:].sum()

    #     # Create a new series with the top categories and "others" count
    #     editors_data = top_editors.append(
    #         pd.Series(other_editors_count, index=["Others"])
    #     )

    #     # Plot the data as a pie chart using matplotlib
    #     plt.figure(figsize=(10, 10))
    #     plt.pie(
    #         editors_data.values,
    #         labels=editors_data.index,
    #         autopct="%1.1f%%",
    #         startangle=90,
    #         colors=sns.color_palette("pastel")[0 : len(editors_data)],
    #     )

    #     # Set the title
    #     plt.title("Editors Distribution")

    #     # Save the chart
    #     plt.savefig(f"{fname}_editors_pie_chart.png", bbox_inches="tight")
    #     created_charts.append(f"{fname}_editors_pie_chart.png")

    if "editors" in df.columns[df.astype(bool).any()]:
        split_df = (
            df["editors"]
            .str.split(",", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("editors")
            .dropna()
            .loc[lambda x: x.str.strip().astype(bool)]
            .apply(get_editors_name_strapped)  # Apply the function to each editor name
        )

        new_df = split_df.to_frame().join(df[["name"]]).reset_index(drop=True)
        # Group the data by editors and count the number of users for each editor
        grouped_editors = (
            new_df.groupby("editors")["name"].count().sort_values(ascending=False)
        )

        # Determine the number of categories to show in the pie chart
        num_categories = min(len(grouped_editors), 8)

        # Select the top categories and group the rest as "others"
        top_editors = grouped_editors.head(num_categories)
        other_editors_count = grouped_editors.iloc[num_categories:].sum()

        # Create a new series with the top categories and "others" count
        editors_data = top_editors.append(
            pd.Series(other_editors_count, index=["Others"])
        )

        # Plot the data as a pie chart using matplotlib
        plt.figure(figsize=(10, 10))
        patches, _ = plt.pie(
            editors_data.values,
            startangle=90,
            colors=sns.color_palette("pastel")[0 : len(editors_data)],
        )

        # Calculate the percentages for the pie chart slices
        percentages = editors_data.values / editors_data.values.sum() * 100

        # Create labels for the legend with the editor names and percentages
        legend_labels = [
            f"{label} ({percentage:.1f}%)"
            for label, percentage in zip(editors_data.index, percentages)
        ]

        # Add labels outside the pie chart
        plt.legend(
            patches,
            legend_labels,
            title="Editors",
            loc="center left",
            bbox_to_anchor=(1, 0.5),
            fontsize=12,
        )

        # Set the title
        plt.title("Editors / Users Distribution")

        plt.savefig(f"{fname}_editors_pie_chart.png", bbox_inches="tight")
        created_charts.append(f"{fname}_editors_pie_chart.png")

    if (
        "tags_create" in df.columns[df.astype(bool).any()]
        and "tags_modify" in df.columns[df.astype(bool).any()]
    ):
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
        plt.savefig(f"{fname}_tags.png", bbox_inches="tight")
        created_charts.append(f"{fname}_tags.png")

    return created_charts


# Function to create profile link
def create_profile_link(name):
    # Encode name for URL
    encoded_name = urllib.parse.quote(name)
    # Create URL string
    url = f"https://www.openstreetmap.org/user/{encoded_name}"
    return url


# Define a function to sum up the tag values across all rows
def sum_tags(tags_list):
    tag_counts = {}
    for tags_dict in tags_list:
        tags_dict = ast.literal_eval(tags_dict)
        for tag, count in tags_dict.items():
            if tag not in tag_counts:
                tag_counts[tag] = 0
            tag_counts[tag] += count
    return tag_counts


def get_file_path_from_url(url, mode):
    url_splitted_list = url.split("/")
    temp_path = os.path.join(os.getcwd(), f"temp/{mode}", url_splitted_list[-4])
    file_path = os.path.join(
        temp_path,
        f"{url_splitted_list[-3]}_{url_splitted_list[-2]}_{url_splitted_list[-1]}",
    )
    return file_path


def download_osm_files(url, mode="changefiles", cookies=None):
    file_path = get_file_path_from_url(url, mode)

    if not os.path.exists(file_path[:-3]):
        # Read the cookies from the file
        if not os.path.exists(file_path):
            if "geofabrik" in url.lower():
                cookies_fmt = {}
                test = cookies.split("=")
                # name, value = line.strip().split("=")
                cookies_fmt[test[0]] = f'{test[1]}=="'
                response = session.get(url, cookies=cookies_fmt)
            else:
                response = session.get(url)
            response.raise_for_status()

            file_data = response.content
            # Create the directory if it does not exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "xb") as f:
                f.write(file_data)

        with gzip.open(file_path, "rb") as f_in, open(file_path[:-3], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(file_path)


def update_stats(df1, df2):
    # Merge the dataframes on 'ID'
    merged_df = pd.merge(df1, df2, on="uid", how="outer")
    merged_df["name"] = merged_df["name_x"].fillna(merged_df["name_y"]).astype(str)
    # Get the list of integer columns to update
    int_cols = [
        col
        for col in df1.columns
        if df1[col].dtype in ["int64", "float64"] and col not in ["uid", "rank"]
    ]

    # Iterate over the integer columns and update the values
    for col in int_cols:
        merged_df[col] = merged_df.apply(
            lambda row: pd.to_numeric(row[f"{col}_x"], errors="coerce")
            + pd.to_numeric(row[f"{col}_y"], errors="coerce")
            if pd.notnull(row[f"{col}_x"]) and pd.notnull(row[f"{col}_y"])
            else pd.to_numeric(row[f"{col}_x"], errors="coerce") or 0
            if pd.notnull(row[f"{col}_x"])
            else pd.to_numeric(row[f"{col}_y"], errors="coerce") or 0,
            axis=1,
        )

    if set(["countries", "hashtags", "editors"]).issubset(df1.columns):
        # Get the list of string columns to update
        str_cols = [
            col
            for col in df1.columns
            if df1[col].dtype == "object"
            and col in ["countries", "hashtags", "editors"]
        ]
        # Iterate over the string columns and update the values
        for col in str_cols:
            merged_df[col] = merged_df.apply(
                lambda row: ",".join(
                    set(
                        filter(
                            lambda x: str(x) != "nan",
                            str(row[f"{col}_x"]).split(",")
                            + str(row[f"{col}_y"]).split(","),
                        )
                    )
                ),
                axis=1,
            )

    if set(["tags_create", "tags_modify"]).issubset(df1.columns):
        # Update the 'tags_create' column
        for i, row in merged_df.iterrows():
            tags1 = (
                json.loads(row["tags_create_x"])
                if isinstance(row["tags_create_x"], str)
                else {}
            )
            tags2 = (
                json.loads(row["tags_create_y"])
                if isinstance(row["tags_create_y"], str)
                else {}
            )
            tags = {
                k: tags1.get(k, 0) + tags2.get(k, 0) for k in set(tags1) | set(tags2)
            }
            merged_df.at[i, "tags_create"] = json.dumps(
                dict(
                    sorted(
                        tags.items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                )
            )

        for i, row in merged_df.iterrows():
            tags1 = (
                json.loads(row["tags_modify_x"])
                if isinstance(row["tags_modify_x"], str)
                else {}
            )
            tags2 = (
                json.loads(row["tags_modify_y"])
                if isinstance(row["tags_modify_y"], str)
                else {}
            )
            tags = {
                k: tags1.get(k, 0) + tags2.get(k, 0) for k in set(tags1) | set(tags2)
            }
            merged_df.at[i, "tags_modify"] = json.dumps(
                dict(
                    sorted(
                        tags.items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                )
            )

    # Drop the redundant columns
    merged_df.drop(
        [
            col
            for col in merged_df.columns
            if col.endswith("_x") or col.endswith("_y") and col
        ],
        axis=1,
        inplace=True,
    )

    merged_df = merged_df.sort_values("map_changes", ascending=False)
    merged_df.insert(0, "rank", range(1, len(merged_df) + 1), True)
    print("Updated the stats")
    return merged_df


def update_summary(df1, df2):
    # Merge the dataframes on 'ID'
    merged_df = pd.merge(df1, df2, on="timestamp", how="outer")

    # Get the list of integer columns to update
    int_cols = [
        col
        for col in df1.columns
        if df1[col].dtype in ["int64", "float64"] and col not in ["timestamp"]
    ]

    # Iterate over the integer columns and update the values
    for col in int_cols:
        merged_df[col] = merged_df.apply(
            lambda row: pd.to_numeric(row[f"{col}_x"], errors="coerce")
            + pd.to_numeric(row[f"{col}_y"], errors="coerce")
            if pd.notnull(row[f"{col}_x"]) and pd.notnull(row[f"{col}_y"])
            else pd.to_numeric(row[f"{col}_x"], errors="coerce") or 0
            if pd.notnull(row[f"{col}_x"])
            else pd.to_numeric(row[f"{col}_y"], errors="coerce") or 0,
            axis=1,
        )
    if "editors" in df1.columns:
        # Update the 'editors' column
        for i, row in merged_df.iterrows():
            editors1 = (
                json.loads(row["editors_x"])
                if isinstance(row["editors_x"], str)
                else {}
            )
            editors2 = (
                json.loads(row["editors_y"])
                if isinstance(row["editors_y"], str)
                else {}
            )
            editors = {
                k: editors1.get(k, 0) + editors2.get(k, 0)
                for k in set(editors1) | set(editors2)
            }
            merged_df.at[i, "editors"] = json.dumps(
                dict(
                    sorted(
                        editors.items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                )
            )

    if set(["tags_create", "tags_modify"]).issubset(df1.columns):
        # Update the 'tags_create' column
        for i, row in merged_df.iterrows():
            tags1 = (
                json.loads(row["tags_create_x"])
                if isinstance(row["tags_create_x"], str)
                else {}
            )
            tags2 = (
                json.loads(row["tags_create_y"])
                if isinstance(row["tags_create_y"], str)
                else {}
            )
            tags = {
                k: tags1.get(k, 0) + tags2.get(k, 0) for k in set(tags1) | set(tags2)
            }
            merged_df.at[i, "tags_create"] = json.dumps(
                dict(
                    sorted(
                        tags.items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                )
            )

        for i, row in merged_df.iterrows():
            tags1 = (
                json.loads(row["tags_modify_x"])
                if isinstance(row["tags_modify_x"], str)
                else {}
            )
            tags2 = (
                json.loads(row["tags_modify_y"])
                if isinstance(row["tags_modify_y"], str)
                else {}
            )
            tags = {
                k: tags1.get(k, 0) + tags2.get(k, 0) for k in set(tags1) | set(tags2)
            }
            merged_df.at[i, "tags_modify"] = json.dumps(
                dict(
                    sorted(
                        tags.items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                )
            )

    # Drop the redundant columns
    merged_df.drop(
        [col for col in merged_df.columns if col.endswith("_x") or col.endswith("_y")],
        axis=1,
        inplace=True,
    )
    merged_df = merged_df.sort_values("timestamp", ascending=True)
    return merged_df


def extract_projects(hashtags):
    matches = re.findall(r"#hotosm-project-(\d+)", hashtags)
    return matches


def generate_tm_stats(tm_projects, usernames):
    TM_API_URL = "https://tasking-manager-tm4-production-api.hotosm.org/api/v2/projects"
    tm_user_stats = {}
    for project in tm_projects:
        api_call = f"{TM_API_URL}/{project}/contributions/"
        response = session.get(api_call)
        # response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            for user in data["userContributions"]:
                if user["username"] in usernames:
                    user_project_key = f"{user['username']}_{project}"
                    if user_project_key not in tm_user_stats:
                        tm_user_stats[user_project_key] = {
                            "name": user["username"],
                            "tm_projects": project,
                            "tm_mapping_level": user["mappingLevel"],
                            "tasks_mapped": 0,
                            "tasks_validated": 0,
                            "tasks_total": 0,
                        }
                    tm_user_stats[user_project_key]["tasks_mapped"] += user["mapped"]
                    tm_user_stats[user_project_key]["tasks_validated"] += user[
                        "validated"
                    ]
                    tm_user_stats[user_project_key]["tasks_total"] += user["total"]

    tm_df = pd.DataFrame(list(tm_user_stats.values()))

    tm_df = tm_df.groupby(["name", "tm_projects"], as_index=False).agg(
        {
            "tm_mapping_level": "first",
            "tasks_mapped": "sum",
            "tasks_validated": "sum",
            "tasks_total": "sum",
        }
    )
    return tm_df


def process_boundary(input_data):
    if isinstance(input_data, str):
        try:
            geojson_data = json.loads(input_data)
        except json.JSONDecodeError:
            # If it's not a valid JSON string, treat it as a file path
            if not os.path.isfile(input_data):
                raise ValueError("Invalid file path provided.")
            with open(input_data) as file:
                geojson_data = json.load(file)
    else:
        raise ValueError("Invalid input type. JSON string/file path.")
    geometry = geojson_data.get("geometry")

    if geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("Invalid GeoJSON. Expected Polygon or MultiPolygon geometry.")

    coordinates = geometry.get("coordinates")[0]
    if geometry.get("type") == "Polygon":
        if len(coordinates) < 3:
            raise ValueError(
                "Invalid GeoJSON Polygon. Expected at least three coordinate tuples."
            )
        polygons = [Polygon(coordinates)]
    else:
        polygons = []
        for coords in coordinates:
            if len(coords) < 3:
                raise ValueError(
                    "Invalid GeoJSON MultiPolygon. Expected at least three coordinate tuples."
                )
            polygons.append(Polygon(coords))

    if geometry.get("type") == "MultiPolygon":
        geom = MultiPolygon(polygons)
    else:
        geom = polygons[0]
    ### return geom gdf here
    gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(geom))
    print("Filtering data with: ", gdf)
    return gdf


def get_bbox_centroid(bounds):
    bounds = str(bounds)
    if "invalid" not in bounds:
        bbox_list = bounds.strip("()").split(" ")
        minx, miny = bbox_list[0].split("/")
        maxx, maxy = bbox_list[1].split("/")
        bbox = box(float(minx), float(miny), float(maxx), float(maxy))
        # Create a point for the centroid of the bounding box
        centroid = bbox.centroid
        return centroid
    return None
