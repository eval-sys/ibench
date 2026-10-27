const app = document.querySelector("#app");
const nav = document.querySelector("#task-nav");
const releaseMeta = document.querySelector("#release-meta");
const toast = document.querySelector("#toast");
const readStorageKey = "ibench.preview.read";
let readCases;
try {
  const stored = JSON.parse(localStorage.getItem(readStorageKey) || "{}");
  readCases = stored && typeof stored === "object" && !Array.isArray(stored) ? stored : {};
} catch {
  readCases = {};
}
const isRead = (caseId) => readCases[caseId] === true;
const readCount = (task) => task.case_ids.filter(isRead).length;
const taskIsRead = (task) => readCount(task) === task.case_count;
const readFilter = () => `<label><span>Reading status</span><select data-read-filter aria-label="Reading status">
  <option value="">All reading states</option><option value="unread">Unread</option><option value="read">Read</option>
</select></label>`;
const readButton = (caseId, label = "") => {
  const read = isRead(caseId);
  const action = `Mark as ${read ? "unread" : "read"}`;
  return `<span class="reading-control">
    <span class="reading-status" data-read="${read}">${label ? `${escapeHtml(label)}: ` : ""}${read ? "Read" : "Unread"}</span>
    <button class="btn read-toggle" type="button" data-read-case="${escapeHtml(caseId)}" aria-label="${escapeHtml(label ? `${label}: ${action}` : action)}">${action}</button>
  </span>`;
};

function wireReadButtons(render) {
  app.addEventListener("click", (event) => {
    const button = event.target.closest("[data-read-case]");
    if (!button) return;
    const caseId = button.dataset.readCase;
    const value = !isRead(caseId);
    const next = { ...readCases, [caseId]: value };
    try {
      localStorage.setItem(readStorageKey, JSON.stringify(next));
    } catch {
      showToast("Could not save reading status in this browser.");
      return;
    }
    readCases = next;
    render();
    showToast(`Marked as ${value ? "read" : "unread"}`);
  });
  window.addEventListener("storage", (event) => {
    if (event.key !== readStorageKey && event.key !== null) return;
    try {
      const stored = JSON.parse(event.newValue || "{}");
      readCases = stored && typeof stored === "object" && !Array.isArray(stored) ? stored : {};
      render();
    } catch { /* Ignore malformed storage from another tab. */ }
  });
}

const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[character]));

