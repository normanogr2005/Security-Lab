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

The first version of the contract lives in:

- `schemas/security_event.schema.json`
- `examples/network_event.json`
- `examples/auth_event.json`

The schema intentionally stays small at first. New fields should be added only when an actual integration requirement exists.

## Current status

- [x] Security-Lab repository created
- [x] Integration architecture documented
- [x] Common event schema drafted
- [x] Example network event
- [x] Example authentication event
- [ ] NetScope JSON exporter
- [ ] SOC-Forge event ingestion
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
