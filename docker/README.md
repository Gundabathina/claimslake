# docker/

Supporting Docker assets referenced by `docker-compose.yml` at the repo root: Postgres init scripts (`postgres-init/`), and any custom Dockerfiles for services that need extra Python packages (e.g. a PySpark image with project dependencies pre-installed).

The root-level `docker-compose.yml` is what you actually run; this folder holds the supporting pieces it references.
