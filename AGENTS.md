# MinimapPR Agent Guidelines

This document provides guidelines for agents working on the MinimapPR codebase.

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
- **Refactor When Useful:** Code base is not deployed in production. Breaking changes are fine when they add clear value.
