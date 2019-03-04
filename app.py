import os
import string
import random
from flask import Flask, jsonify
from subprocess import check_output
from textgenrnn import textgenrnn
import tensorflow as tf
from keras.backend import clear_session

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

global graph
clear_session()
graph = tf.get_default_graph()

host_ip = check_output(
    ["hostname", "-I"]).splitlines()[0].decode("utf-8").strip()

registered_names_file = 'derby_names.txt'
with open(registered_names_file) as f:
    registered_names = f.read().splitlines()
print("Loaded %s existing names from %s" %
      (len(registered_names), registered_names_file))

textgen = textgenrnn(weights_path='model/derbynames_weights.hdf5',
                     vocab_path='model/derbynames_vocab.json', config_path='model/derbynames_config.json')

app = Flask(__name__, static_url_path='')


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/api/names')
def generate_names():
    temperature = [1.0, 0.5, 0.5, 0.2]
    if textgen is not None:
        with graph.as_default():
            generated_names = textgen.generate(
                temperature=temperature, return_as_list=True)[0].split('\n')
            new_names = [n.strip()
                         for n in generated_names if n not in registered_names]
            return jsonify(names=new_names)


if __name__ == '__main__':
    app.run(host=host_ip)
