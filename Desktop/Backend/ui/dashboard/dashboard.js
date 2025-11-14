/**
 * Miktos StreamLab Dashboard - JavaScript
 * Week 9-10 Implementation
 */

// Configuration
const API_BASE_URL = 'http://localhost:8765';
const WS_URL = 'ws://localhost:8765/ws';

// State
let ws = null;
let reconnectInterval = null;
let charts = {};
let metricsHistory = {
    bitrate: [],
    fps: [],
    cpu: [],
    drops: []
};

// Theme
let currentTheme = 'dark';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initializing...');
    initializeTheme();
    initializeWebSocket();
    initializeCharts();
    attachEventListeners();
    loadAlertSettings();
});

// Theme Functions
function initializeTheme() {
    // Load theme from localStorage
    const saved = localStorage.getItem('miktos-theme');
    currentTheme = saved || 'dark';
    applyTheme(currentTheme);
    
    // Add theme toggle listener
    document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
}

function applyTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update toggle button emoji
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
        toggleBtn.title = `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`;
    }
    
    // Save to localStorage
    localStorage.setItem('miktos-theme', theme);
}

function toggleTheme() {
    applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
}

// WebSocket Connection
function initializeWebSocket() {
    console.log('Connecting to WebSocket...');
    
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
        clearInterval(reconnectInterval);
        reconnectInterval = null;
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        
        // Attempt reconnection
        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                initializeWebSocket();
            }, 5000);
        }
    };
}

// Update dashboard with new data
function updateDashboard(data) {
    updateLastUpdate();
    updateStreamStatus(data);
    updateFailoverStatus(data);
    updateHealthStatus(data);
    updateMetrics(data);
    updateCharts(data);
}

// Update connection status badge
function updateConnectionStatus(connected) {
    const badge = document.getElementById('connection-status');
    if (connected) {
        badge.textContent = 'Connected';
        badge.className = 'status-badge connected';
    } else {
        badge.textContent = 'Disconnected';
        badge.className = 'status-badge disconnected';
    }
}

// Update stream status
function updateStreamStatus(data) {
    const statusBadge = document.getElementById('stream-status');
    const indicator = document.getElementById('streaming-indicator');
    const text = document.getElementById('streaming-text');
    const uptime = document.getElementById('uptime-text');
    
    if (data.streaming) {
        statusBadge.textContent = 'Streaming';
        statusBadge.className = 'status-badge streaming';
        indicator.className = 'indicator healthy';
        text.textContent = 'Live';
        
        // Format uptime
        if (data.uptime_seconds) {
            const hours = Math.floor(data.uptime_seconds / 3600);
            const minutes = Math.floor((data.uptime_seconds % 3600) / 60);
            uptime.textContent = `Uptime: ${hours}h ${minutes}m`;
        }
    } else {
        statusBadge.textContent = 'Stopped';
        statusBadge.className = 'status-badge stopped';
        indicator.className = 'indicator unknown';
        text.textContent = 'Not Streaming';
        uptime.textContent = 'Uptime: --';
    }
}

// Update failover status
function updateFailoverStatus(data) {
    const indicator = document.getElementById('failover-indicator');
    const text = document.getElementById('failover-text');
    const detail = document.getElementById('failover-detail');
    
    const state = data.failover_state || 'normal';
    
    if (state === 'normal') {
        indicator.className = 'indicator healthy';
        text.textContent = 'Normal';
        detail.textContent = 'Primary connection active';
    } else if (state === 'failover') {
        indicator.className = 'indicator warning';
        text.textContent = 'Failover Active';
        detail.textContent = 'Running on backup connection';
    } else if (state === 'recovering') {
        indicator.className = 'indicator warning';
        text.textContent = 'Recovering';
        detail.textContent = 'Switching back to primary';
    } else {
        indicator.className = 'indicator unknown';
        text.textContent = 'Unknown';
        detail.textContent = '--';
    }
}

// Update overall health status
function updateHealthStatus(data) {
    const indicator = document.getElementById('health-indicator');
    const text = document.getElementById('health-text');
    const issuesDiv = document.getElementById('health-issues');
    
    const status = data.status || 'unknown';
    
    if (status === 'healthy') {
        indicator.className = 'indicator healthy';
        text.textContent = 'Healthy';
    } else if (status === 'warning') {
        indicator.className = 'indicator warning';
        text.textContent = 'Warning';
    } else if (status === 'critical') {
        indicator.className = 'indicator critical';
        text.textContent = 'Critical';
    } else {
        indicator.className = 'indicator unknown';
        text.textContent = 'Unknown';
    }
    
    // Display issues
    const issues = data.issues || [];
    if (issues.length > 0) {
        issuesDiv.innerHTML = issues.map(issue => `<div>• ${issue}</div>`).join('');
    } else {
        issuesDiv.textContent = 'No issues';
    }
}

