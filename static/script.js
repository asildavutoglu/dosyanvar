const dropzone = document.getElementById("dropzone");
const dropzoneLabel = document.getElementById("dropzone-label");
const resumeInput = document.getElementById("resume-input");
const criteriaInput = document.getElementById("criteria-input");
const githubInput = document.getElementById("github-input");
const submitBtn = document.getElementById("submit-btn");
const errorMessage = document.getElementById("error-message");

const intakeForm = document.getElementById("intake-form");
const loadingSection = document.getElementById("loading");
const reportSection = document.getElementById("report");
const resetBtn = document.getElementById("reset-btn");

document.getElementById("case-number").textContent = String(Math.floor(1000 + Math.random() * 8999));

resumeInput.addEventListener("change", () => {
  if (resumeInput.files.length > 0) {
    dropzoneLabel.textContent = `Seçildi: ${resumeInput.files[0].name}`;
    dropzone.classList.add("has-file");
  }
});

["dragenter", "dragover"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("drag-over");
  });
});
["dragleave", "drop"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag-over");
  });
});
dropzone.addEventListener("drop", (e) => {
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    resumeInput.files = files;
    dropzoneLabel.textContent = `Seçildi: ${files[0].name}`;
    dropzone.classList.add("has-file");
  }
});

function showError(msg) {
  errorMessage.textContent = msg;
  errorMessage.hidden = false;
}

function clearError() {
  errorMessage.hidden = true;
  errorMessage.textContent = "";
}

function scoreClass(score) {
  if (score >= 75) return "";
  if (score >= 45) return "mid";
  return "low";
}

function renderReport(data) {
  document.getElementById("score-number").textContent = data.overall_score ?? "--";
  const stamp = document.getElementById("score-stamp");
  stamp.className = "score-stamp " + scoreClass(data.overall_score ?? 0);

  document.getElementById("overall-summary").textContent = data.overall_summary || "";

  const strengthsList = document.getElementById("strengths-list");
  strengthsList.innerHTML = "";
  (data.strengths || []).forEach((s) => {
    const li = document.createElement("li");
    li.textContent = s;
    strengthsList.appendChild(li);
  });

  const improvementsList = document.getElementById("improvements-list");
  improvementsList.innerHTML = "";
  (data.top_improvements || []).forEach((imp) => {
    const li = document.createElement("li");
    li.textContent = imp;
    improvementsList.appendChild(li);
  });

  const breakdown = document.getElementById("criteria-breakdown");
  breakdown.innerHTML = "";
  (data.criteria_breakdown || []).forEach((c) => {
    const status = (c.status || "").toLowerCase();
    const card = document.createElement("div");
    card.className = `criterion-card status-${status}`;
    card.innerHTML = `
      <div class="criterion-header">
        <h4>${escapeHtml(c.criterion || "")}</h4>
        <div>
          <span class="status-tag ${status}">${escapeHtml(c.status || "")}</span>
          <span class="criterion-score">${c.score ?? "--"}/100</span>
        </div>
      </div>
      <dl>
        <dt>Kanıt</dt><dd>${escapeHtml(c.evidence || "—")}</dd>
        ${c.gap ? `<dt>Eksik</dt><dd>${escapeHtml(c.gap)}</dd>` : ""}
        <dt>Öneri</dt><dd>${escapeHtml(c.suggestion || "—")}</dd>
      </dl>
    `;
    breakdown.appendChild(card);
  });

  const warningEl = document.getElementById("github-warning");
  if (data.github_warning) {
    warningEl.hidden = false;
    warningEl.textContent = `GitHub notu: ${data.github_warning}`;
  } else {
    warningEl.hidden = true;
  }

  intakeForm.hidden = true;
  loadingSection.hidden = true;
  reportSection.hidden = false;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

submitBtn.addEventListener("click", async () => {
  clearError();

  if (!resumeInput.files.length) {
    showError("Lütfen PDF formatında bir CV yükle.");
    return;
  }
  if (!criteriaInput.value.trim()) {
    showError("Lütfen kriterleri veya iş ilanını yapıştır.");
    return;
  }

  const formData = new FormData();
  formData.append("resume", resumeInput.files[0]);
  formData.append("criteria", criteriaInput.value.trim());
  if (githubInput.value.trim()) {
    formData.append("github_username", githubInput.value.trim());
  }

  intakeForm.hidden = true;
  loadingSection.hidden = false;
  submitBtn.disabled = true;

  try {
    const resp = await fetch("/evaluate", { method: "POST", body: formData });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.error || "Bilinmeyen bir hata oluştu.");
    }
    renderReport(data);
  } catch (err) {
    intakeForm.hidden = false;
    loadingSection.hidden = true;
    showError(err.message);
  } finally {
    submitBtn.disabled = false;
  }
});

resetBtn.addEventListener("click", () => {
  reportSection.hidden = true;
  intakeForm.hidden = false;
  resumeInput.value = "";
  criteriaInput.value = "";
  githubInput.value = "";
  dropzoneLabel.textContent = "PDF dosyasını buraya sürükle veya seç";
  dropzone.classList.remove("has-file");
  document.getElementById("case-number").textContent = String(Math.floor(1000 + Math.random() * 8999));
});
