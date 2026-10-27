# Replay-round checks

Start only with the main skill's definition gate satisfied for these exact inputs. Read the confirmed scene and observation plan first, then complete before / reference-after fixtures and recordings. A diff helps find changes; it does not replace full script review. Before actual execution, inspect `uv run ibench debug --help` or `uv run ibench replay --help` for the available options; do not invent CLI flags.

## R01 — Given and reproduction setup

**Action:** Trace the actual entrypoint, environment, data seed, setup, action, and cleanup in execution order. Verify roles, objects, permissions, pages, and initial state.

**Criterion:** Replay setup establishes Given, action preserves When, and cleanup does not falsify the observed result. Reproduction data preparation is part of the agent's work: solver and replay need not start with identical or equivalent business records. A replay-only order, form, account, or configuration is not by itself a defect or a reason to copy the fixture into solver initialization. Assess an actual impossibility or contradiction separately, with evidence. Replay seed instantiates the scene; it is not an additional repair criterion. Keep hidden actions, rubric, reference videos, and answers out of solver inputs.

For a required external destination or service, inspect the relevant environment's actual network policy and verify access from that environment. Host access alone is insufficient. Distinguish policy blocking from DNS/TLS failures, service outages and product navigation defects using browser URLs/errors, request evidence and proxy/sidecar logs where available. A new tab or initially correct URL proves only that part of the operation; check the destination content when the criterion requires it. One failed request alone does not prove a policy block. If the current network prevents required observations, record an environment/evidence blocker rather than a solver failure or invalid GoldPatch. Do not automatically broaden network access or weaken the criterion; retain the confirmed policy or exclusion decision.

**Record:** Script / seed paths and version, state evidence, and any demonstrated failure to establish Given. For external dependencies, include the required destinations, effective policy, in-environment results and what remains observable or blocked. Do not report a seed difference alone as an audit problem. A fixture name alone does not establish its role.

## R02 — Faithful user operation and setup boundary

**Action:** Follow every relevant input, timing condition, data mutation, and fault injection. Check that the intended input modality actually reaches the product, especially touch versus mouse or synthetic DOM events.

**Criterion:** The operation matches confirmed When. Realistic context loss or database locking may establish a legitimate scene; classify by effect, not by the mere presence of injection. Product-source edits, manufactured DOM results, or bypassing the target operation cannot demonstrate repair. Passive diagnostics must not change the interaction.

**Record:** Input / state trace, injected conditions and business justification, and which observations show the operation occurred. Do not certify mobile behavior from a different input modality.

## R03 — Per-criterion evidence on both sides

**Action:** Fill the confirmed observation plan with actual before and reference-after evidence. Inspect transient intervals as well as final frames. For independently required behavior, test whether a minimal partial repair could still look correct under this replay.

**Criterion:** Before supports the stated target anomaly; reference-after satisfies Require with Allow respected. Each required distinction is observable without one failure masking another. A successful capture, Oracle process, or protocol check alone is insufficient.

**Record:** `criterion → executed operation → video timestamp / runtime evidence → supported conclusion / gap`. Separate a bad definition, bad script, insufficient video, and invalid reference repair; these require different remedies.

## R04 — Valid alternatives and observable failures

**Action:** Walk each relevant Allow branch and the broken implementation through the script. Inspect selectors, waits, disabled / absent controls, shortcuts, and early returns.

**Criterion:** Require / Allow must distinguish a genuine user-visible defect from a legitimate repair. For a suspected restriction, state a concrete implementation that satisfies both, then identify the extra condition that would reject it. Reference defaults, DOM structure, control visibility, Tab counts, page sizes, or labels are not additional grading rules. If the rubric itself lacks a defensible pass/failure distinction, reopen definition review rather than inventing stricter replay conditions.

Judge may adapt selectors, waits, controls, and observation routes while preserving Given / When and the scoring boundary. The supplied reference replay need not run unchanged on every legitimate implementation. Ordinary implementation-specific waits are adaptation work, not standalone Case blockers; do not schedule a broad wait rewrite without a demonstrated semantic or evidence problem. Prefer recording the actual outcome when authoring scripts. Safe conditional paths accommodate missing / disabled controls without force-clicking or skipping another required entrance. A default frame with no message is insufficient to reject an allowed tooltip or expansion that has not been inspected.

**Record:** Normative criterion, legitimate-repair counterexample, extra restriction, and semantic adaptation needed. Distinguish a rubric defect, an unjustified grading condition, and editable replay scaffolding. Record whether actual evidence remains obtainable after adaptation; do not claim unexecuted alternatives were dynamically verified.

## R05 — Recording provenance and freshness

**Action:** Match each recording to script bytes, product revision, seed, environment, and capture method. Verify presentation descriptions and guides against the actual video timeline. Use independent clean states for the two sides.

**Criterion:** Behavioral claims refer to the right recording and version. Editing execution scripts invalidates old video as evidence of the new execution; rerecord affected sides before declaring validation. Preserve trusted recordings as captured; do not substitute edited video. Text-only edits require a semantic consistency check, not automatic rerecording.

**Record:** Artifact paths / hashes, revisions, video intervals, capture checks, and what was actually rerun. If recording is outside the authorized scope, report it as pending instead of claiming freshness.

## R06 — Supported verdict and definition feedback

**Action:** Conclude separately for every Case: evidence supports satisfaction, supports violation, or is insufficient. Check observations and explanation text against the actual supported behavior.

**Criterion:** A sibling Case cannot compensate for failure. Environment / replay / evidence failures remain distinct from product failure; in scoring they require `verifier_failed` when no supported binary verdict is possible. New semantic contradictions go back to a definition round; the replay cannot decide a new goal on its own.

**Record:** Criterion-linked conclusion, unresolved evidence gaps, proposed remedy, and whether the definition gate must reopen. Do not promote a single valid reference implementation into the only acceptable solution.

