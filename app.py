import os
import random
import json
import string
from pathlib import Path
from mastodon import Mastodon
from decouple import config

API_BASE_URL = config('API_BASE_URL', default='https://mastodon.social')
BOT_NAME = config('BOT_NAME', default='derbot')
ACCESS_TOKEN = config('ACCESS_TOKEN')
NAME_BUFFER_SIZE = config('NAME_BUFFER_SIZE', default=20)

registered_names_filename = 'data/registered_names.json'
registered_names_file = Path(registered_names_filename)

generated_names_filename = 'data/generated_names.json'
generated_names_file = Path(generated_names_filename)

used_names_filename = 'data/used_names.json'
used_names_file = Path(used_names_filename)


def download_names():
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
        url3 = "https://rollerderbyroster.com/view-names/?ini={}".format(letter)
        print("Downloading names from %s" % url3)
        r3 = session.get(url3)
        d3 = r3.text
        soup3 = BeautifulSoup(d3, "lxml")

        rows3 = soup3.find_all('ul')
        # Use only last unordered list - this is where names are!
        for idx, li in enumerate(rows3[-1]):
            name_set.add(li.get_text())

    name_list = list(name_set)
    print("Writing %s names to %s..." %
          (len(name_list), registered_names_file))
    registered_names_file.write_text(json.dumps(name_list))


def generate_new_names(name_list):
    from textgenrnn import textgenrnn
    textgen = textgenrnn(weights_path='model/derbynames_weights.hdf5',
                         vocab_path='model/derbynames_vocab.json',
                         config_path='model/derbynames_config.json')

    temperature = [1.0, 0.5, 0.5, 0.2]
    new_names = textgen.generate(
        temperature=temperature, return_as_list=True)[0].split('\n')
    unused_names = [n.strip()
                    for n in generated_names if (n not in registered_names) and (len(n) > 2)]
    return(name_list + new_names)


generated_names = list()
if generated_names_file.is_file():
    json_data = generated_names_file.open().read()
    print(json_data)
    generated_names = json.loads(json_data)

if not registered_names_file.is_file():
    download_names()
registered_names = json.loads(registered_names_file.read_text())
print("Loaded %s existing names from %s" %
      (len(registered_names), registered_names_file))

used_names = list()
if used_names_file.is_file():
    used_names = json.loads(used_names_file.read_text())

mastodon = Mastodon(
    access_token=ACCESS_TOKEN,
    api_base_url=API_BASE_URL
)
print("Logging on to %s..." % API_BASE_URL)

if len(generated_names) < NAME_BUFFER_SIZE:
    # generated_names = generate_new_names(generated_names)
    # Remove first and last names generated, as these are often (usually?) incomplete or nonsensical
    generated_names = generate_new_names(generated_names)[1:-1]
    print("Generated names: {}".format(generated_names))
chosen_name = random.choice(generated_names)
while len(chosen_name) < 2 or (chosen_name in used_names):
    generated_names.remove(chosen_name)
    chosen_name = random.choice(generated_names)
print("Tooting name: {}".format(chosen_name))
generated_names.remove(chosen_name)
mastodon.toot(chosen_name)
used_names.append(chosen_name)
print("Used names: {}".format(used_names))
used_names_file.write_text(json.dumps(used_names))
generated_names_file.write_text(json.dumps(generated_names))
