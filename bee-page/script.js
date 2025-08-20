// Configuration
// Use local proxy server to avoid CORS issues with the external API
const API_BASE_URL = '/api/v1';
const DETECTIONS_ENDPOINT = `${API_BASE_URL}/detections`;

// Global variables
let chart = null;
let allDetections = [];

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    loadDetections();
});

// Initialize the chart
function initializeChart() {
    const ctx = document.getElementById('beeChart').getContext('2d');
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Bee Coverage (%)',
                data: [],
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Bee Detection Over Time'
                },
                legend: {
                    display: true
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Coverage (%)'
                    },
                    beginAtZero: true,
                    max: 100
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Load detections from API
async function loadDetections() {
    try {
        showLoading(true);
        hideError();
        
        const response = await fetch(DETECTIONS_ENDPOINT);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Check if this is an error response from proxy
        if (data.error) {
            console.warn('API error:', data.error);
            showError(`API Error: ${data.error}`);
            return;
        }
        
        allDetections = data;
        updateHiveSelector(allDetections);
        updateStats(allDetections);
        updateChart(allDetections);
        
        showLoading(false);
        console.log(`Loaded ${allDetections.length} detections successfully`);
        
    } catch (error) {
        console.error('Error loading detections:', error);
        
        // Use fallback mock data if everything fails
        const mockData = [
            {"timestamp": "2025-08-20 17:37:02", "coverage": 8.798, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:08", "coverage": 7.732, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:12", "coverage": 8.244, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:18", "coverage": 7.753, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:22", "coverage": 8.288, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:26", "coverage": 5.524, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:30", "coverage": 5.892, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:34", "coverage": 11.685, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:39", "coverage": 7.972, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:43", "coverage": 7.591, "hiveId": "1"}
        ];
        
        allDetections = mockData;
        updateHiveSelector(allDetections);
        updateStats(allDetections);
        updateChart(allDetections);
        
        showError(`Failed to load data: ${error.message}. Showing sample data.`);
        showLoading(false);
    }
}

// Update hive selector dropdown
function updateHiveSelector(detections) {
    const hiveSelect = document.getElementById('hiveSelect');
    const uniqueHives = [...new Set(detections.map(d => d.hiveId))].sort();
    
    // Clear existing options except "All Hives"
    hiveSelect.innerHTML = '<option value="">All Hives</option>';
    
    uniqueHives.forEach(hiveId => {
        const option = document.createElement('option');
        option.value = hiveId;
        option.textContent = `Hive ${hiveId}`;
        hiveSelect.appendChild(option);
    });
    
    // Add event listener for hive selection
    hiveSelect.addEventListener('change', function() {
        const selectedHive = this.value;
        const filteredData = selectedHive ? 
            allDetections.filter(d => d.hiveId === selectedHive) : 
            allDetections;
        
        updateChart(filteredData);
        updateStats(filteredData);
    });
}

// Update statistics
function updateStats(detections) {
    const statsDiv = document.getElementById('stats');
    
    if (detections.length === 0) {
        statsDiv.style.display = 'none';
        return;
    }
    
    // Calculate statistics
    const totalDetections = detections.length;
    const avgCoverage = detections.reduce((sum, d) => sum + (d.coverage || 0), 0) / totalDetections;
    const uniqueHives = new Set(detections.map(d => d.hiveId)).size;
    
    // Find latest detection
    const sortedDetections = detections.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    const lastDetection = sortedDetections.length > 0 ? 
        formatDate(new Date(sortedDetections[0].timestamp)) : 'N/A';
    
    // Update DOM
    document.getElementById('totalDetections').textContent = totalDetections;
    document.getElementById('avgCoverage').textContent = avgCoverage.toFixed(1) + '%';
    document.getElementById('uniqueHives').textContent = uniqueHives;
    document.getElementById('lastDetection').textContent = lastDetection;
    
    statsDiv.style.display = 'grid';
}

// Update chart with new data
function updateChart(detections) {
    if (!chart) return;
    
    // Sort by timestamp
    const sortedDetections = detections.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    // Prepare chart data
    const labels = sortedDetections.map(d => formatTime(new Date(d.timestamp)));
    const coverageData = sortedDetections.map(d => d.coverage || 0);
    
    // Update chart
    chart.data.labels = labels;
    chart.data.datasets[0].data = coverageData;
    
    // Update chart title based on selected hive
    const hiveSelect = document.getElementById('hiveSelect');
    const selectedHive = hiveSelect.value;
    chart.options.plugins.title.text = selectedHive ? 
        `Bee Detection Over Time - Hive ${selectedHive}` : 
        'Bee Detection Over Time - All Hives';
    
    chart.update();
}

// Utility function to format date
function formatDate(date) {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Utility function to format time for chart labels
function formatTime(date) {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Show/hide loading indicator
function showLoading(show) {
    const loadingDiv = document.getElementById('loading');
    loadingDiv.style.display = show ? 'block' : 'none';
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

// Hide error message
function hideError() {
    const errorDiv = document.getElementById('error');
    errorDiv.style.display = 'none';
}

// Refresh data function
function refreshData() {
    loadDetections();
}

// Auto-refresh every 5 minutes
setInterval(refreshData, 5 * 60 * 1000);
