async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || response.statusText);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function setStatus(elementId, message, isError = false) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.classList.toggle("text-rose-500", isError);
}

async function loadJobs() {
  const container = document.getElementById("jobs");
  if (!container) return;
  const jobs = await fetchJson("/jobs");
  if (!jobs.length) {
    container.textContent = "No jobs yet.";
    return;
  }
  container.innerHTML = jobs
    .map(
      (job) =>
        `<div class="flex items-center justify-between">
          <div>
            <div class="font-medium">${job.file_name || "(path scan)"}</div>
            <div class="text-xs text-slate-400">${job.id}</div>
          </div>
          <span class="badge">${job.status}</span>
        </div>`
    )
    .join("");
}

async function initScansPage() {
  const uploadForm = document.getElementById("upload-form");
  const pathForm = document.getElementById("path-form");

  uploadForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(uploadForm);
    setStatus("upload-status", "Starting scan...");
    try {
      const response = await fetch("/scan", { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Scan failed");
      setStatus("upload-status", `Queued job ${data.job_id}`);
      await loadJobs();
    } catch (error) {
      setStatus("upload-status", error.message, true);
    }
  });

  pathForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(pathForm);
    setStatus("path-status", "Starting scan...");
    try {
      const response = await fetch("/scan", { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Scan failed");
      setStatus("path-status", `Queued job ${data.job_id}`);
      await loadJobs();
    } catch (error) {
      setStatus("path-status", error.message, true);
    }
  });

  await loadJobs();
}

async function initFindingsPage() {
  const list = document.getElementById("findings-list");
  const refresh = document.getElementById("findings-refresh");

  async function loadFindings() {
    const jobId = document.getElementById("finding-job")?.value || "";
    const entityType = document.getElementById("finding-entity")?.value || "";
    const params = new URLSearchParams();
    if (jobId) params.append("job_id", jobId);
    if (entityType) params.append("entity_type", entityType);
    const findings = await fetchJson(`/findings?${params.toString()}`);
    if (!findings.length) {
      list.textContent = "No findings loaded.";
      return;
    }
    list.innerHTML = findings
      .map(
        (finding) =>
          `<div class="border border-slate-200 rounded-lg p-3">
            <div class="flex items-center justify-between">
              <div class="font-medium">${finding.entity_type}</div>
              <div class="text-xs text-slate-400">${finding.job_id}</div>
            </div>
            <div class="text-xs text-slate-500 mt-1">${finding.context || ""}</div>
            <div class="text-xs text-slate-500 mt-2">Primary regex: ${finding.primary_regex}</div>
            <div class="text-xs text-slate-500 mt-1">Keywords: ${(finding.supporting_keywords || []).join(", ")}</div>
          </div>`
      )
      .join("");
  }

  refresh?.addEventListener("click", loadFindings);
  await loadFindings();
}

async function loadSits() {
  const list = document.getElementById("sits-list");
  if (!list) return;
  const sits = await fetchJson("/sits");
  if (!sits.length) {
    list.textContent = "No SITs loaded.";
    return;
  }
  list.innerHTML = sits
    .map(
      (sit) =>
        `<div class="border border-slate-200 rounded-lg p-3">
          <div class="font-medium">${sit.name}</div>
          <div class="text-xs text-slate-400">${sit.id}</div>
        </div>`
    )
    .join("");
}

async function initSitsPage() {
  const form = document.getElementById("sit-form");
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    let supportingGroups = [];
    try {
      supportingGroups = JSON.parse(data.get("supporting_groups"));
    } catch (error) {
      setStatus("sit-status", "Supporting groups must be valid JSON", true);
      return;
    }
    const minNValue = data.get("supporting_min_n");
    const payload = {
      name: data.get("name"),
      description: data.get("description"),
      version: {
        entity_type: data.get("entity_type"),
        confidence: data.get("confidence"),
        primary_element: {
          type: data.get("primary_type"),
          value: data.get("primary_value"),
        },
        supporting_logic: {
          mode: data.get("supporting_mode"),
          min_n: minNValue ? Number(minNValue) : null,
        },
        supporting_groups: supportingGroups,
      },
    };
    setStatus("sit-status", "Creating SIT...");
    try {
      await fetchJson("/sits", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setStatus("sit-status", "SIT created.");
      form.reset();
      await loadSits();
    } catch (error) {
      setStatus("sit-status", error.message, true);
    }
  });
  await loadSits();
}

async function loadRulepacks() {
  const list = document.getElementById("rulepacks-list");
  if (!list) return;
  const rulepacks = await fetchJson("/rulepacks");
  if (!rulepacks.length) {
    list.textContent = "No rulepacks loaded.";
    return;
  }
  list.innerHTML = rulepacks
    .map(
      (rp) =>
        `<div class="border border-slate-200 rounded-lg p-3 space-y-2">
          <div>
            <div class="font-medium">${rp.name}</div>
            <div class="text-xs text-slate-400">${rp.id}</div>
          </div>
          <div class="text-xs text-slate-500">Version ${rp.version}</div>
          <div class="text-xs text-slate-500">Selections: ${rp.selections.join(", ") || "none"}</div>
          <div class="flex flex-wrap gap-2">
            <input class="input" data-rulepack-id="${rp.id}" placeholder="Comma-separated SIT version ids" />
            <button class="btn-secondary" data-action="select" data-rulepack-id="${rp.id}">Update Selections</button>
            <button class="btn-primary" data-action="export" data-rulepack-id="${rp.id}">Export XML</button>
          </div>
        </div>`
    )
    .join("");

  list.querySelectorAll("button[data-action='select']").forEach((button) => {
    button.addEventListener("click", async () => {
      const rulepackId = button.dataset.rulepackId;
      const input = list.querySelector(`input[data-rulepack-id='${rulepackId}']`);
      const values = input.value
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean);
      try {
        await fetchJson(`/rulepacks/${rulepackId}/selections`, {
          method: "POST",
          body: JSON.stringify({ version_ids: values }),
        });
        await loadRulepacks();
      } catch (error) {
        alert(error.message);
      }
    });
  });

  list.querySelectorAll("button[data-action='export']").forEach((button) => {
    button.addEventListener("click", async () => {
      const rulepackId = button.dataset.rulepackId;
      try {
        const response = await fetch(`/rulepacks/${rulepackId}/export`, {
          method: "POST",
        });
        const xml = await response.text();
        if (!response.ok) {
          throw new Error(xml);
        }
        const blob = new Blob([xml], { type: "application/xml" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${rulepackId}.xml`;
        link.click();
      } catch (error) {
        alert(error.message);
      }
    });
  });
}

async function initRulepacksPage() {
  const form = document.getElementById("rulepack-form");
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const payload = {
      name: data.get("name"),
      version: data.get("version"),
      description: data.get("description"),
      publisher: data.get("publisher"),
      locale: data.get("locale"),
    };
    setStatus("rulepack-status", "Creating rulepack...");
    try {
      await fetchJson("/rulepacks", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setStatus("rulepack-status", "Rulepack created.");
      form.reset();
      await loadRulepacks();
    } catch (error) {
      setStatus("rulepack-status", error.message, true);
    }
  });
  await loadRulepacks();
}

document.addEventListener("DOMContentLoaded", async () => {
  const page = document.querySelector("[data-page]")?.dataset.page;
  if (page === "scans") {
    await initScansPage();
  }
  if (page === "findings") {
    await initFindingsPage();
  }
  if (page === "sits") {
    await initSitsPage();
  }
  if (page === "rulepacks") {
    await initRulepacksPage();
  }
});
