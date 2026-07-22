# docs/data_lineage/

Data lineage documentation: traces each Gold-layer column back through Silver and Bronze to its original source field.

Will include a lineage diagram plus a column-level lineage table (e.g. gold.fact_claims.paid_amount <- silver.claims.paid_amount <- bronze.claims_raw.paid_amt <- source claims file), so any number in a report can be traced back to where it originated.
