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
        # timestamp means user supplied time
        if desired_sequence >= current_sequence:
            desired_sequence = current_sequence
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
        start_seq_time = self.sequence_to_timestamp(start_seq)
        if start_seq_time > start_date :
            start_seq = (
                    start_seq - int((start_seq_time - start_date).total_seconds() / 60)
                ) # reduce start_seq to make it even 
            start_seq_time = self.sequence_to_timestamp(start_seq)
        if (start_date - start_seq_time).seconds != 15*60: 
            # difference should be a day difference to calculate accurate changeset stats
            if start_date > start_seq_time:
                start_seq = (
                    start_seq + int((start_date - start_seq_time).total_seconds() / 60)
                ) - 60  # go 1 hour earlier
        if not end_date:
            current_sequence, last_run = self.get_current_state()
            end_date = last_run
            end_seq = current_sequence
        else:
            current_sequence, last_run = self.get_current_state()
            if end_date > last_run:
                print(
                    f"End Date is not available on changeset server changing to latest available date {last_run} "
                )
                end_seq = current_sequence
            else:
                end_seq = self.timestamp_to_sequence(end_date)
                end_seq_time = self.sequence_to_timestamp(end_seq)
                if end_date > end_seq_time:
                    end_seq = (
                            end_seq + int((end_date-end_seq_time).total_seconds() / 60)
                        )+1 # increase end_seq to make it even
                    end_seq_time = self.sequence_to_timestamp(end_seq)
                if end_seq_time > end_date:
                    end_seq = (
                        end_seq + int((end_seq_time - end_date).total_seconds() / 60)
                    ) + 60  # go 1 hours ahead
                if (
                    end_seq > current_sequence
                ):  # if it exceeds more than current seuquence
                    end_seq = current_sequence
        if start_seq >= end_seq:
            print("Changeset : Already up-to-date.")
            sys.exit()
        initial_seq = start_seq
        print(f"Changesets: Generating Download URLS from {start_seq} to {end_seq}")
        while start_seq <= end_seq:
            seq_url = self.get_diff_url(start_seq)
            download_urls.append(seq_url)
            start_seq = start_seq + 1
        return download_urls, initial_seq, end_seq
