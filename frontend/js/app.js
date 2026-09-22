/**
 * NER Landslide Early Warning & Risk Monitoring Platform
 * Frontend Foundation Controller
 */

const API_BASE = "/api/v1";

document.addEventListener("DOMContentLoaded", () => {
  console.log("Initializing NER Landslide Monitoring System UI...");
  initSystemHealthCheck();
  loadIncidentReports();
  setupReportForm();
});

/**
 * Pings backend health endpoint and updates UI diagnostics.
 */
async function initSystemHealthCheck() {
  const statusPill = document.getElementById("backend-status-pill");
  const statusText = document.getElementById("backend-status-text");
  const footerDiag = document.getElementById("footer-diagnostics");

  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    statusPill.style.color = "var(--risk-green)";
    statusPill.style.backgroundColor = "rgba(34, 197, 94, 0.1)";
    statusPill.style.borderColor = "rgba(34, 197, 94, 0.3)";
    statusText.textContent = `Connected (API v${data.version} - ${data.environment})`;

    footerDiag.textContent = `API: v${data.version} | Database: ${data.database} | ML Service: ${data.ml_service_status}`;
  } catch (err) {
    console.error("Health check error:", err);
    statusPill.style.color = "var(--risk-red)";
    statusPill.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
    statusPill.style.borderColor = "rgba(239, 68, 68, 0.3)";
    statusText.textContent = "Backend Offline / Disconnected";
    footerDiag.textContent = "API: Disconnected | Database: Unavailable | ML Service: Offline";
  }
}

/**
 * Fetches recorded citizen and field hazard observations from SQLite DB.
 */
async function loadIncidentReports() {
  const feed = document.getElementById("incident-feed");
  const countVal = document.getElementById("reports-count-val");

  try {
    const res = await fetch(`${API_BASE}/reports?limit=10`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const reports = await res.json();

    countVal.textContent = reports.length;

    if (reports.length === 0) {
      feed.innerHTML = `
        <div style="color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 1rem;">
          No incidents reported yet. Submit a field report above.
        </div>
      `;
      return;
    }

    feed.innerHTML = reports
      .map(
        (r) => `
      <div class="incident-item">
        <div class="incident-item-header">
          <span>${escapeHtml(r.incident_type)} (${escapeHtml(r.severity)})</span>
          <span style="color: var(--text-muted); font-size: 0.7rem;">${escapeHtml(r.district)}, ${escapeHtml(r.state)}</span>
        </div>
        <div style="color: var(--text-secondary); font-size: 0.78rem;">
          ${escapeHtml(r.description)}
        </div>
        <div style="margin-top: 0.25rem; font-size: 0.7rem; color: var(--accent-blue);">
          Reported by: ${escapeHtml(r.reporter_name)} | Status: ${escapeHtml(r.status)}
        </div>
      </div>
    `
      )
      .join("");
  } catch (err) {
    console.error("Failed to load reports:", err);
    feed.innerHTML = `
      <div style="color: var(--risk-yellow); font-size: 0.8rem; text-align: center; padding: 1rem;">
        Could not connect to incident database.
      </div>
    `;
  }
}

/**
 * Handles submission of new ground observation reports.
 */
function setupReportForm() {
  const form = document.getElementById("incident-form");
  const btn = document.getElementById("submit-report-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      reporter_name: document.getElementById("reporter-name").value,
      contact_number: document.getElementById("reporter-contact").value || null,
      state: document.getElementById("report-state").value,
      district: document.getElementById("report-district").value,
      latitude: parseFloat(document.getElementById("report-lat").value),
      longitude: parseFloat(document.getElementById("report-lon").value),
      incident_type: document.getElementById("incident-type").value,
      severity: document.getElementById("incident-severity").value,
      description: document.getElementById("incident-desc").value,
      sync_status: "synced",
    };

    btn.disabled = true;
    btn.textContent = "Saving to Database...";

    try {
      const res = await fetch(`${API_BASE}/reports/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      btn.textContent = "Report Recorded!";
      btn.style.backgroundColor = "var(--risk-green)";

      // Refresh incident feed
      await loadIncidentReports();

      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = "Submit to Incident Database";
        btn.style.backgroundColor = "";
      }, 2000);
    } catch (err) {
      console.error("Submission failed:", err);
      alert("Failed to record incident report. Please check API server.");
      btn.disabled = false;
      btn.textContent = "Submit to Incident Database";
    }
  });
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
