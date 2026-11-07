"""Shared configuration loader for job-search-kit.

Reads ``config.json`` from the repository root. When that file does not exist,
falls back to ``config.example.json`` so the tools still run out of the box.
Only the standard library is required.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.json"
EXAMPLE_FILE = ROOT / "config.example.json"

DEFAULTS: dict = {
    "candidate": {
        "name": "Your Name",
        "location": "",
        "email": "",
        "phone": "",
        "github": "",
        "linkedin": "",
        "master_cv": "cv/MASTER_CV_TEMPLATE.docx",
    },
    "search": {
        "categories": "devops",
        "keywords": "kubernetes terraform cloud",
        "seniority": "mid,senior",
        "city": "",
        "remote_only": True,
        "uop_only": True,
        "hybrid_city": "",
        "limit": 20,
    },
    "apply": {
        "default_queue_statuses": "cv-ready,found",
        "recruitment_consent_only": True,
    },
    "skills": {
        "daily": [
            "AWS", "Azure", "GCP", "Kubernetes", "Terraform", "Terragrunt",
            "GitHub Actions", "GitLab CI", "Karpenter", "Docker",
        ],
        "working": [
            "Prometheus", "Grafana", "Loki", "Thanos", "Istio",
            "CloudFormation", "Azure DevOps", "Jenkins", "Ansible",
        ],
        "ai_assisted": ["Python", "Bash", "Go"],
        "forbidden_core": ["Linkerd", "Elasticsearch", "ServiceNow", "Jira"],
    },
}


def _merge(base: dict, override: dict) -> dict:
    """Recursively merge ``override`` into a copy of ``base``."""
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config() -> tuple[dict, Path | None]:
    """Return ``(config, source_path)``.

    ``source_path`` is ``None`` only when neither config file exists, in which
    case built-in defaults are returned.
    """
    path = CONFIG_FILE if CONFIG_FILE.exists() else EXAMPLE_FILE
    if not path.exists():
        return copy.deepcopy(DEFAULTS), None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Cannot parse {path.name}: {exc}. Fix the JSON or delete the file "
            "to fall back to config.example.json."
        ) from exc
    return _merge(DEFAULTS, data), path


def is_example(config_path: Path | None) -> bool:
    """True when the tools are running on the example config."""
    return config_path is None or config_path.name == EXAMPLE_FILE.name


def warn_if_example(config_path: Path | None) -> None:
    if is_example(config_path):
        print(
            "Note: using config.example.json. Copy it to config.json and fill in "
            "your details before applying to real offers.\n"
        )
