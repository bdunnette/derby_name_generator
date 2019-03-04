import os
import random
from textgenrnn import textgenrnn
from mastodon import Mastodon
from decouple import config

API_BASE_URL = config('API_BASE_URL', default='https://mastodon.social')
BOT_NAME = config('BOT_NAME', default='derbot')
CLIENTCRED_FILE = config(
    'CLIENTCRED_FILE', default='{}_clientcred.secret'.format(BOT_NAME))
USERCRED_FILE = config(
    'USERCRED_FILE', default='{}_usercred.secret'.format(BOT_NAME))
USERNAME = config('USERNAME')
PASSWORD = config('PASSWORD')

registered_names_file = 'derby_names.txt'
with open(registered_names_file) as f:
    registered_names = f.read().splitlines()
print("Loaded %s existing names from %s" %
      (len(registered_names), registered_names_file))

if not os.path.isfile(CLIENTCRED_FILE):
    Mastodon.create_app(
        BOT_NAME,
        api_base_url=API_BASE_URL,
        to_file=CLIENTCRED_FILE
    )

mastodon = Mastodon(
    client_id=CLIENTCRED_FILE,
    api_base_url=API_BASE_URL
)

mastodon.log_in(
    USERNAME,
    PASSWORD,
    to_file=USERCRED_FILE
)

textgen = textgenrnn(weights_path='model/derbynames_weights.hdf5',
                     vocab_path='model/derbynames_vocab.json', config_path='model/derbynames_config.json')

temperature = [1.0, 0.5, 0.5, 0.2]
generated_names = textgen.generate(
    temperature=temperature, return_as_list=True)[0].split('\n')
new_names = [n.strip()
             for n in generated_names if n not in registered_names]
print("Generated names: {}".format(new_names))
chosen_name = random.choice(new_names)
print("Tooting name: {}".format(chosen_name))
mastodon.toot(chosen_name)
