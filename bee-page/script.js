const API_BASE_URL = 'https://bee-monitoring.duckdns.org/api/v1';
const DETECTIONS_ENDPOINT = `${API_BASE_URL}/detections`;

let chart = null;
let allDetections = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    setupDatePicker();
    loadDetections();
});

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

function setupDatePicker() {
    const dateSelect = document.getElementById('dateSelect');
    dateSelect.addEventListener('change', function() {
        applyFilters();
    });
}

async function loadDetections() {
    try {
        closeDetectionImage();
        showLoading(true);
        hideError();
        
        const response = await fetch(DETECTIONS_ENDPOINT);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            console.warn('API error:', data.error);
            showError(`API Error: ${data.error}`);
            return;
        }
        
        allDetections = data;
        updateHiveSelector(allDetections);
        setLatestDate();
        
        showLoading(false);
        console.log(`Loaded ${allDetections.length} detections successfully`);
        
    } catch (error) {
        console.error('Error loading detections:', error);
        
        allDetections = [];
        updateHiveSelector(allDetections);
        
        showError(`Failed to load data: ${error.message}`);
        showLoading(false);
    }
}

function updateHiveSelector(detections) {
    const hiveSelect = document.getElementById('hiveSelect');
    const uniqueHives = [...new Set(detections.map(d => d.hiveId))].sort();
    
    hiveSelect.innerHTML = '<option value="">All Hives</option>';
    
    uniqueHives.forEach(hiveId => {
        const option = document.createElement('option');
        option.value = hiveId;
        option.textContent = `Hive ${hiveId}`;
        hiveSelect.appendChild(option);
    });
    
    hiveSelect.addEventListener('change', function() {
        applyFilters();
    });
}

function applyFilters() {
    closeDetectionImage();
    
    const hiveSelect = document.getElementById('hiveSelect');
    const dateSelect = document.getElementById('dateSelect');
    
    const selectedHive = hiveSelect.value;
    const selectedDate = dateSelect.value;
    
    let filteredData = allDetections;
    
    if (selectedHive) {
        filteredData = filteredData.filter(d => d.hiveId === selectedHive);
    }
    
    if (selectedDate) {
        filteredData = filteredData.filter(d => {
            const detectionDate = new Date(d.timestamp).toISOString().split('T')[0];
            return detectionDate === selectedDate;
        });
    }
    
    updateChart(filteredData);
    updateStats(filteredData);
}

function updateStats(detections) {
    console.log('updateStats called with', detections.length, 'detections');
    const statsDiv = document.getElementById('stats');
    
    if (detections.length === 0) {
        console.log('No detections, hiding stats');
        statsDiv.style.display = 'none';
        return;
    }
    
    const totalDetections = detections.length;
    const avgCoverage = detections.reduce((sum, d) => sum + (d.coverage || 0), 0) / totalDetections;
    const allHiveIds = allDetections.map(d => d.hiveId);
    const uniqueHives = allDetections.length > 0 ? 
        new Set(allHiveIds).size : 0;
    console.log('All hive IDs:', allHiveIds);
    console.log('Unique hives:', uniqueHives);
    
    const sortedDetections = detections.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    const lastDetection = sortedDetections.length > 0 ? 
        formatDate(new Date(sortedDetections[0].timestamp)) : 'N/A';
    
    document.getElementById('totalDetections').textContent = totalDetections;
    document.getElementById('avgCoverage').textContent = avgCoverage.toFixed(1) + '%';
    document.getElementById('uniqueHives').textContent = uniqueHives;
    document.getElementById('lastDetection').textContent = lastDetection;
    
    statsDiv.style.display = 'grid';
}

function updateChart(detections) {
    if (!chart) return;
    
    const sortedDetections = detections.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    chart._sortedDetections = Array.from(sortedDetections);
    
    const labels = sortedDetections.map(d => formatTime(new Date(d.timestamp)));
    const coverageData = sortedDetections.map(d => d.coverage || 0);
    
    chart.data.labels = labels;
    chart.data.datasets[0].data = coverageData;
    
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

    const applyTransform = function() {
        if (imageElement.naturalHeight > imageElement.naturalWidth) {
            imageElement.style.transform = 'rotate(90deg)';
            imageElement.style.width = '70vh';
            imageElement.style.height = 'auto';
            imageElement.style.maxWidth = '70vh';
            imageElement.style.maxHeight = '90vw';
        } else {
            imageElement.style.transform = 'none';
            imageElement.style.width = 'auto';
            imageElement.style.height = 'auto';
            imageElement.style.maxWidth = '100%';
            imageElement.style.maxHeight = '70vh';
        }
    };
    
    imageElement.onload = applyTransform;
    imageElement.src = imageUrl;
    
    if (imageElement.complete && imageElement.naturalHeight > 0) {
        applyTransform();
    }
    
    imageContainer.style.display = 'block';
}

function closeDetectionImage() {
    const imageContainer = document.getElementById('imageContainer');
    if (imageContainer) {
        imageContainer.style.display = 'none';
    }
}

function formatDate(date) {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatTime(date) {
    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function formatDateForTitle(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function setToday() {
    const dateSelect = document.getElementById('dateSelect');
    const today = new Date();
    dateSelect.value = today.toISOString().split('T')[0];
    applyFilters();
}

function setLatestDate() {
    if (allDetections.length === 0) {
        console.warn('No data available to find latest date');
        return;
    }
    
    const hiveSelect = document.getElementById('hiveSelect');
    const selectedHive = hiveSelect.value;
    
    let filteredDetections = allDetections;
    if (selectedHive) {
        filteredDetections = allDetections.filter(d => d.hiveId === selectedHive);
    }
    
    if (filteredDetections.length === 0) {
        console.warn('No data available for selected hive');
        return;
    }
    
    const latestTimestamp = filteredDetections.reduce((latest, detection) => {
        const detectionDate = new Date(detection.timestamp);
        return detectionDate > latest ? detectionDate : latest;
    }, new Date(filteredDetections[0].timestamp));
    
    const dateSelect = document.getElementById('dateSelect');
    dateSelect.value = latestTimestamp.toISOString().split('T')[0];
    applyFilters();
}

function showLoading(show) {
    const loadingDiv = document.getElementById('loading');
    loadingDiv.style.display = show ? 'block' : 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    const errorDiv = document.getElementById('error');
    errorDiv.style.display = 'none';
}

function refreshData() {
    closeDetectionImage();
    loadDetections();
}

setInterval(refreshData, 5 * 60 * 1000);
