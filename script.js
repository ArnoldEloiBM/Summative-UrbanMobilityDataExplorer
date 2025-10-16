let timeChart = null;      // Chart showing trips by time of day (morning, afternoon, etc.)
let distanceChart = null;  // Chart showing trips by distance category (short, medium, long)

// === UTILITY FUNCTIONS ===
function formatDuration(seconds) {
    // Convert trip duration from seconds to a readable format.
    const minutes = Math.round(seconds / 60);
    return `${minutes} min`;
}

function formatDistance(km) {
    // Format distance with units for display.
    return `${km} km`;
}

function formatCoordinate(coord) {
    // Format GPS coordinates to 4 decimal places.
    return coord ? coord.toFixed(4) : 'N/A';
}

// === DATA DISPLAY FUNCTIONS ===
function updateTable(trips) {
    const tbody = document.querySelector('#trips-table tbody');
    tbody.innerHTML = '';
    trips.slice(0, 50).forEach(trip => {
        const row = document.createElement('tr');
        const pickupDate = new Date(trip.pickup_datetime);
        
        // Fill the row with trip data - each <td> is a table cell
        row.innerHTML = `
            <td>${trip.trip_id.substring(0, 10)}...</td>         <!-- Trip ID (shortened) -->
            <td>${pickupDate.toLocaleString()}</td>               <!-- Pickup time -->
            <td>${Math.round(trip.trip_duration / 60)}</td>       <!-- Duration in minutes -->
            <td>${trip.distance_km}</td>                          <!-- Distance -->
            <td>${trip.speed_kmh}</td>                            <!-- Speed -->
            <td>${trip.passenger_count}</td>                      <!-- Number of passengers -->
            <td>${trip.vendor_id}</td>                            <!-- Taxi company -->
            <td class="time-of-day time-${trip.time_of_day}">${trip.time_of_day}</td>  <!-- Time period with color coding -->
        `;
        tbody.appendChild(row);
    });
}

// === CHART FUNCTIONS ===
// These functions create and update our visual charts using Chart.js library

function updateTimeChart(chartData) {
    if (timeChart) {
        timeChart.destroy();
    }

    const ctx = document.getElementById('time-chart').getContext('2d');
    const colorMap = {
        'morning': '#FFD93D',
        'afternoon': '#FF6B35',
        'evening': '#6A0572',
        'night': '#1A1A1A'
    };

    const backgroundColor = chartData.labels.map(label => colorMap[label] || '#FF6384');

    timeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
            datasets: [{
                label: 'Number of Trips',
                data: chartData.values,
                backgroundColor: backgroundColor,
                borderColor: backgroundColor.map(c => c + '80'),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const trips = context.raw;
                            const avgDuration = chartData.avg_duration ? chartData.avg_duration[index] : 0;
                            const avgDistance = chartData.avg_distance ? chartData.avg_distance[index] : 0;
                            
                            return [
                                `Trips: ${trips}`,
                                `Avg Duration: ${avgDuration} min`,
                                `Avg Distance: ${avgDistance} km`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Trips'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time of Day'
                    }
                }
            }
        }
    });
}

function updateDistanceChart(chartData) {
    if (distanceChart) {
        distanceChart.destroy();
    }

    const ctx = document.getElementById('distance-chart').getContext('2d');
    const colorMap = {
        'short': '#4ECDC4',
        'medium': '#44A08D',
        'long': '#093637'
    };

    const backgroundColor = chartData.labels.map(label => colorMap[label] || '#FF6384');

    distanceChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: chartData.labels.map(l => l.charAt(0).toUpperCase() + l.slice(1) + ' Trips'),
            datasets: [{
                data: chartData.values,
                backgroundColor: backgroundColor,
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const trips = context.raw;
                            const avgSpeed = chartData.avg_speed ? chartData.avg_speed[index] : 0;
                            const percentage = ((trips / chartData.values.reduce((a, b) => a + b, 0)) * 100).toFixed(1);
                            return [
                                `${context.label}: ${trips} trips (${percentage}%)`,
                                `Avg Speed: ${avgSpeed} km/h`
                            ];
                        }
                    }
                }
            }
        }
    });
}

function updateStats(data) {
    document.getElementById('total-count').textContent = data.total_count || 0;
    document.getElementById('avg-duration').textContent = formatDuration((data.avg_duration || 0) * 60);
    document.getElementById('avg-distance').textContent = formatDistance(data.avg_distance || 0);
}

