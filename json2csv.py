import csv
import json

json_files = ['generated_names', 'registered_names', 'used_names']

for jf in json_files:
    infile = open('data/{}.json'.format(jf), 'r')
    outfile = open('data/{}.csv'.format(jf), 'w')
    print('{} > {}'.format(infile, outfile))
    writer = csv.DictWriter(outfile, fieldnames=['name', 'registered'])
    writer.writeheader()
    for row in json.loads(infile.read()):
        row_dict = {'name': row}
        if jf == 'registered_names':
            row_dict['registered'] = 1
        else:
            row_dict['registered'] = 0
        print(row, row_dict)
        writer.writerow(row_dict)
