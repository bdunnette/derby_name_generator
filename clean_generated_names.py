import os
import json
import string
import pprint
from itertools import chain
from pathlib import Path
import nltk


registered_names_filename = 'data/registered_names.json'
registered_names_file = Path(registered_names_filename)

generated_names_filename = 'data/generated_names.json'
generated_names_file = Path(generated_names_filename)

used_names_filename = 'data/used_names.json'
used_names_file = Path(used_names_filename)

dictionary_words = nltk.corpus.words.words()


def is_dictionary_word(word, check_lower=True):
    if word in dictionary_words:
        return True
    if check_lower is True and word.lower().strip() in dictionary_words:
        return True
    else:
        return False


def main():
    registered_names = json.loads(registered_names_file.read_text())
    print("Loaded %s registered names from %s" %
          (len(registered_names), registered_names_file))

    used_names = json.loads(used_names_file.read_text())
    print("Loaded %s used names from %s" %
          (len(used_names), used_names_file))

    skip_names = set(chain(used_names, registered_names))
    nltk.download('words')

    generated_names = list()
    json_data = generated_names_file.open().read()
    generated_names = sorted(list(set(json.loads(json_data))))
    print("Loaded %s generated names from %s" %
          (len(generated_names), generated_names_file))
    print("Filtering used names...")
    generated_names = [n for n in generated_names if n not in skip_names]
    print("%s unused names available!" % len(generated_names))
    print("Filtering dictionary names...")
    dictionary_names = list()
    for n in generated_names:
        if is_dictionary_word(n):
            generated_names.remove(n)
            dictionary_names.append(n)
            generated_names_file.write_text(json.dumps(generated_names))
            print(n, len(generated_names))
    # generated_names = [n for n in generated_names if not is_dictionary_word(n)]
    # dict_names = [n for n in generated_names if is_dictionary_word(n)]
    print("Removed {} dictionary names".format(len(dictionary_names)))
    print("%s generated names ready!" % len(generated_names))


if __name__ == "__main__":
    main()