// Update metrics
function updateMetrics(data) {
    const metrics = data.metrics || {};
    
    // Bitrate
    updateMetricCard('bitrate', metrics.bitrate_kbps || 0, 'kbps');
    
    // FPS
    updateMetricCard('fps', metrics.fps || 0, 'fps');
    
    // Drop Rate
    updateMetricCard('drop', metrics.drop_percentage || 0, '%');
    
    // CPU
    updateMetricCard('cpu', metrics.cpu_usage || 0, '%');
    
    // Check alert thresholds
    checkAlerts(metrics);
}

// Update individual metric card
function updateMetricCard(name, value, unit) {
    const valueEl = document.getElementById(`${name}-value`);
    const avgEl = document.getElementById(`${name}-avg`);
    
    if (valueEl) {
        valueEl.textContent = value.toFixed(1);
    }
    
    // Update history for averaging
    if (!metricsHistory[name]) {
        metricsHistory[name] = [];
    }
    metricsHistory[name].push(value);
    
    // Keep last 60 samples (1 minute at 1s intervals)
    if (metricsHistory[name].length > 60) {
        metricsHistory[name].shift();
    }
    
    // Calculate average
    if (avgEl && metricsHistory[name].length > 0) {
        const avg = metricsHistory[name].reduce((a, b) => a + b, 0) / metricsHistory[name].length;
        avgEl.textContent = avg.toFixed(1);
    }
}

// Initialize Chart.js charts
function initializeCharts() {
    // Bitrate & FPS Chart
    const bitrateCtx = document.getElementById('bitrate-chart');
    if (bitrateCtx) {
        charts.bitrate = new Chart(bitrateCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Bitrate (kbps)',
                        data: [],
                        borderColor: '#4a9eff',
                        backgroundColor: 'rgba(74, 158, 255, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'FPS',
                        data: [],
                        borderColor: '#4caf50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#e0e0e0'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#b0b0b0' },
                        grid: { color: '#3a3a3a' }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        ticks: { color: '#4a9eff' },
                        grid: { color: '#3a3a3a' }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        ticks: { color: '#4caf50' },
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
    // CPU & Drop Rate Chart
    const systemCtx = document.getElementById('system-chart');
    if (systemCtx) {
        charts.system = new Chart(systemCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU (%)',
                        data: [],
                        borderColor: '#ff9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Drop Rate (%)',
                        data: [],
                        borderColor: '#f44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#e0e0e0'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#b0b0b0' },
                        grid: { color: '#3a3a3a' }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        ticks: { color: '#ff9800' },
                        grid: { color: '#3a3a3a' }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        ticks: { color: '#f44336' },
                        grid: { display: false }
                    }
                }
            }
        });
    }
}

// Update charts with new data
function updateCharts(data) {
    const metrics = data.metrics || {};
    const now = new Date().toLocaleTimeString();
    
    // Update bitrate chart
    if (charts.bitrate) {
        charts.bitrate.data.labels.push(now);
        charts.bitrate.data.datasets[0].data.push(metrics.bitrate_kbps || 0);
        charts.bitrate.data.datasets[1].data.push(metrics.fps || 0);
        
        // Keep last 60 data points (1 minute)
        if (charts.bitrate.data.labels.length > 60) {
            charts.bitrate.data.labels.shift();
            charts.bitrate.data.datasets[0].data.shift();
            charts.bitrate.data.datasets[1].data.shift();
        }
        
        charts.bitrate.update('none'); // Update without animation for performance
    }
    
    // Update system chart
    if (charts.system) {
        charts.system.data.labels.push(now);
        charts.system.data.datasets[0].data.push(metrics.cpu_usage || 0);
        charts.system.data.datasets[1].data.push(metrics.drop_percentage || 0);
        
        // Keep last 60 data points
        if (charts.system.data.labels.length > 60) {
            charts.system.data.labels.shift();
            charts.system.data.datasets[0].data.shift();
            charts.system.data.datasets[1].data.shift();
        }
        
        charts.system.update('none');
    }
}

// Update last update timestamp
function updateLastUpdate() {
    const lastUpdate = document.getElementById('last-update');
    if (lastUpdate) {
        lastUpdate.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
    }
}

// Attach event listeners to action buttons
function attachEventListeners() {
    // Export CSV
    document.getElementById('export-csv')?.addEventListener('click', () => {
        exportData('csv');
    });
    
    // Export JSON
    document.getElementById('export-json')?.addEventListener('click', () => {
        exportData('json');
    });
    
    // Export HTML Report
    document.getElementById('export-html')?.addEventListener('click', () => {
        exportData('html');
    });
    
    // Configure Alerts
    document.getElementById('config-alerts')?.addEventListener('click', () => {
        showAlertModal();
    });
    
    // Modal close buttons
    document.getElementById('close-modal')?.addEventListener('click', () => {
        hideAlertModal();
    });
    
    document.getElementById('cancel-alerts')?.addEventListener('click', () => {
        hideAlertModal();
    });
    
    document.getElementById('save-alerts')?.addEventListener('click', () => {
        saveAlertSettings();
    });
    
    // Click outside modal to close
    document.getElementById('alert-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'alert-modal') {
            hideAlertModal();
        }
    });
}