function populateVendorFilter(vendors) {
    const vendorFilter = document.getElementById('filter-vendor');
    const currentValue = vendorFilter.value;
    
    // Clear existing options except the first one
    while (vendorFilter.options.length > 1) {
        vendorFilter.remove(1);
    }
    
    // Add vendor options
    vendors.forEach(vendor => {
        if (vendor) {
            const option = document.createElement('option');
            option.value = vendor;
            option.textContent = `Vendor ${vendor}`;
            vendorFilter.appendChild(option);
        }
    });

    // Restore previous selection if it still exists
    if (currentValue && vendors.includes(currentValue)) {
        vendorFilter.value = currentValue;
    }
}

function generateInsights(data) {
    const insights = [];
    
    // Insight 1: Enhanced Peak Activity Analysis
    if (data.time_chart_data && data.time_chart_data.labels.length > 0) {
        const maxIndex = data.time_chart_data.values.indexOf(Math.max(...data.time_chart_data.values));
        const minIndex = data.time_chart_data.values.indexOf(Math.min(...data.time_chart_data.values));
        const peakTime = data.time_chart_data.labels[maxIndex];
        const quietTime = data.time_chart_data.labels[minIndex];
        const peakTrips = data.time_chart_data.values[maxIndex];
        const quietTrips = data.time_chart_data.values[minIndex];
        const peakRatio = (peakTrips / quietTrips).toFixed(1);
        
        insights.push(`🕐 <strong>Urban Mobility Peak:</strong> ${peakTime} shows ${peakRatio}x more taxi activity than ${quietTime}, with ${peakTrips} trips (${((peakTrips/data.total_count)*100).toFixed(1)}% of daily volume). This indicates concentrated demand during commuter periods.`);
    }
    
    // Insight 2: Enhanced Distance & Urban Planning Analysis
    if (data.distance_chart_data && data.distance_chart_data.labels.length > 0) {
        const totalTrips = data.distance_chart_data.values.reduce((a, b) => a + b, 0);
        const shortIdx = data.distance_chart_data.labels.indexOf('short');
        const mediumIdx = data.distance_chart_data.labels.indexOf('medium');
        const longIdx = data.distance_chart_data.labels.indexOf('long');
        
        const shortTrips = data.distance_chart_data.values[shortIdx] || 0;
        const mediumTrips = data.distance_chart_data.values[mediumIdx] || 0;
        const longTrips = data.distance_chart_data.values[longIdx] || 0;
        
        const shortPercentage = ((shortTrips / totalTrips) * 100).toFixed(1);
        const mediumPercentage = ((mediumTrips / totalTrips) * 100).toFixed(1);
        
        if (shortTrips > mediumTrips + longTrips) {
            insights.push(`🏙️ <strong>Neighborhood Mobility:</strong> ${shortPercentage}% are local trips (<2km), suggesting taxis serve as vital "last-mile" connectors in dense urban areas. This indicates strong walkability challenges or weather-dependent transportation needs.`);
        } else {
            insights.push(`🌉 <strong>Cross-Borough Movement:</strong> ${mediumPercentage}% are medium-distance trips (2-10km), indicating significant cross-neighborhood mobility patterns typical of metropolitan commuting.`);
        }
    }
    
    // Insight 3: Enhanced Traffic & Efficiency Analysis
    if (data.distance_chart_data && data.distance_chart_data.avg_speed) {
        const speeds = data.distance_chart_data.avg_speed;
        const labels = data.distance_chart_data.labels;
        const avgSpeed = (speeds.reduce((a, b) => a + b, 0) / speeds.length).toFixed(1);
        
        const maxSpeedIdx = speeds.indexOf(Math.max(...speeds));
        const minSpeedIdx = speeds.indexOf(Math.min(...speeds));
        const fastestCategory = labels[maxSpeedIdx];
        const slowestCategory = labels[minSpeedIdx];
        const speedRange = (Math.max(...speeds) - Math.min(...speeds)).toFixed(1);
        
        if (avgSpeed < 15) {
            insights.push(`🚦 <strong>Congestion Impact:</strong> Average speed of ${avgSpeed} km/h indicates severe urban congestion. ${fastestCategory} trips average ${speeds[maxSpeedIdx].toFixed(1)} km/h while ${slowestCategory} trips only ${speeds[minSpeedIdx].toFixed(1)} km/h - a ${speedRange} km/h difference suggesting traffic management challenges.`);
        } else {
            insights.push(`⚡ <strong>Traffic Flow:</strong> Average speed of ${avgSpeed} km/h shows moderate traffic conditions. Speed variation of ${speedRange} km/h between trip types reflects NYC's diverse traffic patterns from local streets to highway segments.`);
        }
    }
    
    // Insight 4: Economic and Environmental Implications
    if (data.time_chart_data && data.time_chart_data.avg_duration) {
        const durations = data.time_chart_data.avg_duration;
        const avgDuration = (durations.reduce((a, b) => a + b, 0) / durations.length).toFixed(1);
        const totalTripHours = (data.total_count * avgDuration / 60).toFixed(0);
        
        insights.push(`💼 <strong>Urban Efficiency:</strong> With ${totalTripHours} total trip-hours and average ${avgDuration}-minute journeys, this represents significant urban mobility demand. Optimization could reduce city-wide travel time and environmental impact.`);
    }
    
    // Insight 5: Transit System Integration Analysis
    if (data.distance_chart_data && data.time_chart_data) {
        const shortTrips = data.distance_chart_data.values[data.distance_chart_data.labels.indexOf('short')] || 0;
        const totalTrips = data.total_count;
        const shortRatio = (shortTrips / totalTrips * 100).toFixed(1);
        
        if (shortRatio > 70) {
            insights.push(`🚇 <strong>Transit Integration:</strong> High proportion of short trips (${shortRatio}%) suggests taxis complement public transit as last-mile solutions. This indicates potential for integrated transportation planning to reduce congestion.`);
        }
    }
    
    return insights.slice(0, 3); // Return top 3 most relevant insights
}

