"""Routing rules uploaded by team leads as YAML."""
import yaml


def parse_rules(document: str) -> list[dict]:
    """Parse an uploaded routing-rules document into a list of rules."""
    rules = yaml.load(document, Loader=yaml.Loader)
    if not isinstance(rules, list):
        raise ValueError("a rules document is a list")
    return rules
