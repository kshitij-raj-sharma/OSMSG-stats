import json
import os

import tweepy

# Authenticate using your API keys and access tokens
auth = tweepy.OAuthHandler(os.environ["API_KEY"], os.environ["API_KEY_SECRET"])
auth.set_access_token(os.environ["ACCESS_TOKEN"], os.environ["ACCESS_TOKEN_SECRET"])

api = tweepy.API(auth)

files = os.listdir(os.getcwd())
json_files = [f for f in files if f.endswith(".json")]
first_file = os.path.join(os.getcwd(), json_files[0])


filename = os.path.basename(first_file)

lstfile = filename.split("_")


try:
    api.verify_credentials()
    print("Authentication OK")
except:
    print("Error during authentication")

image = "stats.png"
media = api.media_upload(image)


api.update_status(
    status=f"Top 10 Nepal's {lstfile[0]} This week (from {lstfile[1]} to {lstfile[2][:-5]})\n",
    media_ids=[media.media_id],
)
print("twitted")
