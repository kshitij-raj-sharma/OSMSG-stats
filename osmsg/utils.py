#! /usr/bin/env python3
# Copyright 2018 Geofabrik GmbH
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import ast
import gzip
import json
import os
import re
import shutil
import sys
import urllib.parse
from collections import defaultdict

import humanize
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import requests
import seaborn as sns

CUSTOM_HEADER = {"user-agent": "oauth_cookie_client.py"}


class RaiseError(Exception):
    def __init__(self, message):
        self.message = message


def report_error(message):
    sys.stderr.write("{}\n".format(message))
    raise RaiseError(message)


def find_authenticity_token(response):
    """
    Search the authenticity_token in the response of the server
    """
    pattern = r"name=\"csrf-token\" content=\"([^\"]+)\""
    m = re.search(pattern, response)
    if m is None:
        report_error(
            "Could not find the authenticity_token in the website to be scraped."
        )
    try:
        return m.group(1)
    except IndexError:
        sys.stderr.write(
            "ERROR: The login form does not contain an authenticity_token.\n"
        )
        exit(1)


def verify_me_osm(
    user,
    password,
    osm_host="https://www.openstreetmap.org/",
    consumer_url="https://osm-internal.download.geofabrik.de/get_cookie",
    format="http",
):

    username = user
    if username is None:
        report_error("The username must not be empty.")
    if len(password) == 0 or password is None:
        report_error("The password must not be empty.")
    if consumer_url is None:
        report_error("No consumer URL provided")

    # get request token
    url = consumer_url + "?action=request_token"
    r = requests.post(url, data={}, headers=CUSTOM_HEADER)
    if r.status_code != 200:
        report_error(
            "POST {}, received HTTP status code {} but expected 200".format(
                url, r.status_code
            )
        )
    json_response = json.loads(r.text)
    authorize_url = osm_host + "/oauth/authorize"
    try:
        oauth_token = json_response["oauth_token"]
        oauth_token_secret_encr = json_response["oauth_token_secret_encr"]
    except KeyError:
        report_error("oauth_token was not found in the first response by the consumer")

    # get OSM session
    login_url = osm_host + "/login?cookie_test=true"
    s = requests.Session()
    r = s.get(login_url, headers=CUSTOM_HEADER)
    if r.status_code != 200:
        report_error("GET {}, received HTTP code {}".format(login_url, r.status_code))

    # login
    authenticity_token = find_authenticity_token(r.text)
    login_url = osm_host + "/login"
    r = s.post(
        login_url,
        data={
            "username": username,
            "password": password,
            "referer": "/",
            "commit": "Login",
            "authenticity_token": authenticity_token,
        },
        allow_redirects=False,
        headers=CUSTOM_HEADER,
    )
    if r.status_code != 302:
        report_error(
            "POST {}, received HTTP code {} but expected 302".format(
                login_url, r.status_code
            )
        )

    # authorize
    authorize_url = "{}/oauth/authorize?oauth_token={}".format(osm_host, oauth_token)
    r = s.get(authorize_url, headers=CUSTOM_HEADER)
    if r.status_code != 200:
        report_error(
            "GET {}, received HTTP code {} but expected 200".format(
                authorize_url, r.status_code
            )
        )
    authenticity_token = find_authenticity_token(r.text)

    post_data = {
        "oauth_token": oauth_token,
        "oauth_callback": "",
        "authenticity_token": authenticity_token,
        "allow_read_prefs": [0, 1],
        "commit": "Save changes",
    }
    authorize_url = "{}/oauth/authorize".format(osm_host)
    r = s.post(authorize_url, data=post_data, headers=CUSTOM_HEADER)
    if r.status_code != 200:
        report_error(
            "POST {}, received HTTP code {} but expected 200".format(
                authorize_url, r.status_code
            )
        )

    # logout
    logout_url = "{}/logout".format(osm_host)
    r = s.get(logout_url, headers=CUSTOM_HEADER)
    if r.status_code != 200 and r.status_code != 302:
        report_error(
            "POST {}, received HTTP code {} but expected 200 or 302".format(logout_url)
        )

    # get final cookie
    url = consumer_url + "?action=get_access_token_cookie&format={}".format(format)
    r = requests.post(
        url,
        data={
            "oauth_token": oauth_token,
            "oauth_token_secret_encr": oauth_token_secret_encr,
        },
        headers=CUSTOM_HEADER,
    )

    return str(r.text)


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
    if "countries" in df.columns[df.astype(bool).any()]:

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

        font = fm.FontProperties(family="Arial", size=12)
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
        plt.savefig("tags.png", bbox_inches="tight")


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
                response = requests.get(url, cookies=cookies_fmt)
            else:
                response = requests.get(url)

            if not response.status_code == 200:
                sys.exit()

            file_data = response.content
            # Create the directory if it does not exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "xb") as f:
                f.write(file_data)

        with gzip.open(file_path, "rb") as f_in, open(file_path[:-3], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(file_path)
