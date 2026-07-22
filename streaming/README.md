# streaming/ (optional local demo)

A small, clearly-labeled local Kafka demonstration of what a real-time claim-submission event stream could look like, run entirely with Docker Compose on this machine.

**Important honesty note:** this is a local simulation for learning/demo purposes, not a production streaming deployment. It shows a producer publishing synthetic claim-submission events to a Kafka topic and a consumer processing them with basic windowing/watermarking concepts. It does not represent real production Kafka experience, and the README and interview guide are explicit about that distinction.
