# ai-generated: ??% - TODO one line on how (this skeleton is the course's; say what you added)
"""bakeoff.py - scanner SARIF + a labels file -> a per-tool confusion matrix (CI-SPEC.md P-23).

This skeleton has the command line and the output shape and nothing of the rules: sections 3.1 to 3.3 of
CI-SPEC.md are yours to implement. Standard library only - it runs as `python3 -S -E bakeoff.py`.

    python3 bakeoff.py --labels labels.json a.sarif b.sarif > bakeoff.json
"""

from __future__ import annotations

import argparse
import json
import sys


def confusion_matrix(labels: dict, sarif_documents: list[dict]) -> dict:
    """The matrix of P-21 and P-22 for the labels (P-14) and the parsed SARIF documents."""
    tools: dict[str, dict] = {}
    # TODO: P-15 tools, P-16 results, P-17 paths and scope, P-18 lines, P-19 classes, P-20 matching,
    #       P-21 counting, P-22 scores
    return {"set": labels["set"], "defects": len(labels["defects"]), "tools": tools}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="per-tool confusion matrix of SARIF against labels (CI-SPEC.md P-23)")
    parser.add_argument("--labels", required=True, help="the labels file (P-14)")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)
    with open(args.labels, encoding="utf-8") as fh:
        labels = json.load(fh)
    documents = []
    for path in args.sarif:
        with open(path, encoding="utf-8") as fh:
            documents.append(json.load(fh))
    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
