# Definition-round checks

Apply before replay or trajectory review. Read the actual compiled solver prompt when available; otherwise inspect the selected prompt template and profile with `user-task.json` and mark the rendered prompt unverified. Read all natural-language fields in each `rubric.json`, including observations, rationale, and theory, plus textual presentation metadata. Do not treat Actions visible in Preview as prompt content under the `intent` profile.

## Field meanings

Case inputs live under `tasks/<task-id>/score/steps/score/workdir/case-context/`, with Case order and identity in `manifest.json` and per-Case files under `issues/<n>/`. For a completed run, use its frozen compiled inputs instead of current task files.

| Field / source | Meaning |
| --- | --- |
| Task name / title in `tasks/release.json` | PR-level display labels; not grading criteria. |
| Case title in `fixtures/reference-after/presentation.json` | Recording display label; not an independent requirement. |
| Intention: `user-task.json.intent` | The user's goal. The `intent` prompt profile exposes this without Actions. |
| Actions: `user-task.json.actions` | Ordered reproduction steps; exposed under `intent-actions`, not grading assertions. |
| Given: `rubric.json.definition.given` | Initial data, user state, page, or selection prerequisites. |
| When: `rubric.json.definition.when` | The user operation being evaluated. |
| Require: `rubric.json.definition.require` | Mandatory observable repair outcomes under Given / When. |
| Allow: `rubric.json.definition.allow` | Explicitly accepted alternative implementations or behavior. |
| Observed before: `rubric.json.definition.observed` | Historical target anomaly; not an additional repair criterion. |
| Reference observation: `rubric.json.reference_observation` | One repaired example; its incidental details are not mandatory. |
| Requirement rationale: `rubric.json.requirement_rationale` | Business justification and reasoning; cannot add criteria or narrow Allow. |
| Theory: `rubric.json.definition.theory` | Supporting design references and explanations; not independent grading criteria. |
| Presentation text in fixture `presentation.json` | Labels and descriptions of the recorded scene; not a new goal or criterion. |

Require / Allow alone define acceptable repairs in the Given / When scenario. Definition review checks the coherence of textual claims; replay review later checks whether they actually happened.

For each rule below, write the indicated output and a status using the main skill's finding format. A plausible interpretation without sufficient evidence is `pending`, not `pass`.

## N01 — Source and chosen scope

**Action:** Identify the source PR's actual user-observable change, the relevant base / merge history, and which part this Case selects. For ambiguity, use `gh` to inspect the PR, linked issue, relevant discussion, and diff. Prefer the maintainer's explicitly adopted final decision over early suggestions.

**Criterion:** The Case concerns this PR's change, not an already-fixed related issue. Selecting part of a PR is valid if the boundary is explicit. Source code explains the mechanism, not a mandatory implementation.

Inspect the adopted PR diff for dependency changes and compare the reference repair with the actual solver's allowed modifications. Check dependency declarations, resolved versions and vendored content; distinguish a dependency-only repair, a mixed source/dependency repair, and incidental lockfile metadata changes. A changed lockfile alone does not establish a dependency change, and a dependency-only reference does not prove that all source-only repairs are impossible. When the reference relies on a forbidden dependency change and no compliant repair has been validated, record a scope/feasibility blocker for selection. Do not silently relax the solver contract, label the upstream fix invalid, or advance that Case to evidence review as ready. A source-based alternative remains unverified until tested in the evidence phase after its definition gate is resolved.

**Record:** Source links and supporting excerpts, selected behavior, excluded behavior, and unresolved source claims. Include changed dependency paths and versions/content, the solver constraint, whether the selected repair is dependency-only or mixed, and the evidence or uncertainty about a compliant alternative. Record any explicit exclusion decision separately from repair impossibility. Source lookup resolves meaning; it does not prove runtime correctness.

## N02 — Standalone goal and natural business connection

**Action:** Read only the solver-visible prompt first. State the application area, user object, and intended goal. Then explain why the Given / When scene and each required result naturally relate to that goal.

