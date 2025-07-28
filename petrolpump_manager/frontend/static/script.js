// Global variables
let accuracyChart, lossChart;
let updateInterval;
const API_BASE_URL = '/api';

// DOM Elements
const startButton = document.getElementById('startTraining');
const stopButton = document.getElementById('stopTraining');
const statusDiv = document.getElementById('status');
const statusText = document.getElementById('statusText');
const numRoundsInput = document.getElementById('numRounds');
const numClientsInput = document.getElementById('numClients');

// Initialize the application when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait a small amount of time to ensure all elements are available
    setTimeout(() => {
        try {
            initializeCharts();
            setupEventListeners();
            // Start polling for updates
            updateInterval = setInterval(fetchAndUpdateData, 3000);
            // Initial data fetch
            fetchAndUpdateData();
        } catch (error) {
            console.error('Error initializing application:', error);
        }
    }, 100);
});

// Set up event listeners
function setupEventListeners() {
    startButton.addEventListener('click', startTraining);
    stopButton.addEventListener('click', stopTraining);
}

// Initialize Chart.js charts
function initializeCharts() {
    const accuracyCtx = document.getElementById('accuracyChart').getContext('2d');
    const lossCtx = document.getElementById('lossChart').getContext('2d');
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                max: 1.0
            }
        },
        animation: {
            duration: 1000
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    };

    accuracyChart = new Chart(accuracyCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Accuracy',
                data: [],
                borderColor: 'rgba(59, 130, 246, 1)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    max: 1.0
                }
            }
        }
    });

    lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Loss',
                data: [],
                borderColor: 'rgba(239, 68, 68, 1)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: chartOptions
    });
}

// Start training process
async function startTraining() {
    const numRounds = parseInt(numRoundsInput.value);
    const numClients = parseInt(numClientsInput.value);
    
    if (isNaN(numRounds) || numRounds < 1) {
        alert('Please enter a valid number of rounds (minimum 1)');
        return;
    }
    
    if (isNaN(numClients) || numClients < 1) {
        alert('Please enter a valid number of clients (minimum 1)');
        return;
    }
    
    try {
        // Update UI
        startButton.disabled = true;
        stopButton.classList.remove('hidden');
        statusDiv.classList.remove('hidden', 'bg-red-100', 'text-red-700');
        statusDiv.classList.add('bg-blue-100', 'text-blue-700');
        statusText.textContent = 'Starting training...';
        
        // Send request to start training
        const response = await fetch(`${API_BASE_URL}/train`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                num_rounds: numRounds,
                num_clients: numClients
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to start training');
        }
        
        const data = await response.json();
        console.log('Training started:', data);
        
        // Update status
        statusText.textContent = `Training in progress (${numRounds} rounds, ${numClients} clients)`;
        
    } catch (error) {
        console.error('Error starting training:', error);
        statusDiv.classList.remove('bg-blue-100', 'text-blue-700');
        statusDiv.classList.add('bg-red-100', 'text-red-700');
        statusText.textContent = `Error: ${error.message}`;
        startButton.disabled = false;
        stopButton.classList.add('hidden');
    }
}

// Stop training process
async function stopTraining() {
    try {
        stopButton.disabled = true;
        statusText.textContent = 'Stopping training...';
        
        const response = await fetch(`${API_BASE_URL}/stop`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to stop training');
        }
        
        const data = await response.json();
        console.log('Training stopped:', data);
        
        // Reset UI
        resetTrainingUI();
        
    } catch (error) {
        console.error('Error stopping training:', error);
        statusDiv.classList.remove('bg-blue-100', 'text-blue-700');
        statusDiv.classList.add('bg-red-100', 'text-red-700');
        statusText.textContent = `Error: ${error.message}`;
        stopButton.disabled = false;
    }
}

