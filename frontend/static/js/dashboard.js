let charts = {};
let autoRefreshInterval = null;
let isAutoRefreshEnabled = false;
let lastRealTimeCheck = null;

// Initialize dashboard
document.addEventListener("DOMContentLoaded", function () {
  checkRealTimeStatus(); // Check live status first
  loadHistoricalData(); // Then load historical data

  // Time range change handler
  document.getElementById("timeRange").addEventListener("change", function () {
    loadHistoricalData();
  });
});

// Check real-time cluster status
// async function checkRealTimeStatus() {
//   try {
//     document.getElementById("realTimeStatusLoading").style.display = "flex";
//     document.getElementById("realTimeStatus").style.display = "none";

//     // const response = await fetch('http://127.0.0.1:8000/metrics');

//     const response = await fetch("http://10.101.1.50:5000/metrics", {
//       method: "GET",
//       headers: {
//         Accept: "application/json",
//       },
//       // Add mode to handle potential CORS issues
//       mode: "cors",
//     });

//     // Check if the response is OK (status in the range 200-299)
//     if (!response.ok) {
//       throw new Error(`HTTP error! status: ${response.status}`);
//     }
//     const data = await response.json();

//     const liveStatusContainer = document.getElementById("liveClusterStatus");
//     liveStatusContainer.innerHTML = "";

//     lastRealTimeCheck = new Date().toLocaleString();

//     // Check if the expected data structure exists
//     if (!data.postgres_cluster || !data.mysql_cluster) {
//       throw new Error("Invalid data structure received from server");
//     }

//     // PostgreSQL Cluster
//     const pgStatus = data.postgres_cluster.status;
//     const pgItem = document.createElement("div");
//     pgItem.innerHTML = `
//                     <div class="real-time-status">
//                         <div>
//                             <div class="cluster-name">
//                                 PostgreSQL Cluster
//                                 <span class="status-indicator ${pgStatus}"></span>
//                             </div>
//                             <div class="last-check">Last checked: ${lastRealTimeCheck}</div>
//                         </div>
//                         <div class="status-item status-${pgStatus}">
//                             ${pgStatus.toUpperCase()}
//                         </div>
//                     </div>
//                     <div style="font-size: 0.9rem; color: #666;">
//                         Master: ${data.postgres_cluster.master_node.connection_status.toUpperCase()}, 
//                         Slave1: ${data.postgres_cluster.slave1_node.connection_status.toUpperCase()}, 
//                         Slave2: ${data.postgres_cluster.slave2_node.connection_status.toUpperCase()}
//                     </div>
//                 `;
//     liveStatusContainer.appendChild(pgItem);

//     // MySQL Cluster
//     const mysqlStatus = data.mysql_cluster.status;
//     const mysqlItem = document.createElement("div");
//     mysqlItem.style.marginTop = "15px";
//     mysqlItem.innerHTML = `
//                     <div class="real-time-status">
//                         <div>
//                             <div class="cluster-name">
//                                 MySQL Cluster
//                                 <span class="status-indicator ${mysqlStatus}"></span>
//                             </div>
//                             <div class="last-check">Last checked: ${lastRealTimeCheck}</div>
//                         </div>
//                         <div class="status-item status-${mysqlStatus}">
//                             ${mysqlStatus.toUpperCase()}
//                         </div>
//                     </div>
//                     <div style="font-size: 0.9rem; color: #666;">
//                         Master: ${data.mysql_cluster.master_node.connection_status.toUpperCase()}, 
//                         Slave1: ${data.mysql_cluster.slave1_node.connection_status.toUpperCase()}, 
//                         Slave2: ${data.mysql_cluster.slave2_node.connection_status.toUpperCase()}
//                     </div>
//                 `;
//     liveStatusContainer.appendChild(mysqlItem);