**Criterion:** The prompt supplies enough context for a reasonable business scene or exploration scope without relying on hidden Actions. It need not uniquely identify the evaluated page, defect, subtle operation, or reproduction route. Multiple reasonable readings and exploration paths are compatible with a valid intention. A concrete exploration goal is valid; a vague “Explore” added solely to justify a predetermined trigger is not sufficient.

The evaluated scene and required outcomes must still have an explainable business connection to the goal. Distinguish insufficient context, an unrelated or contradictory criterion, and a reasonable exploration path that simply missed the target. A competing reading does not by itself establish a definition defect. Record the specific missing or conflicting connection before proposing clarification; do not add the hidden anomaly or trigger merely to guarantee a hit.

Check whether a goal's ordinary business term also names a distinct product field or entity. Use source and product context to distinguish those meanings before blaming the prompt or the solver; prefer minimal object clarification over prescribing the evaluated mechanism. A phrase identifying an object in a list does not necessarily restrict work to that list; preserve explicit location constraints when actually stated. Completing the goal through another path does not by itself invalidate a justified quality requirement in the selected Given / When scene.

Make that connection explicit: "To accomplish [user goal], a developer has reason to inspect [business relationship or operation], because [repository-specific business reason]; [available product entrypoint, state or feedback] supports that exploration path." Being in the same application or page is insufficient. Assess the business relevance of the outcome separately from the basis for reaching the selected conditions. Do not fill a missing bridge with invented product facts or assume that a justified workflow guarantees discovery of its exact hidden trigger.

A rollout can show which reading the agent followed, not how likely users or agents are to misunderstand the intention. One missed target does not establish that the prompt is invalid or needs rewriting. Alternative exploration paths do not make repairs to unrelated defects acceptable: grade the selected Given / When against its frozen Require / Allow.

**Record:** Prompt excerpt, goal / area / object, business connection to the tested scene and required outcomes, and any reasonable competing interpretation. Separate observed divergence from a supported definition problem; leave unsupported claims pending. Functional / UX mixtures and advanced settings are scope questions, not automatic exclusions.

## N03 — Useful context without revealing the answer

**Action:** Mark each prompt constraint as a necessary business fact, incidental seed detail / implementation choice, or answer-bearing hint. Check Actions too when solver-visible. For proposed removals, test whether the remaining goal is still understandable.

**Criterion:** Keep relevant business entities, relations, and genuine constraints. Avoid telling the agent the anomaly, exact hidden trigger, fix, or selection consequence. Do not universally remove names, quantities, state words, or action verbs; justify each change in context.

For incidental names, counts, or interaction methods, ask whether changing the sample or using another method would preserve the user's goal. If so, and the detail is unnecessary to identify the intended business object, express the object type, business relation, and goal instead. Keep concrete sample identifiers in Given / replay data when needed. Preserve genuine user constraints and necessary disambiguation; the generalized intention must still satisfy N02. For example, "my Teclib proposal" can become "my draft proposal for a customer" when the customer name is only a seed label, while retaining the requested 25% mark rate and all-lines scope. This removes incidental specificity, not an answer leak; an exact name is not inherently a hint.

Apply incidental-identifier cleanup to both Intention and Actions. Actions must still identify the same objects by their business roles and preserve the ordered operations, relevant starting conditions, input modality, and timing; do not turn an action sequence into a vague goal or remove a value that defines the problematic input.

When the application context is already established, omit redundant product names from Intention and express the activity directly: "Visit the community forum" rather than "Visit the Oppia community forum." Check that removing the name leaves the destination and goal clear. Keep names that distinguish products, integrations, source data formats or genuinely different destinations. A redundant brand is a naturalness issue, not automatically an answer leak; do not remove product identity from scenario or provenance records merely to shorten the goal.

Audit Intention separately for reproduction-path disclosure. A detail required to reproduce or grade the Case is not automatically required in the user's goal. Mark any named field, exact invalid input, command, menu route, selected option, state combination, or observation instruction that directs exploration to the hidden trigger. Ask whether an ordinary user needs that constraint to express their activity independently of knowing the bug. If not, keep the application area, business object and natural activity, and leave the precise trigger in Actions / Given / When. Do not tell the solver which anomaly to observe, what must be preserved, or which control to repair. This check concerns the information disclosed, not just sentence length.

