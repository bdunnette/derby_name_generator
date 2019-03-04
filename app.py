import os
import random
from textgenrnn import textgenrnn
from mastodon import Mastodon
from decouple import config

API_BASE_URL = config('API_BASE_URL', default='https://mastodon.social')
BOT_NAME = config('BOT_NAME', default='derbot')
ACCESS_TOKEN = config('ACCESS_TOKEN')

registered_names_file = 'derby_names.txt'
with open(registered_names_file) as f:
    registered_names = f.read().splitlines()
print("Loaded %s existing names from %s" %
      (len(registered_names), registered_names_file))

mastodon = Mastodon(
    access_token=ACCESS_TOKEN,
    api_base_url=API_BASE_URL
)
print("Logging on to %s..." % API_BASE_URL)

textgen = textgenrnn(weights_path='model/derbynames_weights.hdf5',
                     vocab_path='model/derbynames_vocab.json', 
                     config_path='model/derbynames_config.json')

temperature = [1.0, 0.5, 0.5, 0.2]
generated_names = textgen.generate(
    temperature=temperature, return_as_list=True)[0].split('\n')
new_names = [n.strip()
             for n in generated_names if n not in registered_names]
print("Generated names: {}".format(new_names))
chosen_name = random.choice(new_names)
print("Tooting name: {}".format(chosen_name))
mastodon.toot(chosen_name)
