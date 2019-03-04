import os
from textgenrnn import textgenrnn

registered_names_file = 'derby_names.txt'
with open(registered_names_file) as f:
    registered_names = f.read().splitlines()
print("Loaded %s existing names from %s" %
      (len(registered_names), registered_names_file))

textgen = textgenrnn(weights_path='model/derbynames_weights.hdf5',
                     vocab_path='model/derbynames_vocab.json', config_path='model/derbynames_config.json')

textgen.generate()