For example, express sorting the Songs list without prescribing Composer, choosing a translation language without prescribing the fixture's English option, or adding an Actions secret without prescribing `1DEPLOY_KEY`. A real requested rate, data format, authentication method or keyboard-only workflow may still be necessary: identify its business role rather than banning all specific inputs. Previous explicit user decisions remain authoritative. When necessity is unclear, use `gh` to inspect the PR, linked issue, adopted discussion and relevant diff; distinguish a reported reproduction route from an established necessary condition. Code-level inference is not a runtime reproduction. If the goal would become vague or unrelated to the criterion, retain the necessary context or record a pending scope question instead of adding an answer-bearing hint.

The `intent-actions` profile deliberately exposes a reproduction sequence. Preserve that sequence and flag its disclosure in the audit; do not delete essential trigger inputs from Actions merely to make it resemble `intent`, or claim the same exploration freedom for both profiles.

Do not restore a trigger hint merely to guarantee that the solver follows the fixed replay. A broader natural goal may support other valid exploration paths; assess their connection to the evaluated scene and later use rollout evidence to record the pursued interpretation and scenario coverage. A missed target does not require narrowing the goal to hidden acceptance. Removing a hint alone does not establish that the Case is suitable or requires browser interaction.

**Record:** Exact suspect text, its informational role, why it is needed or leaks the target, and a minimal proposed edit if justified.

## N04 — Acceptable outcomes and multiple valid solutions

**Action:** For each Require, state a user-observable pass and failure. For each Allow branch, explain how it preserves the selected user result. Check for contradictions, requirements hidden in explanatory fields, and accidental dependence on the reference DOM / layout / mechanism.

**Criterion:** Criteria are observable, mutually coherent, and preserve the goal. Allow must not permit the opposite outcome, such as losing changes in a preservation Case. Reference-specific details are mandatory only if explicitly justified in Require / Allow.

Express Require / Allow as accepted outcomes and legitimate variations, rather than making reviewers reconstruct the contract from a rejection list. A user's requested operation need not be supported: a truthful unavailable state may satisfy the defined goal when Allow explicitly permits it.

Keep Require to the observable outcomes needed to distinguish a valid repair from a partial or incorrect one. Remove repeated starting conditions, action transcripts, explanations and redundant restatements; Given / When carry the scene and operation, rationale carries the business reason, and Allow carries implementation freedom. Preserve any condition, timing distinction, independent outcome or regression protection that changes acceptance. Prefer one clear statement per independent outcome; brevity is not a word limit or a reason to delete requirements.

Before editing, map each existing acceptance condition and Allow branch to its location in the revised text. Check a passing example and a minimally incomplete repair against both versions. A changed verdict indicates a scope change requiring an explicit decision, not merely wording cleanup. Do not turn incidental reference details into requirements while shortening.

**Record:** Criterion-to-outcome mapping, allowed alternatives, counterexamples, and disputed boundaries. Do not expand a sampled Case to the entire PR or workflow.

## N05 — Consistent scene across all text

**Action:** Compare Intention, Actions, Given, When, Require, Allow, Observed, reference observation, rationale, theory, and presentation text for object, role, state, operation, and order. Distinguish prerequisites from timing conditions that arise during When.

**Criterion:** All fields describe the same selected scene without conflicting states or labels. Intention may be broader than When. “Attempt an operation” must not silently become “successfully execute it” when Allow permits the control to be absent or disabled.

Given should state the necessary business objects, relationships, permissions and initial UI state. When should state the evaluated user operations, preserving their order, problematic inputs, input modality and causal timing. Neither field should become a setup log or implementation transcript.

