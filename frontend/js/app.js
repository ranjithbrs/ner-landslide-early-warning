/**
 * NER Landslide Early Warning & Risk Monitoring Platform
 * GIS Dashboard & Tactical Control Room Engine (Leaflet.js + REST API)
 */

const API_BASE = "/api/v1";

// Global map and layer groups
let map = null;
let riskZonesLayer = null;
let roadsLayer = null;
let sensorsLayer = null;
let incidentsLayer = null;

// Cache for active zones and current features
let cachedZonesGeoJSON = null;

// Corridor camera focus coordinate presets
const REGION_COORDINATES = {
  ALL: { center: [26.2006, 92.9376], zoom: 7 },
  SKM: { center: [27.1520, 88.5250], zoom: 10 },  // Sikkim NH-10
  ASM: { center: [25.1700, 93.0200], zoom: 10 },  // Assam Haflong NH-27
  NGL: { center: [25.6751, 94.1106], zoom: 10 },  // Nagaland Kohima NH-29
  MEG: { center: [25.5788, 91.8933], zoom: 10 },  // Meghalaya Shillong NH-6
  ARN: { center: [27.2600, 92.4200], zoom: 9 },   // Arunachal Bomdila
  MNP: { center: [24.7800, 93.6500], zoom: 10 },  // Manipur Tupul
  MIZ: { center: [23.4700, 93.3200], zoom: 9 },   // Mizoram Champhai
  TRP: { center: [23.9500, 92.2700], zoom: 10 },  // Tripura Jampui Hills
};

document.addEventListener("DOMContentLoaded", async () => {
  console.log("Initializing NER Landslide GIS Dashboard...");
  initMap();
  setupEventListeners();
  await refreshDashboard();
});

/**
 * Initializes the Leaflet interactive map with dark basemaps and layer controls.
 */
function initMap() {
  map = L.map("gis-map", {
    center: [25.85, 93.2],
    zoom: 7,
    minZoom: 5,
    maxZoom: 18,
    zoomControl: true,
  });

  // 1. Esri Dark Gray Tactical Canvas (Zero watermarks, high-contrast dark theme)
  const esriDark = L.layerGroup([
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
      attribution: "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
      maxZoom: 16,
    }),
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 16,
    }),
  ]).addTo(map);

  // 2. Esri World Satellite Imagery (Realistic Himalayan mountain relief)
  const esriSatellite = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      attribution: "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
      maxZoom: 18,
    }
  );

  // 3. OpenStreetMap Standard Topo
  const osmStandard = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  });

  // Ensure Leaflet calculates viewport dimensions properly on startup
  setTimeout(() => {
    map.invalidateSize();
    map.setView([25.85, 93.2], 7);
  }, 250);

  // Layer groups for GIS overlays
  riskZonesLayer = L.layerGroup().addTo(map);
  roadsLayer = L.layerGroup().addTo(map);
  sensorsLayer = L.layerGroup().addTo(map);
  incidentsLayer = L.layerGroup().addTo(map);

  // Leaflet Layer Switcher Control
  const baseLayers = {
    "Tactical Dark Canvas": esriDark,
    "Satellite Topography": esriSatellite,
    "OpenStreetMap": osmStandard,
  };

  const overlayLayers = {
    "🔴 Landslide Risk Catchments": riskZonesLayer,
    "🛣️ Critical Road Corridors": roadsLayer,
    "📡 IoT Ground Telemetry Stations": sensorsLayer,
    "⚠️ Crowdsourced Ground Reports": incidentsLayer,
  };

  L.control.layers(baseLayers, overlayLayers, { position: "topright" }).addTo(map);

  // Custom Map Legend
  addMapLegend();
}

/**
 * Adds an on-map legend explaining risk levels, road corridors, and sensor icons.
 */
