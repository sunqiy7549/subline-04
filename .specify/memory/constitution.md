# Project Constitution

This document establishes the governing principles and development guidelines for the News Aggregator project. All AI agents and developers must adhere to these principles.

## 1. Operational Philosophy: Spec-Driven Development
*   **Think Before Coding**: We strictly follow the **Spec -> Plan -> Task -> Implement** workflow.
*   **Explicit Specifications**: No code is written without a clear, written specification (`specs/<feature>/spec.md`) that defines *what* we are building and *why*.
*   **Technical Planning**: We validate our approach with a technical plan (`specs/<feature>/plan.md`) before writing a single line of code.
*   **Atomic Tasks**: Work is broken down into granular, verifiable tasks (`specs/<feature>/tasks.md`).

## 2. Design & User Experience (UX)
*   **Premium Aesthetics**: The UI must be visually stunning ("Wow" factor). We avoid generic Bootstrap-like looks in favor of curated color palettes, modern typography, and subtle micro-animations.
*   **Responsiveness**: All interfaces must be fully responsive and mobile-friendly.
*   **User-Centric**: Features are designed with the end-user's convenience and delight in mind.

## 3. Code Quality & Architecture
*   **Modularity**: Code should be organized into logical modules. Avoid monolithic files.
*   **Readability**: Code must be self-documenting and follow standard conventions (PEP 8 for Python).
*   **Simplicity**: Prefer simple, robust solutions over complex, over-engineered ones. "Keep it simple, stupid" (KISS).
*   **Tech Stack**:
    *   **Backend**: Python (Flask/Django as appropriate).
    *   **Frontend**: HTML5, Vanilla CSS (or Tailwind if specified), Vanilla JavaScript.
    *   **Data**: SQLite for local simplicity, scalable patterns for future growth.

## 4. Verification & Testing
*   **Test-Driven**: Where possible, define success criteria and tests before implementation.
*   **Self-Correction**: If a verification step fails, we pause, analyze, and fix before moving forward. We do not "force" progress.
*   **Manual Verification**: We explicitly list steps for manual verification of UI/UX elements.

## 5. AI Agent Behavior
*   **Proactive**: Do not just wait for instructions; suggest improvements and identify risks.
*   **Transparent**: Clearly communicate what is being done and why.
*   **Context-Aware**: Always check existing files and context before creating new ones to avoid duplication.
