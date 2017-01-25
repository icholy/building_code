#!/usr/bin/env python

import requests
import json
import ipdb
from BeautifulSoup import BeautifulSoup

url = "https://www.ontario.ca/laws/regulation/120332"
class_names = [
    "ruleb-e",
    "section-e",
    "subsection-e",
    "clause-e",
    "subclause-e"
]
out_file = "workspace/raw.json"

def inner_html(e):
    return "".join([str(x) for x in e.contents])

def download():
    print("fetching {}".format(url))
    resp = requests.get(url)
    print("parsing html ...")
    soup = BeautifulSoup(resp.text)
    elements = soup("p", { "class": class_names })
    lines = [ inner_html(e) for e in elements ]
    print("writing {} lines to {} ...".format(len(lines), out_file))
    with open(out_file, "w") as f:
        f.write(json.dumps(lines, indent = 2))
    print("done!")

def main():
    download()

if __name__ == "__main__":
    main()
