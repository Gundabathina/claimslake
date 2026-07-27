# ClaimsLake application image
# --------------------------------------------------------------------------
# Runs the Python ingestion layer and the PySpark Silver pipeline, and
# executes the pytest suite inside a reproducible container.
#
# PySpark requires a JVM, so we start from a slim Python 3.11 base and add a
# headless JDK 17. Build context is the repository root (see docker-compose.yml
# / .dockerignore). Build with:
#   docker build -f docker/Dockerfile -t claimslake:local .
# Run the tests with:
#   docker run --rm claimslake:local
# --------------------------------------------------------------------------
FROM python:3.11-slim

# --- System dependencies: JDK 17 for Spark, plus small build/runtime tools ---
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        procps \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Spark/py4j discover Java through JAVA_HOME. The JDK path is arch-specific
# (arm64 vs amd64), so resolve it dynamically and expose it via a stable symlink.
RUN JAVA_DIR="$(dirname "$(dirname "$(readlink -f "$(which java)")")")" \
    && ln -sfn "$JAVA_DIR" /usr/lib/jvm/current-java
ENV JAVA_HOME=/usr/lib/jvm/current-java \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# --- Python dependencies (cached layer: re-runs only when these files change) ---
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install pyspark==4.0.0

# --- Application code ---
COPY . .

# Install the first-party package so "import ingestion.src..." resolves.
RUN pip install -e .

# Default command runs the PySpark Silver test suite. Override to run the
# pipeline instead, e.g.:
#   docker run --rm claimslake:local python -m spark_jobs.src.silver_pipeline
CMD ["python", "-m", "pytest", "tests/pyspark", "-v"]