//     document.getElementById("realTimeStatusLoading").style.display = "none";
//     document.getElementById("realTimeStatus").style.display = "block";
//   } catch (error) {
//     console.error("Error checking real-time status:", error);
//     const liveStatusContainer = document.getElementById("liveClusterStatus");
//     liveStatusContainer.innerHTML = `
//                     <div class="connection-error">
//                         <h3>Connection Error</h3>
//                         <p>Unable to check live cluster status</p>
//                         <small>Check if the monitoring backend is running</small>
//                     </div>
//                 `;
//     document.getElementById("realTimeStatusLoading").style.display = "none";
//     document.getElementById("realTimeStatus").style.display = "block";
//   }
// }
// Check real-time cluster status
async function checkRealTimeStatus() {
  try {
    document.getElementById("realTimeStatusLoading").style.display = "flex";
    document.getElementById("realTimeStatus").style.display = "none";

    // const response = await fetch('http://127.0.0.1:8000/metrics');

    const response = await fetch("http://10.101.1.50:5000/metrics", {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      // Add mode to handle potential CORS issues
      mode: "cors",
    });

    // Check if the response is OK (status in the range 200-299)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();

    const liveStatusContainer = document.getElementById("liveClusterStatus");
    liveStatusContainer.innerHTML = "";

    lastRealTimeCheck = new Date().toLocaleString();

    // Check if the expected data structure exists
    if (!data.postgres_cluster || !data.mysql_cluster) {
      throw new Error("Invalid data structure received from server");
    }

    // PostgreSQL Cluster
    const pgStatus = data.postgres_cluster.status;
    const pgItem = document.createElement("div");
    pgItem.className = "cluster-status-card";
    pgItem.innerHTML = `
        <div class="real-time-status">
            <div>
                <div class="cluster-name">
                    PostgreSQL Cluster
                    <span class="status-indicator ${pgStatus}"></span>
                </div>
                <div class="last-check">Last checked: ${lastRealTimeCheck}</div>
            </div>
            <div class="status-item status-${pgStatus}">
                ${pgStatus.toUpperCase()}
            </div>
        </div>
        <div class="node-status-details">
            <div class="node-status-item">
                <span class="node-name">Master:</span>
                <span class="node-status-badge status-${data.postgres_cluster.master_node.connection_status}">
                    ${data.postgres_cluster.master_node.connection_status.toUpperCase()}
                </span>
            </div>
            <div class="node-status-item">
                <span class="node-name">Slave1:</span>
                <span class="node-status-badge status-${data.postgres_cluster.slave1_node.connection_status}">
                    ${data.postgres_cluster.slave1_node.connection_status.toUpperCase()}
                </span>
            </div>
            <div class="node-status-item">
                <span class="node-name">Slave2:</span>
                <span class="node-status-badge status-${data.postgres_cluster.slave2_node.connection_status}">
                    ${data.postgres_cluster.slave2_node.connection_status.toUpperCase()}
                </span>
            </div>
        </div>
    `;
    liveStatusContainer.appendChild(pgItem);

    // MySQL Cluster
    const mysqlStatus = data.mysql_cluster.status;
    const mysqlItem = document.createElement("div");
    mysqlItem.className = "cluster-status-card";
    mysqlItem.style.marginTop = "15px";
        mysqlItem.innerHTML = `
        <div class="real-time-status">
            <div>
                <div class="cluster-name">
                    MySQL Cluster
                    <span class="status-indicator ${mysqlStatus}"></span>
                </div>
                <div class="last-check">Last checked: ${lastRealTimeCheck}</div>
            </div>
            <div class="status-item status-${mysqlStatus}">
                ${mysqlStatus.toUpperCase()}
            </div>
        </div>
        <div class="node-status-details">
            <div class="node-status-item">
                <span class="node-name">Master:</span>
                <span class="node-status-badge status-${data.mysql_cluster.master_node.connection_status}">${data.mysql_cluster.master_node.connection_status.toUpperCase()}</span>
            </div>
            <div class="node-status-item">
                <span class="node-name">Slave1:</span>
                <span class="node-status-badge status-${data.mysql_cluster.slave1_node.connection_status}">${data.mysql_cluster.slave1_node.connection_status.toUpperCase()}</span>
            </div>
            <div class="node-status-item">
                <span class="node-name">Slave2:</span>
                <span class="node-status-badge status-${data.mysql_cluster.slave2_node.connection_status}">${data.mysql_cluster.slave2_node.connection_status.toUpperCase()}</span>
            </div>
        </div>
    `;

    liveStatusContainer.appendChild(mysqlItem);

    document.getElementById("realTimeStatusLoading").style.display = "none";
    document.getElementById("realTimeStatus").style.display = "block";
  } catch (error) {
    console.error("Error checking real-time status:", error);
    const liveStatusContainer = document.getElementById("liveClusterStatus");
    liveStatusContainer.innerHTML = `
                    <div class="connection-error">
                        <h3>Connection Error</h3>
                        <p>Unable to check live cluster status</p>
                        <small>Check if the monitoring backend is running</small>
                    </div>
                `;
    document.getElementById("realTimeStatusLoading").style.display = "none";
    document.getElementById("realTimeStatus").style.display = "block";
  }
}

