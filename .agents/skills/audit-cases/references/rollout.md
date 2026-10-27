# Rollout checks and measurement

Apply only after confirming the natural-language definition of the frozen run inputs. Audit the actual solver instruction, baseline source, solver trajectory, production patch, and scorer evidence. Reference repair and scorer replay do not establish what the solver knew or did.

Record each value with reasoning and an evidence location. Use `U` for insufficient evidence and `NA` for inapplicable. Separate material definitions, observed run facts, and audit inference. Missing evidence is not a negative result.

## Case features C1–C5

Classify before assessing run behavior and outcome. If the result was already seen, disclose this; the review is not blind. These labels describe Cases, not difficulty ranks.

| Dimension | Categories and decision rule | Required evidence |
| --- | --- | --- |
| C1: prompt localization | G1: explicit Case-relevant state / relation / result; otherwise G2: specific function with key condition / feedback implicit; otherwise G3: broad work scope admitting multiple subfunctions; U: actual prompt unavailable. | Actual prompt excerpt, area / object / constraint, and relation to acceptance. G3 needs at least two compatible work directions. |
| C2: business relationships | Multi-label B1: object values / presentation; B2: collection membership / operation scope; B3: eligibility / constraints; B4: cross-entity relationships; B5: state ownership / continuity. | A concrete proposition for each label: relationship → behavior that should hold. |
| C3: code clues | K1: a naturally reachable local implementation contradiction supports the defect; K2: support requires tracing lifecycle, events, geometry, or data flow / testing a hypothesis; U: no supported diagnostic chain. | Baseline entrypoint, exact clue, causal reasoning, and locating steps. Finding a reference-changed file is insufficient. K1 does not establish low discovery cost. |
| C4: trigger conditions | Multi-label T1: single local action; T2: combined / sequential actions; T3: leave and revisit; T4: parallel contexts; T5: boundary data / state; T6: transient timing; T7: pointer path / spatial gesture; T8: equivalent entrances required by the criterion. | Frozen When and the conditions actually relevant to the anomaly. Ordinary loading is not T6; ordinary click is not automatically T7. |
| C5: recognition signals | Multi-label O1: content / values / options; O2: visual / spatial feedback; O3: input response / operability; O4: continuity / persistence; O5: transient feedback. | User-visible carrier, observation time, and distinguishable normal / abnormal result. Internal API state cannot replace required user-visible evidence. |

For C4, also record operation blocks and count **A**. Count one business state-changing / navigation action per block; drawing one path is one block rather than one per vertex. Selection, save, leave, and reopen are separate. Exclude Given setup, passive observations, waits, and tool-level calls. A hover that triggers a required popup counts; merely hovering to inspect does not. Preserve conditional branches. A describes the selected workflow, not the shortest possible discovery route.

## Run behavior P1–P6 and browser depth

Use `hit / partial / no target evidence / U / NA` per stage. Stages need not occur in order; code discovery can identify the anomaly without browser reproduction.

| Stage | Evidence needed |
| --- | --- |
| P1: target selection | Explicit work direction and production patch address the target business defect; compatibility with intent is assessed separately. |
| P2: scenario exploration | Actual establishment of target objects / state and operation, with the tested surface stated. |
| P3: anomaly recognition | Specific target anomaly expressed and supported by then-available code, tests, or browser observations. |
| P4: cause diagnosis | An explicit causal explanation connecting mechanism to behavior; unsupported hypotheses remain partial. |
| P5: implementation | Production patch mapped to criteria; runtime evidence is needed to confirm behavioral repair. |
| P6: verification | Actual checks and assertions cover the target outcome and scope. Code tests can cover their asserted relationships; do not credit UI / timing / integration behavior they did not check. |

Browser depth: `D0` no observed browser operation; `DX` attempted but blocked; `D1` page / object inspection; `D2` local operation and result inspection; `D3` continuous / boundary operations or comparisons; `D4` cross-context return and continuity verification; `U` insufficient trace. Local dropdown close / reopen is D3, not automatically D4. Separately record surface: `app / frontend-fixture / component / none / unknown`. jsdom / hook tests are non-browser tests. Depth describes the reached workflow, not its relevance or quality.