// Reset training UI
function resetTrainingUI() {
    startButton.disabled = false;
    stopButton.disabled = false;
    stopButton.classList.add('hidden');
    statusDiv.classList.remove('bg-blue-100', 'text-blue-700');
    statusDiv.classList.add('bg-green-100', 'text-green-700');
    statusText.textContent = 'Training completed successfully';
    
    // Hide status after 5 seconds
    setTimeout(() => {
        statusDiv.classList.add('hidden');
    }, 5000);
}

// Show loading state
function setLoading(isLoading) {
    const loadingElements = document.querySelectorAll('.loading-state');
    loadingElements.forEach(el => {
        if (isLoading) {
            el.classList.remove('hidden');
            el.innerHTML = '<div class="loading"></div> Loading...';
        } else {
            el.classList.add('hidden');
        }
    });
}

// Show error message in UI
function showError(message) {
    console.error('UI Error:', message);
    const errorDiv = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    if (errorDiv && errorText) {
        errorText.textContent = message;
        errorDiv.classList.remove('hidden');
    }
}

// Hide error message
function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.classList.add('hidden');
    }
}

// Fetch data from API and update UI
async function fetchAndUpdateData() {
    let ledgerData = [];
    let blockchainData = [];
    
    try {
        console.log('Fetching data from API...');
        setLoading(true);
        hideError();
        
        // Update Flower status (don't block on this)
        updateFlowerStatus().catch(error => {
            console.error('Error in Flower status update:', error);
        });
        
        // Fetch ledger data
        try {
            const startTime = performance.now();
            const ledgerResponse = await fetch(`${API_BASE_URL}/ledger`);
            const requestTime = performance.now() - startTime;
            
            if (!ledgerResponse.ok) {
                const errorText = await ledgerResponse.text().catch(() => 'No error details');
                console.error(`Ledger API error (${requestTime.toFixed(1)}ms): ${ledgerResponse.status} ${ledgerResponse.statusText}`, errorText);
                throw new Error(`Failed to fetch ledger: ${ledgerResponse.status} ${ledgerResponse.statusText}`);
            }
            
            ledgerData = await ledgerResponse.json();
            console.log(`Ledger data received (${requestTime.toFixed(1)}ms):`, ledgerData);
        } catch (ledgerError) {
            console.error('Error fetching ledger:', ledgerError);
            throw new Error(`Failed to load training data: ${ledgerError.message}`);
        }
        
        // Fetch blockchain data
        try {
            const startTime = performance.now();
            const blockchainResponse = await fetch(`${API_BASE_URL}/blockchain`);
            const requestTime = performance.now() - startTime;
            
            if (!blockchainResponse.ok) {
                const errorText = await blockchainResponse.text().catch(() => 'No error details');
                console.error(`Blockchain API error (${requestTime.toFixed(1)}ms): ${blockchainResponse.status} ${blockchainResponse.statusText}`, errorText);
                throw new Error(`Failed to fetch blockchain data: ${blockchainResponse.status} ${blockchainResponse.statusText}`);
            }
            
            blockchainData = await blockchainResponse.json();
            console.log(`Blockchain data received (${requestTime.toFixed(1)}ms):`, blockchainData);
        } catch (blockchainError) {
            console.error('Error fetching blockchain:', blockchainError);
            throw new Error(`Failed to load blockchain data: ${blockchainError.message}`);
        }
        
        // Update charts and tables
        try {
            if (ledgerData && ledgerData.length > 0) {
                updateCharts(ledgerData);
            }
            updateLedgerTable(ledgerData || []);
            updateBlockchainTable(blockchainData || []);
            
            // Hide loading state when everything is done
            setLoading(false);
        } catch (updateError) {
            console.error('Error updating UI:', updateError);
            throw new Error(`Failed to update UI: ${updateError.message}`);
        }
        
        // Update training status (non-critical, so don't let it fail the whole operation)
        try {
            const statusResponse = await fetch(`${API_BASE_URL}/status`);
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                console.log('Status data:', statusData);
                
                if (statusData.training_in_progress) {
                    if (startButton) startButton.disabled = true;
                    if (stopButton) stopButton.classList.remove('hidden');
                    if (statusDiv) statusDiv.classList.remove('hidden');
                    if (statusText) {
                        statusText.textContent = `Training in progress (Round ${ledgerData.length || 1})`;
                    }
                } else if (ledgerData.length > 0) {
                    resetTrainingUI();
                }
            } else {
                console.warn('Failed to fetch status:', statusResponse.status, statusResponse.statusText);
            }
        } catch (statusError) {
            console.warn('Error fetching training status (non-critical):', statusError);
            // Non-critical, continue
        }
        
        // Clear any previous errors if everything succeeded
        hideError();
        
    } catch (error) {
        console.error('Error in fetchAndUpdateData:', error);
        
        // Show error in UI
        showError(`Error: ${error.message}`);
        setLoading(false);
        
        // Try to show any partial data we might have
        try {
            if (ledgerData && ledgerData.length > 0) updateLedgerTable(ledgerData);
            if (blockchainData && blockchainData.length > 0) updateBlockchainTable(blockchainData);
        } catch (e) {
            console.error('Error updating tables with partial data:', e);
        }
    }
}

