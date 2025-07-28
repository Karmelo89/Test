// Solar Monitor Dashboard JavaScript

class SolarMonitor {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.powerData = [];
        this.voltageData = [];
        this.currentData = [];
        this.tempData = [];
        this.timeLabels = [];
        this.maxDataPoints = 20;
        
        this.init();
    }

    init() {
        this.initializeSocket();
        this.initializeCharts();
        this.setupEventHandlers();
    }

    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });

        this.socket.on('solar_update', (data) => {
            this.updateDashboard(data);
            this.updateCharts(data);
        });
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('connectionStatus');
        
        if (connected) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Disconnected';
        }
    }

    updateDashboard(data) {
        // Update status cards
        document.getElementById('powerValue').textContent = `${data.power.toLocaleString()} W`;
        document.getElementById('voltageValue').textContent = `${data.voltage} V`;
        document.getElementById('currentValue').textContent = `${data.current.toFixed(1)} A`;
        document.getElementById('tempValue').textContent = `${data.temperature}°C`;
        document.getElementById('efficiencyValue').textContent = `${data.efficiency}%`;
        document.getElementById('energyValue').textContent = `${data.daily_energy.toLocaleString()} Wh`;

        // Update system status
        const statusBadge = document.getElementById('systemStatus');
        statusBadge.textContent = data.status;
        statusBadge.className = 'status-badge';
        
        switch (data.status.toLowerCase()) {
            case 'normal':
                statusBadge.classList.add('normal');
                break;
            case 'low output':
            case 'low efficiency':
            case 'high temperature':
                statusBadge.classList.add('warning');
                break;
            default:
                statusBadge.classList.add('error');
        }

        // Update last update time
        const lastUpdate = new Date(data.timestamp).toLocaleTimeString();
        document.getElementById('lastUpdate').textContent = lastUpdate;

        // Add smooth number animations
        this.animateValue('powerValue', data.power);
        this.animateValue('voltageValue', data.voltage);
        this.animateValue('currentValue', data.current);
        this.animateValue('tempValue', data.temperature);
    }

    animateValue(elementId, newValue) {
        const element = document.getElementById(elementId);
        const currentText = element.textContent;
        const currentValue = parseFloat(currentText.replace(/[^\d.-]/g, ''));
        
        if (isNaN(currentValue)) return;
        
        const increment = (newValue - currentValue) / 10;
        let current = currentValue;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= newValue) || (increment < 0 && current <= newValue)) {
                current = newValue;
                clearInterval(timer);
            }
            
            const unit = currentText.match(/[^\d.-]+$/)?.[0] || '';
            element.textContent = `${current.toFixed(1)}${unit}`;
        }, 50);
    }

    updateCharts(data) {
        const now = new Date();
        const timeLabel = now.toLocaleTimeString();

        // Add new data point
        this.powerData.push(data.power);
        this.voltageData.push(data.voltage);
        this.currentData.push(data.current);
        this.tempData.push(data.temperature);
        this.timeLabels.push(timeLabel);

        // Remove old data points
        if (this.powerData.length > this.maxDataPoints) {
            this.powerData.shift();
            this.voltageData.shift();
            this.currentData.shift();
            this.tempData.shift();
            this.timeLabels.shift();
        }

        // Update charts
        this.updatePowerChart();
        this.updateParametersChart();
    }

    initializeCharts() {
        // Power Generation Chart
        const powerCtx = document.getElementById('powerChart').getContext('2d');
        this.charts.power = new Chart(powerCtx, {
            type: 'line',
            data: {
                labels: this.timeLabels,
                datasets: [{
                    label: 'Power (W)',
                    data: this.powerData,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + ' W';
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `Power: ${context.parsed.y.toLocaleString()} W`;
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        });

        // System Parameters Chart
        const parametersCtx = document.getElementById('parametersChart').getContext('2d');
        this.charts.parameters = new Chart(parametersCtx, {
            type: 'line',
            data: {
                labels: this.timeLabels,
                datasets: [
                    {
                        label: 'Voltage (V)',
                        data: this.voltageData,
                        borderColor: '#9b59b6',
                        backgroundColor: 'rgba(155, 89, 182, 0.1)',
                        yAxisID: 'y',
                        tension: 0.4,
                        pointRadius: 3
                    },
                    {
                        label: 'Current (A)',
                        data: this.currentData,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        yAxisID: 'y1',
                        tension: 0.4,
                        pointRadius: 3
                    },
                    {
                        label: 'Temperature (°C)',
                        data: this.tempData,
                        borderColor: '#f39c12',
                        backgroundColor: 'rgba(243, 156, 18, 0.1)',
                        yAxisID: 'y2',
                        tension: 0.4,
                        pointRadius: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Voltage (V)'
                        },
                        grid: {
                            color: 'rgba(155, 89, 182, 0.2)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Current (A)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    },
                    y2: {
                        type: 'linear',
                        display: false,
                        position: 'right',
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label;
                                const value = context.parsed.y;
                                if (label.includes('Voltage')) {
                                    return `${label}: ${value.toFixed(1)} V`;
                                } else if (label.includes('Current')) {
                                    return `${label}: ${value.toFixed(1)} A`;
                                } else if (label.includes('Temperature')) {
                                    return `${label}: ${value.toFixed(1)} °C`;
                                }
                                return `${label}: ${value}`;
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    updatePowerChart() {
        this.charts.power.data.labels = [...this.timeLabels];
        this.charts.power.data.datasets[0].data = [...this.powerData];
        this.charts.power.update('none');
    }

    updateParametersChart() {
        this.charts.parameters.data.labels = [...this.timeLabels];
        this.charts.parameters.data.datasets[0].data = [...this.voltageData];
        this.charts.parameters.data.datasets[1].data = [...this.currentData];
        this.charts.parameters.data.datasets[2].data = [...this.tempData];
        this.charts.parameters.update('none');
    }

    setupEventHandlers() {
        // Handle window resize
        window.addEventListener('resize', () => {
            Object.values(this.charts).forEach(chart => {
                chart.resize();
            });
        });

        // Handle page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page is hidden, reduce update frequency or pause
                console.log('Page hidden - reducing updates');
            } else {
                // Page is visible, resume normal updates
                console.log('Page visible - resuming updates');
            }
        });
    }

    // Method to fetch historical data on page load
    async loadHistoricalData() {
        try {
            const response = await fetch('/api/historical');
            const data = await response.json();
            
            if (data && data.length > 0) {
                // Process historical data for charts
                data.slice(-this.maxDataPoints).forEach(point => {
                    const time = new Date(point.timestamp).toLocaleTimeString();
                    this.powerData.push(point.power);
                    this.voltageData.push(point.voltage);
                    this.currentData.push(point.current);
                    this.tempData.push(point.temperature);
                    this.timeLabels.push(time);
                });
                
                this.updatePowerChart();
                this.updateParametersChart();
            }
        } catch (error) {
            console.error('Error loading historical data:', error);
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const monitor = new SolarMonitor();
    monitor.loadHistoricalData();
    
    // Add some visual flair
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        }, index * 100);
    });
});