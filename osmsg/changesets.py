import datetime
import os

import requests


def sequence_to_url(sequence):
    # convert the sequence number to a string
    sequence_str = str(sequence)
    # append leading zeros to make it 9 digits long
    sequence_str = sequence_str.zfill(9)
    # insert slashes in appropriate positions
    state_url = (
        sequence_str[:3]
        + "/"
        + sequence_str[3:6]
        + "/"
        + sequence_str[6:]
        + ".state.txt"
    )
    changefile_url = (
        sequence_str[:3] + "/" + sequence_str[3:6] + "/" + sequence_str[6:] + ".osm.gz"
    )
    return state_url, changefile_url


def sequence_to_timestamp(state_url):

    state_yml = requests.get(state_url).text
    captured_sequence = int(state_yml.split("sequence: ")[1])
    last_run = datetime.datetime.strptime(
        state_yml.split("last_run: ")[1][:19], "%Y-%m-%d %H:%M:%S"
    )
    return last_run, captured_sequence


def find_replication_file(timestamp):
    # Define the replication URL
    replication_url = "https://planet.openstreetmap.org/replication/changesets/"
    # Get the current sequence number and last run date from the state.yml file
    state_yml = requests.get(replication_url + "state.yaml").text
    print(state_yml)
    current_sequence = int(state_yml.split("sequence: ")[1])
    last_run = datetime.datetime.strptime(
        state_yml.split("last_run: ")[1][:19], "%Y-%m-%d %H:%M:%S"
    )
    # Convert the provided timestamp to a sequence number
    desired_sequence = (
        int((timestamp - last_run).total_seconds() / 60) + current_sequence
    )

    (
        sequenceurl,
        change_file_url,
    ) = f"{replication_url}{sequence_to_url(desired_sequence)}"
    print(sequenceurl)
    captured_timestamp, captured_sequence = sequence_to_timestamp(sequenceurl)
    if captured_timestamp < timestamp:
        return change_file_url, captured_sequence