async function loadHistoricalData() {
  const timeRange = document.getElementById("timeRange").value;

  await Promise.all([
    loadClusterStatus(),
    loadNodeStatus(timeRange),
    loadClusterTrend(timeRange),
    loadReplicationLag(timeRange),
    loadConnectionTimeline(timeRange),
    loadHistoricalEvents(timeRange),
  ]);
}

async function loadClusterStatus() {
  try {
    document.getElementById("clusterStatusLoading").style.display = "flex";
    document.getElementById("clusterStatus").style.display = "none";

    const response = await fetch("/api/cluster-summary");
    const data = await response.json();

    const statusGrid = document.getElementById("clusterStatusGrid");
    statusGrid.innerHTML = "";

    if (data.clusters && data.clusters.length > 0) {
      data.clusters.forEach((cluster) => {
        const statusClass = `status-${cluster.status}`;
        const item = document.createElement("div");
        item.className = `status-item ${statusClass}`;
        item.innerHTML = `
                            <h3>${cluster.db_type.toUpperCase()} (Historical)</h3>
                            <div style="font-size: 1.2rem; font-weight: bold;">${cluster.status.toUpperCase()}</div>
                            <div style="font-size: 0.9rem; margin-top: 8px;">
                                Master: ${cluster.master_status}<br>
                                Slave1: ${cluster.slave1_status}<br>
                                Slave2: ${cluster.slave2_status}
                            </div>
                            <div style="font-size: 0.8rem; margin-top: 8px; opacity: 0.8;">
                                Last recorded: ${cluster.timestamp}
                            </div>
                        `;
        statusGrid.appendChild(item);
      });
    } else {
      const message =
        data.message || data.error || "No historical data available";
      statusGrid.innerHTML = `
                        <div class="status-item" style="background: #f8f9fa; color: #666;">
                            <h3>No Historical Data</h3>
                            <p>${message}</p>
                        </div>
                    `;
    }

    document.getElementById("clusterStatusLoading").style.display = "none";
    document.getElementById("clusterStatus").style.display = "block";
  } catch (error) {
    console.error("Error loading historical cluster status:", error);
    const statusGrid = document.getElementById("clusterStatusGrid");
    statusGrid.innerHTML = `
                    <div class="connection-error">
                        <h3>Error Loading Historical Data</h3>
                        <p>Unable to load historical cluster status</p>
                    </div>
                `;
    document.getElementById("clusterStatusLoading").style.display = "none";
    document.getElementById("clusterStatus").style.display = "block";
  }
}

async function loadNodeStatus(timeRange) {
  try {
    document.getElementById("nodeStatusLoading").style.display = "flex";
    document.getElementById("nodeStatus").style.display = "none";

    const response = await fetch(`/api/node-status?range=${timeRange}`);
    const data = await response.json();

    const nodeList = document.getElementById("nodeStatusList");
    nodeList.innerHTML = "";

    if (data.nodes && data.nodes.length > 0) {
      data.nodes.forEach((node) => {
        const statusClass =
          node.current_status === "up" ? "status-up" : "status-down";
        const item = document.createElement("div");
        item.className = "node-status";
        item.innerHTML = `
                            <div class="node-info">
                                <h4>${node.db_type.toUpperCase()} ${
          node.role
        }</h4>
                                <small>Avg Uptime: ${
                                  node.uptime_percentage
                                }% | Total Checks: ${node.total_checks}</small>
                                <div class="uptime-bar">
                                    <div class="uptime-fill" style="width: ${
                                      node.uptime_percentage
                                    }%"></div>
                                </div>
                                <small>Range: ${timeRange}</small>
                            </div>
                            <div class="status-item ${statusClass}" style="margin: 0; min-width: 80px;">
                                ${node.current_status.toUpperCase()}
                            </div>
                        `;
        nodeList.appendChild(item);
      });
    } else {
      nodeList.innerHTML =
        '<div style="text-align: center; color: #666;">No node statistics available for selected range</div>';
    }

    document.getElementById("nodeStatusLoading").style.display = "none";
    document.getElementById("nodeStatus").style.display = "block";
  } catch (error) {
    console.error("Error loading node status:", error);
    document.getElementById("nodeStatusList").innerHTML =
      '<div class="connection-error">Error loading node statistics</div>';
    document.getElementById("nodeStatusLoading").style.display = "none";
    document.getElementById("nodeStatus").style.display = "block";
  }
}

