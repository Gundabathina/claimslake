# ClaimsLake application image
# --------------------------------------------------------------------------
# Runs the Python ingestion layer and the PySpark Silver pipeline, and
# executes the pytest suite inside a reproducible container.
#
# PySpark requires a JVM, so we start from a slim Python 3.11 base and add a
# headless JRE. The base image (python:3.11-slim) tracks the current Debian
# release (Trixie), where the correct package is default-jre-headless
# (Java 21, supported by Spark 4.x). Build context is the repository root
# (see docker-compose.yml / .dockerignore). Build with:
#   docker build -f docker/Dockerfile -t claimslake:local .
# Run the tests with:
#   docker run --rm claimslake:local
# --------------------------------------------------------------------------
FROM python:3.11-slim

# --- System dependencies: a headless JRE for Spark, plus small tools ---
# default-jre-headless resolves to the JRE supported by the current Debian
# release, avoiding hard-coding a version-specific package name that may be
# dropped between Debian releases.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-jre-headless \
        procps \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Spark/py4j discover Java through JAVA_HOME. The JDK path is arch- and
# version-specific, so resolve it dynamically from the installed java binary
# and expose it via a stable symlink.
RUN JAVA_DIR="$(dirname "$(dirname "$(readlink -f "$(which java)")")")" \
    && ln -sfn "$JAVA_DIR" /usr/lib/jvm/current-java
ENV JAVA_HOME=/usr/lib/jvm/current-java \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# --- Python dependencies (cached layer: re-runs only when these files change) ---
COPY requirements.txt pyproject.toml ./
COPY dbt/requirements-dbt.txt ./dbt/requirements-dbt.txt

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r dbt/requirements-dbt.txt \
    && pip install pyspark==4.0.0

# --- Application code ---
COPY . .

# Install the first-party package so "import ingestion.src..." resolves.
RUN pip install -e .

# Default command runs the PySpark Silver test suite. Override to run the
# pipeline instead, e.g.:
#   docker run --rm claimslake:local python -m spark_jobs.src.silver_pipeline
CMD ["python", "-m", "pytest", "tests/pyspark", "-v"]
