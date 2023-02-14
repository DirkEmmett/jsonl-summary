"""Count JSON Lines records without keeping them in memory."""

import argparse
import json
import sys


def summarize(lines):
    counts = dict.fromkeys(("null", "boolean", "number", "string", "array", "object"), 0)
    records = 0
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(
                line,
                parse_constant=reject_constant,
                parse_int=count_number,
                parse_float=count_number,
            )
        except (ValueError, RecursionError) as error:
            raise ValueError(f"line {line_number}: {error}") from None
        counts[value_type(value)] += 1
        records += 1
    return {"records": records, "types": counts}


def value_type(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def reject_constant(token):
    raise ValueError(f"invalid JSON constant {token}")


def count_number(token):
    # Only the type matters; avoid numeric overflow and integer digit limits.
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="UTF-8 JSON Lines file")
    args = parser.parse_args(argv)
    try:
        with open(args.path, encoding="utf-8") as source:
            result = summarize(source)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"jsonl-summary: {args.path}: {error}", file=sys.stderr)
        return 2
    try:
        sys.stdout.write(json.dumps(result, sort_keys=True) + "\n")
        sys.stdout.flush()
    except (OSError, UnicodeError) as error:
        try:
            sys.stdout.close()
        except (OSError, UnicodeError):
            pass
        print(f"jsonl-summary: cannot write output: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
