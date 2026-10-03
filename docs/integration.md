# Integration Plan

## Stage 1

Keep both projects independent and define only the shared JSON contract.

## Stage 2

Add a small exporter/adapter to NetScope.

The adapter should transform existing NetScope observations into Security-Lab events rather than rewriting NetScope's core telemetry code.

## Stage 3

Add an ingestion boundary to SOC-Forge.

Existing SOC-Forge log parsing should continue to work. The integration path should be additive.

## Stage 4

Persist normalized events and detections in a common storage workflow.

## Stage 5

Implement correlation rules.

A first correlation rule can combine:

- network connection event
- authentication failure event
- same source IP
- bounded time window

## Non-goals

Security-Lab is not intended to become a replacement for mature SIEM platforms.

The project is a modular learning and portfolio laboratory for Linux telemetry, detection engineering, event normalization, testing, and correlation.