async function loadClusterTrend(timeRange) {
  try {
    const response = await fetch(`/api/cluster-trend?range=${timeRange}`);
    const data = await response.json();

    const ctx = document.getElementById("clusterTrendChart").getContext("2d");

    if (charts.clusterTrend) {
      charts.clusterTrend.destroy();
    }

    const datasets = [];
    const colors = {
      postgres: {
        healthy: "#4CAF50",
        degraded: "#FF9800",
        critical: "#f44336",
      },
      mysql: { healthy: "#2196F3", degraded: "#FF5722", critical: "#9C27B0" },
    };

    if (data.trends && Object.keys(data.trends).length > 0) {
      Object.keys(data.trends).forEach((dbType) => {
        const trends = data.trends[dbType];
        const statusCounts = {};

        trends.forEach((trend) => {
          if (!statusCounts[trend.status]) {
            statusCounts[trend.status] = 0;
          }
          statusCounts[trend.status] += trend.count;
        });

        Object.keys(statusCounts).forEach((status) => {
          datasets.push({
            label: `${dbType.toUpperCase()} ${status}`,
            data: [statusCounts[status]],
            backgroundColor: colors[dbType]
              ? colors[dbType][status] || "#666"
              : "#666",
            borderColor: colors[dbType]
              ? colors[dbType][status] || "#666"
              : "#666",
            borderWidth: 2,
          });
        });
      });
    }

    if (datasets.length === 0) {
      datasets.push({
        label: "No Data",
        data: [1],
        backgroundColor: "#e0e0e0",
        borderColor: "#ccc",
        borderWidth: 1,
      });
    }

    charts.clusterTrend = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: datasets.map((d) => d.label),
        datasets: [
          {
            data: datasets.map((d) => d.data[0]),
            backgroundColor: datasets.map((d) => d.backgroundColor),
            borderColor: datasets.map((d) => d.borderColor),
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
          title: {
            display: true,
            text: `Historical Status Distribution (${timeRange})`,
          },
        },
      },
    });
  } catch (error) {
    console.error("Error loading cluster trend:", error);
  }
}

async function loadReplicationLag(timeRange) {
  try {
    const response = await fetch(`/api/replication-lag?range=${timeRange}`);
    const data = await response.json();

    const ctx = document.getElementById("replicationLagChart").getContext("2d");

    if (charts.replicationLag) {
      charts.replicationLag.destroy();
    }

    const datasets = [];
    const groupedData = {};

    if (data.replication_lag && data.replication_lag.length > 0) {
      data.replication_lag.forEach((item) => {
        const key = `${item.db_type}_${item.role}`;
        if (!groupedData[key]) {
          groupedData[key] = [];
        }
        groupedData[key].push({
          x: item.timestamp,
          y: item.lag_seconds,
        });
      });
    }

    const colors = [
      "#f44336",
      "#2196F3",
      "#4CAF50",
      "#FF9800",
      "#9C27B0",
      "#607D8B",
    ];
    let colorIndex = 0;

    Object.keys(groupedData).forEach((key) => {
      datasets.push({
        label: key.replace("_", " ").toUpperCase(),
        data: groupedData[key],
        borderColor: colors[colorIndex % colors.length],
        backgroundColor: colors[colorIndex % colors.length] + "20",
        fill: false,
        tension: 0.1,
      });
      colorIndex++;
    });

    if (datasets.length === 0) {
      datasets.push({
        label: "No Data",
        data: [],
        borderColor: "#ccc",
        backgroundColor: "#e0e0e0",
        fill: false,
      });
    }

    charts.replicationLag = new Chart(ctx, {
      type: "line",
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: "time",
            time: {
              parser: "YYYY-MM-DD HH:mm:ss",
            },
            title: {
              display: true,
              text: "Time",
            },
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Lag (seconds)",
            },
          },
        },
        plugins: {
          legend: {
            position: "bottom",
          },
          title: {
            display: true,
            text: "Replication Lag Over Time",
          },
        },
      },
    });
  } catch (error) {
    console.error("Error loading replication lag:", error);
  }
}

