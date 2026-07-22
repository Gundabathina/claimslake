# docs/data_dictionary/

Data dictionary for every dataset in ClaimsLake, added as each entity is built.

Will include, per table/column: name, data type, description, nullability, example values, and source system of origin. Covers source (raw) schemas as well as the Silver and Gold (star schema) layers.

Files (added incrementally):

- `source_schemas.md` — raw member/provider/diagnosis/claim schemas
- `silver_schemas.md` — cleaned and standardized schemas
- `gold_star_schema.md` — fact and dimension table definitions, grain, and keys
