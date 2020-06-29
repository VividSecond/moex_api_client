import csv
import json
import requests

def save_json(data, file_name):
    with open(file_name, "w") as f:
        json.dump(data, f, indent=2)


def save_to_csv(data, file_name):
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def read_csv(file_name):
    rows = []
    with open(file_name, 'r', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        rows = [row for row in spamreader]
    return rows


def get_raw_html(url):
    page_request = requests.get(url)
    page_request.raise_for_status()
    return page_request.text

def get_node(node, *node_names):
    next_node = node
    # TODO: wrap with try/catch block
    for next_name in node_names:
        next_node = next_node[next_name]
    return next_node
    
