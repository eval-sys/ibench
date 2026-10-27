# Replay audit experiences

## R01 — Capture success is not behavioral correctness

- **Example:** A recording can complete and pass its protocol while never exposing an independently required state or result.
- **Rule:** Map each criterion to the executed operation and observable evidence; keep product failure separate from an unjudgeable run.
- **Reason:** The recording protocol establishes provenance, not satisfaction of Require.

## R02 — Correct-result waits can hide the bug

- **Example:** Waiting for Send now to become disabled prevents capture when a broken implementation leaves it enabled. A disabled or absent control can also be a valid accepted branch.
- **Rule:** Establish prerequisites, then record the actual outcome. Adapt locators and conditional controls without changing When or skipping required entrances.
- **Reason:** A replay should leave judgeable evidence of both valid and broken behavior.
- **Current handling:** On 2026-10-10 the user deferred standalone wait cleanup because the scoring agent can adapt it. Preserve this authoring guidance; an implementation-specific wait alone is not a Case rejection reason or an automatic rerecording task.

## R03 — Edited scripts need matching recordings

- **Example:** A new execution script cannot be validated by a video captured from its old version. Touch behavior cannot be certified by a different input modality.
- **Rule:** Track script / revision / seed provenance, use faithful input, and freshly capture affected execution after script edits.
- **Reason:** Otherwise the evidence supports a different experiment.
- **Limit:** Text-only edits require consistency review, not automatic rerecording. Legitimate setup or fault injection is not automatically invalid.

## R04 — Reproduction data is agent work

- **Example:** Round 011 RP01 identified a pending purchase order, a closed shipment, and a conditional form created by replay fixtures but absent from solver initialization.
- **Rule:** Do not require equivalent solver / replay business seeds or synchronize them merely because they differ. Preparing data to reproduce a scenario is part of the agent's work.
- **Reason:** A fixture supplies a controlled observation scene, while the solver is expected to explore and construct relevant business state.
- **Limit:** Replay must still establish Given faithfully. An actually impossible scenario or contradiction needs its own evidence; seed differences do not prove either. Do not expose hidden grading materials to help the solver.

## R05 — Grade the defect, preserve legitimate repairs

- **Example:** A stock-restoration control may default to checked; album actions may remain visible; a compatible collection may use a scroll region rather than 25-item pages. These alternatives are explicitly allowed by the respective rubrics.
- **Rule:** Identify the user-visible defect and its observable pass/failure boundary in Require / Allow. Use a concrete legitimate-repair counterexample to detect extra restrictions introduced by reference scripts or observations.
- **Reason:** A benchmark should supply defensible evidence of a defect without excluding legitimate solutions because they differ from the reference implementation.
- **Limit:** Judge may adapt selectors, waits, and observation routes. Do not require one universal script to execute unchanged on every allowed implementation, and do not treat routine adaptation as proof that a Case is invalid. Ordinary wait cleanup was explicitly deferred for Round 011.

## R06 — Required external destinations must work under the evaluation network policy

- **Evaluated example:** Oppia PR #26180 / Case 1 (`forum-link-browsing-context`) requires a native Forum click to open `https://groups.google.com/g/oppia` in an additional context while retaining the original page. Reference debugging creates the tab and initially reaches the correct URL, but the container ends at `chrome-error://chromewebdata/`. Container curl fails while the host returns HTTP 200; sidecar logs support policy blocking.
- **Rule:** Verify required external access from the real evaluation environment, including the target content when required. Record the effective network policy and distinguish partial navigation success from destination availability.
- **Reason:** A correct application repair cannot supply complete evidence when the harness blocks a required destination. Counting that as model failure would conflate environment and product behavior.
- **Limit:** A timeout alone does not identify the cause, and host availability does not establish container access. Do not automatically allow new domains, weaken the criterion, or classify the upstream GoldPatch as invalid. Other Tasks require their own evidence and policy decision.
