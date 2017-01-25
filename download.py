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


def tag_entries(entries):

    section_re    = re.compile(r"^Section (\d+\.\d+)")
    article_re    = re.compile(r"^(\d+\.\d+\.\d+\.\d+)")
    subsection_re = re.compile(r"^(\d+\.\d+\.\d+)")
    sentence_re   = re.compile(r"^\((\d+)\)")
    clause_re     = re.compile(r"^\(([a-z]+(?:\.\d+)?)\)")
    subclause_re  = re.compile(r"^\(([ivx]+(?:\.\d+)?)\)")

    def is_section(text, class_name):
        return section_re.match(text)

    def is_article(text, class_name):
        return class_name == "section-e" and article_re.match(text)

    def is_subsection(text, class_name):
        return class_name == "ruleb-e" and subsection_re.match(text)

    def is_sentence(text, class_name):
        return sentence_re.match(text)

    def is_clause(text, class_name):
        return class_name == "clause-e" and clause_re.match(text)

    def is_subclause(text, class_name):
        return class_name == "subclause-e" and subclause_re.match(text)

    for entry in entries:
        text = entry["text"]
        class_name = entry["class_name"]
        if is_section(text, class_name):
            entry["tag"] = "section"
            entry["partial_qualifier"] = section_re.findall(text)[0]
        elif is_article(text, class_name):
            entry["tag"] = "article"
            entry["partial_qualifier"] = article_re.findall(text)[0]
        elif is_subsection(text, class_name):
            entry["tag"] = "subsection"
            entry["partial_qualifier"] = subsection_re.findall(text)[0]
        elif is_sentence(text, class_name):
            entry["tag"] = "sentence"
            entry["partial_qualifier"] = sentence_re.findall(text)[0]
        elif is_clause(text, class_name):
            entry["tag"] = "clause"
            entry["partial_qualifier"] = clause_re.findall(text)[0]
        elif is_subclause(text, class_name):
            entry["tag"] = "subclause"
            entry["partial_qualifier"] = subclause_re.findall(text)[0]
        else:
            entry["tag"] = "fragment"
            entry["partial_qualifier"] = None

def stitch_fragments(entries):
    prev = None
    out_entries = []
    for entry in entries:
        if entry["tag"] == "fragment":
            prev["html"] += " " + entry["html"]
            prev["text"] += " " + entry["text"]
        else:
            out_entries.append(entry)
            prev = entry
    return out_entries

def create_tree(entries):

    def tag_level(entry):
        levels = {
            "root":       0,
            "section":    1,
            "subsection": 2,
            "article":    3,
            "sentence":   4,
            "clause":     5,
            "subclause":  6
        }
        tag = entry["tag"]
        return levels[tag]

    def is_sibling(a, b):
        return tag_level(a) == tag_level(b)

    def is_child_of(a, b):
        return tag_level(a) > tag_level(b)

    def create_node(entry):
        node = dict(entry)
        node["children"] = []
        return node

    stack = [{ "tag": "root", "children": [] }]
    for entry in entries:
        node = create_node(entry)
        if is_sibling(stack[-1], entry):
            stack.pop()
        else:
            while not is_child_of(node, stack[-1]):
                stack.pop()
        stack[-1]["children"].append(node)
        stack.append(node)

    return stack[0]

def main():
    with open(out_file) as f:
        entries = json.loads(f.read())
        tag_entries(entries)
        entries = stitch_fragments(entries)
        tree = create_tree(entries)
        with open("workspace/tree.json", "w") as f:
            tagged_json = json.dumps(tree, indent = 2)
            f.write(tagged_json)

if __name__ == "__main__":
    main()
