# HART (Shared Foundation Layer)

`src/hart` is the centralized shared foundation package for cross-module contracts and reusable import-safe logic.

## What goes here

- Canonical enums (`enums/`)
- Canonical models/contracts (`models/`)
- Other shared, runtime-light assets that are reused across modules (for example constants, protocol/typing contracts, portable helpers)

## Design rules

- Keep modules side-effect-free on import.
- Do not duplicate shared contracts in feature/runtime modules.
- Add/adjust shared contracts in `hart` first, then consume from runtime modules.
- Keep naming aligned to MARBTS domain semantics for discoverability.

## Why this matters

- Prevents contract drift across modules.
- Simplifies maintainability and contributor onboarding.
- Supports future online/hosted service boundaries where shared contracts must remain stable and portable.

## Current Shared Contracts

The active codebase uses `src/hart` for the following shared contracts:

- simulation/environment models and run metadata
- observability envelopes, provenance, and replay contracts
- policy models for adaptive planning, deception events, ablation config, stress-test config, and research artifact manifests
- scenario taxonomy and catalog entry models
