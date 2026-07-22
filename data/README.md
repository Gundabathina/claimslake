# data/

This folder holds small **synthetic** sample data files used for local development, testing, and demos.

- All data here is synthetic, generated to resemble realistic healthcare claims structures. It does not contain any real patient, member, or provider information.
- The canonical generator is `scripts/generate_synthetic_data.py` (Python standard library only). Running it locally produces the same four entities: `diagnoses`, `members`, `providers`, and `claims` (in two batches, `claims_batch_1` and `claims_batch_2`, where batch 2 deliberately has an extra `adjustment_amount` column to demonstrate schema drift).
- Full-size generated data is **not** committed to Git; only small samples are kept in `data/sample/` so the repository stays lightweight and clonable. Full-size output goes to `data/generated/` (gitignored) when you run the script locally.

## How the committed data/sample/ files were produced (full transparency)

The environment used to build this repository has browser automation tools but **no local Python interpreter**. To still commit *real, executed* sample output rather than hand-typed fake rows, the exact same generation logic (same fields, same probabilities for each injected data quality issue) was re-implemented in JavaScript and actually executed in-browser, and that real output is what's committed in `data/sample/`.

This means: the **Python script is the canonical, reviewed source of truth** you should run and read to understand and extend the project, while the sample CSVs are a faithful, executed reproduction of what it produces. If you run `python scripts/generate_synthetic_data.py --sample-only` locally, you will get the same structure, same columns, and the same categories of data quality issues (duplicates, missing values, invalid codes, late-arriving claims, schema drift) — with different randomly generated values since no fixed seed is shared between the two implementations.

## Structure

- `sample/diagnoses_sample.csv` — all 12 reference diagnosis codes
- `sample/members_sample.csv` — 50 sample member rows
- `sample/providers_sample.csv` — sample provider rows, including records showing a network status change
- `sample/claims_batch_1_sample.csv` — 50 sample claims (standard schema)
- `sample/claims_batch_2_sample.csv` — 50 sample claims (schema-drift batch, includes `adjustment_amount`)

See `docs/data_dictionary/source_schemas.md` for full column definitions and the complete list of intentionally injected data quality issues.
