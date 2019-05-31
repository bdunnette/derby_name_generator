import os
import random
from time import sleep
import json
import string
import pprint
from pathlib import Path
from operator import itemgetter, attrgetter
from mastodon import Mastodon
from decouple import config
from inscriptis import get_text

API_BASE_URL = config('API_BASE_URL', default='https://mastodon.social')
ACCESS_TOKEN = config('ACCESS_TOKEN')

faved_names_filename = 'data/faved_names.json'
faved_names_file = Path(faved_names_filename)


def download_good_names(mastodon):
    account_id = mastodon.account_verify_credentials()['id']
    print("Downloading favourited statuses...")
    statuses = mastodon.account_statuses(account_id, exclude_replies=True)
    faved = []
    while statuses:
        for s in statuses:
            # print(s)
            if s.favourites_count > 0:
                text = get_text(s.content).strip()
                faves = s.favourites_count
                faved.append({'id': s.id, 'text': text, 'faves': faves})
        faved_sorted = sorted(
            faved, key=lambda toot: toot.get('faves'), reverse=True)
        print("Found {} faved toots...".format(len(faved_sorted)))
        faved_names_file.write_text(json.dumps(faved_sorted))
        statuses = mastodon.fetch_next(statuses)
    return(faved_sorted)


def main():

    mastodon = Mastodon(
        access_token=ACCESS_TOKEN,
        api_base_url=API_BASE_URL,
        ratelimit_method='pace'
    )
    print("Logging on to %s..." % API_BASE_URL)

    faved_names = download_good_names(mastodon)
    print(faved_names)
    # TODO: Pin most-faved toot(s)?


if __name__ == "__main__":
    main()
