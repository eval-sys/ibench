---
name: audit-cases
description: Audit iBench task and case quality in documented rounds, first confirming natural-language definitions, then reviewing replay evidence or solver rollouts. Use for benchmark case audits, intention and rubric review, replay validity, and post-run discovery analysis.
---

# Audit iBench cases

Work from the repository root. Audit per Case, even when several Cases share one Task or solver trajectory. Use stable Task / Case IDs rather than Preview positions.

## Round sequence

1. **Definition round:** read [definition checks](references/definition.md). Review natural-language materials and their source before inspecting replay scripts, videos, runtime behavior, or solver trajectories. Inventory paths without using their behavioral contents to infer the intended requirement.
2. **Definition gate:** report the intended goal, evaluation boundary, findings, and unresolved decisions. Record a confirmed definition for the scoped batch only after applicable checks pass and semantic or scope disputes are resolved. Existing explicit decisions count; do not ask again. An unresolved definition blocks evidence review for that Case. Do not quietly skip it: finish the batch or explicitly record a narrower scope before advancing.
3. **Evidence round:** open a later round referencing the confirmed definition round and exact material version. For replay audits, read [replay checks](references/replay.md). For solver / judge audits, use the after-run procedure below. A changed goal or scoring boundary reopens definition review; do not change it merely to make a replay or verdict fit.

Keep definition and evidence review in separate rounds. A prior confirmed definition can be reused only after checking that it matches the materials being audited and recording that comparison. Definition confirmation establishes what the Case means; it does not assert that its defect, reference repair, or recording is valid.

Create local audit outputs using these conventions. These are output locations, not references to historical documents required by this skill:

- Pre-run definition and replay rounds: `audits/pre-run/rounds/NNN/` (next unused number).
- Post-run evidence rounds: `audits/after-run/roundN/` (next unused number), referencing a definition round for the frozen run inputs.

Continue an explicitly assigned current round; otherwise create a new round when execution starts. Do not rewrite historical findings with new materials or create empty future rounds while only planning an audit.

## Baseline and deliverables

Before reading Case contents, record the repository's full SHA, scoped IDs, material paths, and working-tree differences. For dirty or untracked audit inputs, preserve a diff or file-hash inventory and its location; a commit alone does not identify those bytes. For after-run work, also identify `runs/<run>/run.json`, frozen compiled inputs, and native `jobs/solve` / `jobs/score` evidence. Current `tasks/` cannot replace a run's frozen inputs.

Keep each round small:

- `README.md`: mode (`definition`, `replay`, or `after-run`), scope, baseline, input sources, prior-round link, check coverage, and gate status.
- `review.md`: per-Case conclusions and findings; add a separate artifact only when evidence or actual changes justify it. For rollout annotations, use the delivery fields in [rollout checks](references/rollout.md).

Definition gate records must identify the scoped Case IDs, reviewed material version, completed checks, resolved decisions and their sources, remaining blockers, and which Cases may enter the next round. A release-selection label does not establish definition confirmation.

For each applicable rule, record `pass`, `problem`, `pending`, or `unreviewed`; use `NA` with a reason when inapplicable. Keep a coverage table in `review.md`: `Task / Case | N01–N07 or R01–R06 statuses | finding IDs | conclusion / gate`. A round is complete only when its scoped checks are covered and remaining problems / limits are explicit. A failed check can be a completed audit finding; it is not a confirmed definition.

Every finding needs:

| Field | Required content |
| --- | --- |
| Identity | Finding ID, rule ID, Task and Case ID |
| Evaluated content | Original field text, or script path / segment, or video source / timestamps, or trajectory step |
| Evidence and reasoning | Traceable source; what it proves; why this meets or violates the rule; uncertainty |
| Proposed action | Specific change or decision needed, without silently applying a new scope |
| Decision and revision | Confirmed decision and source, or pending; actual changed files and validation limits if edited |