function addMapLegend() {
  const legend = L.control({ position: "bottomleft" });
  legend.onAdd = function () {
    const div = L.DomUtil.create("div", "map-legend");
    div.innerHTML = `
      <div class="legend-title">Early Warning Legend</div>
      <div class="legend-item"><span class="legend-color" style="background: var(--risk-red);"></span> <span>RED: Critical Hazard (DLHI ≥ 75)</span></div>
      <div class="legend-item"><span class="legend-color" style="background: var(--risk-orange);"></span> <span>ORANGE: High Alert (DLHI 50-74)</span></div>
      <div class="legend-item"><span class="legend-color" style="background: var(--risk-yellow);"></span> <span>YELLOW: Advisory (DLHI 30-49)</span></div>
      <div class="legend-item"><span class="legend-color" style="background: var(--risk-green);"></span> <span>GREEN: Normal (DLHI &lt; 30)</span></div>
      <div style="margin-top: 0.35rem; border-top: 1px solid #334155; padding-top: 0.25rem;"></div>
      <div class="legend-item"><span style="color: #ef4444; font-weight: bold;">-- --</span> <span>Highway Blocked / Single-Lane</span></div>
      <div class="legend-item"><span style="color: var(--accent-blue); font-weight: bold;">◉</span> <span>IoT Ground Sensor Station</span></div>
    `;
    return div;
  };
  legend.addTo(map);
}

/**
 * Refreshes all dashboard feeds from the backend API.
 */
async function refreshDashboard() {
  await checkSystemHealth();
  await fetchRiskSummary();
  await loadRiskZones();
  await loadRoadCorridors();
  await loadSensors();
  await loadIncidentReports();
}

/**
 * Checks system health via GET /api/v1/health.
 */
async function checkSystemHealth() {
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
    statusText.textContent = `Connected (${data.ml_service_status})`;

    footerDiag.textContent = `API: v${data.version} | DB: ${data.database} | Active Model: ${data.ml_service_status}`;
  } catch (err) {
    statusPill.style.color = "var(--risk-red)";
    statusPill.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
    statusPill.style.borderColor = "rgba(239, 68, 68, 0.3)";
    statusText.textContent = "API Offline";
    footerDiag.textContent = "API Server Disconnected";
  }
}

/**
 * Fetches regional risk summary from GET /api/v1/risk/summary and updates top KPI cards.
 */