function updateInsights(data) {
    const insights = generateInsights(data);
    const insightsContainer = document.getElementById('insights');
    
    if (insights.length > 0) {
        insightsContainer.innerHTML = insights.map(insight => `<div class="insight-item">${insight}</div>`).join('');
    } else {
        insightsContainer.innerHTML = '<p>No insights available for current filter selection.</p>';
    }
}

// DATA FETCHING FUNCTIONS

async function fetchData() {
    try {
        // Get the current filter values from the dropdown menus
        const timeOfDay = document.getElementById('filter-time').value;
        const vendorId = document.getElementById('filter-vendor').value;
        const distanceCategory = document.getElementById('filter-distance').value;
        const limit = document.getElementById('limit-trips').value;
        
        // Show loading indicator while we wait for data
        document.body.classList.add('loading');
        
        // Build the URL parameters to send to our server
        const params = new URLSearchParams({
            time_of_day: timeOfDay,
            vendor_id: vendorId,
            distance_category: distanceCategory,
            limit: limit
        });
        
        // Make the request to our Python server's /data endpoint
        const response = await fetch(`/data?${params}`);
        
        // Check if the request was successful
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Convert the response to JSON format
        const data = await response.json();
        if (data.error) {
            console.error('Server error:', data.error);
            return;
        }
        
        // Check if the server sent us an error message
        if (data.error) {
            console.error('Server error:', data.error);
            return;
        }
        
        // Update all parts of our dashboard with the new data
        updateTable(data.trips || []);
        updateTimeChart(data.time_chart_data || {labels: [], values: []});
        updateDistanceChart(data.distance_chart_data || {labels: [], values: []});
        updateStats(data);
        updateInsights(data);
        
        // Update the vendor dropdown with available taxi companies
        if (data.vendors && data.vendors.length > 0) {
            populateVendorFilter(data.vendors);
        }
        
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('insights').innerHTML = '<p class="error">Error loading data. Please try again.</p>';
    } finally {
        document.body.classList.remove('loading');
    }
}

async function fetchStats() {
    // This function gets overall statistics about our dataset.
    // It runs once when the page loads to show the date range of our data.
    try {
        const response = await fetch('/stats');
        if (response.ok) {
            const stats = await response.json();
            if (stats.earliest_trip && stats.latest_trip) {
                const earliest = new Date(stats.earliest_trip).toLocaleDateString();
                const latest = new Date(stats.latest_trip).toLocaleDateString();
                document.getElementById('date-range').textContent = `${earliest} - ${latest}`;
            }
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
        document.getElementById('date-range').textContent = 'Date range unavailable';
    }
}

// PERFORMANCE OPTIMIZATION

function debounce(func, wait) {
    // Debouncing delays function execution until after a pause in calls.
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Create a debounced version of fetchData (waits 500ms after user stops changing filters)
const debouncedFetchData = debounce(fetchData, 500);

// EVENT LISTENERS
document.getElementById('filter-time').addEventListener('change', debouncedFetchData);
document.getElementById('filter-vendor').addEventListener('change', debouncedFetchData);
document.getElementById('filter-distance').addEventListener('change', debouncedFetchData);
document.getElementById('limit-trips').addEventListener('input', debouncedFetchData);

// INITIALIZATION
console.log('NYC Taxi Dashboard - JavaScript loaded successfully');
console.log('Original implementation by: Gedeon Ntigibesh');
fetchData();
fetchStats();
