import json
import sys
from http.client import HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

from settings import SERVER_URL


def fetch_items():
    with urlopen(f"{SERVER_URL}/items", timeout=5) as reply:
        items = json.loads(reply.read().decode("utf-8"))["items"]
    if not isinstance(items, list):
        raise ValueError("Expected a list of items.")
    return items


def format_report(items):
    items_by_building = {}
    for item in items:
        items_by_building.setdefault(item["building"], []).append(item)

    lines = ["Campus Lost & Found", f"Saved items ({len(items)})"]
    if not items:
        lines.extend(("", "No items found."))
    for building in sorted(items_by_building):
        lines.extend(("", building))
        for item in items_by_building[building]:
            lines.append(f'- #{item["id"]} | {item["date_found"]} | {item["item_name"]}')
    return "\n".join(lines) + "\n"


def write_report(output_path, report_text, errors):
    try:
        # Stage the file beside its destination so a failed write preserves the previous report.
        with TemporaryDirectory(dir=output_path.parent) as folder:
            draft = Path(folder) / output_path.name
            with draft.open("w", encoding="utf-8") as report:
                report.write(report_text)
            draft.replace(output_path)
    except (OSError, UnicodeError) as error:
        errors.append(error)


def main():
    try:
        items = fetch_items()
        report_text = format_report(items)
    except HTTPError as error:
        error.close()
        print(f"Could not fetch items. Flask returned HTTP {error.code}.", file=sys.stderr)
        return 1
    except (OSError, HTTPException):
        print("Could not fetch items from Flask. Start the server and try again.", file=sys.stderr)
        return 1
    except (KeyError, TypeError, ValueError):
        print("Flask returned unreadable item data. The report could not be saved.", file=sys.stderr)
        return 1

    output_path = Path.cwd() / "found_items_report.txt"
    errors = []
    worker = Thread(target=write_report, args=(output_path, report_text, errors))
    worker.start()
    worker.join()

    if errors:
        print(f"Could not save the report. {errors[0]}", file=sys.stderr)
        return 1
    print(f"Report saved to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
