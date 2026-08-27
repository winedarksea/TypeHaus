# TypeHaus Agent Guidelines

This document provides guidelines for agents working on the TypeHaus codebase.

## Architectural Principles

### 1.1 Small Files & Single Responsibility (SRP)
- **Aim to keep files < 500 lines.** Large files are difficult to reason about and cause merge conflicts.
- **Single Responsibility per File:** Each module should have one reason to change.
- **Decompose "God Classes":** Avoid monolithic classes. Extract responsibilities into focused components.

### 1.2 Module Boundaries & Dependency Injection
- **Explicit Boundaries:** Avoid deep coupling between modules.

### 1.3 Configuration-Driven Logic
- **No Magic Numbers:** Move operational constants (thresholds, multipliers, timings) into domain-specific sub-configs.

## 2. Coding Standards

### 2.1 Hyper-Descriptive Naming
- **Favor Explicit Over Concise:** Use long, descriptive names that explain intent

### 2.3 Error Handling
- **Robustness at the Edge:** Wrap potentially unstable operations (like `np.linalg.solve`) with try/except blocks to handle `LinAlgError` or singular matrices gracefully.
- **Avoid Pointless Fallbacks** Only include fallbacks where the fallback is effective. Heuristic fallbacks can hide errors and slow debugging, so avoid them.

### 2.4 High-Signal Comments
- **Explain "Why", Not "What":** Comments should explain the reasoning behind complex algorithms or architectural decisions.
- **Be Token-Efficient in Comments:** Use concise, informative language. Focus on documenting interface contracts and capability tiers.

## 3. Testing & Benchmarking
- **Shared Fixtures:** Place reusable fixtures into a shared helper module if reused across 3+ files.
- **Avoid Test Duplication:** If the same setup appears in multiple test files, factor it into a fixture or a helper module.
- **The catlin fixture ladder** (`packages/engine/tests/conftest.py`), cheapest first:
  `catlin_plan` (session, frozen) → `catlin_model_ro` (session, **read-only**) →
  `catlin_ifc_path` (session, the emitted framed IFC, **read-only**) → `catlin_model`
  (module, the mutable copy). Take the highest one you can. Mutating a session fixture
  corrupts whatever module runs next, which is a failure that lands nowhere near its cause —
  if a test edits the model, it takes `catlin_model`. A test that emits a *mutated* model,
  another house, or a non-default LOD calls `emit_ifc` itself.
- **The `slow` marker:** one marker, registered in the root `pyproject.toml`, applied at
  module level (`pytestmark = pytest.mark.slow`). `scripts/verify.sh --fast` deselects it;
  the full gate runs everything, so `slow` is a fast-loop convenience and never a
  quarantine. Earn it by measuring — `pytest --durations=40` — and un-mark a module that
  stops being slow, or it becomes a test nobody runs.
- **Refactor When Useful:** Code base is not deployed in production. Breaking changes are fine when they add clear value.
