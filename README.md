# JSONL Summary

A Python 3.9+ standard-library CLI for counting JSON Lines records and their types.
No installation or dependencies are required.

## Provenance

This project was created in 2026 with commit dates assigned to 2023. It is not recovered historical source or commit history.

## Usage

```sh
python3 jsonl_summary.py events.jsonl
```

The input must be UTF-8, with one JSON value per physical line. Blank lines are
ignored. Values may be objects, arrays, strings, numbers, booleans, or null.
Output is one JSON object with sorted keys:

- `records`: the total number of nonblank JSON records.
- `types`: counts for `null`, `boolean`, `number`, `string`, `array`, and `object`,
  including zero counts. Booleans are not numbers.

The program reads one line at a time and keeps no record history. Memory depends
on the largest line and its parsed value, not the number of records. Numbers are
classified without converting their magnitude; very large numbers are supported.

Malformed JSON, including `NaN`, `Infinity`, and `-Infinity`, produces an error
on stderr naming the physical line number and exits with status 2. File and
encoding errors also exit 2 with an explanation. Input errors produce no stdout.
Successful runs exit 0. Python's JSON parser nesting limit applies.