## H: first complete target-anomaly recognition

1. Build a reviewer-only semantic probe from frozen Observed before plus Given / When: essential situation, state / relationship, and abnormal behavior. It is not sent to the solver and adds no scoring criterion.
2. Read the trajectory chronologically. H is the first agent event explicitly expressing the complete target anomaly with supporting evidence already available in that prefix. Root-cause explanation is unnecessary. Opening a relevant file, tool output containing the defect, vague suspicion, or a final successful patch does not establish recognition.
3. Keep partial recognition separate. If no complete expression is observed, record `not observed`; if the trace is missing or uncheckable, record `U`. Do not infer internal understanding or backfill H with later explanations. Record whether recognition preceded the relevant edits.
4. For ATIF, count `source == "agent"` events from the first such event through H inclusive. Keep original `step_id`. System / user messages and observations do not add turns; parallel tool calls in one event remain one turn. Include preparation, failed searches, and detours. This is a harness event count, not a universal model request or reasoning-step count.
5. Record actual browser operations before / during H separately from later operations. Any browser interaction counts, even off-target. Same-event ordering that cannot be established is `U`, not evidence of no interaction. Installed tools or failed startup are not successful browser interaction. If H is absent, do not invent an “after H” interval.
6. Record key-scenario coverage (`hit / partial / miss / U`) and information contribution (`advanced diagnosis / later verification / no observed target contribution / U`) with observations and the agent's resulting understanding. Visiting the right URL alone does not establish coverage; temporal precedence alone does not establish contribution.

Optional reading cost: sum UTF-8 bytes of tool-returned text actually exposed through H. Count repeated returns, not duplicate archival wrappers; exclude JSON container / escaping overhead and image / video conversion. If reliable extraction is unavailable, use U. Batch reads can lower turn counts, so the 10-turn Astra selection rule is an operational threshold, not a universal cost measure.

## Outcome and attribution

Record **Y** as original per-Case `accept / reject / unjudged` with its source. Separate Task reward, protocol / build failures, and behavioral verdict. Do not apply later prompt restrictions to earlier runs.

For judge review, record `supported / verifiable conflict / insufficient evidence / no behavioral verdict`; a claimed conflict needs observable facts contradicting frozen Require / Allow or the verdict.

Describe successful discovery as `code / browser / mixed / U` using diagnostic evidence, not browser depth or outcome. Code diagnosis followed by browser verification remains a code discovery path. For failures or incomplete work, name the evidenced gap: wrong target, missing scenario, unchecked feedback, unsupported diagnosis, incomplete implementation, insufficient verification, environment obstruction, or scorer build failure. Multiple gaps may coexist; they are not automatically independent causes. Verification limits can coexist with accept.

Interaction defects do not imply browser discovery is necessary. A successful non-browser route proves that route existed in this run. Model failure does not establish intrinsic difficulty. To attribute a detour to a competing prompt reading, show that reading and actual pursuit of it, while checking environment and business-understanding explanations. Even supported reading divergence does not establish a defective intention or justify revealing the hidden trigger; assess the goal-to-acceptance connection under N02 separately. One rollout does not estimate misunderstanding probability.

## Per-Case delivery

Include actual prompt; frozen scene / criteria; C1–C5 with propositions; operation blocks and A; browser depth and surface; P1–P6; Observed excerpt and semantic probe; recognition status; H turn / step and agent quotation with prefix evidence; whether before edits; optional reading cost or U; browser operations before / during / after H, key-scenario coverage and contribution; cause-location step separately from H; patch / verification summary; Y and judge cross-check; supported gaps and unknowns.

Shared Task trajectories require separate H measurements per Case. Report Case distributions and deduplicated Task counts separately, include unknowns, and state denominators. Multi-label counts can exceed totals; shared trajectories are not independent trials. Do not claim repeated-run stability, causal effects, or annotation agreement without corresponding experiments. Cite actual evidence paths and intervals; do not claim new execution or viewing when reusing existing records.