For each technical or sample detail, ask whether changing it would change the selected scene, distinguish its objects, or change the acceptance decision. Remove or generalize irrelevant database tables, internal IDs, source paths, implementation classes, fixed capture dimensions, traversal counts and fixture-verification commentary. Express a missing record as missing, a shipment setting as its business behavior, and an off-screen field as off-screen. Keep exact routes or values when their identity is genuinely under test or necessary to distinguish entrances; otherwise name the user-facing destinations and keep executable reproduction details in Actions or replay materials. Concrete business labels may remain when they connect the fields and evidence unambiguously. Preserve quantities and relationships needed for calculations, permission precedence, dependency eligibility, focus, scrolling and timing; this is not a blanket ban on names, numbers or technical terms.

Before editing, map each prerequisite and operation to the revised text and compare it with Require / Allow and both observations. Removing capture parameters must not remove the state they established. Record any execution detail removed here so later replay review can still identify the original reproduction.

**Record:** Conflicting excerpts or an explicit coherent scene summary, including required initial business data; original and revised Given / When, removed details and their roles, and the preserved prerequisites / operations. Physical seed and script consistency remain for the evidence round.

## N06 — Supported business reasoning

**Action:** Trace rationale and theory claims to business relationships, source facts, calculations, or cited references. Reconstruct any formula from defined entities. Separate facts, inference, and design judgment.

**Criterion:** The explanation shows why the criterion serves the goal. It does not invent business facts, silently narrow Allow, add new grading conditions, or merely narrate a script. Published task material is English.

Requirement rationale should directly explain the business objects, their relationships, and why the behavior matters. Keep PR provenance, source paths, capture logs, and reviewer uncertainty in the audit record. Reference observation should concisely describe the claimed repaired behavior, without a replay transcript, diagnostic sample counts, or a comparison essay. Preserve essential branch distinctions; a concise claim still needs evidence review later.

Ground the rationale in this repository's actual business semantics and connect **user intention → relevant action path → correct / incorrect outcome and user consequence**. Explain why that path serves the goal, which domain rule or relationship governs the result, and why the required behavior respects it while the target anomaly violates it. Name the relevant roles, object relationships, permission precedence, calculations or lifecycle transitions when needed; generic claims such as "better UX" or a theory label cannot substitute for that reasoning. Describe the path at the business-operation level, not as click-by-click reproduction. A selected path may be one of several reasonable paths; the rationale must not claim it is the only interpretation or proof of likely discovery.

If the business chain is unsupported, record the gap under N02 / N06 rather than write a persuasive justification after seeing the hidden test. Evidence for specific reachability or discovery claims belongs in the audit record. The rationale explains existing criteria; it must not create new ones or make hidden information solver-visible.

Write rationale as the shortest sufficient explanation of the business relationship and user consequence behind the criterion. Do not paraphrase the whole Require / Allow contract or narrate setup and clicks. Retain non-obvious domain relationships and calculations needed to understand the expected outcome. Check each sentence for whether it supplies a distinct reason or necessary fact; remove repetition without inventing new rationale or silently moving grading conditions out of Require / Allow.

**Record:** Claim / source / reasoning, unsupported assertions, and the minimal clarification needed. Do not put the full audit background or answer into the solver prompt.

## N07 — Planned observability

**Action:** Without inspecting recordings or scripts, map each Require and relevant Allow branch to the user operation and observable signal needed to judge it. Consider a minimal partial repair: could one satisfied condition mask another still-broken condition?

**Criterion:** Each selected requirement has a discriminating observation plan. Identify essential transient timing or independent states. Additional coverage outside the defined scope is a suggestion, not a newly imposed requirement; do not default to a complete input matrix.

**Record:** `criterion → scene / operation → signal and timing → distinguishable pass / failure`. Mark actual evidence coverage unverified until the replay round. A missing recording does not by itself make the textual definition invalid.

## Definition handoff

Summarize N01–N07 per Case and resolve definition blockers before evidence review. The handoff must explain the goal, Given / When, full target anomaly, Require / Allow boundary, business justification, and planned observable signals; link to source fields instead of duplicating unchanged files. Preserve rejected interpretations and explicit scope decisions so the next round cannot silently reopen them as facts.
