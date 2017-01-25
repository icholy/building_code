#!/usr/bin/env python

import requests
import json
import ipdb
import re
from BeautifulSoup import BeautifulSoup

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

    def is_child_of(a, b):
        return tag_level(a) > tag_level(b)

    def create_node(entry):
        node = dict(entry)
        node["children"] = []
        return node

    stack = [{ "tag": "root", "children": [], "partial_qualifier": "" }]
    for entry in entries:
        node = create_node(entry)
        while not is_child_of(node, stack[-1]):
            stack.pop()
        stack[-1]["children"].append(node)
        stack.append(node)

    return stack[0]

def qualify_tree(node, parent=None):
    tag = node["tag"]
    if tag in ["root", "section", "subsection", "article"]:
        node["qualifier"] = node["partial_qualifier"]
    else:
        node["qualifier"] = "{}.({})".format(parent["qualifier"], node["partial_qualifier"])
    for child in node["children"]:
        qualify_tree(child, node)

def download_entries():

    def parse_element(e):
        return {
            "html":       "".join([str(x) for x in e.contents]),
            "text":       e.text,
            "class_name": e.attrMap["class"]
        }

    url = "https://www.ontario.ca/laws/regulation/120332"
    class_names = [
        "ruleb-e",
        "section-e",
        "subsection-e",
        "clause-e",
        "subclause-e"
    ]

    print("fetching {}".format(url))
    resp = requests.get(url)
    print("parsing html ...")
    soup = BeautifulSoup(resp.text)
    elements = soup("p", { "class": class_names })
    return [ parse_element(e) for e in elements ]

def clean_up_tree(node):
    del node["partial_qualifier"]
    if node["tag"] != "root":
        del node["class_name"]
        del node["text"]
    for child in node["children"]:
        clean_up_tree(child)

def main():
    entries = download_entries()
    tag_entries(entries)
    entries = stitch_fragments(entries)
    print("parsing {} entries into tree ...".format(len(entries)))
    tree = create_tree(entries)
    qualify_tree(tree)
    clean_up_tree(tree)
    out_file = "workspace/tree.json"
    print("writing to {} ...".format(out_file))
    with open(out_file, "w") as f:
        tagged_json = json.dumps(tree, indent = 2)
        f.write(tagged_json)
    print("done!")

if __name__ == "__main__":
    main()
