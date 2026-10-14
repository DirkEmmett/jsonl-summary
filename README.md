# JSONL Summary

A Python 3.9+ standard-library CLI for counting JSON Lines records and their types.
No installation or dependencies are required.

## Usage

```sh
python3 jsonl_summary.py events.jsonl
python3 jsonl_summary.py - < events.jsonl
python3 jsonl_summary.py < events.jsonl
```

The path is optional and defaults to `-`, which reads stdin. Stdin and files use
strict UTF-8 decoding, independent of the terminal's encoding.

The input must be UTF-8, with one JSON value per physical line. Blank lines are
ignored. Values may be objects, arrays, strings, numbers, booleans, or null.
Output is one JSON object with sorted keys:

- `records`: the total number of nonblank JSON records.
- `types`: counts for `null`, `boolean`, `number`, `string`, `array`, and `object`,
  including zero counts. Booleans are not numbers.
- `fields`: presence counts for each top-level object key. A key counts once per
  object, even when repeated in its JSON text. Nested keys and objects inside
  arrays do not count. A null-valued field still counts as present.

The program reads one line at a time and keeps no record history. Memory depends
on the largest line and its parsed value, plus the number of distinct top-level
keys. Numbers are classified without converting their magnitude; very large
numbers are supported.

Malformed JSON, including `NaN`, `Infinity`, and `-Infinity`, produces an error
on stderr naming the physical line number and exits with status 2. File and
encoding errors also exit 2 with an explanation. Input errors produce no stdout.
Successful runs exit 0. Python's JSON parser nesting limit applies.

## Examples

Count two objects and a boolean:

```sh
printf '%s\n' '{"user":"Ada","active":true}' '{"user":"Lin"}' 'false' | python3 jsonl_summary.py
```

```json
{"fields": {"active": 1, "user": 2}, "records": 3, "types": {"array": 0, "boolean": 1, "null": 0, "number": 0, "object": 2, "string": 0}}
```

Only top-level values contribute to `types`: the strings and boolean inside
the objects above do not increment their type counts.

Empty input still includes every type with a zero count:

```sh
printf '' | python3 jsonl_summary.py
```

```json
{"fields": {}, "records": 0, "types": {"array": 0, "boolean": 0, "null": 0, "number": 0, "object": 0, "string": 0}}
```

Blank lines do not hide an invalid record's position:

```sh
printf '%s\n' '{}' '' 'NaN' | python3 jsonl_summary.py
```

This exits 2, writes nothing to stdout, and writes this error to stderr:

```text
jsonl-summary: -: line 3: invalid JSON constant NaN
```

## Tests

From this directory, run:

```sh
python3 -m unittest -v
```

The tests cover all value types, field presence, duplicate and nested keys,
blank lines, large numbers, stdin and files, sorted output, strict constants,
encoding failures, missing files, and malformed input without partial output.