// Export data in various formats
async function exportData(format) {
    try {
        if (format === 'html') {
            // Open HTML report in new tab
            window.open(`${API_BASE_URL}/export/html`, '_blank');
        } else {
            const response = await fetch(`${API_BASE_URL}/metrics`);
            const data = await response.json();
            
            if (format === 'json') {
                downloadJSON(data, 'miktos-metrics.json');
            } else if (format === 'csv') {
                downloadCSV(data, 'miktos-metrics.csv');
            }
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Failed to export data. Check console for details.');
    }
}

// Download JSON file
function downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadBlob(blob, filename);
}

// Download CSV file
function downloadCSV(data, filename) {
    let csv = 'Metric,Current,Average,Min,Max,Trend\n';
    
    for (const [name, metric] of Object.entries(data)) {
        const minMax = metric.min_max || [null, null];
        csv += `${name},${metric.current || 'N/A'},${metric.average || 'N/A'},${minMax[0] || 'N/A'},${minMax[1] || 'N/A'},${metric.trend || 'N/A'}\n`;
    }
    
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, filename);
}

// Download blob as file
function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Alert Modal Functions
const alertSettings = {
    cpu_threshold: 75,
    bitrate_threshold: 2000,
    drop_threshold: 1.0,
    fps_threshold: 25,
    enabled: true
};

// Load alert settings from localStorage
function loadAlertSettings() {
    const saved = localStorage.getItem('miktos-alert-settings');
    if (saved) {
        Object.assign(alertSettings, JSON.parse(saved));
    }
    updateAlertInputs();
}

// Update modal inputs with current settings
function updateAlertInputs() {
    document.getElementById('cpu-threshold').value = alertSettings.cpu_threshold;
    document.getElementById('bitrate-threshold').value = alertSettings.bitrate_threshold;
    document.getElementById('drop-threshold').value = alertSettings.drop_threshold;
    document.getElementById('fps-threshold').value = alertSettings.fps_threshold;
    document.getElementById('alert-enabled').checked = alertSettings.enabled;
}

// Show alert configuration modal
function showAlertModal() {
    loadAlertSettings();
    document.getElementById('alert-modal').classList.remove('hidden');
}

// Hide alert configuration modal
function hideAlertModal() {
    document.getElementById('alert-modal').classList.add('hidden');
}

// Save alert settings
function saveAlertSettings() {
    alertSettings.cpu_threshold = parseFloat(document.getElementById('cpu-threshold').value);
    alertSettings.bitrate_threshold = parseFloat(document.getElementById('bitrate-threshold').value);
    alertSettings.drop_threshold = parseFloat(document.getElementById('drop-threshold').value);
    alertSettings.fps_threshold = parseFloat(document.getElementById('fps-threshold').value);
    alertSettings.enabled = document.getElementById('alert-enabled').checked;
    
    // Save to localStorage
    localStorage.setItem('miktos-alert-settings', JSON.stringify(alertSettings));
    
    hideAlertModal();
    console.log('Alert settings saved:', alertSettings);
}

// Check if current metrics exceed thresholds
function checkAlerts(metrics) {
    if (!alertSettings.enabled) return;
    
    const alerts = [];
    
    if (metrics.cpu_usage > alertSettings.cpu_threshold) {
        alerts.push(`CPU usage (${metrics.cpu_usage.toFixed(1)}%) exceeds threshold (${alertSettings.cpu_threshold}%)`);
    }
    
    if (metrics.bitrate_kbps < alertSettings.bitrate_threshold) {
        alerts.push(`Bitrate (${metrics.bitrate_kbps.toFixed(1)} kbps) below threshold (${alertSettings.bitrate_threshold} kbps)`);
    }
    
    if (metrics.drop_percentage > alertSettings.drop_threshold) {
        alerts.push(`Drop rate (${metrics.drop_percentage.toFixed(1)}%) exceeds threshold (${alertSettings.drop_threshold}%)`);
    }
    
    if (metrics.fps < alertSettings.fps_threshold) {
        alerts.push(`FPS (${metrics.fps.toFixed(1)}) below threshold (${alertSettings.fps_threshold})`);
    }
    
    // Show visual indicators (could add browser notifications here)
    if (alerts.length > 0) {
        console.warn('Alerts triggered:', alerts);
        // Could flash the health indicator or show a notification banner
    }
}
