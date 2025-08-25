// Configuration
// Direct API endpoint for deployment
const API_BASE_URL = 'https://bee-monitoring.duckdns.org/api/v1';
const DETECTIONS_ENDPOINT = `${API_BASE_URL}/detections`;

// Global variables
let chart = null;
let allDetections = [];

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    setupDatePicker();
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
                borderColor: '#F4E09C',
                backgroundColor: 'rgba(244, 224, 156, 0.2)',
                borderWidth: 1,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#F4E09C',
                pointBorderColor: '#E8DCC6',
                pointRadius: 1,
                pointHoverBackgroundColor: '#E8DCC6',
                pointHoverBorderColor: '#F4E09C'
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
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x'
                    },
                    pan: {
                        enabled: true,
                        mode: 'x'
                    }
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
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const selectedDetection = chart._sortedDetections[index];
                    if (selectedDetection) {
                        showDetectionImage(selectedDetection);
                    }
                }
            }
        }
    });
}

// Setup date picker
function setupDatePicker() {
    const dateSelect = document.getElementById('dateSelect');
    
    // Don't set a default date - let user choose
    // dateSelect.value = '';
    
    // Add event listener for date changes
    dateSelect.addEventListener('change', function() {
        applyFilters();
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
        setLatestDate(); // Automatically set to latest date when data loads
        
        showLoading(false);
        console.log(`Loaded ${allDetections.length} detections successfully`);
        
    } catch (error) {
        console.error('Error loading detections:', error);
        
        // Use fallback mock data if everything fails
        const mockData = [
            {"timestamp": "2025-08-20 17:37:02", "coverage": 8.798, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:08", "coverage": 7.732, "hiveId": "1"},
            {"timestamp": "2025-08-20 17:37:12", "coverage": 8.244, "hiveId": "1"},
            {"timestamp": "2025-08-19 17:37:18", "coverage": 7.753, "hiveId": "1"},
            {"timestamp": "2025-08-19 17:37:22", "coverage": 8.288, "hiveId": "1"},
            {"timestamp": "2025-08-19 17:37:26", "coverage": 5.524, "hiveId": "2"},
            {"timestamp": "2025-08-18 17:37:30", "coverage": 5.892, "hiveId": "2"},
            {"timestamp": "2025-08-18 17:37:34", "coverage": 11.685, "hiveId": "2"},
            {"timestamp": "2025-08-18 17:37:39", "coverage": 7.972, "hiveId": "1"},
            {"timestamp": "2025-08-17 17:37:43", "coverage": 7.591, "hiveId": "1"}
        ];
        
        allDetections = mockData;
        updateHiveSelector(allDetections);
        setLatestDate(); // Automatically set to latest date for mock data too
        
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
        applyFilters();
    });
}

// Apply both hive and date filters
function applyFilters() {
    const hiveSelect = document.getElementById('hiveSelect');
    const dateSelect = document.getElementById('dateSelect');
    
    const selectedHive = hiveSelect.value;
    const selectedDate = dateSelect.value;
    
    let filteredData = allDetections;
    
    // Filter by hive
    if (selectedHive) {
        filteredData = filteredData.filter(d => d.hiveId === selectedHive);
    }
    
    // Filter by date
    if (selectedDate) {
        filteredData = filteredData.filter(d => {
            const detectionDate = new Date(d.timestamp).toISOString().split('T')[0];
            return detectionDate === selectedDate;
        });
    }
    
    updateChart(filteredData);
    updateStats(filteredData);
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
    const sortedDetections = detections.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    chart._sortedDetections = sortedDetections;
    
    // Prepare chart data
    const labels = sortedDetections.map(d => formatTime(new Date(d.timestamp)));
    const coverageData = sortedDetections.map(d => d.coverage || 0);
    
    // Update chart
    chart.data.labels = labels;
    chart.data.datasets[0].data = coverageData;
    
    // Update chart title based on selected hive and date
    const hiveSelect = document.getElementById('hiveSelect');
    const dateSelect = document.getElementById('dateSelect');
    const selectedHive = hiveSelect.value;
    const selectedDate = dateSelect.value;
    
    let title = 'Bee Detection Over Time';
    if (selectedHive && selectedDate) {
        title = `Bee Detection - Hive ${selectedHive} - ${formatDateForTitle(selectedDate)}`;
    } else if (selectedHive) {
        title = `Bee Detection - Hive ${selectedHive}`;
    } else if (selectedDate) {
        title = `Bee Detection - ${formatDateForTitle(selectedDate)}`;
    } else {
        title = 'Bee Detection Over Time - All Data';
    }
    
    chart.options.plugins.title.text = title;
    
    chart.update();
}

function showDetectionImage(detection) {
    const imageContainer = document.getElementById('imageContainer');
    const imageElement = document.getElementById('detectionImage');

    const imageUrl = `${API_BASE_URL}/detections/image/${detection.id}`;

    imageElement.src = imageUrl;
    imageContainer.style.display = 'block';
}

// Utility function to format date
function formatDate(date) {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Utility function to format time for chart labels
function formatTime(date) {
    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Utility function to format date for chart title
function formatDateForTitle(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Set date to today
function setToday() {
    const dateSelect = document.getElementById('dateSelect');
    const today = new Date();
    dateSelect.value = today.toISOString().split('T')[0];
    applyFilters();
}

// Set date to the latest date available in the database
function setLatestDate() {
    if (allDetections.length === 0) {
        console.warn('No data available to find latest date');
        return;
    }
    
    // Find the most recent timestamp in the data
    const latestTimestamp = allDetections.reduce((latest, detection) => {
        const detectionDate = new Date(detection.timestamp);
        return detectionDate > latest ? detectionDate : latest;
    }, new Date(allDetections[0].timestamp));
    
    const dateSelect = document.getElementById('dateSelect');
    dateSelect.value = latestTimestamp.toISOString().split('T')[0];
    applyFilters();
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