async function fetchRiskSummary() {
  try {
    const res = await fetch(`${API_BASE}/risk/summary`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const summary = await res.json();

    document.getElementById("corridor-count-val").textContent = summary.total_monitored_zones || 8;
    document.getElementById("val-red").textContent = summary.warning_breakdown?.RED || 0;
    document.getElementById("val-orange").textContent = summary.warning_breakdown?.ORANGE || 0;

    if (summary.highest_risk_zone) {
      const top = summary.highest_risk_zone;
      document.getElementById("highest-risk-val").textContent = `${top.name} (${top.hazard_index})`;
      document.getElementById("highest-risk-sub").textContent = `Warning: ${top.warning_level} | ${top.district}, ${top.state}`;
    }
  } catch (err) {
    console.error("Failed to fetch risk summary:", err);
  }
}

/**
 * Fetches and renders GIS Risk Zones from GET /api/v1/risk/zones.
 */
async function loadRiskZones() {
  riskZonesLayer.clearLayers();
  const listEl = document.getElementById("vulnerable-zones-list");

  try {
    const res = await fetch(`${API_BASE}/risk/zones`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const geojson = await res.json();
    cachedZonesGeoJSON = geojson;

    // Render Leaflet GeoJSON layer
    const zonesGeoLayer = L.geoJSON(geojson, {
      style: (feature) => getRiskZoneStyle(feature.properties.early_warning_level),
      onEachFeature: (feature, layer) => {
        const p = feature.properties;
        const badgeClass = getBadgeClass(p.early_warning_level);

        const popupContent = `
          <div class="popup-card">
            <div class="popup-title">${escapeHtml(p.name)}</div>
            <span class="popup-badge ${badgeClass}">${p.early_warning_level} STAGE (DLHI: ${p.dynamic_hazard_index})</span>
            <div class="popup-grid">
              <div><strong>State:</strong> ${escapeHtml(p.state)}</div>
              <div><strong>District:</strong> ${escapeHtml(p.district)}</div>
              <div><strong>Slope:</strong> ${p.slope_deg}°</div>
              <div><strong>ML Susceptibility:</strong> ${p.susceptibility_class} (${(p.susceptibility_probability * 100).toFixed(1)}%)</div>
              <div><strong>24h Rain:</strong> ${p.rainfall_24h_mm} mm</div>
              <div><strong>Antecedent 72h:</strong> ${p.rainfall_72h_mm} mm</div>
              <div><strong>Soil Moisture:</strong> ${p.soil_moisture_pct}%</div>
              <div><strong>Tilt Velocity:</strong> ${p.tilt_rate_mm_h} mm/h</div>
            </div>
            <div class="popup-action">
              <strong>Action:</strong> ${escapeHtml(p.recommended_action)}
            </div>
          </div>
        `;
        layer.bindPopup(popupContent, {
          autoPan: true,
          autoPanPadding: [60, 60],
          offset: [0, -10],
          maxWidth: 340,
        });
      },
    });

    riskZonesLayer.addLayer(zonesGeoLayer);

    // Also add high-visibility center beacons for each risk zone
    geojson.features.forEach((feature) => {
      const p = feature.properties;
      const fillColor = getLevelColor(p.early_warning_level);
      const beacon = L.circleMarker([p.center[1], p.center[0]], {
        radius: 8,
        fillColor: fillColor,
        color: "#ffffff",
        weight: 1.5,
        opacity: 1,
        fillOpacity: 0.9,
      });

      beacon.bindTooltip(`⚠️ ${p.name} [${p.early_warning_level}: ${p.dynamic_hazard_index}]`, {
        direction: "top",
        offset: [0, -8],
      });

      beacon.on("click", () => {
        focusOnZone(p.zone_id, [p.center[1], p.center[0]]);
      });

      riskZonesLayer.addLayer(beacon);
    });

    // Populate Sidebar Vulnerability Matrix
    const features = geojson.features || [];
    // Sort descending by hazard index
    features.sort((a, b) => b.properties.dynamic_hazard_index - a.properties.dynamic_hazard_index);

    listEl.innerHTML = features
      .map((f) => {
        const p = f.properties;
        const borderClass = `border-${p.early_warning_level.toLowerCase()}`;
        const fillColor = getLevelColor(p.early_warning_level);

        return `
        <div class="zone-item ${borderClass}" onclick="focusOnZone('${p.zone_id}', [${p.center[1]}, ${p.center[0]}])">
          <div class="zone-item-header">
            <span>${escapeHtml(p.name)}</span>
            <span style="color: ${fillColor}; font-weight: 700;">${p.dynamic_hazard_index}</span>
          </div>
          <div style="font-size: 0.7rem; color: var(--text-muted); display: flex; justify-content: space-between;">
            <span>${escapeHtml(p.district)}, ${escapeHtml(p.state)}</span>
            <span style="color: ${fillColor}; font-weight: 600;">${p.early_warning_level}</span>
          </div>
          <div class="hazard-bar-wrap">
            <div class="hazard-bar-fill" style="width: ${p.dynamic_hazard_index}%; background-color: ${fillColor};"></div>
          </div>
        </div>
      `;
      })
      .join("");
  } catch (err) {
    console.error("Failed to load risk zones:", err);
    listEl.innerHTML = `<div style="color: var(--risk-yellow); font-size: 0.78rem; text-align: center;">Could not load risk zones.</div>`;
  }
}

/**
 * Fetches and renders Critical Road Corridors from GET /api/v1/roads/geojson.
 */
async function loadRoadCorridors() {
  roadsLayer.clearLayers();

  try {
    const res = await fetch(`${API_BASE}/roads/geojson`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const geojson = await res.json();

    const roadGeoLayer = L.geoJSON(geojson, {
      style: (feature) => {
        const status = feature.properties.status;
        let color = "#22c55e"; // Open
        let dashArray = null;
        let weight = 4;

        if (status === "blocked") {
          color = "#ef4444";
          dashArray = "6, 8";
          weight = 5;
        } else if (status === "single_lane") {
          color = "#eab308";
          dashArray = "4, 4";
        } else if (status === "risky") {
          color = "#f97316";
        }

        return { color, weight, dashArray, opacity: 0.9 };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties;
        const statusText = p.status.replace("_", " ").toUpperCase();

        layer.bindPopup(`
          <div class="popup-card">
            <div class="popup-title">🛣️ ${escapeHtml(p.corridor_code)}: ${escapeHtml(p.name)}</div>
            <div style="margin-bottom: 0.4rem; font-size: 0.75rem;">
              <strong>Route:</strong> ${escapeHtml(p.start_point)} ➔ ${escapeHtml(p.end_point)} (${escapeHtml(p.state)})
            </div>
            <div style="font-size: 0.75rem;">
              <strong>Operational Status:</strong> 
              <span style="font-weight: bold; color: ${p.status === 'blocked' ? 'var(--risk-red)' : 'var(--risk-green)'};">
                ${statusText}
              </span>
            </div>
            <div style="font-size: 0.75rem; margin-top: 0.2rem;">
              <strong>Slope Risk Rating:</strong> ${escapeHtml(p.risk_level)}
            </div>
            ${p.detour_available ? `<div class="popup-action" style="margin-top: 0.4rem;">⚠️ Traffic Warning: Single-lane or debris blockage active. Alternate detour recommended.</div>` : ""}
          </div>
        `);
      },
    });

    roadsLayer.addLayer(roadGeoLayer);
  } catch (err) {
    console.error("Failed to load road corridors:", err);
  }
}

/**
 * Fetches and renders IoT Ground Sensors from GET /api/v1/sensors/geojson.
 */
async function loadSensors() {
  sensorsLayer.clearLayers();

  try {
    const res = await fetch(`${API_BASE}/sensors/geojson`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const geojson = await res.json();

    document.getElementById("sensor-count-val").textContent = geojson.features?.length || 0;

    geojson.features.forEach((feature) => {
      const [lon, lat] = feature.geometry.coordinates;
      const p = feature.properties;

      // Custom HTML Pulsing Sensor Marker
      const customIcon = L.divIcon({
        className: "sensor-marker",
        html: `<div class="sensor-core" style="background-color: ${p.soil_moisture_pct > 80 ? 'var(--risk-red)' : 'var(--accent-blue)'};"></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const marker = L.marker([lat, lon], { icon: customIcon });

      marker.bindPopup(`
        <div class="popup-card">
          <div class="popup-title">📡 ${escapeHtml(p.station_name)}</div>
          <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.35rem;">
            Station ID: ${escapeHtml(p.station_id)} | ${escapeHtml(p.district)}, ${escapeHtml(p.state)}
          </div>
          <div class="popup-grid">
            <div><strong>Soil Moisture:</strong> ${p.soil_moisture_pct}%</div>
            <div><strong>Pore Pressure:</strong> ${p.pore_pressure_kpa} kPa</div>
            <div><strong>1h Rainfall:</strong> ${p.rainfall_1h_mm} mm</div>
            <div><strong>Tilt Displacement:</strong> ${p.tilt_displacement_mm} mm</div>
            <div><strong>Battery:</strong> ${p.battery_pct}%</div>
            <div><strong>Telemetry:</strong> Online</div>
          </div>
          <div style="font-size: 0.7rem; color: var(--accent-blue);">
            Last Transmission: ${escapeHtml(p.recorded_at)}
          </div>
        </div>
      `);

      sensorsLayer.addLayer(marker);
    });
  } catch (err) {
    console.error("Failed to load sensors:", err);
  }
}

/**
 * Fetches and renders Crowdsourced Incident Reports from GET /api/v1/reports/geojson.
 */
async function loadIncidentReports() {
  incidentsLayer.clearLayers();
  const feedEl = document.getElementById("incident-feed");

  try {
    const res = await fetch(`${API_BASE}/reports/geojson`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const geojson = await res.json();
    const features = geojson.features || [];

    // Render map markers
    features.forEach((feature) => {
      const [lon, lat] = feature.geometry.coordinates;
      const p = feature.properties;

      let color = "var(--risk-yellow)";
      if (p.severity === "Critical") color = "var(--risk-red)";
      else if (p.severity === "High") color = "var(--risk-orange)";

      const marker = L.circleMarker([lat, lon], {
        radius: 8,
        fillColor: color,
        color: "#ffffff",
        weight: 1.5,
        opacity: 1,
        fillOpacity: 0.85,
      });

      marker.bindPopup(`
        <div class="popup-card">
          <div class="popup-title">⚠️ ${escapeHtml(p.incident_type)}</div>
          <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.35rem;">
            Severity: <strong style="color: ${color};">${escapeHtml(p.severity)}</strong> | ${escapeHtml(p.district)}, ${escapeHtml(p.state)}
          </div>
          <div style="font-size: 0.75rem; margin-bottom: 0.4rem;">
            ${escapeHtml(p.description)}
          </div>
          <div style="font-size: 0.7rem; color: var(--accent-blue);">
            Reported by: ${escapeHtml(p.reporter_name)} | Status: ${escapeHtml(p.status)}
          </div>
        </div>
      `);

      incidentsLayer.addLayer(marker);
    });

    // Populate Sidebar Incident Feed
    if (features.length === 0) {
      feedEl.innerHTML = `<div style="color: var(--text-muted); font-size: 0.78rem; text-align: center; padding: 0.5rem;">No incidents logged yet.</div>`;
      return;
    }

    feedEl.innerHTML = features
      .slice(0, 8)
      .map((f) => {
        const p = f.properties;
        return `
        <div class="incident-item">
          <div style="display: flex; justify-content: space-between; font-weight: 600;">
            <span>${escapeHtml(p.incident_type)} (${escapeHtml(p.severity)})</span>
            <span style="color: var(--text-muted); font-size: 0.68rem;">${escapeHtml(p.district)}</span>
          </div>
          <div style="color: var(--text-secondary); font-size: 0.72rem; margin-top: 0.15rem;">
            ${escapeHtml(p.description)}
          </div>
          <div style="font-size: 0.68rem; color: var(--accent-blue); margin-top: 0.2rem;">
            By: ${escapeHtml(p.reporter_name)} | Status: ${escapeHtml(p.status)}
          </div>
        </div>
      `;
      })
      .join("");
  } catch (err) {
    console.error("Failed to load incident reports:", err);
  }
}

/**
 * Sets up user interaction listeners.
 */
function setupEventListeners() {
  // 1. Camera Fly-To Selector
  document.getElementById("region-camera-select").addEventListener("change", (e) => {
    const key = e.target.value;
    if (key === "ALL") {
      map.flyTo([25.85, 93.2], 7, { duration: 1.2 });
    } else {
      const target = REGION_COORDINATES[key] || REGION_COORDINATES.ALL;
      map.flyTo(target.center, target.zoom, { duration: 1.2 });
    }
  });

  // 2. Refresh Button
  document.getElementById("refresh-layers-btn").addEventListener("click", () => {
    refreshDashboard();
  });

  // 3. ML Simulation Sliders
  const rainSlider = document.getElementById("sim-rain-slider");
  const moistSlider = document.getElementById("sim-moist-slider");
  const rainDisplay = document.getElementById("val-rain-display");
  const moistDisplay = document.getElementById("val-moist-display");

  rainSlider.addEventListener("input", (e) => {
    rainDisplay.textContent = `${e.target.value} mm`;
  });

  moistSlider.addEventListener("input", (e) => {
    moistDisplay.textContent = `${e.target.value} %`;
  });

  // 4. Run ML Simulation Button
  document.getElementById("run-simulation-btn").addEventListener("click", runSimulation);

  // 5. Incident Form Submit
  setupIncidentForm();
}

/**
 * Smoothly flies map camera to a specific slope catchment and opens its popup.
 */
window.focusOnZone = function (zoneId, centerCoords) {
  // Offset latitude slightly north (+0.035) so the popup has full clearance from top header
  const targetLat = centerCoords[0] + 0.035;
  const targetLon = centerCoords[1];
  map.flyTo([targetLat, targetLon], 11, { duration: 0.8 });

  setTimeout(() => {
    riskZonesLayer.eachLayer((layer) => {
      if (layer.feature && layer.feature.properties && layer.feature.properties.zone_id === zoneId) {
        layer.openPopup();
      } else if (layer.eachLayer) {
        layer.eachLayer((sub) => {
          if (sub.feature && sub.feature.properties && sub.feature.properties.zone_id === zoneId) {
            sub.openPopup();
          }
        });
      }
    });
  }, 900);
};

/**
 * Executes a real-time ML prediction using POST /api/v1/risk/predict.
 */
async function runSimulation() {
  const zoneId = document.getElementById("sim-zone-select").value;
  const rain24h = parseFloat(document.getElementById("sim-rain-slider").value);
  const soilMoist = parseFloat(document.getElementById("sim-moist-slider").value);
  const btn = document.getElementById("run-simulation-btn");
  const resBox = document.getElementById("sim-result-box");

  btn.disabled = true;
  btn.textContent = "Calling ML Predictor...";

  // Find baseline zone properties from cache
  const zoneFeature = cachedZonesGeoJSON?.features?.find((f) => f.properties.zone_id === zoneId);
  const p = zoneFeature ? zoneFeature.properties : { slope_deg: 40.0, state: "NER", district: "Slope Zone", name: "Simulated Corridor" };

  const payload = {
    location_name: p.name,
    state: p.state,
    district: p.district,
    terrain: {
      elevation_m: 1200.0,
      slope_deg: p.slope_deg || 38.0,
      aspect_deg: 180.0,
      profile_curvature: -0.02,
      plan_curvature: 0.01,
      topographic_wetness_index: 8.5,
      dist_to_fault_m: 350.0,
      dist_to_drainage_m: 120.0,
      lithology_code: 3,
      lulc_code: 3,
    },
    meteorology: {
      rainfall_24h_mm: rain24h,
      rainfall_72h_antecedent_mm: rain24h * 1.8,
      rainfall_intensity_mm_h: rain24h / 4.0,
    },
    geotechnical: {
      soil_moisture_pct: soilMoist,
      pore_water_pressure_kpa: Math.max(0.0, (soilMoist - 70.0) * 1.4),
      tilt_rate_mm_h: soilMoist > 80.0 && rain24h > 100.0 ? 2.5 : 0.2,
    },
  };

  try {
    const res = await fetch(`${API_BASE}/risk/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const pred = await res.json();

    resBox.style.display = "block";
    document.getElementById("sim-res-title").textContent = `${pred.location_name}`;
    const badgeEl = document.getElementById("sim-res-badge");
    badgeEl.textContent = pred.early_warning_level;
    badgeEl.className = `popup-badge ${getBadgeClass(pred.early_warning_level)}`;

    document.getElementById("sim-res-susc").textContent = `${(pred.susceptibility_probability * 100).toFixed(1)}% (${pred.susceptibility_class})`;
    document.getElementById("sim-res-dlhi").textContent = pred.dynamic_hazard_index;
    document.getElementById("sim-res-action").textContent = pred.recommended_action;
  } catch (err) {
    console.error("Simulation failed:", err);
    alert("Simulation prediction failed. Check API server.");
  } finally {
    btn.disabled = false;
    btn.textContent = "⚡ Recompute Risk with ML Model";
  }
}

/**
 * Handles field hazard report submission to POST /api/v1/reports/.
 */
function setupIncidentForm() {
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
    btn.textContent = "Saving to Database & GIS...";

    try {
      const res = await fetch(`${API_BASE}/reports/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const created = await res.json();

      btn.textContent = "Report Placed on Map!";
      btn.style.backgroundColor = "var(--risk-green)";

      // Fly map to newly created hazard location
      map.flyTo([created.latitude, created.longitude], 11, { duration: 1.0 });

      // Reload reports layer
      await loadIncidentReports();

      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = "Submit to GIS Map & Database";
        btn.style.backgroundColor = "";
      }, 2000);
    } catch (err) {
      console.error("Submission failed:", err);
      alert("Failed to submit hazard report. Please check API server.");
      btn.disabled = false;
      btn.textContent = "Submit to GIS Map & Database";
    }
  });
}

/**
 * Helper styling and color mapping functions.
 */
function getRiskZoneStyle(level) {
  const color = getLevelColor(level);
  let fillOpacity = 0.45;
  let weight = 2.5;
  if (level === "RED") {
    fillOpacity = 0.65;
    weight = 3.5;
  } else if (level === "ORANGE") {
    fillOpacity = 0.55;
    weight = 3.0;
  }

  return {
    color: color,
    weight: weight,
    opacity: 0.95,
    fillColor: color,
    fillOpacity: fillOpacity,
  };
}

function getLevelColor(level) {
  switch (level) {
    case "RED": return "#ef4444";
    case "ORANGE": return "#f97316";
    case "YELLOW": return "#eab308";
    case "GREEN": return "#22c55e";
    default: return "#38bdf8";
  }
}

function getBadgeClass(level) {
  switch (level) {
    case "RED": return "badge-red";
    case "ORANGE": return "badge-orange";
    case "YELLOW": return "badge-yellow";
    case "GREEN": return "badge-green";
    default: return "badge-yellow";
  }
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
