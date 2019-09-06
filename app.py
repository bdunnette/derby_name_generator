import os
import random
from time import sleep
import json
import string
import pprint
from itertools import chain
from pathlib import Path
from mastodon import Mastodon
from decouple import config
from inscriptis import get_text
import nltk

API_BASE_URL = config('API_BASE_URL', default='https://mastodon.social')
ACCESS_TOKEN = config('ACCESS_TOKEN')
ACTUALLY_TOOT = config('ACTUALLY_TOOT', default=False, cast=bool)

MODEL_NAME = config('MODEL_NAME', default='derbynames')
NAME_BUFFER_SIZE = config('NAME_BUFFER_SIZE', default=100)

DEFAULT_TEMP = config('DEFAULT_TEMP', default=1.0)
USE_RANDOM_TEMPS = config('USE_RANDOM_TEMPS', default=True, cast=bool)
MIN_TEMP = config('MIN_TEMP', default=0.2, cast=float)
MAX_TEMP = config('MAX_TEMP', default=1.0, cast=float)

DO_WAIT = config('DO_WAIT', default=False, cast=bool)
MIN_WAIT = config('MIN_WAIT', default=10, cast=int)
MAX_WAIT = config('MAX_WAIT', default=300, cast=int)

registered_names_filename = 'data/registered_names.json'
registered_names_file = Path(registered_names_filename)

generated_names_filename = 'data/generated_names.json'
generated_names_file = Path(generated_names_filename)

used_names_filename = 'data/used_names.json'
used_names_file = Path(used_names_filename)

nltk.download('words')
dictionary_words = nltk.corpus.words.words()


def is_dictionary_word(word):
    if word in dictionary_words or word.lower().strip() in dictionary_words:
        return True
    else:
        return False


def download_registered_names():
    from bs4 import BeautifulSoup
    import requests

    name_set = set()
    session = requests.Session()

    url1 = "https://www.twoevils.org/rollergirls/"
    print("Downloading names from %s" % url1)
    r1 = session.get(url1)
    soup1 = BeautifulSoup(r1.text, "lxml")
    rows1 = soup1.find_all('tr', {'class': ['trc1', 'trc2']})

    for idx, row in enumerate(rows1):
        td = row.find('td')
        name_set.add(td.get_text())

    url2 = "http://www.derbyrollcall.com/everyone"
    print("Downloading names from %s" % url2)
    r2 = session.get(url2)
    soup2 = BeautifulSoup(r2.text, "lxml")
    rows2 = soup2.find_all('td', {'class': 'name'})

    for idx, td in enumerate(rows2):
        name_set.add(td.get_text())

    initial_letters = string.ascii_uppercase
    # Loop through initial letters (A-Z)
    for letter in initial_letters:
        url3 = "https://rollerderbyroster.com/view-names/?ini={}".format(
            letter)
        print("Downloading names from {}".format(url3))
        r3 = session.get(url3)
        d3 = r3.text
        soup3 = BeautifulSoup(d3, "lxml")

        rows3 = soup3.find_all('ul')
        # Use only last unordered list - this is where names are!
        for idx, li in enumerate(rows3[-1]):
            # Name should be the text of the link within the list item
            name = li.find('a').get_text()
            name_set.add(name)

    name_list = list(name_set)
    print("Writing %s names to %s..." %
          (len(name_list), registered_names_file))
    registered_names_file.write_text(json.dumps(name_list))


def download_used_names(mastodon):
    downloaded_names = list()
    account_id = mastodon.account_verify_credentials()['id']
    statuses = mastodon.account_statuses(account_id, exclude_replies=True)
    names = [get_text(s.content).strip() for s in statuses]
    downloaded_names.extend(names)
    print("Downloaded {} used names...".format(len(downloaded_names)))
    next_page = mastodon.fetch_next(statuses)
    while next_page:
        names = [get_text(s.content).strip() for s in next_page]
        downloaded_names.extend(names)
        print("Downloaded {} used names...".format(len(downloaded_names)))
        used_names_file.write_text(json.dumps(downloaded_names))
        next_page = mastodon.fetch_next(next_page)
    print("Saved {} used names to {}".format(
        len(downloaded_names), used_names_file))


def generate_new_names(skip_names=[], model_name=MODEL_NAME, batch_size=10, random_temps=True):
    from textgenrnn import textgenrnn
    textgen = textgenrnn(weights_path='model/{}_weights.hdf5'.format(model_name),
                         vocab_path='model/{}_vocab.json'.format(model_name),
                         config_path='model/{}_config.json'.format(model_name))

    temperature = []
    if random_temps is True:
        for i in range(batch_size):
            temp = round(random.uniform(MIN_TEMP, MAX_TEMP), 1)
            temperature.append(temp)
    else:
        temperature.append(DEFAULT_TEMP)
    new_names = textgen.generate(batch_size,
                                 temperature=temperature, return_as_list=True)
    # Discard used and short names
    unused_names = [n.strip()
                    for n in new_names if (len(n.strip()) > 3) and (n not in skip_names) and (not is_dictionary_word(n))]
    return(unused_names)


def main():
    registered_names = list()
    if not registered_names_file.is_file():
        download_registered_names()
    registered_names = sorted(json.loads(registered_names_file.read_text()))
    print("Loaded %s existing names from %s" %
          (len(registered_names), registered_names_file))
    
    mastodon = Mastodon(
        access_token=ACCESS_TOKEN,
        api_base_url=API_BASE_URL,
        ratelimit_method='pace'
    )
    print("Logging on to %s..." % API_BASE_URL)

    used_names = list()
    if not used_names_file.is_file():
        print("Used names not found, downloading...")
        download_used_names(mastodon)
    used_names = json.loads(used_names_file.read_text())
    print("Loaded %s existing names from %s" %
          (len(used_names), used_names_file))

    skip_names = used_names + registered_names

    generated_names = list()
    if generated_names_file.is_file():
        json_data = generated_names_file.open().read()
        # print(json_data)
        generated_names = list(set(json.loads(json_data)))
        print("Loaded %s existing names from %s" %
              (len(generated_names), generated_names_file))
        print("Filtering generated names...")
        generated_names = [
            n for n in generated_names if n not in skip_names]
        generated_names.sort()

    if len(generated_names) < NAME_BUFFER_SIZE:
        new_names = generate_new_names(
            skip_names=skip_names)
        print("Generated names: {}".format(new_names))
        generated_names.extend(new_names)

    print("%s generated names ready!" % len(generated_names))
    chosen_name = random.choice(generated_names)
    print("Chosen name: {}".format(chosen_name))
    
    if DO_WAIT is True:
        sleep_time = random.randint(MIN_WAIT, MAX_WAIT)
        print("Waiting {} seconds...".format(sleep_time))
        sleep(sleep_time)

    if ACTUALLY_TOOT is True:
        print("Tooting name: {}".format(chosen_name))
        mastodon.toot(chosen_name)
        generated_names.remove(chosen_name)
        generated_names_file.write_text(json.dumps(generated_names))
        used_names.append(chosen_name)
        used_names_file.write_text(json.dumps(used_names))


if __name__ == "__main__":
    main()
