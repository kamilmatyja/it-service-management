# ai-generated: 100% - Implemented from the published Lab 5 CI-SPEC.md P-14..P-23 and checked against its practice set
"""Build per-tool confusion matrices from SARIF and labelled defects."""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import unquote


CLASSES = {
    "secret",
    "injection",
    "deserialization",
    "weak-crypto",
    "insecure-transport",
    "path-traversal",
    "ssrf",
    "vulnerable-dependency",
    "misconfiguration",
    "access-control",
}

CWE_CLASSES = {
    259: "secret", 260: "secret", 321: "secret", 798: "secret",
    74: "injection", 77: "injection", 78: "injection", 79: "injection",
    80: "injection", 88: "injection", 89: "injection", 90: "injection",
    91: "injection", 94: "injection", 95: "injection", 96: "injection",
    611: "injection", 776: "injection", 917: "injection", 943: "injection",
    1336: "injection",
    502: "deserialization",
    261: "weak-crypto", 326: "weak-crypto", 327: "weak-crypto",
    328: "weak-crypto", 330: "weak-crypto", 331: "weak-crypto",
    338: "weak-crypto", 759: "weak-crypto", 760: "weak-crypto",
    916: "weak-crypto",
    295: "insecure-transport", 297: "insecure-transport",
    319: "insecure-transport", 322: "insecure-transport",
    757: "insecure-transport",
    22: "path-traversal", 23: "path-traversal", 35: "path-traversal",
    36: "path-traversal", 73: "path-traversal",
    918: "ssrf",
    937: "vulnerable-dependency", 1035: "vulnerable-dependency",
    1104: "vulnerable-dependency", 1395: "vulnerable-dependency",
    16: "misconfiguration", 215: "misconfiguration",
    250: "misconfiguration", 489: "misconfiguration",
    668: "misconfiguration", 732: "misconfiguration",
    1188: "misconfiguration",
    284: "access-control", 285: "access-control", 639: "access-control",
    862: "access-control", 863: "access-control",
}

CWE_PATTERN = re.compile(r"(?<![A-Za-z0-9])CWE-(\d+)", re.IGNORECASE)
PACKAGE_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
PACKAGE_SEPARATOR_PATTERN = re.compile(r"[-_.]+")
TOOL_SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")


def _object(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _array(value: object) -> list:
    return value if isinstance(value, list) else []


def _tool_id(run: dict) -> str:
    driver = _object(_object(run.get("tool")).get("driver"))
    name = driver.get("name")
    if not isinstance(name, str) or not name.strip():
        return "unknown"
    normalized = name.strip().lower()
    if normalized in {
        "trivy", "grype", "osv-scanner", "gitleaks",
        "semgrep", "semgrep oss", "semgrep ce", "semgrep community edition",
        "semgrep pro",
    }:
        return "semgrep" if normalized.startswith("semgrep") else normalized
    return TOOL_SEPARATOR_PATTERN.sub("-", normalized).strip("-") or "unknown"


def _result_is_active(result: dict) -> bool:
    kind = result.get("kind")
    if kind is not None and kind != "fail":
        return False
    suppressions = result.get("suppressions")
    if suppressions is None:
        return True
    if isinstance(suppressions, (list, dict, str)):
        return len(suppressions) == 0
    return suppressions is False or (type(suppressions) is int and suppressions == 0)


def _result_location(result: dict) -> tuple[str, int | None, int | None] | None:
    locations = _array(result.get("locations"))
    if not locations:
        return None
    physical = _object(_object(locations[0]).get("physicalLocation"))
    artifact = _object(physical.get("artifactLocation"))
    uri = artifact.get("uri")
    if not isinstance(uri, str) or not uri:
        return None

    path = unquote(uri)
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]

    region = _object(physical.get("region"))
    start = region.get("startLine")
    if type(start) is not int or start < 1:
        return path, None, None
    end = region.get("endLine")
    if type(end) is not int or end < start:
        end = start
    return path, start, end


def _in_set(path: str, root: str) -> str | None:
    parts = path.split("/")
    matches = [index for index, part in enumerate(parts) if part == root]
    if not matches:
        return None
    return "/".join(parts[matches[-1]:])


