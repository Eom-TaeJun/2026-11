#!/usr/bin/env python3
"""Validate, aggregate, or explicitly refresh public GitHub star-history snapshots.

Offline examples (run from the repository root)::

    python scripts/ai_stars.py validate --input data/ai_star_history.json
    python scripts/ai_stars.py aggregate --input data/ai_star_history.json
    python scripts/ai_stars.py aggregate --input snapshot.json --compare previous.json

Only ``refresh`` uses the network. It needs no token and refuses to overwrite::

    python scripts/ai_stars.py refresh --output snapshots/stars-YYYY-MM-DD.json

The input repository catalog contains a ``projects`` array with ``repo`` and
``repository_created_at_utc``. The old raw snapshot is a list of repository
records; new snapshots wrap that same list in ``records``. Month labels use the
UTC date of the API's week epoch. GitHub does not guarantee UTC day boundaries,
so these are neither exact Korean-calendar counts nor verified historical net
growth. Removed-star treatment is not assumed. This is a selected cohort, not
a ranking of all GitHub repositories.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import email.utils
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


UTC = dt.timezone.utc
DEFAULT_REPOS = Path(__file__).resolve().parent.parent / "data" / "ai_tools.json"
API_VERSION = "2026-03-10"
PER_PAGE = 30
MAX_RESPONSE_BYTES = 2_000_000
METHOD = (
    "GitHub history observed at snapshot time, grouped by star creation-date "
    "labels derived from week epochs; UTC/KST boundaries and removed-star "
    "treatment are not guaranteed. Not historical net growth or global ranking."
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid ISO date: {value!r}") from exc


def parse_timestamp(value: str) -> dt.datetime:
    try:
        stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Invalid timestamp: {value!r}") from exc
    if stamp.tzinfo is None:
        raise ValueError(f"Timestamp needs a timezone: {value!r}")
    return stamp.astimezone(UTC)


def repository_catalog(data: Any) -> dict[str, dt.date]:
    entries = data.get("projects") if isinstance(data, dict) else data
    if not isinstance(entries, list) or not entries:
        raise ValueError("Repository catalog needs a nonempty projects array")
    result: dict[str, dt.date] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each repository entry must be an object")
        repo = entry.get("repo", "")
        if not isinstance(repo, str) or not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo
        ) or any(part in {".", ".."} for part in repo.split("/")):
            raise ValueError(f"Invalid owner/repository: {repo!r}")
        if repo.casefold() in {name.casefold() for name in result}:
            raise ValueError(f"Duplicate repository in catalog: {repo}")
        result[repo] = parse_timestamp(entry.get("repository_created_at_utc")).date()
    return result


def snapshot_records(snapshot: Any) -> list[dict[str, Any]]:
    records = snapshot.get("records") if isinstance(snapshot, dict) else snapshot
    if not isinstance(records, list) or not records:
        raise ValueError("Snapshot needs a nonempty record list or records array")
    if any(not isinstance(record, dict) for record in records):
        raise ValueError("Each snapshot record must be an object")
    return records


def observation_date(snapshot: Any, records: list[dict[str, Any]]) -> dt.date:
    dates = [parse_timestamp(record.get("observed_at_utc")).date() for record in records]
    if isinstance(snapshot, dict) and snapshot.get("as_of_date"):
        dates.append(parse_date(snapshot["as_of_date"]))
    # The earliest observation bounds a snapshot collected across midnight.
    return min(dates)


def aggregate(
    snapshot: Any,
    repositories: dict[str, dt.date],
    *,
    year: int | None = None,
    as_of: dt.date | None = None,
) -> dict[str, Any]:
    """Aggregate without network access; incomplete or invalid data stays null."""
    records = snapshot_records(snapshot)
    observed = observation_date(snapshot, records)
    as_of = as_of or observed
    if as_of > observed:
        raise ValueError("--as-of cannot be later than the earliest snapshot observation")
    year = year or as_of.year
    if year < 1970 or year > as_of.year:
        raise ValueError("Year must be between 1970 and the observation year")
    final_month = as_of.month if year == as_of.year else 12
    months = [f"{year}-{month:02d}" for month in range(1, final_month + 1)]
    mapped: dict[str, list[dict[str, Any]]] = {}
    global_errors: list[str] = []
    for record in records:
        repo = record.get("repo")
        if not isinstance(repo, str):
            global_errors.append("Snapshot record has no repository name")
            continue
        if repo not in repositories:
            global_errors.append(f"Snapshot repository is absent from catalog: {repo}")
            continue
        mapped.setdefault(repo, []).append(record)

    rows, checks = [], []
    for repo, created in repositories.items():
        repo_records = mapped.get(repo, [])
        errors: list[str] = []
        warnings: list[str] = []
        weeks: dict[int, dict[str, Any]] = {}
        daily: dict[dt.date, int] = {}
        urls: list[str] = []
        if len(repo_records) != 1:
            errors.append("missing repository record" if not repo_records else "duplicate repository record")
        record = repo_records[0] if repo_records else {}
        pages = record.get("github_history", [])
        if not isinstance(pages, list):
            errors.append("github_history is not an array")
            pages = []
        if record.get("github_errors"):
            warnings.append("snapshot contains recorded request failures; covered months only")

        for page_index, page in enumerate(pages, 1):
            if not isinstance(page, dict) or page.get("status") != 200:
                errors.append(f"page {page_index}: missing successful HTTP status")
                continue
            if isinstance(page.get("url"), str):
                urls.append(page["url"])
            data = page.get("data")
            if not isinstance(data, list):
                errors.append(f"page {page_index}: data is not an array")
                continue
            page_epochs = []
            for item in data:
                if not isinstance(item, dict):
                    errors.append(f"page {page_index}: week is not an object")
                    continue
                epoch, total, days = item.get("week"), item.get("total"), item.get("days")
                if type(epoch) is not int or epoch < 0:
                    errors.append(f"page {page_index}: invalid week epoch")
                    continue
                page_epochs.append(epoch)
                if epoch in weeks:
                    errors.append(f"duplicate week: {epoch}")
                    continue
                weeks[epoch] = item
                if not isinstance(days, list) or len(days) != 7:
                    errors.append(f"week {epoch}: days must have exactly 7 entries")
                    continue
                if type(total) is not int or total < 0 or any(type(n) is not int or n < 0 for n in days):
                    errors.append(f"week {epoch}: counts must be nonnegative integers")
                    continue
                if sum(days) != total:
                    errors.append(f"week {epoch}: sum(days) != total")
                    continue
                try:
                    first_day = dt.datetime.fromtimestamp(epoch, UTC).date()
                except (ValueError, OverflowError, OSError):
                    errors.append(f"week {epoch}: timestamp out of range")
                    continue
                for offset, value in enumerate(days):
                    day = first_day + dt.timedelta(days=offset)
                    if day in daily:
                        errors.append(f"overlapping calendar date: {day}")
                    if day < created and value:
                        errors.append(f"nonzero count before repository creation: {day}")
                    daily[day] = value
            if page_epochs != sorted(page_epochs, reverse=True):
                errors.append(f"page {page_index}: weeks are not ordered newest first")

        ordered = sorted(weeks)
        if any(right - left != 604800 for left, right in zip(ordered, ordered[1:])):
            errors.append("week epochs are not contiguous at seven-day intervals")

        counts, statuses = {}, {}
        invalid_structure = bool(errors)
        for month in months:
            numeric_month = int(month[5:])
            first = dt.date(year, numeric_month, 1)
            end = min(dt.date(year, numeric_month, calendar.monthrange(year, numeric_month)[1]), as_of)
            if end < created:
                counts[month], statuses[month] = None, "repository_not_created"
                continue
            if invalid_structure:
                counts[month], statuses[month] = None, "invalid_history"
                continue
            start = max(first, created)
            expected = [start + dt.timedelta(days=offset) for offset in range((end - start).days + 1)]
            if not expected or any(day not in daily for day in expected):
                counts[month], statuses[month] = None, "missing_history_coverage"
                errors.append(f"missing history coverage: {month}")
                continue
            counts[month] = sum(daily[day] for day in expected)
            statuses[month] = (
                "partial_current_month" if month == as_of.strftime("%Y-%m")
                else "covered_api_calendar_labels"
            )
        rows.append({
            "repo": repo,
            "monthly_history_counts": counts,
            "month_status": statuses,
            "observed_at_utc": record.get("observed_at_utc"),
            "source_urls": urls,
        })
        checks.append({"repo": repo, "weeks": len(weeks), "checks_passed": not errors,
                       "errors": errors, "warnings": warnings})
    return {
        "schema_version": 1, "as_of_date": as_of.isoformat(), "year": year,
        "method": METHOD, "global_monthly_rank_verified": False,
        "valid": not global_errors and all(check["checks_passed"] for check in checks),
        "global_errors": global_errors, "monthly_stars": rows, "star_validation": checks,
    }


def compare_monthly(result: dict[str, Any], previous: Any) -> list[str]:
    """Compare values/statuses only, leaving retrieval metadata independent."""
    previous_rows = previous.get("monthly_stars") if isinstance(previous, dict) else previous
    if not isinstance(previous_rows, list) or not all(
        isinstance(row, dict) and "repo" in row and "monthly_history_counts" in row
        for row in previous_rows
    ):
        raise ValueError("Comparison file needs monthly_stars with monthly_history_counts")
    expected = {row["repo"]: row for row in previous_rows}
    if len(expected) != len(previous_rows):
        raise ValueError("Comparison file has duplicate repositories")
    actual = {row["repo"]: row for row in result["monthly_stars"]}
    differences = []
    for repo in sorted(set(expected) | set(actual)):
        if repo not in expected or repo not in actual:
            differences.append(f"repository set differs: {repo}")
            continue
        if actual[repo]["monthly_history_counts"] != expected[repo]["monthly_history_counts"]:
            differences.append(f"monthly counts differ: {repo}")
        if "month_status" in expected[repo] and actual[repo]["month_status"] != expected[repo]["month_status"]:
            differences.append(f"month status differs: {repo}")
    return differences


def write_new_json(path: Path, data: Any) -> None:
    """Exclusive create is required even if a caller already checked exists()."""
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


class GitHubOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname != "api.github.com":
            raise urllib.error.URLError("Refusing redirect outside https://api.github.com")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def retry_after_seconds(value: str | None, now: dt.datetime) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            stamp = email.utils.parsedate_to_datetime(value)
            return max(0.0, (stamp.astimezone(UTC) - now).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def refresh(
    repositories: dict[str, dt.date], *, year: int,
    max_pages: int = 3, timeout: float = 20,
) -> dict[str, Any]:
    """Public GET only. Record failures; do not retry or sleep implicitly."""
    now = dt.datetime.now(UTC)
    if year < 1970 or year > now.year:
        raise ValueError("Refresh year must be between 1970 and the current year")
    if not 1 <= max_pages <= 20 or not 0 < timeout <= 60:
        raise ValueError("max-pages must be 1..20 and timeout must be >0 and <=60")
    start = dt.datetime(year, 1, 1, tzinfo=UTC)
    cutoff = int(start.timestamp())
    opener = urllib.request.build_opener(GitHubOnlyRedirect())
    records = []
    for repo in repositories:
        record: dict[str, Any] = {
            "repo": repo, "observed_at_utc": dt.datetime.now(UTC).isoformat(),
            "github_history": [], "github_errors": [],
        }
        for page in range(1, max_pages + 1):
            url = "https://api.github.com/repos/" + "/".join(
                urllib.parse.quote(part, safe="") for part in repo.split("/")
            ) + f"/stargazers/history?per_page={PER_PAGE}&page={page}"
            request = urllib.request.Request(url, method="GET", headers={
                "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "finance-research-ai-stars/1.0",
            })
            try:
                with opener.open(request, timeout=timeout) as response:
                    payload = response.read(MAX_RESPONSE_BYTES + 1)
                    if len(payload) > MAX_RESPONSE_BYTES:
                        raise ValueError("Response exceeds bounded size")
                    data = json.loads(payload.decode("utf-8"))
                    if not isinstance(data, list):
                        raise ValueError("History response is not an array")
                    epochs = [item.get("week") for item in data if isinstance(item, dict)]
                    if len(epochs) != len(data) or any(type(epoch) is not int for epoch in epochs):
                        raise ValueError("History response has invalid week epochs")
                    record["github_history"].append({
                        "url": url, "status": response.status,
                        "server_date": response.headers.get("Date"),
                        "etag": response.headers.get("ETag"), "data": data,
                    })
                if not epochs or min(epochs) <= cutoff or len(data) < PER_PAGE:
                    record["stop_reason"] = "cutoff_or_repository_start_reached"
                    break
                if page == max_pages:
                    record["stop_reason"] = "page_limit_reached"
            except urllib.error.HTTPError as exc:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                record["github_errors"].append({
                    "url": url, "status": exc.code, "error": str(exc),
                    "retry_after": retry_after,
                    "retry_after_seconds": retry_after_seconds(retry_after, dt.datetime.now(UTC)),
                    "rate_limit_remaining": exc.headers.get("X-RateLimit-Remaining") if exc.headers else None,
                    "rate_limit_reset": exc.headers.get("X-RateLimit-Reset") if exc.headers else None,
                    "detail": exc.read(4096).decode("utf-8", errors="replace"),
                })
                record["stop_reason"] = "http_error_no_implicit_retry"
                break
            except (urllib.error.URLError, OSError, ValueError) as exc:
                record["github_errors"].append({"url": url, "status": None, "error": str(exc)})
                record["stop_reason"] = "request_or_response_error"
                break
        records.append(record)
    snapshot = {
        "schema_version": 1, "observed_at_utc": now.isoformat(),
        "as_of_date": now.date().isoformat(), "start_date": start.date().isoformat(),
        "api_version": API_VERSION, "per_page": PER_PAGE, "max_pages": max_pages,
        "method": METHOD, "records": records,
    }
    validation = aggregate(snapshot, repositories, year=year)
    snapshot["validation"] = {
        "valid": validation["valid"], "global_errors": validation["global_errors"],
        "star_validation": validation["star_validation"],
    }
    return snapshot


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("validate", "aggregate", "refresh"):
        command = commands.add_parser(name)
        command.add_argument("--repos", type=Path, default=DEFAULT_REPOS,
                             help="Repository catalog (default: script-relative data/ai_tools.json)")
        command.add_argument("--year", type=int, help="January 1 start year; defaults to observation year")
        if name == "refresh":
            command.add_argument("--output", type=Path, required=True, help="New snapshot; parent directory must exist")
            command.add_argument("--max-pages", type=int, default=3, help="Bounded at 20; default 3 pages per repository")
            command.add_argument("--timeout", type=float, default=20, help="Seconds per request, at most 60")
        else:
            command.add_argument("--input", type=Path, required=True, help="Saved raw star-history snapshot")
            command.add_argument("--as-of", type=parse_date, help="Calendar-label cutoff, not later than observation")
            command.add_argument("--compare", type=Path, help="Existing monthly_stars aggregate to compare exactly")
            command.add_argument("--output", type=Path, help="Optional new output file; never overwrite")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        repositories = repository_catalog(read_json(args.repos))
        if args.output and args.output.exists():
            raise FileExistsError(f"Refusing to overwrite existing output: {args.output}")
        if args.command == "refresh":
            if not args.output.parent.is_dir():
                raise ValueError("Output parent directory must already exist")
            result = refresh(repositories, year=args.year or dt.datetime.now(UTC).year,
                             max_pages=args.max_pages, timeout=args.timeout)
            write_new_json(args.output, result)
            failures = sum(len(record["github_errors"]) for record in result["records"])
            print(json.dumps({"output": str(args.output), "repositories": len(repositories),
                              "request_failures": failures, "valid": result["validation"]["valid"]}, ensure_ascii=False))
            return 0 if result["validation"]["valid"] and not failures else 1
        result = aggregate(read_json(args.input), repositories, year=args.year, as_of=args.as_of)
        differences = compare_monthly(result, read_json(args.compare)) if args.compare else []
        if args.compare:
            result["comparison"] = {"matches": not differences, "differences": differences}
        if args.command == "validate":
            result = {key: value for key, value in result.items() if key != "monthly_stars"}
        if args.output:
            write_new_json(args.output, result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] and not differences else 1
    except (OSError, ValueError, TypeError) as exc:
        print(f"ai_stars: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