const list = (items) => items?.length
  ? `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
  : '<div class="muted">None published.</div>';

const theory = (items) => items?.length
  ? `<div class="theory-list">${items.map((item) => `
      <article class="theory-item">
        <h5>${escapeHtml(item.title)}</h5>
        <p>${escapeHtml(item.rationale)}</p>
        <code>${escapeHtml(item.reference)}</code>
      </article>`).join("")}</div>`
  : '<div class="muted">None published.</div>';

const video = (label, context, url, tone, guide, fps) => `
  <div class="video-frame" data-video-side="${tone}">
    <div class="video-label video-label-${tone}"><strong>${escapeHtml(label)}</strong><span class="context">${escapeHtml(context)}</span></div>
    ${AcceptanceVideoPlayer.render(url, guide, label, fps)}
  </div>`;

const fileStatus = (file) => file.changed
  ? `<span class="addition" data-file-status hidden>+${file.additions}</span><span class="deletion" data-file-status hidden>-${file.deletions}</span>`
  : '<span class="identical-status" data-file-status hidden>No changes</span>';

const sourcePane = (file, side, label, badge = "") => {
  const source = file[side];
  const fixturePath = source.path.includes("fixtures/") ? source.path.slice(source.path.indexOf("fixtures/")) : source.path;
  return `
    <section class="source-pane source-${side}">
      <header class="source-head">
        <div><strong>${label}</strong>${badge ? `<span class="source-badge">${badge}</span>` : ""}</div>
        <code title="${escapeHtml(source.path)}">${escapeHtml(fixturePath)}</code>
      </header>
      <div class="code-head"><button class="btn copy" type="button" data-copy-file="${escapeHtml(file.name)}" data-copy-side="${side}">Copy</button></div>
      <pre><code>${source.highlighted}</code></pre>
    </section>`;
};

const pairedFile = (file, index) => `
  <div data-file-content="${escapeHtml(file.name)}" ${index ? "hidden" : ""}>
    <div class="source-pair" data-full-sources>
      ${sourcePane(file, "before", "Reproduction witness")}
      ${sourcePane(file, "after", "Published judge", "Used by scorer")}
    </div>
    <div class="split-diff" data-split-diff hidden></div>
  </div>`;

const fileGroup = (files, group) => files.length ? `
  <div class="file-group" data-file-group="${group}">
    ${files.length > 1 ? `<div class="file-tabs" role="tablist" aria-label="${group} replay files">
      ${files.map((file, index) => `<button type="button" role="tab" aria-selected="${index === 0}" data-audit-file="${escapeHtml(file.name)}"><code>${escapeHtml(file.name)}</code>${fileStatus(file)}</button>`).join("")}
    </div>` : `<div class="single-file-title"><code>${escapeHtml(files[0].name)}</code>${fileStatus(files[0])}</div>`}
    ${files.map(pairedFile).join("")}
  </div>` : '<div class="empty-files">No published files.</div>';

const replayObservations = (item) => `
  <article class="replay-description"><h5>Requirement rationale</h5><p>${escapeHtml(item.requirement_rationale)}</p></article>
  <div class="outcome-pair">
    <article class="outcome-side outcome-before"><h5>Observed before</h5><p>${escapeHtml(item.observed)}</p></article>
    <article class="outcome-side outcome-after"><h5>Reference observation</h5><p>${escapeHtml(item.reference_observation)}</p></article>
  </div>`;

const replayAudit = (item) => {
  const files = item.replay.files.filter((file) => [file.before, file.after].some((source) => {
    const content = source.content.trim();
    return content !== "" && !(file.name.endsWith(".sql") && /^SELECT\s+1\s*;?$/i.test(content));
  }));
  const when = files.filter((file) => file.role === "when");
  const given = files.filter((file) => file.role === "given");
  const support = files.filter((file) => file.role === "support");
  return `
    <section class="replay-audit" data-replay-audit>
      <div class="audit-heading">
        <div>
          <h4>Replay Scripts</h4>
          <div class="diff-summary">
            <strong>${item.replay.changed_file_count} / ${item.replay.total_file_count}</strong> files changed
            <span class="addition">+${item.replay.additions}</span><span class="deletion">-${item.replay.deletions}</span>
          </div>
        </div>
        <label class="compare-control"><input type="checkbox" data-compare> Compare changes</label>
      </div>
      <div class="audit-tabs" role="tablist" aria-label="Replay scripts">
        <button type="button" role="tab" aria-selected="true" data-audit-tab="given">Given <span>Setup</span></button>
        <button type="button" role="tab" aria-selected="false" data-audit-tab="when">When <span>Actions</span></button>
      </div>
      <div class="audit-panel" data-audit-panel="given">
        <div class="replay-description"><h5>Given</h5><p>${escapeHtml(item.given)}</p></div>
        ${fileGroup(given, "given")}
        ${support.length ? `<details class="support-files">
          <summary>Support files (${support.length})</summary>
          <div class="support-body">${fileGroup(support, "support")}</div>
        </details>` : ""}
      </div>
      <div class="audit-panel" data-audit-panel="when" hidden>
        <div class="replay-description"><h5>When</h5><p>${escapeHtml(item.when)}</p></div>
        ${fileGroup(when, "when")}
      </div>
    </section>`;
};

const modelResults = (rows) => {
  const models = [...new Set(rows.map((row) => row.model))];
  const labels = { passed: "Passed", failed: "Failed", pending: "Pending", unjudged: "Not judged" };
  return `<table class="model-table" aria-label="Model results"><thead><tr>
    ${models.length ? models.map((model) => `<th scope="col">${escapeHtml(model.split("/").pop())}</th>`).join("") : '<th scope="col">Model</th>'}
    </tr></thead><tbody><tr>${models.length ? models.map((model) => `<td>${rows.filter((row) => row.model === model).map((row) => {
      const label = row.status === "error" ? row.error.match(/\b[A-Za-z_]\w*(?:Error|Exception)\b/)?.[0] || "Error" : labels[row.status];
      return `<span class="model-status" data-status="${escapeHtml(row.status)}">${escapeHtml(label)}</span>`;
    }).join("<br>")}</td>`).join("") : '<td>—</td>'}</tr></tbody></table>`;
};

function wireModelResults(task) {
  let busy = false;
  const refresh = async () => {
    if (busy || document.hidden) return;
    busy = true;
    try {
      const response = await fetch(`/api/tasks/${encodeURIComponent(task.name)}/runs`, { cache: "no-store" });
      if (!response.ok) throw new Error(`Runs API returned ${response.status}`);
      const data = await response.json();
      document.querySelectorAll("[data-case]").forEach((element) => {
        const item = task.cases[Number(element.dataset.caseIndex)];
        const body = element.querySelector("[data-model-body]");
        const html = modelResults(data.cases[item.case_id] || []);
        if (body.innerHTML !== html) body.innerHTML = html;
        body.removeAttribute("title");
      });
    } catch (error) {
      document.querySelectorAll("[data-model-body]").forEach((body) => {
        body.title = `${error.message}; retrying automatically`;
      });
    } finally {
      busy = false;
    }
  };
  document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });
  setInterval(refresh, 10000);
  refresh();
}

function wireModelScores() {
  const body = document.querySelector("[data-model-scores]");
  let busy = false;
  const refresh = async () => {
    if (busy || document.hidden) return;
    busy = true;
    try {
      const response = await fetch("/api/scores", { cache: "no-store" });
      if (!response.ok) throw new Error(`Scores API returned ${response.status}`);
      const { models } = await response.json();
      models.sort((a, b) => b.score - a.score || a.model.localeCompare(b.model));
      body.innerHTML = models.length ? `<table class="model-table" aria-label="Model scores">
        <thead><tr><th scope="col">Model</th><th scope="col">Score</th></tr></thead>
        <tbody>${models.map((item) => `<tr><th scope="row">${escapeHtml(item.model.split("/").pop())}</th>
          <td>${item.score.toLocaleString(undefined, { maximumFractionDigits: 2 })} / ${item.total}</td></tr>`).join("")}</tbody></table>` : "No model runs yet.";
      body.removeAttribute("title");
    } catch (error) {
      body.title = `${error.message}; retrying automatically`;
    } finally {
      busy = false;
    }
  };
  document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });
  setInterval(refresh, 10000);
  refresh();
}

const caseView = (task, item, caseIndex) => {
  const anchor = `case-${encodeURIComponent(task.id)}-${caseIndex}`;
  return `
    <article class="case" id="${anchor}" data-case data-case-index="${caseIndex}">
      <div class="case-heading">
        <h3>${escapeHtml(item.label)}</h3>
        <div class="case-id">${escapeHtml(item.case_id)}</div>
        <span data-read-control>${readButton(item.case_id)}</span>
      </div>
      <div class="summary-grid">
        <section class="prompt-column" aria-labelledby="prompt-${anchor}">
          <div class="section-label prompt-heading" id="prompt-${anchor}">Task prompt</div>
          <div class="panel panel-body prompt-panel">
            <div class="prompt-key">Intention</div>
            <p class="intent">${escapeHtml(item.intent)}</p>
          </div>
          <div class="panel panel-body prompt-panel">
            <div class="prompt-key">Actions</div>
            <ol class="actions">${item.actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ol>
          </div>
        </section>
        <section class="prompt-column" aria-labelledby="contract-${anchor}">
          <div class="section-label prompt-heading" id="contract-${anchor}">Expected behavior</div>
          <div class="panel panel-body">
            <div class="contract-row"><div class="contract-key">Given</div><div class="contract-value">${escapeHtml(item.given)}</div></div>
            <div class="contract-row"><div class="contract-key">When</div><div class="contract-value">${escapeHtml(item.when)}</div></div>
            <div class="contract-row required"><div class="contract-key">Require</div><div class="contract-value">${escapeHtml(item.require)}</div></div>
            ${item.allow.length ? `<div class="contract-row"><div class="contract-key">Allowed variation</div><div class="contract-value">${list(item.allow)}</div></div>` : ""}
          </div>
        </section>
      </div>
      <section class="model-results" aria-label="Model results">
        <div data-model-body>${modelResults([])}</div>
      </section>
      <section class="evidence" aria-label="Before and after videos">
        <div class="section-header">
          <div class="video-actions">
            <button class="btn" type="button" data-play>Play both</button>
          </div>
        </div>
        <div class="video-grid">
          ${video("Before", "Observed defect", item.before_url, "before", item.before_video_guide, item.before_video_fps)}
          ${video("Reference after", "Non-normative example", item.after_url, "after", item.after_video_guide, item.after_video_fps)}
        </div>
        ${replayObservations(item)}
      </section>
      ${replayAudit(item)}
      <div class="details-stack">
        <details>
          <summary>Design rationale (${item.theory.length})</summary>
          <div class="details-content">${theory(item.theory)}</div>
        </details>
      </div>
    </article>`;
};

const taskView = (task) => `
  <section class="task" id="task-${encodeURIComponent(task.id)}">
    <header class="task-header">
      <div>
        <div class="eyebrow">${task.cases.length} case${task.cases.length === 1 ? "" : "s"}</div>
        <h2>${escapeHtml(task.title)}</h2>
        <div class="task-id">${escapeHtml(task.id)}</div>
      </div>
      <div class="commits">
        <span>Base</span><code title="${escapeHtml(task.base_commit_sha)}">${escapeHtml(task.base_commit_sha.slice(0, 9))}</code>
        <span>Merge</span><code title="${escapeHtml(task.merge_commit_sha)}">${escapeHtml(task.merge_commit_sha.slice(0, 9))}</code>
      </div>
    </header>
    <div class="task-filters case-filters">${readFilter()}<span data-case-count></span></div>
    <div data-case-list>${task.cases.map((item, index) => caseView(task, item, index)).join("")}</div>
    <div class="empty-filter" data-empty-cases hidden>No cases match this reading status.</div>
  </section>`;

const formatDuration = (seconds) => seconds == null ? "-" : `${seconds}s`;

const formatCapacity = (megabytes) => {
  if (megabytes == null) return "-";
  if (megabytes >= 1024 && megabytes % 1024 === 0) return `${megabytes / 1024} GB`;
  return `${megabytes} MB`;
};

const filterOptions = (items, label) => `
  <option value="">All ${label}</option>
  ${items.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("")}`;

const presence = (value, title = "") => `<span class="presence ${value ? "present" : "absent"}"${title ? ` title="${escapeHtml(title)}"` : ""}>${value ? "Yes" : "No"}</span>`;

const taskRows = (tasks) => tasks.map((task) => `
  <tr>
    <td class="task-name-cell">
      <a href="/tasks/${encodeURIComponent(task.name)}">${escapeHtml(task.title)}</a>
      <code>${escapeHtml(task.name)}</code>
      <div class="task-repository">${escapeHtml(task.repository)}</div>
      <div class="task-taxonomy">
        ${task.difficulty ? `<span>${escapeHtml(task.difficulty)}</span>` : ""}
        ${task.category ? `<span>${escapeHtml(task.category)}</span>` : ""}
        ${(task.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
      </div>
    </td>
    <td><div class="read-buttons">${task.case_ids.map((caseId, index) => readButton(caseId, task.case_count > 1 ? `Case ${index + 1}` : "")).join("")}</div>${task.case_count > 1 ? `<div class="read-progress">${readCount(task)}/${task.case_count} read</div>` : ""}</td>
    <td>${formatDuration(task.agent_timeout_sec)}</td>
    <td>${formatDuration(task.verifier_timeout_sec)}</td>
    <td>${escapeHtml(task.os || "-")}</td>
    <td>${task.cpus ?? "-"}</td>
    <td>${formatCapacity(task.memory_mb)}</td>
    <td>${formatCapacity(task.storage_mb)}</td>
    <td>${task.gpus ?? "-"}</td>
    <td>${presence(task.has_solution, task.has_solution ? `Merged commit: ${task.merge_commit_sha}` : "")}</td>
    <td>${presence(task.has_docker_compose)}</td>
  </tr>`).join("");

const groupedTaskRows = (tasks) => [false, true].map((read) => {
  const group = tasks.filter((task) => taskIsRead(task) === read);
  return group.length ? `<tr class="read-divider"><th colspan="11">${read ? "Read" : "Unread"} (${group.length})</th></tr>${taskRows(group)}` : "";
}).join("");

const taskIndexView = (data) => {
  const difficulties = [...new Set(data.tasks.map((task) => task.difficulty).filter(Boolean))].sort();
  const categories = [...new Set(data.tasks.map((task) => task.category).filter(Boolean))].sort();
  const tags = [...new Set(data.tasks.flatMap((task) => task.tags || []))].sort();
  const repositories = Object.values(data.tasks.reduce((groups, task) => {
    const group = groups[task.repository] ||= { name: task.repository, tasks: 0, cases: 0 };
    group.tasks += 1;
    group.cases += task.case_count;
    return groups;
  }, Object.create(null))).sort((a, b) => b.tasks - a.tasks || a.name.localeCompare(b.name));
  const maxTasks = Math.max(1, ...repositories.map((repository) => repository.tasks));
  return `
  <header class="release-intro">
    <div class="eyebrow">Published dataset</div>
    <h1>${escapeHtml(data.release.name)}</h1>
    <div class="counts"><span class="count">${data.release.task_count} task${data.release.task_count === 1 ? "" : "s"}</span><span class="count">${data.release.case_count} case${data.release.case_count === 1 ? "" : "s"}</span><span class="count">${repositories.length} repositor${repositories.length === 1 ? "y" : "ies"}</span></div>
  </header>
  <section class="model-scoreboard" aria-labelledby="model-scores-heading">
    <div class="definitions-heading"><h2 id="model-scores-heading">Model scores</h2></div>
    <div class="model-score-table" data-model-scores>Reading model scores…</div>
  </section>
  <section class="repository-distribution" aria-labelledby="repository-distribution-heading">
    <div class="definitions-heading">
      <h2 id="repository-distribution-heading">Repository distribution</h2>
      <span>Click a repository to filter tasks</span>
    </div>
    <div class="repository-chart">
      <div class="repository-chart-head"><span>Upstream repository</span><span>Tasks per repository</span><span>Tasks</span><span>Cases</span></div>
      ${repositories.map((repository) => `
        <button type="button" class="repository-row" data-repository="${escapeHtml(repository.name)}" aria-pressed="false" aria-label="${escapeHtml(repository.name)}: ${repository.tasks} task${repository.tasks === 1 ? "" : "s"}, ${repository.cases} case${repository.cases === 1 ? "" : "s"}">
          <span class="repository-name">${escapeHtml(repository.name)}</span>
          <span class="repository-track" aria-hidden="true"><span class="repository-bar" style="width: ${repository.tasks / maxTasks * 100}%"></span></span>
          <span class="repository-tasks">${repository.tasks}</span><span class="repository-cases">${repository.cases}</span>
        </button>`).join("")}
    </div>
  </section>
  <section class="definitions" aria-labelledby="task-definitions-heading">
    <div class="definitions-heading">
      <h2 id="task-definitions-heading">Task definitions</h2>
      <span data-result-count>${data.tasks.length} task${data.tasks.length === 1 ? "" : "s"}</span>
    </div>
    <div class="task-filters">
      ${readFilter()}
      <label><span>Repository</span><select data-filter="repository">${filterOptions(repositories.map((repository) => repository.name).sort(), "repositories")}</select></label>
      <label><span>Difficulty</span><select data-filter="difficulty">${filterOptions(difficulties, "difficulties")}</select></label>
      <label><span>Category</span><select data-filter="category">${filterOptions(categories, "categories")}</select></label>
      <label><span>Tag</span><select data-filter="tag">${filterOptions(tags, "tags")}</select></label>
    </div>
    <div class="task-table-wrap">
      <table class="task-table">
        <thead><tr>
          <th>Name</th><th>Reading status</th><th>Agent Timeout</th><th>Verifier Timeout</th><th>OS</th><th>CPUs</th>
          <th>Memory</th><th>Storage</th><th>GPUs</th><th>Solution</th><th>Compose</th>
        </tr></thead>
        <tbody data-task-rows>${groupedTaskRows(data.tasks)}</tbody>
      </table>
      <div class="empty-filter" data-empty-filter hidden>No tasks match these filters.</div>
    </div>
  </section>`;
};

function wireTaskFilters(data) {
  const filters = [...document.querySelectorAll("[data-filter]")];
  const reading = document.querySelector("[data-read-filter]");
  const rows = document.querySelector("[data-task-rows]");
  const count = document.querySelector("[data-result-count]");
  const empty = document.querySelector("[data-empty-filter]");
  const repositoryFilter = filters.find((filter) => filter.dataset.filter === "repository");
  const repositoryRows = [...document.querySelectorAll("[data-repository]")];
  const render = () => {
    const values = Object.fromEntries(filters.map((filter) => [filter.dataset.filter, filter.value]));
    const visible = data.tasks.filter((task) =>
      (!values.repository || task.repository === values.repository)
      && (!values.difficulty || task.difficulty === values.difficulty)
      && (!values.category || task.category === values.category)
      && (!values.tag || (task.tags || []).includes(values.tag))
      && (!reading.value || taskIsRead(task) === (reading.value === "read")));
    rows.innerHTML = groupedTaskRows(visible);
    nav.innerHTML = [false, true].map((read) => {
      const group = visible.filter((task) => taskIsRead(task) === read);
      return group.length ? `<section class="nav-read-group"><div class="sidebar-heading">${read ? "Read" : "Unread"} (${group.length})</div>${group.map((task) => `<div class="nav-task"><a href="/tasks/${encodeURIComponent(task.name)}">${escapeHtml(task.title)}</a></div>`).join("")}</section>` : "";
    }).join("");
    count.textContent = `${visible.length} task${visible.length === 1 ? "" : "s"}`;
    empty.hidden = visible.length !== 0;
    repositoryRows.forEach((row) => row.setAttribute("aria-pressed", String(row.dataset.repository === values.repository)));
  };
  filters.forEach((filter) => filter.addEventListener("change", render));
  reading.addEventListener("change", render);
  wireReadButtons(render);
  repositoryRows.forEach((row) => row.addEventListener("click", () => {
    repositoryFilter.value = repositoryFilter.value === row.dataset.repository ? "" : row.dataset.repository;
    render();
  }));
  render();
}

function wireCaseReading(task, renderNavigation) {
  const container = document.querySelector("[data-case-list]");
  const cases = [...container.querySelectorAll("[data-case]")];
  const filter = document.querySelector("[data-read-filter]");
  const render = () => {
    container.querySelectorAll(".case-read-divider").forEach((heading) => heading.remove());
    let count = 0;
    [false, true].forEach((read) => {
      const group = cases.filter((element) => isRead(task.cases[Number(element.dataset.caseIndex)].case_id) === read);
      const visible = !filter.value || (filter.value === "read") === read;
      if (group.length && visible) {
        const heading = document.createElement("h3");
        heading.className = "case-read-divider";
        heading.textContent = `${read ? "Read" : "Unread"} (${group.length})`;
        container.append(heading);
      }
      group.forEach((element) => {
        element.hidden = !visible;
        if (visible) count += 1;
        else element.querySelectorAll("video").forEach((video) => video.pause());
        element.querySelector("[data-read-control]").innerHTML = readButton(task.cases[Number(element.dataset.caseIndex)].case_id);
        container.append(element);
      });
    });
    document.querySelector("[data-case-count]").textContent = `${count}/${cases.length} cases`;
    document.querySelector("[data-empty-cases]").hidden = count !== 0;
    renderNavigation();
  };
  filter.addEventListener("change", render);
  wireReadButtons(render);
  render();
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  setTimeout(() => toast.classList.remove("visible"), 1400);
}

function renderSplitDiff(target, file) {
  if (target.dataset.rendered === file.name) return;
  if (!file.changed) {
    target.innerHTML = '<div class="identical-diff">The reproduction and published judge are identical.</div>';
  } else {
    const viewer = new Diff2HtmlUI(target, file.patch, {
      drawFileList: false,
      fileContentToggle: false,
      fileListStartVisible: false,
      fileListToggle: false,
      highlight: true,
      matching: "lines",
      outputFormat: "side-by-side",
      renderNothingWhenEmpty: false,
      stickyFileHeaders: false,
      synchronisedScroll: true,
    });
    viewer.draw();
    viewer.highlightCode();
    viewer.synchronisedScroll();
  }
  target.dataset.rendered = file.name;
}

function wireFileGroup(group, item, compare) {
  const buttons = [...group.querySelectorAll("[data-audit-file]")];
  const panels = [...group.querySelectorAll("[data-file-content]")];
  const selectedPanel = () => panels.find((panel) => !panel.hidden) || panels[0];
  const applyMode = () => {
    const panel = selectedPanel();
    if (!panel) return;
    panel.querySelector("[data-full-sources]").hidden = compare.checked;
    const diff = panel.querySelector("[data-split-diff]");
    diff.hidden = !compare.checked;
    if (compare.checked) {
      const file = item.replay.files.find((candidate) => candidate.name === panel.dataset.fileContent);
      renderSplitDiff(diff, file);
    }
  };
  buttons.forEach((button) => button.addEventListener("click", () => {
    buttons.forEach((candidate) => candidate.setAttribute("aria-selected", String(candidate === button)));
    panels.forEach((panel) => { panel.hidden = panel.dataset.fileContent !== button.dataset.auditFile; });
    applyMode();
  }));
  return applyMode;
}

function wireReplayAudit(caseElement, item) {
  const audit = caseElement.querySelector("[data-replay-audit]");
  const compare = audit.querySelector("[data-compare]");
  const tabs = [...audit.querySelectorAll("[data-audit-tab]")];
  const panels = [...audit.querySelectorAll("[data-audit-panel]")];
  const groupModes = new Map(
    [...audit.querySelectorAll("[data-file-group]")].map((group) => [group, wireFileGroup(group, item, compare)]),
  );
  const activePanel = () => panels.find((panel) => !panel.hidden);
  const applyCompare = () => {
    audit.querySelectorAll("[data-file-status]").forEach((status) => { status.hidden = !compare.checked; });
    activePanel()?.querySelectorAll("[data-file-group]").forEach((group) => {
      const disclosure = group.closest("details");
      if (!disclosure || disclosure.open) groupModes.get(group)();
    });
  };

  tabs.forEach((button) => button.addEventListener("click", () => {
    tabs.forEach((candidate) => candidate.setAttribute("aria-selected", String(candidate === button)));
    panels.forEach((panel) => { panel.hidden = panel.dataset.auditPanel !== button.dataset.auditTab; });
    applyCompare();
  }));
  compare.addEventListener("change", applyCompare);
  audit.querySelectorAll("details").forEach((details) => details.addEventListener("toggle", applyCompare));
  applyCompare();
}

function wireCaseControls(task) {
  document.querySelectorAll("[data-case]").forEach((caseElement) => {
    const item = task.cases[Number(caseElement.dataset.caseIndex)];
    const videos = [...caseElement.querySelectorAll("[data-audit-video]")];
    const play = caseElement.querySelector("[data-play]");
    if (!videos.length) {
      play.disabled = true;
      return;
    }
    const updatePlayLabel = () => {
      play.textContent = videos.some((video) => !video.paused && !video.ended) ? "Pause both" : "Play both";
    };
    const players = [...caseElement.querySelectorAll("[data-video-player]")].map((root) => {
      const guide = root.closest(".video-frame").dataset.videoSide === "before" ? item.before_video_guide : item.after_video_guide;
      const player = AcceptanceVideoPlayer.wire(root, guide?.chapters || [],
        () => videos.forEach((video) => video.pause()),
        (error) => { if (error.name !== "AbortError") showToast(`Playback failed: ${error.message}`); });
      ["play", "pause", "ended"].forEach((event) => player.video.addEventListener(event, updatePlayLabel));
      return player;
    });
    play.addEventListener("click", async () => {
      if (videos.some((video) => !video.paused && !video.ended)) {
        videos.forEach((video) => video.pause());
        return;
      }
      try {
        players.forEach((player) => player.seek(0));
        await Promise.all(videos.map((video) => video.play()));
      } catch (error) {
        videos.forEach((video) => video.pause());
        if (error.name === "AbortError") return;
        showToast(`Playback failed: ${error.message}`);
      }
    });
    wireReplayAudit(caseElement, item);
  });
  document.querySelectorAll("[data-copy-file]").forEach((button) => button.addEventListener("click", async () => {
    const caseElement = button.closest("[data-case]");
    const item = task.cases[Number(caseElement.dataset.caseIndex)];
    const file = item.replay.files.find((candidate) => candidate.name === button.dataset.copyFile);
    await navigator.clipboard.writeText(file[button.dataset.copySide].content);
    showToast(`${file.name} copied`);
  }));
}

function caseNavigation(task, release, caseIndex) {
  const tasks = release.tasks;
  const destinations = tasks.map((entry) => `/tasks/${encodeURIComponent(entry.name)}`);
  const taskIndex = tasks.findIndex((entry) => entry.id === task.id);
  const nextUnread = tasks.find((entry) => entry.id !== task.id && !taskIsRead(entry));
  const filter = document.querySelector("[data-read-filter]")?.value || "";
  const step = (href, label, symbol) => href
    ? `<a class="nav-step" href="${href}" aria-label="${label}" title="${label}">${symbol}</a>`
    : `<button class="nav-step" type="button" aria-label="${label}" title="${label}" disabled>${symbol}</button>`;
  return `<div class="nav-task">
    <div class="sidebar-heading">Task (${taskIndex + 1}/${destinations.length})</div>
    <div class="nav-case-row">
      ${step(destinations[taskIndex - 1], "Previous task", "&lt;")}
      <a class="nav-case" href="${destinations[taskIndex]}" aria-current="page">${escapeHtml(task.title)}</a>
      ${step(destinations[taskIndex + 1], "Next task", "&gt;")}
    </div>
    <nav class="nav-cases" aria-label="Cases">
      <div class="sidebar-heading">Cases</div>
      <ol class="nav-case-list">
        ${[false, true].map((read) => {
          const group = task.cases.map((item, index) => ({ ...item, index })).filter((item) => isRead(item.case_id) === read);
          if (!group.length || (filter && (filter === "read") !== read)) return "";
          return `<li class="nav-read-divider">${read ? "Read" : "Unread"} (${group.length})</li>${group.map((item) => `<li>
            <a class="nav-case-link" href="#case-${encodeURIComponent(task.id)}-${item.index}"${item.index === caseIndex ? ' aria-current="location"' : ""}>
              <span class="nav-case-number">${item.index + 1}.</span><span>${escapeHtml(item.label)}</span>
            </a>
          </li>`).join("")}`;
        }).join("")}
      </ol>
    </nav>
    ${nextUnread ? `<a href="/tasks/${encodeURIComponent(nextUnread.name)}">Next unread task &rarr;</a>` : ""}
    <a href="/">&larr; All tasks</a>
  </div>`;
}

async function load() {
  try {
    const releaseResponse = await fetch("/api/release");
    if (!releaseResponse.ok) throw new Error(`Release API returned ${releaseResponse.status}`);
    const release = await releaseResponse.json();
    releaseMeta.textContent = `${release.release.name}@${release.release.version} · ${release.release.task_count} task${release.release.task_count === 1 ? "" : "s"} · ${release.release.case_count} case${release.release.case_count === 1 ? "" : "s"}`;
    const match = window.location.pathname.match(/^\/tasks\/([^/]+)$/);
    if (!match) {
      document.title = `${release.release.name} · IBench Preview`;
      app.innerHTML = taskIndexView(release);
      wireTaskFilters(release);
      wireModelScores();
      return;
    }
    const taskName = decodeURIComponent(match[1]);
    const response = await fetch(`/api/tasks/${encodeURIComponent(taskName)}`);
    if (!response.ok) throw new Error(`Task API returned ${response.status}`);
    const task = await response.json();
    document.title = `${task.title} · IBench Preview`;
    const renderNavigation = () => {
      const index = task.cases.findIndex((_, index) => window.location.hash === `#case-${encodeURIComponent(task.id)}-${index}`);
      nav.innerHTML = caseNavigation(task, release, Math.max(0, index));
    };
    renderNavigation();
    window.addEventListener("hashchange", renderNavigation);
    app.innerHTML = taskView(task);
    wireCaseControls(task);
    wireCaseReading(task, renderNavigation);
    wireModelResults(task);
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView({ block: "start", behavior: "instant" });
  } catch (error) {
    app.innerHTML = `<div class="error"><strong>Preview failed.</strong><br>${escapeHtml(error.message)}</div>`;
  }
}

load();
