/**
 * SentinelNet AI - SOC Frontend Dashboard Logic
 * Real-time WebSocket streaming, Chart.js visualizations, table rendering, and controls.
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    let socket = null;
    let reconnectInterval = 3000;
    let isMonitoring = false;
    let currentFilter = "all";
    let allDetections = [];

    // DOM Elements - Status
    const valBackend = document.getElementById("val-backend");
    const valDatabase = document.getElementById("val-database");
    const valModel = document.getElementById("val-model");
    const valInterface = document.getElementById("val-interface");
    const valMonitoring = document.getElementById("val-monitoring");
    const monitoringDot = document.getElementById("monitoring-dot");

    // DOM Elements - Controls
    const btnStart = document.getElementById("btn-start");
    const btnStop = document.getElementById("btn-stop");
    const ifaceSelect = document.getElementById("iface-select");
    const demoButtons = document.querySelectorAll(".btn-demo");
    const filterButtons = document.querySelectorAll(".filter-btn");

    // DOM Elements - Stats
    const statPackets = document.getElementById("stat-packets");
    const statFlows = document.getElementById("stat-flows");
    const statNormal = document.getElementById("stat-normal");
    const statSuspicious = document.getElementById("stat-suspicious");
    const statAttacks = document.getElementById("stat-attacks");

    // DOM Elements - Alert Banner
    const alertBanner = document.getElementById("alert-banner");
    const alertType = document.getElementById("alert-type");
    const alertRisk = document.getElementById("alert-risk");
    const alertTime = document.getElementById("alert-timestamp");
    const alertSrc = document.getElementById("alert-src");
    const alertDst = document.getElementById("alert-dst");
    const alertProto = document.getElementById("alert-proto");
    const alertConf = document.getElementById("alert-conf");

    // DOM Elements - Table
    const tbody = document.getElementById("detections-tbody");

    // DOM Elements - Model Info
    const modelArch = document.getElementById("model-arch");
    const modelDataset = document.getElementById("model-dataset");
    const modelFeatures = document.getElementById("model-features");
    const modelClasses = document.getElementById("model-classes");
    const metricAcc = document.getElementById("metric-acc");
    const metricPrec = document.getElementById("metric-prec");
    const metricRec = document.getElementById("metric-rec");
    const metricF1 = document.getElementById("metric-f1");

    // =========================================================================
    // Chart.js Setup
    // =========================================================================
    const commonChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: "#94a3b8", font: { family: "Inter", size: 11 } }
            }
        }
    };

    // 1. Throughput Time Series Chart
    const throughputCtx = document.getElementById("chart-throughput").getContext("2d");
    const chartThroughput = new Chart(throughputCtx, {
        type: "line",
        data: {
            labels: Array(15).fill(""),
            datasets: [
                {
                    label: "Packets / sec",
                    data: Array(15).fill(0),
                    borderColor: "#06b6d4",
                    backgroundColor: "rgba(6, 182, 212, 0.1)",
                    tension: 0.3,
                    fill: true,
                    borderWidth: 2,
                    pointRadius: 2,
                },
                {
                    label: "Flows / sec",
                    data: Array(15).fill(0),
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                    tension: 0.3,
                    fill: true,
                    borderWidth: 2,
                    pointRadius: 2,
                }
            ]
        },
        options: {
            ...commonChartOptions,
            scales: {
                x: { grid: { color: "#1e293b" }, ticks: { color: "#64748b" } },
                y: { grid: { color: "#1e293b" }, ticks: { color: "#64748b" }, beginAtZero: true }
            }
        }
    });

    // 2. Normal vs Attack Pie Chart
    const pieCtx = document.getElementById("chart-pie").getContext("2d");
    const chartPie = new Chart(pieCtx, {
        type: "doughnut",
        data: {
            labels: ["Normal", "Attacks"],
            datasets: [{
                data: [0, 0],
                backgroundColor: ["#10b981", "#ef4444"],
                borderColor: "#151d2e",
                borderWidth: 3,
            }]
        },
        options: commonChartOptions
    });

    // 3. Attack Categories Bar Chart
    const attacksCtx = document.getElementById("chart-attacks").getContext("2d");
    const chartAttacks = new Chart(attacksCtx, {
        type: "bar",
        data: {
            labels: ["DoS/DDoS", "PortScan", "BruteForce", "Bot/Infiltration"],
            datasets: [{
                label: "Count",
                data: [0, 0, 0, 0],
                backgroundColor: ["#ef4444", "#f59e0b", "#8b5cf6", "#ec4899"],
                borderRadius: 6,
            }]
        },
        options: {
            ...commonChartOptions,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } } },
                y: { grid: { color: "#1e293b" }, ticks: { color: "#64748b", stepSize: 1 }, beginAtZero: true }
            }
        }
    });

    // 4. Protocol Breakdown Pie Chart
    const protocolsCtx = document.getElementById("chart-protocols").getContext("2d");
    const chartProtocols = new Chart(protocolsCtx, {
        type: "doughnut",
        data: {
            labels: ["TCP", "UDP", "ICMP", "OTHER"],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: ["#3b82f6", "#06b6d4", "#a855f7", "#64748b"],
                borderColor: "#151d2e",
                borderWidth: 3,
            }]
        },
        options: commonChartOptions
    });

    // Tracking throughput differential
    let lastPacketCount = 0;
    let lastFlowCount = 0;

    // =========================================================================
    // WebSocket Connection
    // =========================================================================
    function initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log("WebSocket connected to SentinelNet backend.");
            valBackend.textContent = "ONLINE";
            valBackend.style.color = "#10b981";
        };

        socket.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                handleSocketMessage(msg);
            } catch (e) {
                console.error("Error parsing WebSocket message:", e);
            }
        };

        socket.onclose = () => {
            console.warn("WebSocket disconnected. Reconnecting in 3s...");
            valBackend.textContent = "RECONNECTING";
            valBackend.style.color = "#f59e0b";
            setTimeout(initWebSocket, reconnectInterval);
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
            socket.close();
        };
    }

    function handleSocketMessage(msg) {
        switch (msg.type) {
            case "INITIAL_STATE":
                updateSystemStatus(msg.data.status);
                updateStatistics(msg.data.statistics);
                if (msg.data.recent_detections) {
                    allDetections = msg.data.recent_detections;
                    renderTable();
                }
                break;

            case "NEW_DETECTION":
                handleNewDetection(msg.data);
                break;

            case "ALERT":
                displayAlert(msg.data);
                break;

            case "STATS_UPDATE":
                updateStatistics(msg.data);
                break;

            case "MONITORING_STATUS_CHANGE":
                updateSystemStatus(msg.data);
                break;
        }
    }

    function handleNewDetection(detection) {
        allDetections.unshift(detection);
        if (allDetections.length > 200) allDetections.pop();
        renderTable();

        if (detection.is_attack) {
            displayAlert(detection);
        }
    }

    function displayAlert(alert) {
        alertBanner.style.display = "flex";
        alertType.textContent = `INTRUSION DETECTED: ${alert.attack_type}`;
        alertRisk.textContent = `${alert.risk_level} RISK`;
        alertRisk.className = `alert-badge badge-risk ${alert.risk_level.toLowerCase()}`;
        alertTime.textContent = new Date(alert.timestamp || Date.now()).toLocaleTimeString();
        alertSrc.textContent = `${alert.source_ip}:${alert.source_port}`;
        alertDst.textContent = `${alert.destination_ip}:${alert.destination_port}`;
        alertProto.textContent = alert.protocol;
        alertConf.textContent = `${(alert.confidence * 100).toFixed(1)}%`;
    }

    function updateStatistics(stats) {
        if (!stats) return;

        statPackets.textContent = Number(stats.packets_captured || 0).toLocaleString();
        statFlows.textContent = Number(stats.flows_processed || 0).toLocaleString();
        statNormal.textContent = Number(stats.normal_count || 0).toLocaleString();
        statSuspicious.textContent = Number(stats.suspicious_count || 0).toLocaleString();
        statAttacks.textContent = Number(stats.attack_count || 0).toLocaleString();

        // Update Charts
        // 1. Pie (Normal vs Attack)
        chartPie.data.datasets[0].data = [stats.normal_count || 0, stats.attack_count || 0];
        chartPie.update("none");

        // 2. Attack Distribution
        const attackDist = stats.attack_distribution || {};
        chartAttacks.data.datasets[0].data = [
            attackDist["DoS_DDoS"] || 0,
            attackDist["PortScan"] || 0,
            attackDist["BruteForce"] || 0,
            attackDist["Bot_Infiltration"] || 0,
        ];
        chartAttacks.update("none");

        // 3. Protocol Distribution
        const protoDist = stats.protocol_distribution || {};
        chartProtocols.data.datasets[0].data = [
            protoDist["TCP"] || 0,
            protoDist["UDP"] || 0,
            protoDist["ICMP"] || 0,
            protoDist["OTHER"] || 0,
        ];
        chartProtocols.update("none");

        // 4. Throughput Delta
        const currentPkts = stats.packets_captured || 0;
        const currentFlows = stats.flows_processed || 0;
        const pktDelta = Math.max(0, currentPkts - lastPacketCount);
        const flowDelta = Math.max(0, currentFlows - lastFlowCount);
        lastPacketCount = currentPkts;
        lastFlowCount = currentFlows;

        const timeLabel = new Date().toLocaleTimeString();
        chartThroughput.data.labels.shift();
        chartThroughput.data.labels.push(timeLabel);
        chartThroughput.data.datasets[0].data.shift();
        chartThroughput.data.datasets[0].data.push(pktDelta);
        chartThroughput.data.datasets[1].data.shift();
        chartThroughput.data.datasets[1].data.push(flowDelta);
        chartThroughput.update("none");
    }

    function updateSystemStatus(status) {
        if (!status) return;

        isMonitoring = status.monitoring_active;
        valMonitoring.textContent = isMonitoring ? "ACTIVE" : "INACTIVE";
        monitoringDot.className = `status-dot ${isMonitoring ? "green" : "red"}`;

        btnStart.disabled = isMonitoring;
        btnStop.disabled = !isMonitoring;

        if (status.active_interface) {
            valInterface.textContent = status.active_interface;
        }

        if (status.model_loaded) {
            valModel.textContent = "1D-CNN LOADED";
            valModel.style.color = "#10b981";
        }
    }

    function renderTable() {
        let filtered = allDetections;
        if (currentFilter === "attacks") {
            filtered = allDetections.filter(d => d.is_attack);
        } else if (currentFilter === "critical") {
            filtered = allDetections.filter(d => d.risk_level === "HIGH" || d.risk_level === "CRITICAL");
        }

        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="10"><i class="fa-solid fa-circle-info"></i> No matching detections. Start monitoring or trigger safe demonstration traffic.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = filtered.slice(0, 50).map(d => {
            const timeStr = d.timestamp ? new Date(d.timestamp).toLocaleTimeString() : "--";
            const riskClass = (d.risk_level || "normal").toLowerCase();
            const confPercent = (d.confidence * 100).toFixed(1);

            return `
                <tr>
                    <td>${timeStr}</td>
                    <td>${d.source_ip}:${d.source_port}</td>
                    <td>${d.destination_ip}:${d.destination_port}</td>
                    <td><span class="protocol-badge">${d.protocol}</span></td>
                    <td><strong>${d.prediction}</strong></td>
                    <td>${confPercent}%</td>
                    <td><span class="badge-risk ${riskClass}">${d.risk_level}</span></td>
                    <td>${d.flow_duration}</td>
                    <td>${d.packet_count}</td>
                    <td>${d.byte_count}</td>
                </tr>
            `;
        }).join("");
    }

    // =========================================================================
    // REST API Calls & Handlers
    // =========================================================================
    async function fetchHealth() {
        try {
            const res = await fetch("/api/health");
            const data = await res.json();
            if (data.database) {
                valDatabase.textContent = data.database.status === "CONNECTED" ? data.database.type : "OFFLINE";
                valDatabase.style.color = data.database.status === "CONNECTED" ? "#10b981" : "#ef4444";
            }
            updateSystemStatus(data.monitoring);
        } catch (e) {
            console.error("Error fetching health:", e);
        }
    }

    async function fetchInterfaces() {
        try {
            const res = await fetch("/api/interfaces");
            const data = await res.json();
            ifaceSelect.innerHTML = data.interfaces.map(iface => `
                <option value="${iface.name}" ${iface.name === data.active_interface ? "selected" : ""}>
                    ${iface.name} (${iface.ip}) ${iface.is_up ? "[UP]" : "[DOWN]"}
                </option>
            `).join("");
        } catch (e) {
            console.error("Error fetching interfaces:", e);
        }
    }

    async function fetchModelInfo() {
        try {
            const res = await fetch("/api/model/info");
            const info = await res.json();
            if (info.is_loaded) {
                modelArch.textContent = info.architecture || "1D-CNN";
                modelDataset.textContent = info.dataset || "CICIDS2017 Benchmark";
                modelFeatures.textContent = `${info.features_count} Statistical Flow Features`;
                modelClasses.textContent = `${info.classes_count} Classes: ${info.classes.join(", ")}`;

                if (info.metrics && info.metrics.overall) {
                    const o = info.metrics.overall;
                    metricAcc.textContent = `${(o.accuracy * 100).toFixed(2)}%`;
                    metricPrec.textContent = `${(o.precision_macro * 100).toFixed(2)}%`;
                    metricRec.textContent = `${(o.recall_macro * 100).toFixed(2)}%`;
                    metricF1.textContent = `${(o.f1_macro * 100).toFixed(2)}%`;
                }
            }
        } catch (e) {
            console.error("Error fetching model info:", e);
        }
    }

    // Monitoring Controls
    btnStart.addEventListener("click", async () => {
        const selectedIface = ifaceSelect.value;
        btnStart.disabled = true;
        try {
            const res = await fetch("/api/monitoring/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ interface: selectedIface })
            });
            const data = await res.json();
            if (data.status === "STARTED" || data.status === "ALREADY_RUNNING") {
                updateSystemStatus({ monitoring_active: true, active_interface: selectedIface, model_loaded: true });
            }
        } catch (e) {
            console.error("Error starting monitoring:", e);
            btnStart.disabled = false;
        }
    });

    btnStop.addEventListener("click", async () => {
        btnStop.disabled = true;
        try {
            const res = await fetch("/api/monitoring/stop", { method: "POST" });
            const data = await res.json();
            if (data.status === "STOPPED") {
                updateSystemStatus({ monitoring_active: false });
            }
        } catch (e) {
            console.error("Error stopping monitoring:", e);
            btnStop.disabled = false;
        }
    });

    // Demo Traffic Triggers
    demoButtons.forEach(btn => {
        btn.addEventListener("click", async () => {
            const mode = btn.dataset.mode;
            btn.style.opacity = "0.5";
            try {
                await fetch("/api/demo/trigger", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mode: mode, count: 20 })
                });
            } catch (e) {
                console.error("Error triggering demo traffic:", e);
            } finally {
                setTimeout(() => { btn.style.opacity = "1"; }, 600);
            }
        });
    });

    // Table Filters
    filterButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            filterButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.dataset.filter;
            renderTable();
        });
    });

    // Initialization
    fetchHealth();
    fetchInterfaces();
    fetchModelInfo();
    initWebSocket();
});
