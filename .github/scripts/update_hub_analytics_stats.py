#!/usr/bin/env python3
"""Generate docs/hub/analytics-stats.json from a fixed Umami baseline plus PostHog increments."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib import error, request


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "docs" / "hub" / "analytics-stats.json"

SITE = "clianything.cc"
MIGRATION_STARTED_AT = "2026-04-23T09:06:38Z"
MIGRATION_STARTED_AT_MS = 1776935198505
DEFAULT_POSTHOG_APP_HOST = "https://us.posthog.com"
DEFAULT_POSTHOG_PROJECT_ID = "393992"

BASELINE = {
    "provider": "umami",
    "site": SITE,
    "scope": "clianything.cc only",
    "queried_at": "2026-04-23T09:06:38.505000+00:00",
    "total": 21123,
    "human": 7689,
    "agent": 13434,
    "cli_hub_total": 16361,
    "cli_hub_human": 3237,
    "cli_hub_agent": 13124,
}


def _posthog_increment():
    api_key = os.environ.get("POSTHOG_PERSONAL_API_KEY", "").strip()
    app_host = os.environ.get("POSTHOG_APP_HOST", DEFAULT_POSTHOG_APP_HOST).rstrip("/")
    project_id = os.environ.get("POSTHOG_PROJECT_ID", DEFAULT_POSTHOG_PROJECT_ID).strip()

    if not api_key:
        return {
            "status": "missing_api_key",
            "total": 0,
            "human": 0,
            "agent": 0,
            "cli_hub_total": 0,
            "cli_hub_human": 0,
            "cli_hub_agent": 0,
        }

    hogql = (
        "select "
        "countIf(event = 'visit-human' and properties.source = 'web' and properties.site = 'clianything.cc') as human, "
        "countIf(event = 'visit-agent' and properties.source = 'web' and properties.site = 'clianything.cc') as agent, "
        "countIf(event = 'cli-hub call' and properties.source = 'cli' and properties.channel = 'cli-hub' and properties.is_agent = false) as cli_hub_human, "
        "countIf(event = 'cli-hub call' and properties.source = 'cli' and properties.channel = 'cli-hub' and properties.is_agent = true) as cli_hub_agent "
        "from events "
        f"where timestamp >= parseDateTimeBestEffort('{MIGRATION_STARTED_AT}') "
    )
    payload = {
        "query": {
            "kind": "HogQLQuery",
            "query": hogql,
        },
        "name": "cli-anything hub public website stats",
    }
    req = request.Request(
        f"{app_host}/api/projects/{project_id}/query/",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        print(f"Warning: PostHog stats query failed ({exc.code}): {detail}", file=sys.stderr)
        return {
            "status": f"http_{exc.code}",
            "total": 0,
            "human": 0,
            "agent": 0,
            "cli_hub_total": 0,
            "cli_hub_human": 0,
            "cli_hub_agent": 0,
        }
    except Exception as exc:  # pragma: no cover - exercised in CI failure mode
        print(f"Warning: PostHog stats query failed: {exc}", file=sys.stderr)
        return {
            "status": "error",
            "total": 0,
            "human": 0,
            "agent": 0,
            "cli_hub_total": 0,
            "cli_hub_human": 0,
            "cli_hub_agent": 0,
        }

    results = data.get("results") or [[0, 0, 0, 0]]
    row = results[0] if results else [0, 0, 0, 0]
    human = int(row[0] or 0)
    agent = int(row[1] or 0)
    cli_hub_human = int(row[2] or 0)
    cli_hub_agent = int(row[3] or 0)
    return {
        "status": "ok",
        "app_host": app_host,
        "project_id": project_id,
        "human": human,
        "agent": agent,
        "total": human + agent,
        "cli_hub_human": cli_hub_human,
        "cli_hub_agent": cli_hub_agent,
        "cli_hub_total": cli_hub_human + cli_hub_agent,
    }


def main():
    posthog_increment = _posthog_increment()
    totals = {
        "total": BASELINE["total"] + posthog_increment["total"],
        "human": BASELINE["human"] + posthog_increment["human"],
        "agent": BASELINE["agent"] + posthog_increment["agent"],
        "cli_hub_total": BASELINE["cli_hub_total"] + posthog_increment["cli_hub_total"],
        "cli_hub_human": BASELINE["cli_hub_human"] + posthog_increment["cli_hub_human"],
        "cli_hub_agent": BASELINE["cli_hub_agent"] + posthog_increment["cli_hub_agent"],
    }
    payload = {
        "site": SITE,
        "provider": "posthog",
        "generated_at": datetime.now(UTC).isoformat(),
        "migration_started_at": MIGRATION_STARTED_AT,
        "baseline": BASELINE,
        "posthog_increment": posthog_increment,
        "totals": totals,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
