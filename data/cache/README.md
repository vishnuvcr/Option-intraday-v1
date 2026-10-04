# Data Cache

Large raw market datasets are not committed to Git history.

GitHub Actions stores downloaded partitions in an Actions cache keyed by source revision and file hashes. Each acquisition run publishes its exact manifest and validation report as workflow artifacts.

The repository stores deterministic acquisition/validation code and canonical manifests.