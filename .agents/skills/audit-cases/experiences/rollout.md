# Rollout audit experiences

## O01 — Interaction defects can have non-browser discovery paths

- **Example:** An accepted repair can originate in a supported local code diagnosis and tests without browser interaction.
- **Rule:** Separate defect validity, discovery path, and discovery cost. Measure H from the trajectory rather than substituting the K1 label or final verdict.
- **Limit:** One run does not establish stable discovery probability or browser necessity across models.

## O02 — Coverage matters more than action count

- **Example:** Opening the correct page or performing many browser operations can still miss the relevant object state, pointer path, or feedback.
- **Rule:** Record the actual surface, key-scenario coverage, and diagnostic information contributed before / during / after H.
- **Limit:** Depth is not a quality score; scorer replay is not solver interaction.

## O03 — Business understanding and prompt ambiguity are distinct

- **Example:** Fixing group-selector behavior does not establish understanding of the difference between group membership and dashboard access.
- **Rule:** Explain the missed business relationship separately from a reasonable alternative prompt interpretation supported by the actual work.
- **Limit:** A different real bug or missed criterion alone does not prove prompt ambiguity or model inability.

## O04 — Audit the link from goal to hidden acceptance

- **Example:** Drawing a closed path naturally calls for a usable geometric result, but whether it sufficiently locates a particular size-badge defect needs separate evidence and scope judgment.
- **Rule:** Retain business-understanding and goal-to-acceptance explanations until evidence distinguishes them; do not reveal the answer merely to force a hit.
- **Refinement:** A clear intention may admit several reasonable exploration paths. Showing that the agent followed another reading establishes divergence in this run, not an invalid definition or a need to narrow the prompt to hidden acceptance. Assess the business connection separately; one rollout does not estimate misunderstanding probability.
- **Limit:** This experience does not authorize automatic prompt changes, rejection, or regrading. A repair to another defect does not satisfy the selected Case merely because its exploration path was reasonable.
