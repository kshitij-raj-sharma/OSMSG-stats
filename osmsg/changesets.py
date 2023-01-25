import datetime
import datetime as dt
import sys

import requests


class ChangesetToolKit:
    def __init__(
        self, replication_url="https://planet.openstreetmap.org/replication/changesets/"
    ):
        self.replication_url = replication_url

    def get_current_state(self):
        state_yml = requests.get(self.replication_url + "state.yaml").text
        current_sequence = int(state_yml.split("sequence: ")[1])
        last_run = datetime.datetime.strptime(
            state_yml.split("last_run: ")[1][:19], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=dt.timezone.utc)
        return current_sequence, last_run

    def timestamp_to_sequence(self, timestamp):
        current_sequence, last_run = self.get_current_state()
        # Convert the provided timestamp to a sequence number
        desired_sequence = (
            int((timestamp - last_run).total_seconds() / 60) + current_sequence
        )
        # timestamp of sequnce should always be lesser than supplied timestamp
        difference = timestamp - self.sequence_to_timestamp(desired_sequence)

        if self.sequence_to_timestamp(desired_sequence) > timestamp:
            while difference.days != 1:
                desired_sequence = (
                    desired_sequence - 360 if difference >= 2 else 60
                )  # if difference bigger than or equal to  2 day  reduce almost 6 hour else reduce 1 hour
                difference = timestamp - self.sequence_to_timestamp(desired_sequence)

        if (
            difference.days > 1
        ):  # supplied timestamp is higher and captured is lower so increase the sequence
            while difference.days() != 1:
                desired_sequence = (
                    desired_sequence + 360 if difference >= 2 else 60
                )  # if difference bigger than or equal to  2 day  reduce almost 6 hour else reduce 1 hour
                difference = timestamp + self.sequence_to_timestamp(desired_sequence)

        return desired_sequence

    def get_diff_url(self, sequence):
        sequence_str = str(sequence)
        # append leading zeros to make it 9 digits long
        sequence_str = sequence_str.zfill(9)

        diff_url = (
            self.replication_url
            + sequence_str[:3]
            + "/"
            + sequence_str[3:6]
            + "/"
            + sequence_str[6:]
            + ".osm.gz"
        )
        return diff_url

    def get_state_url(self, sequence):
        sequence_str = str(sequence)
        # append leading zeros to make it 9 digits long
        sequence_str = sequence_str.zfill(9)
        # insert slashes in appropriate positions
        state_url = (
            self.replication_url
            + sequence_str[:3]
            + "/"
            + sequence_str[3:6]
            + "/"
            + sequence_str[6:]
            + ".state.txt"
        )
        return state_url

    def sequence_to_timestamp(self, sequence):
        state_url = self.get_state_url(sequence)

        state_yml = requests.get(state_url).text
        last_run = datetime.datetime.strptime(
            state_yml.split("last_run: ")[1][:19], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=dt.timezone.utc)
        return last_run

    def get_download_urls(self, start_date, end_date=None):
        download_urls = []
        start_seq = self.timestamp_to_sequence(start_date)
        if not end_date:
            current_sequence, last_run = self.get_current_state()
            end_date = last_run
            end_seq = current_sequence
        else:
            end_seq = self.timestamp_to_sequence(end_date)
        if start_seq >= end_seq:
            print("Already up-to-date.")
            sys.exit()
        initial_seq = start_seq
        print(f"Changesets: Generating Download URLS from {start_seq} to {end_seq}")
        while start_seq <= end_seq:
            seq_url = self.get_diff_url(start_seq)
            download_urls.append(seq_url)
            start_seq = start_seq + 1
        return download_urls, initial_seq, end_seq