def _rule_for(run: dict, result: dict) -> dict:
    rule_id = result.get("ruleId")
    if rule_id is None:
        return {}
    driver = _object(_object(run.get("tool")).get("driver"))
    for candidate in _array(driver.get("rules")):
        rule = _object(candidate)
        if rule.get("id") == rule_id:
            return rule
    return {}


def _tags(properties: object) -> list[str]:
    return [
        tag for tag in _array(_object(properties).get("tags"))
        if isinstance(tag, str)
    ]


def _result_classes(tool: str, result: dict, rule: dict) -> set[str]:
    result_properties = _object(result.get("properties"))
    direct_class = result_properties.get("class")
    if isinstance(direct_class, str) and direct_class in CLASSES:
        return {direct_class}

    rule_tags = _tags(rule.get("properties"))
    if tool == "gitleaks":
        return {"secret"}
    if tool in {"grype", "osv-scanner"}:
        return {"vulnerable-dependency"}
    if tool == "trivy":
        trivy_classes = {
            "vulnerability": "vulnerable-dependency",
            "secret": "secret",
            "misconfiguration": "misconfiguration",
        }
        found = {
            trivy_classes[tag.lower()]
            for tag in rule_tags
            if tag.lower() in trivy_classes
        }
        if found:
            return found

    cwe_classes = set()
    for tag in _tags(result.get("properties")) + rule_tags:
        for match in CWE_PATTERN.finditer(tag):
            cwe_class = CWE_CLASSES.get(int(match.group(1)))
            if cwe_class:
                cwe_classes.add(cwe_class)
    return cwe_classes or {"other"}


def _package_key(package: str) -> str:
    return PACKAGE_SEPARATOR_PATTERN.sub("-", package.lower())


def _message_names_package(result: dict, package: object) -> bool:
    message = _object(result.get("message"))
    text = message.get("text")
    if not isinstance(text, str) or not isinstance(package, str):
        return False
    wanted = _package_key(package)
    for token in PACKAGE_TOKEN_PATTERN.findall(text):
        normalized = _package_key(token.strip("._-"))
        if normalized and normalized == wanted:
            return True
    return False


def _matches(result: dict, file: str, start: int | None, end: int | None,
             classes: set[str], defect: dict) -> bool:
    if defect.get("file") != file or defect.get("class") not in classes:
        return False
    if defect.get("class") == "vulnerable-dependency":
        return _message_names_package(result, defect.get("package"))
    if start is None or end is None:
        return False
    defect_start = defect["start_line"]
    defect_end = defect["end_line"]
    return start <= defect_end and defect_start <= end


def confusion_matrix(labels: dict, sarif_documents: list[dict]) -> dict:
    defects = labels["defects"]
    root = labels["set"]
    tools: dict[str, dict] = {}

    for document in sarif_documents:
        for run in _array(_object(document).get("runs")):
            if not isinstance(run, dict):
                continue
            tool = _tool_id(run)
            entry = tools.setdefault(tool, {"matched": set(), "false_positives": set()})
            for result in _array(run.get("results")):
                if not isinstance(result, dict) or not _result_is_active(result):
                    continue
                location = _result_location(result)
                if location is None:
                    continue
                path, start, end = location
                file = _in_set(path, root)
                if file is None:
                    continue

                rule = _rule_for(run, result)
                classes = _result_classes(tool, result, rule)
                matches = {
                    index for index, defect in enumerate(defects)
                    if _matches(result, file, start, end, classes, defect)
                }
                if matches:
                    entry["matched"].update(matches)
                else:
                    rule_id = result.get("ruleId")
                    if not isinstance(rule_id, str):
                        rule_id = None
                    entry["false_positives"].add((rule_id, file, start, end))

    matrix = {}
    defect_count = len(defects)
    for tool, counts in tools.items():
        tp = len(counts["matched"])
        fp = len(counts["false_positives"])
        fn = defect_count - tp
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / defect_count if defect_count else None
        f1_denominator = 2 * tp + fp + fn
        f1 = 2 * tp / f1_denominator if f1_denominator else None
        matrix[tool] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return {"set": root, "defects": defect_count, "tools": matrix}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="per-tool confusion matrix of SARIF against labels (CI-SPEC.md P-23)"
    )
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