// Update charts with new data
function updateCharts(ledgerData) {
    if (!ledgerData || ledgerData.length === 0) return;
    
    const labels = ledgerData.map((_, index) => `Round ${index + 1}`);
    const accuracyData = ledgerData.map(entry => entry.accuracy || 0);
    const lossData = ledgerData.map(entry => entry.loss || 0);
    
    // Update accuracy chart
    accuracyChart.data.labels = labels;
    accuracyChart.data.datasets[0].data = accuracyData;
    accuracyChart.update();
    
    // Update loss chart
    lossChart.data.labels = labels;
    lossChart.data.datasets[0].data = lossData;
    lossChart.update();
}

// Format timestamp with relative time
function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    let relativeTime = '';
    if (diffInSeconds < 5) {
        relativeTime = 'Just now';
    } else if (diffInSeconds < 60) {
        relativeTime = `${diffInSeconds} seconds ago`;
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        relativeTime = `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        relativeTime = `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        relativeTime = `${days} day${days > 1 ? 's' : ''} ago`;
    }
    
    return `
        <div class="flex flex-col">
            <span>${date.toLocaleString()}</span>
            <span class="text-xs text-gray-400">${relativeTime}</span>
        </div>`;
}

// Update ledger table
function updateLedgerTable(ledgerData) {
    const tbody = document.getElementById('ledgerBody');
    
    if (!ledgerData || ledgerData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">No training data available</td>
            </tr>`;
        return;
    }
    
    // Sort by timestamp in descending order (newest first)
    const sortedData = [...ledgerData].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
    });
    
    tbody.innerHTML = sortedData.map(entry => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                ${entry.round_num}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${formatTimestamp(entry.timestamp)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${(entry.clients || []).join(', ')}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${entry.accuracy !== null ? (entry.accuracy * 100).toFixed(2) + '%' : 'N/A'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${entry.loss !== null ? parseFloat(entry.loss).toFixed(4) : 'N/A'}
            </td>
        </tr>`
    ).join('');
}

