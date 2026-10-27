/* Adapted from LobeHub's Acceptance video player at d65f485941cca3e558074ac080590f7efd82a9fb.
 * Copyright LobeHub LLC. LobeHub Community License; see vendor/lobehub.LICENSE.
 * React/UI bindings are replaced with the Preview's DOM controls.
 */
(() => {
  const rates = [0.5, 1, 1.5, 2];
  const rateKey = "acceptance-video-rate";
  const escape = (value) => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
  const clock = (seconds, precise = true) => {
    const ticks = Math.round(Math.max(0, seconds) * 100);
    const fraction = String(ticks % 100).padStart(2, "0").replace(/0+$/, "");
    return `${Math.floor(ticks / 6000)}:${String(Math.floor(ticks % 6000 / 100)).padStart(2, "0")}${precise && fraction ? `.${fraction}` : ""}`;
  };
  const icon = (name) => {
    const paths = {
      play: '<path d="m5 3 8 5-8 5Z"/>', pause: '<path d="M5 3v10M11 3v10"/>',
      previous: '<path d="m10 3-5 5 5 5"/>', next: '<path d="m6 3 5 5-5 5"/>',
      captions: '<rect x="1" y="3" width="14" height="10" rx="2"/><path d="M7 6H4v4h3m5-4H9v4h3"/>',
      fullscreen: '<path d="M6 2H2v4m8-4h4v4M2 10v4h4m8-4v4h-4"/>',
    };
    return `<svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">${paths[name]}</svg>`;
  };
  const claimLabel = (claim) => `<span class="av-claim-label"><i class="av-dot" data-kind="${claim.kind}"></i>${claim.kind === "check" ? "Check" : "Flag"}</span>`;
  const button = (action, label, content, title = label) => `<button type="button" class="av-button" data-action="${action}" aria-label="${label}" title="${title}">${content}</button>`;
  const chaptersHTML = (guide, available) => {
    if (!guide) return "";
    const steps = guide.chapters.filter((c) => c.kind === "step");
    const claims = guide.chapters.filter((c) => c.kind !== "step");
    const checks = claims.filter((c) => c.kind === "check").length, flags = claims.length - checks;
    const jump = (c, content, cls) => `<button type="button" class="${cls}" data-video-time="${c.t}" ${available ? "" : "disabled"}>${content}</button>`;
    return `<div class="video-guide"><p>${escape(guide.summary)}</p>
      <div class="av-steps">${steps.map((c) => jump(c, `<time>${clock(c.t, false)}</time>${escape(c.label)}`, "av-step")).join("")}</div>
      ${claims.length ? `<details class="av-claims"><summary>${checks} check${checks === 1 ? "" : "s"} · ${flags} flag${flags === 1 ? "" : "s"}</summary>
        ${claims.map((c) => jump(c, `${claimLabel(c)}<time>${clock(c.t)}</time><span>${escape(c.note)}</span>`, "av-claim")).join("")}</details>` : ""}</div>`;
  };

  function render(src, guide, label, fps) {
    if (!src) return `<div class="video-missing">Evidence unavailable</div>${chaptersHTML(guide, false)}`;
    const chapters = guide?.chapters || [];
    const marks = chapters.map((c, index) => c.kind === "step"
      ? `<span class="av-step-tick" data-mark-time="${c.t}"></span>`
      : `<button type="button" class="av-claim-mark" data-kind="${c.kind}" data-mark-time="${c.t}" data-claim-index="${index}" data-video-time="${c.t}"
          aria-label="${escape(`${label}: ${c.kind} at ${clock(c.t)}: ${c.note}`)}"></button>`).join("");
    return `<div class="av-player" data-video-player data-fps="${fps || 30}" data-exact-fps="${Boolean(fps)}" tabindex="0" aria-label="${escape(label)} video player">
      <div class="av-frame"><video playsinline preload="metadata" data-audit-video src="${escape(src)}"></video>
        <div class="av-overlay" data-video-overlay><span class="av-center-play">${icon("play")}</span><div class="av-caption" data-caption hidden></div></div>
        <div class="av-error" data-video-error hidden><span>Video could not be loaded.</span><button type="button" data-action="reload">Retry</button><a href="${escape(src)}" download>Download video</a></div>
      </div>
      <div class="av-bar" data-video-bar inert>
        <div class="av-timeline"><div class="av-preview" data-hover-preview hidden><canvas width="176" height="99"></canvas><div data-hover-label></div></div>
          <div class="av-track" data-track role="slider" tabindex="0" aria-label="${escape(label)} seek" aria-valuemin="0" aria-valuemax="0" aria-valuenow="0">
            <div class="av-rail"></div><div class="av-played" data-progress></div>${marks}<div class="av-head" data-head></div>
          </div>
        </div>
        <div class="av-controls">
          ${button("toggle", "Play", icon("play"), "Play (Space / K)")}
          ${button("previous", "Previous frame", icon("previous"), "Previous frame (,)")}
          ${button("next", "Next frame", icon("next"), "Next frame (.)")}
          <span class="av-time" data-time>0:00 / 0:00</span><span class="av-frame-no" data-frame-no></span>
          <span class="av-spacer"></span>
          ${chapters.some((c) => c.kind !== "step") ? button("captions", "Show captions", icon("captions")) : ""}
          <select class="av-rate" data-rate aria-label="Playback speed" title="Playback speed (J / L)">${rates.map((r) => `<option value="${r}" ${r === 1 ? "selected" : ""}>${r}×</option>`).join("")}</select>
          ${button("fullscreen", "Fullscreen", icon("fullscreen"))}
        </div>
      </div>
    </div>${chaptersHTML(guide, true)}`;
  }

  function wire(root, chapters, pauseAll, onError) {
    const video = root.querySelector("video");
    const card = root.closest(".video-frame");
    const track = root.querySelector("[data-track]");
    const caption = root.querySelector("[data-caption]");
    const preview = root.querySelector("[data-hover-preview]");
    const fps = Number(root.dataset.fps);
    const frameOf = (time) => Math.floor(time * fps + 1e-6);
    const steps = chapters.filter((c) => c.kind === "step");
    const claims = chapters.filter((c) => c.kind !== "step");
    const stepAt = (time) => steps.findLast((c) => c.t <= time + 0.01);
    let painted, pendingSeek, captions = false, lastCaption = "", probe, pending, busy = false;
    const time = () => video.paused ? video.currentTime : (painted ?? video.currentTime);
    const duration = () => Number.isFinite(video.duration) ? video.duration : 0;
    const seek = (seconds) => {
      painted = undefined;
      if (video.readyState < 1) { pendingSeek = seconds; return; }
      video.currentTime = Math.min(Math.max(seconds, 0), duration());
      update();
    };
    const setRate = (rate) => {
      video.playbackRate = rate;
      try { localStorage.setItem(rateKey, String(rate)); } catch { /* Private mode. */ }
    };
    const toggle = () => {
      if (!video.paused) return video.pause();
      if (video.ended) seek(0);
      video.play().catch(onError);
    };
    const step = (offset) => {
      const from = time();
      painted = undefined;
      video.pause();
      seek((frameOf(from) + offset + 0.5) / fps);
    };
    const jump = (seconds) => {
      pauseAll();
      seek(seconds);
      root.scrollIntoView({ block: "nearest" });
    };
    function update() {
      const now = time(), total = duration();
      const ready = video.readyState >= 1 && !video.error;
      root.querySelector("[data-video-bar]").inert = !ready;
      root.classList.toggle("av-ready", ready);
      root.querySelector("[data-video-error]").hidden = !video.error;
      root.querySelector("[data-video-overlay]").hidden = Boolean(video.error);
      root.querySelector(".av-center-play").hidden = !video.paused || now >= 0.05;
      if (video.videoWidth) {
        root.querySelector(".av-frame").style.aspectRatio = `${video.videoWidth} / ${video.videoHeight}`;
      }
      const pct = total ? now / total * 100 : 0;
      root.querySelector("[data-progress]").style.width = `${pct}%`;
      root.querySelector("[data-head]").style.left = `${pct}%`;
      root.querySelectorAll("[data-mark-time]").forEach((mark) => {
        mark.style.left = `${total ? Math.min(Number(mark.dataset.markTime) / total, 1) * 100 : 0}%`;
      });
      track.setAttribute("aria-valuemax", String(total));
      track.setAttribute("aria-valuenow", String(now));
      track.setAttribute("aria-valuetext", `${clock(now)} of ${clock(total)}`);
      root.querySelector("[data-time]").textContent = `${clock(now)} / ${clock(total)}`;
      root.querySelector("[data-frame-no]").textContent = `${root.dataset.exactFps === "true" ? "Frame" : "Approx. frame"} ${frameOf(now)}${stepAt(now) ? ` · ${stepAt(now).label}` : ""}`;
      const play = root.querySelector('[data-action="toggle"]');
      play.innerHTML = icon(video.paused ? "play" : "pause");
      play.setAttribute("aria-label", video.paused ? "Play" : "Pause");
      play.title = `${video.paused ? "Play" : "Pause"} (Space / K)`;
      root.querySelector("[data-rate]").value = String(video.playbackRate);
      const captionButton = root.querySelector('[data-action="captions"]');
      if (captionButton) {
        captionButton.setAttribute("aria-pressed", String(captions));
        captionButton.setAttribute("aria-label", captions ? "Hide captions" : "Show captions");
        captionButton.title = captions ? "Hide captions" : "Show captions";
      }
      const latest = claims.filter((c) => now >= c.t - 0.5 / fps && now < c.t + 2).reduce((a, c) => !a || c.t >= a.t ? c : a, null);
      const active = captions && latest ? claims.filter((c) => c.t === latest.t) : [];
      const html = active.map((c) => `<div>${claimLabel(c)}<div>${escape(c.note)}</div></div>`).join("");
      if (html !== lastCaption) { caption.innerHTML = html; lastCaption = html; }
      caption.hidden = !active.length;
    }
    const onPause = () => {
      const lastPainted = painted;
      painted = undefined;
      if (lastPainted !== undefined && Math.abs(video.currentTime - lastPainted) > 0.001) video.currentTime = lastPainted;
      update();
    };
    const tick = (_stamp, frame) => {
      if (!root.isConnected) return;
      if (!video.paused) painted = frame?.mediaTime;
      update();
      if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(tick);
      else if (!video.paused) requestAnimationFrame(tick);
    };
    ["loadedmetadata", "durationchange", "seeked", "ratechange", "ended", "error", "timeupdate"].forEach((event) => video.addEventListener(event, update));
    video.addEventListener("loadedmetadata", () => {
      if (pendingSeek === undefined) return;
      const target = pendingSeek;
      pendingSeek = undefined;
      seek(target);
    });
    video.addEventListener("seeking", () => { painted = undefined; });
    video.addEventListener("pause", onPause);
    video.addEventListener("play", () => { update(); if (!video.requestVideoFrameCallback) requestAnimationFrame(tick); });
    if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(tick);
    try {
      const stored = Number(localStorage.getItem(rateKey));
      if (rates.includes(stored)) video.playbackRate = stored;
    } catch { /* Private mode. */ }
    root.querySelectorAll("[data-action]").forEach((control) => control.addEventListener("click", () => {
      switch (control.dataset.action) {
        case "toggle": toggle(); break;
        case "previous": step(-1); break;
        case "next": step(1); break;
        case "captions": captions = !captions; update(); break;
        case "fullscreen": root.requestFullscreen?.().catch(onError); break;
        case "reload": video.load(); break;
      }
    }));
    const overlay = root.querySelector("[data-video-overlay]");
    overlay.addEventListener("click", toggle);
    overlay.addEventListener("dblclick", () => root.requestFullscreen?.().catch(onError));
    caption.addEventListener("click", (event) => event.stopPropagation());
    root.querySelector("[data-rate]").addEventListener("change", (event) => setRate(Number(event.target.value)));
    card.querySelectorAll("[data-video-time]").forEach((control) => {
      control.addEventListener("pointerdown", (event) => event.stopPropagation());
      control.addEventListener("click", () => jump(Number(control.dataset.videoTime)));
    });
    root.addEventListener("keydown", (event) => {
      if (event.target instanceof HTMLSelectElement || event.target.closest("input, textarea, [contenteditable]")) return;
      if (event.target.closest("button") && [" ", "Enter"].includes(event.key)) return;
      if (root.querySelector("[data-video-bar]").inert) return;
      switch (event.key.toLowerCase()) {
        case " ": case "k": toggle(); break;
        case ",": step(-1); break;
        case ".": step(1); break;
        case "arrowleft": seek(time() - (event.shiftKey ? 5 : 1)); break;
        case "arrowright": seek(time() + (event.shiftKey ? 5 : 1)); break;
        case "home": if (event.target !== track) return; seek(0); break;
        case "end": if (event.target !== track) return; seek(duration()); break;
        case "j": case "l": {
          const index = rates.indexOf(video.playbackRate);
          setRate(rates[Math.min(Math.max((index < 0 ? 1 : index) + (event.key.toLowerCase() === "j" ? -1 : 1), 0), rates.length - 1)]);
          break;
        }
        default: return;
      }
      event.preventDefault();
    });
    const timeAt = (clientX) => {
      const box = track.getBoundingClientRect();
      return Math.min(Math.max((clientX - box.left) / box.width, 0), 1) * duration();
    };
    let dragging = false;
    track.addEventListener("pointerdown", (event) => {
      if (event.button !== 0) return;
      event.preventDefault();
      dragging = true;
      track.focus();
      track.setPointerCapture(event.pointerId);
      seek(timeAt(event.clientX));
    });
    const endDrag = () => { dragging = false; };
    ["pointerup", "pointercancel", "lostpointercapture"].forEach((event) => track.addEventListener(event, endDrag));
    const paint = () => {
      if (probe.readyState >= 2) {
        const canvas = preview.querySelector("canvas");
        canvas.getContext("2d").drawImage(probe, 0, 0, canvas.width, canvas.height);
        canvas.dataset.previewTime = probe.currentTime;
      }
      busy = false;
      if (pending !== undefined) seekProbe();
    };
    function seekProbe() {
      if (!probe || probe.readyState < 1 || busy || pending === undefined) return;
      const target = pending;
      pending = undefined;
      if (Math.abs(probe.currentTime - target) < 0.001 && probe.readyState >= 2) { paint(); return; }
      busy = true;
      probe.currentTime = target;
    }
    track.addEventListener("pointermove", (event) => {
      if (dragging) seek(timeAt(event.clientX));
      const seconds = timeAt(event.clientX), box = track.getBoundingClientRect();
      const claim = claims.filter((c) => Math.abs(c.t - seconds) < duration() * 0.012).sort((a, b) => Math.abs(a.t - seconds) - Math.abs(b.t - seconds))[0];
      const target = claim?.t ?? seconds, currentStep = stepAt(target);
      preview.hidden = false;
      preview.style.left = `${Math.min(Math.max(event.clientX - box.left, 88), Math.max(88, box.width - 88))}px`;
      preview.querySelector("[data-hover-label]").innerHTML = `<time>${clock(target)}</time>${currentStep ? ` · ${escape(currentStep.label)}` : ""}${claim ? `<div>${claimLabel(claim)} ${escape(claim.note)}</div>` : ""}`;
      pending = target;
      if (!probe) {
        probe = document.createElement("video");
        probe.muted = true;
        probe.preload = "auto";
        probe.style.display = "none";
        probe.src = video.currentSrc || video.src;
        root.append(probe);
        probe.addEventListener("loadedmetadata", seekProbe);
        probe.addEventListener("loadeddata", () => { if (!busy) paint(); });
        probe.addEventListener("seeked", paint);
      }
      seekProbe();
    });
    track.addEventListener("pointerleave", () => { preview.hidden = true; });
    update();
    return { seek, video };
  }
  window.AcceptanceVideoPlayer = { render, wire };
})();
