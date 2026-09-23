"""Checks the generated JSON: valid against the Postman v2.1 schema, no
credentials committed, and every request documented with an example."""

import json
import re
import sys
from pathlib import Path

import jsonschema
import requests

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_URL = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
KEY_RE = re.compile(r"sk_[A-Za-z0-9]{48}|gho_|ghp_|Bearer [A-Za-z0-9._-]{20,}")

errors = []
schema = requests.get(SCHEMA_URL, timeout=30).json()


def walk(items, trail):
    for it in items:
        name = " / ".join(trail + [it["name"]])
        if "item" in it:
            if not it.get("description"):
                errors.append(f"{name}: folder has no description")
            walk(it["item"], trail + [it["name"]])
            continue
        if not it["request"].get("description"):
            errors.append(f"{name}: request has no description")
        if not it.get("response"):
            errors.append(f"{name}: request has no saved example response")
        for r in it.get("response", []):
            try:
                json.loads(r["body"])
            except ValueError:
                errors.append(f"{name} / {r['name']}: example body is not JSON")


for path in sorted((ROOT / "collections").glob("*.json")):
    coll = json.loads(path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(coll, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"{path.name}: schema: {e.message} at {list(e.absolute_path)}")
    walk(coll["item"], [path.stem])

for path in sorted((ROOT / "environments").glob("*.json")):
    env = json.loads(path.read_text(encoding="utf-8"))
    for v in env["values"]:
        if v["type"] == "secret" and v["value"]:
            errors.append(f"{path.name}: secret {v['key']} has a value committed")

for path in list((ROOT / "collections").glob("*.json")) + list((ROOT / "environments").glob("*.json")):
    if KEY_RE.search(path.read_text(encoding="utf-8")):
        errors.append(f"{path.name}: looks like a real credential")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print("ok: collections match the Postman v2.1 schema, no credentials, every request documented")
