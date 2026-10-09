# Security-Lab 🔴

**Security-Lab** is the integration project for two independent Linux security tools:

- **[SOC-Forge](https://github.com/normanogr2005/SOC-Forge)**: Python-based security event parsing and detection.
- **[NetScope](https://github.com/normanogr2005/NetScope)**: C++17 Linux network telemetry and TCP visibility.

The goal of this repository is **not to replace either project**. Security-Lab provides the common event format and integration layer that allows both tools to participate in the same security monitoring laboratory.

## Architecture

```text
                 SECURITY-LAB
                      │
          ┌───────────┴───────────┐
          │                       │
       NetScope              SOC-Forge
        C++17                   Python
          │                       │
   Network telemetry       Auth/log telemetry
          │                       │
          └───────────┬───────────┘
                      │
                Common Events
                      │
                      ▼
              Detection / Storage
                      │
                      ▼
                SQLite / API
                      │
                      ▼
                  Dashboard
```

## Repository relationship

```text
SOC-Forge ─────────────┐
                       ├──► Security-Lab
NetScope ──────────────┘
```

Security-Lab documents and implements the integration between the two projects while keeping their original repositories independently usable.

## Planned integration

### Phase 1: Common event contract
Define a JSON event structure that can represent both authentication and network telemetry.

### Phase 2: NetScope adapter
Export relevant network observations using the common event format.

### Phase 3: SOC-Forge ingestion
Allow SOC-Forge to consume the normalized events without breaking its existing log pipeline.

### Phase 4: Persistence
Store normalized events and detections in a shared SQLite-backed workflow.

### Phase 5: Correlation
Correlate network and authentication activity, for example:

```text
Network activity
      +
Authentication failures
      ↓
Same source / time window
      ↓
Correlated security event
```

## Event contract

The canonical contract lives in:

- `schemas/security_event.schema.json`
- `examples/network_event.json`
- `examples/auth_event.json`

The ingestion boundary validates events directly against this JSON Schema using Python `jsonschema`.

### Validation guarantees

The current ingestion layer enforces:

- required fields
- allowed sources and severities
- valid ISO 8601/RFC 3339 timestamps
- valid IPv4/IPv6 source and destination addresses
- valid TCP/UDP port ranges
- boolean rejection for integer-only port fields
- rejection of undeclared top-level properties
- non-empty event IDs
- duplicate `event_id` rejection within one NDJSON batch

Persistence-level uniqueness is still a separate concern and will be enforced when the shared storage workflow is introduced.

## First working integration path

NetScope can emit Security-Lab-compatible NDJSON:

```bash
./build/netscope --once --json --connections > events.ndjson
```

Install the validation dependency and validate the generated events:

```bash
python3 -m pip install -r requirements.txt
python3 integration/ingest_ndjson.py events.ndjson
```

Example successful output:

```text
validated_events=2
tcp_connection=2
```

The validator reads the input incrementally, reports the number of validated events by type, and exits with a non-zero status when an input file cannot be read or contains invalid data. It still tracks event IDs for duplicate detection within the file. The `read_events()` helper remains available for callers that explicitly need all events as a list.

This is intentionally additive: NetScope still works normally, and SOC-Forge's existing log pipeline is not replaced.

## Testing

Run the automated unit tests locally:

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

GitHub Actions runs this test suite on pushes and pull requests.

## Current status

- [x] Security-Lab repository created
- [x] Integration architecture documented
- [x] Common event schema drafted and enforced
- [x] Example network event
- [x] Example authentication event
- [x] NetScope JSON exporter
- [x] Schema-backed NDJSON ingestion
- [x] Duplicate event ID protection per ingestion batch
- [x] Incremental NDJSON validation in the CLI
- [x] Automated validation tests in CI
- [ ] Shared persistence workflow
- [ ] Cross-source correlation
- [ ] End-to-end integration tests

## Design principle

Each component should remain useful on its own:

- NetScope remains a network telemetry tool.
- SOC-Forge remains a detection and log-analysis tool.
- Security-Lab becomes the layer that connects their data.

This keeps the projects modular while allowing them to evolve into a single Linux security monitoring laboratory.

## Related projects

- [SOC-Forge](https://github.com/normanogr2005/SOC-Forge)
- [NetScope](https://github.com/normanogr2005/NetScope)
