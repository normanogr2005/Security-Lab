# Architecture

## Components

### NetScope

Collects Linux network telemetry from system interfaces and TCP connection tables.

Its role in Security-Lab is to produce normalized network observations.

### SOC-Forge

Parses security logs and applies detection rules.

Its role in Security-Lab is to produce normalized authentication/security events and consume events for higher-level detection.

### Security-Lab

Security-Lab owns the integration contract and correlation layer.

It should not duplicate the internal implementation of either project.

## Data flow

1. NetScope produces a network observation.
2. The observation is converted to the Security-Lab event schema.
3. SOC-Forge can ingest the normalized event.
4. Events are persisted.
5. Correlation rules inspect events from both sources.
6. A correlated result becomes a security detection.

## Example correlation

A network connection to SSH followed by multiple authentication failures from the same source within a defined time window can become a correlated event.

The correlation logic should be explicit about:

- source identity
- timestamps
- time windows
- event types
- threshold
- resulting severity

