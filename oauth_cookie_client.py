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

import argparse
import json
import re
import sys
from getpass import getpass

import requests

CUSTOM_HEADER = {"user-agent": "oauth_cookie_client.py"}


def report_error(message):
    sys.stderr.write("{}\n".format(message))
    exit(1)


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


parser = argparse.ArgumentParser(
    description="Get a cookie to access service protected by OpenStreetMap OAuth 1.0a and osm-internal-oauth"
)
parser.add_argument(
    "-o",
    "--output",
    default=None,
    help="write the cookie to the specified file instead to STDOUT",
    type=argparse.FileType("w+"),
)
parser.add_argument("-u", "--user", default=None, help="user name", type=str)
parser.add_argument(
    "-p",
    "--password",
    default=None,
    help="Password, leave empty to force input from STDIN.",
    type=str,
)
parser.add_argument(
    "-s",
    "--settings",
    default=None,
    help="JSON file containing parameters",
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-c",
    "--consumer-url",
    default=None,
    help="URL of the OAuth cookie generation API of the provider who provides you OAuth protected access to their ressources",
    type=str,
)
parser.add_argument(
    "-f",
    "--format",
    default="http",
    help="Output format: 'http' for the value of the HTTP 'Cookie' header or 'netscape' for a Netscape-like cookie jar file",
    type=str,
    choices=["http", "netscape"],
)
parser.add_argument(
    "--osm-host",
    default="https://www.openstreetmap.org/",
    help="hostname of the OSM API/website to use (e.g. 'www.openstreetmap.org' or 'master.apis.dev.openstreetmap.org')",
    type=str,
)


args = parser.parse_args()
settings = {}
if args.settings is not None:
    settings = json.load(args.settings)

username = settings.get("user", args.user)
if username is None:
    username = input("Please enter your user name and press ENTER: ")
if username is None:
    report_error("The username must not be empty.")
password = settings.get("password", args.password)
if password is None:
    password = getpass("Please enter your password and press ENTER: ")
if len(password) == 0:
    report_error("The password must not be empty.")

osm_host = settings.get("osm_host", args.osm_host)
consumer_url = settings.get("consumer_url", args.consumer_url)
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
url = consumer_url + "?action=get_access_token_cookie&format={}".format(args.format)
r = requests.post(
    url,
    data={
        "oauth_token": oauth_token,
        "oauth_token_secret_encr": oauth_token_secret_encr,
    },
    headers=CUSTOM_HEADER,
)

cookie_text = r.text
if not cookie_text.endswith("\n"):
    cookie_text += "\n"

if not args.output:
    sys.stdout.write(cookie_text)
else:
    args.output.write(cookie_text)