Keep audit status separate from release selection (`candidate / approve / reject`) and runtime verdict (`accept / reject / unjudged`). Audit findings do not themselves authorize deletion, relabeling, changed scores, publishing, or commits. Follow the user's existing authorization for fixes; retain pre-edit text and evidence. Store bulky temporary investigation artifacts in ignored `jobs/`, and keep traceable conclusions in the round.

## After-run evidence procedure

Read [rollout checks](references/rollout.md) for the classification definitions, measurement rules, and delivery fields.

1. Apply Case features C1–C5 to the confirmed frozen definitions and corresponding baseline source. Then assess actual run behavior P1–P6 and browser depth / surface, and finally outcome Y. Note any prior exposure to the result; do not call retrospective review blind.
2. Measure **H, first complete target-anomaly recognition**, using the semantic probe, original trajectory step, inclusive agent-turn count, and prefix evidence defined in rollout checks. Partial recognition, missing traces, and no observed recognition remain distinct. Do not infer an early H from the final patch or successful verdict.
3. Record browser interaction before / during H and after H separately, along with whether it reached the key page, state, and operation and what information it contributed. Actual browser page navigation counts as browser interaction even off-target; merely visiting the right URL does not establish key-scenario coverage. Browser installation, failed startup, jsdom tests, or scorer replay do not establish solver browser interaction. Ambiguous ordering remains unknown.
4. Explain success or failure with evidence for scenario coverage, business understanding, diagnosis, implementation, and verification. To attribute a detour to a competing prompt reading, show that reading and evidence of the agent following it. This does not itself establish a definition defect or a need to rewrite; assess the business connection under N02 separately.
5. Cross-check judge results against frozen Require / Allow and candidate runtime evidence. Distinguish a verifiable conflict from insufficient evidence or no behavioral verdict. Protocol / build failures and dependency modifications must be reported with the applicable run policy, not retroactive prompt constraints.

The confirmed selection rule is specific to Astra high + Codex: H within the first 10 agent turns with no browser interaction through H. Later browser verification does not undo it; final accept and K1 are not prerequisites. This measures early source discovery in that run, not universal difficulty or browser necessity, and does not authorize automatic rejection of new Cases.

## Withdrawing a published Case

Discuss the finding and selection rationale with the user before rejecting or removing a Case. Execute only after an explicit user decision identifying the Case; an existing decision counts, so do not ask for the same approval again. A failed rollout or a competing reasonable interpretation alone does not authorize withdrawal.

1. Record the stable Task / Case ID, decision source, reason, current material version, and supporting evidence in the active round. Preserve historical runtime verdicts separately from the new selection decision.
2. Preserve the exact current Task and its release entry in Git before deletion, including revised definitions, scripts, videos, permissions and symlinks. Keep the pre-deletion commit SHA in the audit record.
3. Confirm that the preserved Task can be reconstructed from that commit, and verify its files, permissions and symlinks against the current material. Stop before deletion if preservation cannot be verified.
4. Commit the pre-deletion materials and audit record, then confirm a clean working tree. Remove only the confirmed Case and its release / manifest / initialization references; remove the whole Task only if no Cases remain. Keep frozen run inputs and evidence intact.
5. Run the release check, confirm unaffected Cases are unchanged, and make a separate removal commit referencing the pre-deletion commit. Push only when authorized.

## Maintaining rules

Keep the operational rules self-contained in this skill. Latest explicit case decisions override earlier case proposals, but do not turn individual edits into universal rules: state words are not categorically forbidden; a functional / UX mixture does not mandate rejection.

Maintain stage-specific experience records in `experiences/definition.md`, `experiences/replay.md`, and `experiences/rollout.md`. They preserve examples, reasons, confirmation scope, and pending generalizations; executable requirements belong in the corresponding check reference. Reading historical experience files is not a prerequisite for applying the checks.

Record new generalizations as candidates in the current round. Add them to shared rules only after user confirmation, with the original example, reasoning, applicable scope, and decision source. Historical round counts describe historical baselines; compute current coverage from the selected manifest.
