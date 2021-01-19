# A Helm Chart for S3-migrator job deployments

## Introduction

This helm chart define a kubernetes jobs which run S3-migrator

## Prerequisites

- Kubernetes cluster 1.10+
- Helm 3.0.0+

## Installation

### Configure the chart

The following items can be set via `--set` flag during installation or configured by editing the `values.yaml` directly (need to download the chart first).

```
--set global.environment[0].name="bucket_to"
--set global.environment[0].value=""
--set global.environment[1].name="bucket_from"
--set global.environment[1].value=""
--set global.environment[2].name="aws_access_key_id"
--set global.environment[2].value=""
--set global.environment[3].name="aws_secret_access_key"
--set global.environment[3].value=""
--set global.environment[4].name="DBUser"
--set global.environment[4].value=""
--set global.environment[5].name="DBPassword"
--set global.environment[5].value=""
--set global.environment[6].name="DBHost"
--set global.environment[6].value=""
--set global.environment[7].name="DATABASE"
--set global.environment[7].value=""
--set global.environment[8].name="DBPort"
--set global.environment[8].value=""
```

### Install the chart

Install the job helm chart with a release name `s3-migrator`:

**First** either change the env var on `values.yaml` or use the `--set`
commands above

```bash
helm install s3-migrator .
```

## Uninstallation

To uninstall/delete the `my-release` deployment:

```bash
helm uninstall s3-migrator
```
