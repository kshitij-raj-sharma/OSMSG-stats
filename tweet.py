import json
import os

import tweepy

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


api.update_status(
    status=f"Top 20 Nepal's Contributors This week (from {lstfile[1]} to {lstfile[2][:-4]})\n Check full stats on : https://github.com/kshitijrajsharma/OSMSG/tree/master/stats/Nepal",
    media_ids=[media.media_id],
)
print("twitted")
