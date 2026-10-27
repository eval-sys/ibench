
# Score one PR candidate

Read each rubric's `requirement_rationale` to understand the product semantics, user goal, and reasons for Require and Allow. It is an expert-reviewed explanation, not an additional scoring rule. Distinguish cited facts from inference; neither this explanation nor Theory may add conditions or narrow Allow. Judge fresh candidate behavior against Require and Allow, including valid implementations that differ from the reference.

Use the environment’s `APP_URL` and each Issue’s `setup.mjs` / `presentation.json` to locate the running candidate. `/workspace/case-context/manifest.json` lists every Issue that this PR must repair. Evaluate all of them; one repaired Issue cannot compensate for another.

For each manifest entry, read its `input/rubric.json`, original `before.webm`, and non-normative `reference-after.webm`. The rubric is the sole semantic source of truth. Its `Observed` and `reference_observation` are the before/after observations from the historical bug and reference repair. Use them to understand how the abstract conditions were instantiated, not as additional requirements. Require and Allow are the only normative repair criteria; the reference implementation does not constrain other valid solutions, DOM structures, or interaction paths.

Each manifest entry gives the exact historical `input`, editable `replay_root` and `verdict_template`, and executable `capture` paths for one Issue. `input/fixtures/before/` contains the original bug reproduction; `input/fixtures/reference-after/` contains the replay adapted to the reference repair. Both contain `cleanup.sql`, `setup.sql`, `cleanup.sh`, `setup.sh`, `cleanup.mjs`, `setup.mjs`, `action.mjs`, and `presentation.json`. The editable replay directory is pre-populated from reference-after, not before. Adapt those files in place when necessary; do not create substitute submission paths. Preserve the semantic When.

Run the entry's exact `capture` command to prepare Given and record the submitted action as `evidence/after.webm` beside the templates. Keep the generated `evidence/final.png` and `evidence/manifest.json`; the trusted verifier checks them too. Every verdict must be `repaired` or `not_repaired`; do not substitute an `inconclusive` verdict for a completed behavioral decision.

This task records the browser window, including native menus and the tab strip. Use the fresh `evidence/tab-observations.json` and `evidence/opened-page.png` alongside the video to identify the original tab, any new tab, and its actual destination. These observations support the behavioral decision; a link's href or an increased tab count alone does not establish Require.

If you cannot support either binary decision with fresh evidence, do not fabricate a verdict. The run will be treated as `verifier_failed`, with your explanation retained in the agent log.

Replace `verdict_template` in place with a verdict matching `/workspace/case-context/verdict.schema.json`. Put the evidence-based reasoning behind the binary decision in `summary`. Remove every `FIXTURE_NOT_IMPLEMENTED` stub before finishing.

After writing every verdict, run the manifest's exact top-level `validate` command. It runs the same mechanical delivery contract as the trusted verifier in protocol-only mode. Resolve every reported protocol failure before finishing. This preflight accepts either honest binary verdict; it does not turn `not_repaired` into `repaired` or replace the final trusted score.

You may inspect the running application and source, but do not edit product source, dependencies, or the lockfile. Runtime behavior, not source or witness resemblance, determines each verdict. Return `repaired` only when Given and When are established and Require is supported; otherwise return `not_repaired` when fresh evidence refutes Require.
