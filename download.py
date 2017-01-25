#!/usr/bin/env python

import requests
import json
import ipdb
import re
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

def parse_element(e):
    return {
        "html":       "".join([str(x) for x in e.contents]),
        "text":       e.text,
        "class_name": e.attrMap["class"]
    }

def download():
    print("fetching {}".format(url))
    resp = requests.get(url)
    print("parsing html ...")
    soup = BeautifulSoup(resp.text)
    elements = soup("p", { "class": class_names })
    entries = [ parse_element(e) for e in elements ]
    print("writing {} entries to {} ...".format(len(entries), out_file))
    with open(out_file, "w") as f:
        f.write(json.dumps(entries, indent = 2))
    print("done!")

section_re    = re.compile(r"Section \d+\.\d+")
article_re    = re.compile(r"\d+\.\d+\.\d+\.\d+")
subsection_re = re.compile(r"\d+\.\d+\.\d+")
sentence_re   = re.compile(r"\(\d+\)")
clause_re     = re.compile(r"\([a-z]+(\.\d+)?\)")
subclause_re  = re.compile(r"\([ivx]+(\.\d+)?\)")

def get_tag(entry):
    text = entry["text"]
    class_name = entry["class_name"]
    if section_re.match(text):
        return "section"
    if class_name == "section-e" and article_re.match(text):
        return "article"
    if class_name == "ruleb-e" and subsection_re.match(text):
        return "subsection"
    if sentence_re.match(text):
        return "sentence"
    if class_name == "clause-e" and clause_re.match(text):
        return "clause"
    if class_name == "subclause-e" and subclause_re.match(text):
        return "subclause"
    return "fragment"

def tag_entries():
    with open(out_file) as f:
        entries = json.loads(f.read())
        for entry in entries:
            entry["tag"] = get_tag(entry)
        with open("workspace/tagged.json", "w") as f:
            tagged_json = json.dumps(entries, indent = 2)
            f.write(tagged_json)

def main():
    tag_entries()

if __name__ == "__main__":
    main()
