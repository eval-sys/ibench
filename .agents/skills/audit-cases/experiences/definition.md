# Definition audit experiences

## D01 — Business reasoning belongs in the rationale

- **Evaluated example:** A photo / map rationale mixed PR history, source paths, uncertainty, and interface interpretation instead of directly explaining the relation between a photo, its map marker, and the detail card.
- **Rule:** Explain the objects and why their behavior matters. Put provenance and audit reasoning in the round record.
- **Reason:** A judge should understand the business criterion without reconstructing an investigator's work log.
- **Limit:** Preserve entity relationships and calculations needed to justify the criterion; concise does not mean context-free.

## D02 — Describe accepted outcomes positively

- **Evaluated example:** A photo detail card could follow its map marker, or temporarily close during dragging and re-anchor afterward.
- **Rule:** State valid outcomes and their allowed variations directly.
- **Reason:** These alternatives clarify the contract better than an inventory of forbidden behaviors.
- **Limit:** Necessary exclusions may still protect the user goal; do not weaken constraints through wording cleanup.

## D03 — Reference observation describes the reference result

- **Evaluated example:** A reference observation repeated the navigation sequence, photo fields, frame coordinates, and a before / after comparison.
- **Rule:** Concisely describe the claimed repaired behavior and essential distinctions. Store detailed evidence and measurements in the audit record.
- **Reason:** The observation explains one valid result; it is not a script transcript or a second rubric.
- **Limit:** Editing this text does not verify the recording or authorize a new behavior claim.

## D04 — Intended operation does not guarantee availability

- **Evaluated example:** A user wanted to export a dashboard, while accepted repairs included hiding or explaining the unavailable export when there was no report content.
- **Rule:** Audit the natural goal separately from whether the product should permit that operation. Preserve the explicit Require / Allow boundary.
- **Reason:** Truthful prevention can serve the user better than a fake successful action.
- **Limit:** This does not permit disabling arbitrary functionality; the particular unavailable alternative needs support in the definition.

## D05 — Generalize incidental samples while preserving business context

- **Evaluated examples:** Parallel chat review generalized seeded conversation titles, fixed counts, and browser-tab instructions into the goal of reviewing conversations simultaneously. For Dolibarr PR 39305 / Case 1, "Set the mark rate to 25% for all lines on my Teclib proposal." became "Set the mark rate to 25% for all lines on my draft proposal for a customer."
- **Rule:** Test whether changing a sample name, count, or method preserves the goal. When that detail is unnecessary for business-object identification, describe the object type, business relationship, and purpose instead.
- **Reason:** The intention should communicate the user's activity without requiring knowledge of an incidental fixture label or prescribing the reproduction route. Necessary business context remains available.
- **Limit:** Keep actual user constraints and identifiers needed to distinguish objects. Given and replay data may retain concrete names. The 25% target and all-lines scope remain in the proposal intention. Generalizing names does not establish browser necessity or change the acceptance criteria.
- **Actions follow-through:** The user explicitly requested the same cleanup in Actions, then across the new batch on 2026-10-09. Replace fixture identifiers with stable business roles while preserving the sequence and causal conditions. Keep `/shrug`, the ordinary Comments field, and the leading-digit secret name `1DEPLOY_KEY` in Actions where they specify the operation or relevant reproduction input. The user later confirmed omitting `/shrug` and `1DEPLOY_KEY` from their respective Intentions: a necessary reproduction input is not automatically a necessary goal constraint.

## D06 — Concise criteria and business rationale with unchanged acceptance

- **Evaluated example:** FreshRSS user creation repeated the initial neutral Username condition, required/format constraints, invalid-attempt feedback, correction and normal account creation in a long Require. The proposed concise wording keeps those independent outcomes, including correction after leaving the field.
- **Rule:** Separate observable acceptance outcomes, scene/action details, allowed variations and business justification into their respective fields. Map the old and new conditions before accepting a shorter version.
- **Reason:** Reviewers and judges need a clear contract and an explanation of why it serves the user's activity, without reconstructing them from repeated prose.
- **Limit:** Preserve independent outcomes, causal timing, necessary regression checks and all allowed alternatives. In the proposal example, buying costs and the mark-rate calculation explain the expected prices and must not disappear merely to shorten the rationale. Editing text does not verify runtime evidence.