async function loadConnectionTimeline(timeRange) {
  try {
    const response = await fetch(`/api/connection-timeline?range=${timeRange}`);
    const data = await response.json();

    const ctx = document
      .getElementById("connectionTimelineChart")
      .getContext("2d");

    if (charts.connectionTimeline) {
      charts.connectionTimeline.destroy();
    }

    const datasets = [];
    const colors = {
      postgres_master: "#1976D2",
      postgres_slave1: "#42A5F5",
      postgres_slave2: "#90CAF9",
      mysql_master: "#388E3C",
      mysql_slave1: "#66BB6A",
      mysql_slave2: "#A5D6A7",
    };

    if (data.timeline && Object.keys(data.timeline).length > 0) {
      Object.keys(data.timeline).forEach((nodeKey) => {
        const nodeData = data.timeline[nodeKey];
        const chartData = nodeData.map((item) => ({
          x: item.timestamp,
          y: item.status === "up" ? 1 : 0,
        }));

        datasets.push({
          label: nodeKey.replace("_", " ").toUpperCase(),
          data: chartData,
          borderColor: colors[nodeKey] || "#666",
          backgroundColor: (colors[nodeKey] || "#666") + "40",
          stepped: true,
          fill: false,
          tension: 0,
        });
      });
    }

    if (datasets.length === 0) {
      datasets.push({
        label: "No Data",
        data: [],
        borderColor: "#ccc",
        backgroundColor: "#e0e0e0",
        stepped: true,
        fill: false,
      });
    }

    charts.connectionTimeline = new Chart(ctx, {
      type: "line",
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: "time",
            time: {
              parser: "YYYY-MM-DD HH:mm:ss",
            },
            title: {
              display: true,
              text: "Time",
            },
          },
          y: {
            min: -0.1,
            max: 1.1,
            ticks: {
              callback: function (value) {
                return value === 1 ? "UP" : value === 0 ? "DOWN" : "";
              },
            },
            title: {
              display: true,
              text: "Connection Status",
            },
          },
        },
        plugins: {
          legend: {
            position: "bottom",
          },
          title: {
            display: true,
            text: "Connection Status Timeline",
          },
        },
      },
    });
  } catch (error) {
    console.error("Error loading connection timeline:", error);
  }
}

async function loadHistoricalEvents(timeRange) {
  try {
    document.getElementById("eventsLoading").style.display = "flex";
    document.getElementById("historicalEvents").style.display = "none";

    const response = await fetch(`/api/historical-events?range=${timeRange}`);
    const data = await response.json();

    const eventsList = document.getElementById("eventsList");
    eventsList.innerHTML = "";

    if (data.events && data.events.length > 0) {
      data.events.forEach((event) => {
        const item = document.createElement("div");
        item.className = `event-item event-${event.severity}`;
        item.innerHTML = `
                            <div class="event-time">${event.timestamp}</div>
                            <div class="event-description">${event.event}</div>
                        `;
        eventsList.appendChild(item);
      });
    } else {
      const message =
        data.message || "No events found in the selected time range.";
      eventsList.innerHTML = `<div class="event-item">${message}</div>`;
    }

    document.getElementById("eventsLoading").style.display = "none";
    document.getElementById("historicalEvents").style.display = "block";
  } catch (error) {
    console.error("Error loading historical events:", error);
    document.getElementById("eventsList").innerHTML =
      '<div class="connection-error">Error loading events</div>';
    document.getElementById("eventsLoading").style.display = "none";
    document.getElementById("historicalEvents").style.display = "block";
  }
}

function refreshDashboard() {
  showRefreshIndicator();
  checkRealTimeStatus();
  loadHistoricalData();
}

function showRefreshIndicator() {
  const indicator = document.getElementById("refreshIndicator");
  indicator.classList.add("show");
  setTimeout(() => {
    indicator.classList.remove("show");
  }, 2000);
}

function toggleAutoRefresh() {
  const statusSpan = document.getElementById("autoRefreshStatus");

  if (isAutoRefreshEnabled) {
    clearInterval(autoRefreshInterval);
    isAutoRefreshEnabled = false;
    statusSpan.textContent = "OFF";
  } else {
    autoRefreshInterval = setInterval(() => {
      refreshDashboard();
    }, 30000); // Refresh every 30 seconds
    isAutoRefreshEnabled = true;
    statusSpan.textContent = "ON (30s)";
  }
}

// Cleanup on page unload
window.addEventListener("beforeunload", function () {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval);
  }

  Object.values(charts).forEach((chart) => {
    if (chart) chart.destroy();
  });
});
