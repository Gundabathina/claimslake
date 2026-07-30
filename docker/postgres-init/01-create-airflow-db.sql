-- ClaimsLake Postgres initialization
-- Runs automatically on FIRST cluster init via /docker-entrypoint-initdb.d.
-- The postgres image only creates the single database named in POSTGRES_DB
-- (claimslake, the local analytics warehouse). Airflow needs its own separate
-- metadata database on the same server; this script creates it.
--
-- Executed as POSTGRES_USER (the superuser for this container) against the
-- default POSTGRES_DB, so the new database is owned by that same user and
-- Airflow can connect with the existing credentials.

-- Postgres has no CREATE DATABASE IF NOT EXISTS; use the standard gexec guard
-- so re-running is harmless.
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec
