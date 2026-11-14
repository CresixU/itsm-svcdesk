# ai-generated: 90% - Claude Code wrote this from CI-SPEC.md section 3 (P-14..P-22) and checked it against the practice set's expected.json; the author reviews it
"""bakeoff.py - scanner SARIF + a labels file -> a per-tool confusion matrix (CI-SPEC.md P-23).

Standard library only: it runs as `python3 -S -E bakeoff.py`.

    python3 bakeoff.py --labels labels.json a.sarif b.sarif > bakeoff.json

The rules, in the order they are applied (every id is a rule of CI-SPEC.md):

    P-15  every entry of runs[] is a run of a tool; runs with the same tool id are one tool
    P-16  a result counts when its kind is absent/null/"fail" and it has no suppressions
    P-17  its path is the first location's uri, decoded; it is in the set when a component equals the set root
    P-18  its lines are startLine..endLine (integers only)
    P-19  its classes: properties.class, else by tool, else the CWE ids in the tags, else "other"
    P-20  it matches a defect on file + class + (package name | overlapping lines)
    P-21  TP = defects found, FN = defects missed, FP = distinct (ruleId, file, start, end) matching nothing
    P-22  precision, recall and F1, `null` when the denominator is 0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import unquote

# P-19: the ten course classes and their CWE numbers.
CLASS_CWES: dict[str, frozenset[int]] = {
    "secret": frozenset({259, 260, 321, 798}),
    "injection": frozenset({74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336}),
    "deserialization": frozenset({502}),
    "weak-crypto": frozenset({261, 326, 327, 328, 330, 331, 338, 759, 760, 916}),
    "insecure-transport": frozenset({295, 297, 319, 322, 757}),
    "path-traversal": frozenset({22, 23, 35, 36, 73}),
    "ssrf": frozenset({918}),
    "vulnerable-dependency": frozenset({937, 1035, 1104, 1395}),
    "misconfiguration": frozenset({16, 215, 250, 489, 668, 732, 1188}),
    "access-control": frozenset({284, 285, 639, 862, 863}),
}
CLASS_NAMES = frozenset(CLASS_CWES)

SEMGREP_NAMES = frozenset(
    {"semgrep", "semgrep oss", "semgrep ce", "semgrep community edition", "semgrep pro"}
)

# "CWE" in any letter case, not preceded by an ASCII letter or digit, then a hyphen and the whole run of ASCII digits.
CWE_RE = re.compile(r"(?<![A-Za-z0-9])[Cc][Ww][Ee]-([0-9]+)")
# P-20: a token is a maximal run of these characters, with . _ - removed from both ends.
TOKEN_RE = re.compile(r"[A-Za-z0-9._-]+")
PEP503_RE = re.compile(r"[-_.]+")


def as_dict(value) -> dict:
    """A member that is not an object has no members (null counts as absent throughout)."""
    return value if isinstance(value, dict) else {}


def as_list(value) -> list:
    """A member that is not an array has no entries."""
    return value if isinstance(value, list) else []


def is_int(value) -> bool:
    """A JSON integer: 7.0, "7" and true are not."""
    return isinstance(value, int) and not isinstance(value, bool)


# ---------------------------------------------------------------- P-15 tools

def tool_id(run: dict) -> str:
    name = as_dict(as_dict(run.get("tool")).get("driver")).get("name")
    if not isinstance(name, str):
        return "unknown"
    lowered = name.strip().lower()
    if lowered in SEMGREP_NAMES:
        return "semgrep"
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "unknown"


# ---------------------------------------------------------------- P-16 results

def keeps(result: dict) -> bool:
    kind = result.get("kind")
    if kind is not None and kind != "fail":
        return False
    suppressions = result.get("suppressions")
    if suppressions is None:
        return True
    # [], {}, false, 0 and "" are empty; anything else (even [null]) drops the result.
    return not suppressions


def first_physical_location(result: dict) -> dict:
    locations = as_list(result.get("locations"))
    if not locations:
        return {}
    return as_dict(as_dict(locations[0]).get("physicalLocation"))


# ---------------------------------------------------------------- P-17 paths

def normalise_path(uri: str) -> str:
    path = unquote(uri)
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]
    return path


def file_in_set(uri: str, root: str) -> str | None:
    """The file of a result when it is in the set (from the LAST component equal to the root), else None."""
    parts = normalise_path(uri).split("/")
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == root:
            return "/".join(parts[index:])
    return None


# ---------------------------------------------------------------- P-18 lines

def lines_of(location: dict) -> tuple[int | None, int | None]:
    region = as_dict(location.get("region"))
    start = region.get("startLine")
    if not is_int(start) or start < 1:
        return None, None
    end = region.get("endLine")
    if not is_int(end) or end < start:
        end = start
    return start, end


# ---------------------------------------------------------------- P-19 classes

def tags_of(properties) -> list[str]:
    return [tag for tag in as_list(as_dict(properties).get("tags")) if isinstance(tag, str)]


def cwe_classes(tags: list[str]) -> set[str]:
    found: set[str] = set()
    for tag in tags:
        for match in CWE_RE.finditer(tag):
            number = int(match.group(1))
            for name, numbers in CLASS_CWES.items():
                if number in numbers:
                    found.add(name)
    return found


def result_classes(tool: str, result: dict, rule: dict) -> set[str]:
    properties = as_dict(result.get("properties"))
    # (a) the result's own class
    own = properties.get("class")
    if isinstance(own, str) and own in CLASS_NAMES:
        return {own}
    # (b) by tool
    if tool == "gitleaks":
        return {"secret"}
    if tool in ("grype", "osv-scanner"):
        return {"vulnerable-dependency"}
    if tool == "trivy":
        by_tag = {
            "vulnerability": "vulnerable-dependency",
            "secret": "secret",
            "misconfiguration": "misconfiguration",
        }
        found = {by_tag[tag.lower()] for tag in tags_of(rule.get("properties")) if tag.lower() in by_tag}
        if found:
            return found
    # (c) CWE ids in the tags of the result or of its rule
    found = cwe_classes(tags_of(properties) + tags_of(rule.get("properties")))
    if found:
        return found
    # (d) nothing: matches no defect
    return {"other"}


# ---------------------------------------------------------------- P-20 matching

def pep503(name: str) -> str:
    return PEP503_RE.sub("-", name.lower())


def names_package(result: dict, package: str) -> bool:
    text = as_dict(result.get("message")).get("text")
    if not isinstance(text, str):
        return False
    wanted = pep503(package)
    for token in TOKEN_RE.findall(text):
        token = token.strip("._-")
        if token and pep503(token) == wanted:
            return True
    return False


def matches(defect: dict, file: str, classes: set[str], lines: tuple, result: dict) -> bool:
    if defect.get("file") != file or defect.get("class") not in classes:
        return False
    if defect["class"] == "vulnerable-dependency":
        package = defect.get("package")
        return isinstance(package, str) and names_package(result, package)
    start, end = lines
    if start is None:
        return False
    d_start, d_end = defect.get("start_line"), defect.get("end_line")
    if not is_int(d_start) or not is_int(d_end):
        return False
    return start <= d_end and d_start <= end


# ---------------------------------------------------------------- P-21 / P-22 counting and scores

def score(numerator: float, denominator: float):
    return None if denominator == 0 else round(numerator / denominator, 4)


def confusion_matrix(labels: dict, sarif_documents: list) -> dict:
    root = labels["set"]
    defects = [d for d in as_list(labels.get("defects")) if isinstance(d, dict)]
    found: dict[str, set[int]] = {}   # tool id -> indexes of the defects it matched
    false_positives: dict[str, set] = {}  # tool id -> distinct (ruleId, file, start, end)

    for document in sarif_documents:
        for run in as_list(as_dict(document).get("runs")):
            if not isinstance(run, dict):
                continue
            tool = tool_id(run)
            found.setdefault(tool, set())
            false_positives.setdefault(tool, set())

            rules: dict[str, dict] = {}
            for rule in as_list(as_dict(as_dict(run.get("tool")).get("driver")).get("rules")):
                if isinstance(rule, dict) and isinstance(rule.get("id"), str):
                    rules.setdefault(rule["id"], rule)  # the first entry with that id

            for result in as_list(run.get("results")):
                if not isinstance(result, dict) or not keeps(result):
                    continue
                location = first_physical_location(result)
                uri = as_dict(location.get("artifactLocation")).get("uri")
                if not isinstance(uri, str) or uri == "":
                    continue
                file = file_in_set(uri, root)
                if file is None:
                    continue  # outside the set: triage material, not part of the matrix
                lines = lines_of(location)
                rule_id = result.get("ruleId")
                rule = rules.get(rule_id, {}) if isinstance(rule_id, str) else {}
                classes = result_classes(tool, result, rule)

                hit = [i for i, d in enumerate(defects) if matches(d, file, classes, lines, result)]
                if hit:
                    found[tool].update(hit)
                else:
                    key = (rule_id if isinstance(rule_id, str) else None, file, lines[0], lines[1])
                    false_positives[tool].add(key)

    tools = {}
    for tool in found:
        tp = len(found[tool])
        fn = len(defects) - tp
        fp = len(false_positives[tool])
        tools[tool] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": score(tp, tp + fp),
            "recall": score(tp, tp + fn),
            "f1": score(2 * tp, 2 * tp + fp + fn),
        }
    return {"set": root, "defects": len(defects), "tools": tools}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="per-tool confusion matrix of SARIF against labels (CI-SPEC.md P-23)")
    parser.add_argument("--labels", required=True, help="the labels file (P-14)")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)
    with open(args.labels, encoding="utf-8-sig") as fh:
        labels = json.load(fh)
    documents = []
    for path in args.sarif:
        with open(path, encoding="utf-8-sig") as fh:
            documents.append(json.load(fh))
    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
