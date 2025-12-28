# json-semantic-compare

Compare two JSON documents using semantic rules (normalization, numeric tolerance, selective order-insensitive arrays) and report the first deterministic difference.

## CLI

```bash
python3 /app/compare_json.py --expected expected.json --actual actual.json [--tolerance 0.001] [--ignore /pointer]...
```

- Exit `0`: semantically equal
- Exit `2`: not equal
- Exit `1`: usage / parse error

Output:
- Equal: `EQUAL` (single line)
- Not equal:
  - `NOT_EQUAL`
  - `FIRST_DIFF <json-pointer>`
  - `EXPECTED <json>`
  - `ACTUAL <json>`

## Semantic rules (high level)

- Object keys compared with deterministic sorted traversal.
- Default arrays are order-sensitive.
- Arrays located at pointers ending with `/items` or `/entries` are order-insensitive multisets (duplicates matter).
- Numbers compared with absolute tolerance `<= --tolerance`.
- Strings compare after removing trailing spaces/tabs on each line.
- `--ignore <json-pointer>` ignores that node and its subtree.