## D07 — Given / When describe the business scene, not capture machinery

- **Evaluated example:** Dolibarr PR 41125 / Case 1 described missing direct-debit records through `llx_prelevement_bons`, `llx_prelevement_lignes`, the arbitrary `rowid 999999`, and four literal URLs. The scene instead needs an authenticated administrator, enabled modules, a missing order and line, and direct visits to the order details, rejects, statistics and line details.
- **Rule:** Given carries necessary business data, relationships, permissions and initial state; When carries the operations, order, input modality and causal timing. Test each detail for its effect on meaning, object identification or judgment. Keep executable fixture details in reproduction materials when their exact representation is incidental.
- **Reason:** Internal identifiers and capture settings obscure the user scenario and can make an incidental fixture look like part of the acceptance contract. The earlier mobile-swipe cleanup similarly removed fixed viewport and gesture coordinates while preserving touch interaction and the intended scroll behavior.
- **Limit:** Do not delete stock quantities, permission precedence, dependency relationships, focus state, off-screen placement or meaningful polling order merely because they are detailed. User-facing names can link a scenario to its observations. URLs and literal inputs remain when the specific destination or value is the subject of the Case. Text cleanup does not establish replay validity.

## D08 — A necessary reproduction detail is not automatically a goal constraint

- **Evaluated examples:** Sending a shrug did not require `/shrug` in Intention; adding an Actions secret did not require the invalid `1DEPLOY_KEY` name. Skipping to the next song did not require prescribing shuffled playback or watching lyrics. Sorting the Songs list did not require directing exploration to Composer. Exact commands, invalid inputs and the selected sorting field remain in the reproduction materials.
- **Rule:** Test each Intention constraint against the natural user activity independently of the hidden defect. Remove details whose role is to direct the solver to the evaluated trigger, field or anomaly. Preserve enough business context to make the activity understandable. Use `gh` when source interpretation is needed, distinguishing reproduction examples, necessary conditions and code-level inference.
- **Reason:** A prompt that selects the precise failing field or input can make defect discovery a supplied instruction instead of part of the task. Reproduction requirements belong to the evaluated scene; they do not by themselves justify that information in the goal.
- **Limit:** A specific operation is not inherently a leak. Preserve genuine business targets and user constraints, including previously confirmed rates and meaningful input modalities. Do not erase domain context or claim that removing a hint proves browser necessity. Actions remain an explicit reproduction aid in the `intent-actions` profile. The next-song source review found a generic lyric-parser lifecycle repair, but did not dynamically prove every non-shuffle path fails.

## D09 — Omit redundant product names from natural user goals

- **Evaluated object:** `github/oppia/oppia/pull/26180/issue/1`, Intention in `user-task.json`.
- **Original and revision:** `Visit the Oppia community forum.` became `Visit the community forum.` The preceding calendar review similarly replaced `Use the Calendar in my OpenEMR tab.` with `Check my calendar.`
- **Rule:** When the application environment already establishes the product, state the activity without repeating its brand, provided the goal and destination remain clear.
- **Reason:** Users working inside an application can refer directly to its calendar or community forum. Repeating the brand can make the goal read like an external test description. This concerns naturalness and redundant context; a product name is not itself an answer leak.
- **Limit:** Preserve names needed to distinguish products, integrations, source formats or destinations. Do not erase meaningful compatibility constraints such as a recipe import's source format, or remove product identity from reproduction and source records. This experience does not authorize unrelated Case edits or scoring changes.

## D10 — Reference repairs must fit the solver's allowed modifications

