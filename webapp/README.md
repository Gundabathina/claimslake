# ClaimsLake — public site

The recruiter-facing web application for the [ClaimsLake](../README.md) data
engineering project. Deployed independently (Vercel, root directory
`webapp/`) from the pipeline code in the rest of this repository.

This is a static, read-only showcase — it does **not** connect to Airflow,
Postgres, MinIO, or any other local service from the pipeline. All content is
sourced from [`src/content.ts`](src/content.ts), which mirrors facts already
published in the repository's `README.md`, `CHANGELOG.md`, and `docs/`. The
"pipeline demo" section is an explicitly labeled UI simulation of the real
Airflow DAG's stage order — it does not execute Spark, dbt, or Airflow.

## Stack

React 19 + TypeScript + Vite + Tailwind CSS v4 + Framer Motion.

## Develop

```bash
npm install
npm run dev
```

## Build

```bash
npm run build   # tsc -b && vite build, outputs to dist/
```

## Update content

Edit [`src/content.ts`](src/content.ts) only — every section reads from it.
Do not add facts that aren't backed by the main repository.