// Update Flower status panel
async function updateFlowerStatus() {
    try {
        // Fetch Flower server status
        const response = await fetch(`${API_BASE_URL}/flower/status`);
        if (!response.ok) throw new Error('Failed to fetch Flower status');
        
        const status = await response.json();
        const statusElement = document.getElementById('flowerStatus');
        const connectedElement = document.getElementById('connectedClients');
        const currentRoundElement = document.getElementById('currentRound');
        const totalRoundsElement = document.getElementById('totalRounds');
        const progressBar = document.getElementById('trainingProgressBar');
        const progressText = document.getElementById('trainingProgressText');
        const statusDetails = document.getElementById('statusDetails');
        
        // Determine status text and color
        let statusText = '';
        let statusColor = 'gray';
        let statusBgColor = 'gray-100';
        let statusTextColor = 'gray-800';
        
        if (status.connected) {
            statusText = `Connected (${status.clients_connected} client${status.clients_connected !== 1 ? 's' : ''})`;
            statusColor = 'green';
            statusBgColor = 'green-100';
            statusTextColor = 'green-800';
        } else if (status.server_running) {
            statusText = 'Server running but not accessible';
            statusColor = 'yellow';
            statusBgColor = 'yellow-100';
            statusTextColor = 'yellow-800';
        } else if (status.training_in_progress) {
            statusText = 'Starting up...';
            statusColor = 'blue';
            statusBgColor = 'blue-100';
            statusTextColor = 'blue-800';
        } else {
            statusText = 'Disconnected';
            statusColor = 'red';
            statusBgColor = 'red-100';
            statusTextColor = 'red-800';
        }
        
        // Update status indicator
        statusElement.innerHTML = `
            <span class="w-2 h-2 mr-1 rounded-full bg-${statusColor}-500"></span>
            ${statusText}
        `;
        statusElement.className = `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${statusBgColor} text-${statusTextColor}`;
        
        // Show status details for debugging
        if (statusDetails) {
            statusDetails.innerHTML = `
                <div class="text-xs text-gray-600 mt-1">
                    Server: ${status.server_running ? 'Running' : 'Stopped'}, 
                    Flower: ${status.flower_accessible ? 'Accessible' : 'Inaccessible'}, 
                    Training: ${status.training_in_progress ? 'In Progress' : 'Idle'}
                </div>
            `;
        }
        
        // Update client connections
        connectedElement.textContent = status.clients_connected || '0';
        
        // Update round information
        currentRoundElement.textContent = status.current_round || '-';
        totalRoundsElement.textContent = status.total_rounds || '-';
        
        // Update progress bar
        if (status.total_rounds > 0) {
            const progress = Math.min(100, Math.round((status.current_round / status.total_rounds) * 100));
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${progress}%`;
            
            // Update progress bar color based on completion
            if (progress >= 100) {
                progressBar.className = 'bg-green-600 h-2.5 rounded-full';
            } else if (progress > 70) {
                progressBar.className = 'bg-blue-600 h-2.5 rounded-full';
            } else if (progress > 30) {
                progressBar.className = 'bg-yellow-500 h-2.5 rounded-full';
            } else {
                progressBar.className = 'bg-red-500 h-2.5 rounded-full';
            }
        } else {
            progressBar.style.width = '0%';
            progressText.textContent = '0%';
        }
        
    } catch (error) {
        console.error('Error updating Flower status:', error);
        const statusElement = document.getElementById('flowerStatus');
        statusElement.innerHTML = `
            <span class="w-2 h-2 mr-1 rounded-full bg-red-500"></span>
            Error: ${error.message}
        `;
        statusElement.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800';
    }
}

// Update blockchain table
function updateBlockchainTable(blockchainData) {
    const tbody = document.getElementById('blockchainBody');
    
    if (!blockchainData || blockchainData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-4 text-center text-gray-500">No blockchain data available</td>
            </tr>`;
        return;
    }
    
    // Sort by timestamp in descending order (newest first)
    const sortedData = [...blockchainData].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
    });
    
    tbody.innerHTML = sortedData.map(block => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                ${block.round_num !== undefined ? block.round_num : 'N/A'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${formatTimestamp(block.timestamp)}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500 font-mono text-xs truncate max-w-xs" title="${block.data_hash || ''}">
                ${block.data_hash ? block.data_hash.substring(0, 16) + '...' : 'N/A'}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500 font-mono text-xs truncate max-w-xs" title="${block.previous_hash || ''}">
                ${block.previous_hash ? (block.previous_hash === '0000000000000000000000000000000000000000000000000000000000000000' ? 'Genesis' : block.previous_hash.substring(0, 16) + '...') : 'N/A'}
            </td>
        </tr>`
    ).join('');
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