- **Evaluated example:** Navidrome PR #5683 / Case 1 (`shuffled-queue-lyrics`) changes only `ui/package.json` and `ui/package-lock.json`, upgrading `navidrome-music-player` from 4.25.3 to 4.25.4. The actual solver instruction forbids adding, removing or changing project dependencies.
- **Rule:** Inspect the adopted repair's dependency changes and compare them with the solver contract during definition review. Separate dependency-only fixes, mixed repairs and incidental lockfile metadata; record whether a compliant alternative has actually been established.
- **Reason:** A valid upstream fix can still fall outside this benchmark's permitted repair scope. That mismatch must be resolved before treating the Case as ready for evidence review.
- **Limit:** Do not reject every PR that touches a lockfile, infer that all source-only repairs are impossible, or silently permit dependency changes. Runtime validity of an alternative requires later evidence. The confirmed removal applies to C29; other Cases need their own scope decision.

## D11 — A clear intention defines an exploration scope, not a unique hidden path

- **Evaluated example:** A21's goal, "Update a note while previewing my document as an editor," led Astra to comment permissions; the evaluated anomaly concerns explanations for denied table-cell edits. Actual UI and source inspection established distinct comment and cell-edit paths. The investigation was informed by the target and was not a blind discovery experiment.
- **Rule:** Judge whether the intention locates a reasonable business scene or exploration scope and whether hidden acceptance naturally relates to that goal. Do not require the intention to uniquely name the page, defect, subtle operation or replay route. A reasonable alternative reading is not automatically a definition defect.
- **Reason:** Exploring the application and understanding its business behavior are part of the benchmark. Rewriting every missed intention around the hidden result supplies part of the discovery task.
- **Limit:** A business connection is still required; this does not validate unrelated or contradictory acceptance. One trajectory cannot establish misunderstanding probability. Reasonable exploration elsewhere does not satisfy this Case's frozen Require / Allow.

## D12 — Rationale connects the goal, business workflow and outcome

- **Evaluated example:** A21's existing rationale explains column-over-table permission precedence but omits the connection from editing in View as to inspecting denied-edit feedback. Grist's role preview, table-cell editing and access-rule memos provide the business vocabulary for that connection.
- **Rule:** Explain why a selected business action follows from the user's intention, which repository-specific rule governs its outcome, and why the required result is correct while the anomaly is not. Use supported domain semantics rather than generic design slogans or a restatement of Require.
- **Reason:** A judge needs a defensible business argument connecting exploration and acceptance, not an arbitrary test justified only by its existence.
- **Limit:** Do not invent a bridge, narrate replay clicks, add criteria, or claim that a reasonable workflow guarantees finding the exact trigger. Several exploration paths can be legitimate. Explaining a selected path does not resolve outstanding Case selection decisions or change historical scoring.

## D13 — Distinguish product concepts before narrowing the user goal

- **Evaluated example:** A22 asked which company and building a room in the Locations list belonged to. The company in the selected scene is an ancestor Location, while the product also has an independent Company attribute. Source, an enabled-but-empty Company column and the edit form's separate Parent / Company controls establish the distinction. Astra initially mentioned room details, then treated the hidden Company column as the defect without browser verification.
- **Rule:** Check product-specific meanings before attributing a detour. An object identified in a list need not restrict exploration to that page. Clarify the natural goal without prescribing hidden representation: the confirmed intention is "Find where a room is located," without adding "hierarchy," a breadcrumb requirement or a mandatory page.
- **Reason:** The base list already permits inferring the parent chain; the selected defect concerns orientation and navigation on the room detail page. A goal admitting another usable path does not automatically invalidate that scene's quality criteria. The rationale must explain why the selected path and outcomes serve the goal.
- **Limit:** This does not ban hierarchy terminology or justify arbitrary hidden scenes. Respect explicit user constraints, keep criteria grounded in product semantics, and separate business validity from discoverability. One trajectory does not estimate ambiguity frequency.
