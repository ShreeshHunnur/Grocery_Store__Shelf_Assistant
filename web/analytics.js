/**
 * ShelfSense AI Analytics Dashboard
 * Interactive dashboard for comprehensive analytics and insights
 */

class AnalyticsDashboard {
    constructor() {
        this.currentTimeRange = 30;
        this.charts = {};
        this.data = {};
        this.refreshInterval = null;
        this.apiBase = '/api/v1/analytics';
        
        this.init();
    }
    
    init() {
        console.log('🚀 Analytics Dashboard initializing...');
        this.setupEventListeners();
        this.loadInitialData();
        this.startAutoRefresh();
        console.log('✅ Analytics Dashboard ready!');
    }
    
    setupEventListeners() {
        // Time range filter
        document.getElementById('time-range').addEventListener('change', (e) => {
            this.currentTimeRange = parseInt(e.target.value);
            this.loadDashboardData();
        });
        
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadDashboardData(true);
        });
        
        // Export button
        document.getElementById('export-btn').addEventListener('click', () => {
            this.showExportModal();
        });
        
        // Chart controls
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chartType = e.target.dataset.chart;
                this.switchTrendsChart(chartType);
                
                // Update active state
                e.target.parentElement.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
        
        // Table controls
        document.getElementById('products-search').addEventListener('input', (e) => {
            this.filterProductsTable(e.target.value);
        });
        
        document.getElementById('activity-filter').addEventListener('change', (e) => {
            this.filterActivitiesTable(e.target.value);
        });
        
        document.getElementById('activities-refresh').addEventListener('click', () => {
            this.loadRecentActivities();
        });
        
        // Export modal
        document.getElementById('close-export-modal').addEventListener('click', () => {
            this.hideExportModal();
        });
        
        document.getElementById('cancel-export').addEventListener('click', () => {
            this.hideExportModal();
        });
        
        document.getElementById('confirm-export').addEventListener('click', () => {
            this.exportData();
        });
        
        // Error toast
        document.getElementById('close-error').addEventListener('click', () => {
            this.hideError();
        });
    }
    
    async loadInitialData() {
        this.showLoading();
        try {
            await Promise.all([
                this.loadDashboardData(),
                this.checkSystemHealth()
            ]);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadDashboardData(forceRefresh = false) {
        try {
            if (forceRefresh) {
                document.getElementById('refresh-btn').querySelector('i').classList.add('fa-spin');
            }
            
            const response = await fetch(`${this.apiBase}/dashboard?days=${this.currentTimeRange}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            this.data = result.data;
            
            // Update all dashboard components
            this.updateOverviewMetrics();
            this.updateCharts();
            this.updateTables();
            this.updateLastUpdated();
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to refresh dashboard data');
        } finally {
            if (forceRefresh) {
                document.getElementById('refresh-btn').querySelector('i').classList.remove('fa-spin');
            }
        }
    }
    
    updateOverviewMetrics() {
        const overview = this.data.overview || {};
        
        // Update metric values
        this.updateMetricValue('total-queries', overview.total_queries || 0);
        this.updateMetricValue('active-sessions', overview.unique_sessions || 0);
        this.updateMetricValue('avg-response-time', `${(overview.avg_response_time || 0).toFixed(1)}ms`);
        this.updateMetricValue('success-rate', `${(overview.success_rate || 0).toFixed(1)}%`);
        this.updateMetricValue('avg-confidence', `${(overview.avg_confidence || 0).toFixed(1)}%`);
        
        // Update top product
        const popularProducts = this.data.popular_products || [];
        const topProduct = popularProducts[0];
        if (topProduct) {
            this.updateMetricValue('top-product', topProduct.normalized_product);
            document.getElementById('top-product-count').textContent = `${topProduct.search_count} searches`;
        } else {
            this.updateMetricValue('top-product', 'No data');
            document.getElementById('top-product-count').textContent = '';
        }
        
        // Update change indicators (mock data for now)
        this.updateChangeIndicator('queries-change', 12.5, true);
        this.updateChangeIndicator('sessions-change', -2.1, false);
        this.updateChangeIndicator('response-time-change', -8.3, true);
        this.updateChangeIndicator('success-rate-change', 1.2, true);
        this.updateChangeIndicator('confidence-change', 3.7, true);
    }
    
    updateMetricValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateChangeIndicator(elementId, change, isPositive) {
        const element = document.getElementById(elementId);
        if (element) {
            const icon = isPositive ? '↗' : '↘';
            element.textContent = `${icon} ${Math.abs(change)}%`;
            element.className = `metric-change ${isPositive ? 'positive' : 'negative'}`;
        }
    }
    
    updateCharts() {
        this.updateTrendsChart();
        this.updateInputMethodsChart();
        this.updateQueryTypesChart();
        this.updatePeakHoursChart();
        this.updateResponseTimeDistributionChart();
    }
    
    updateTrendsChart() {
        const ctx = document.getElementById('trends-chart').getContext('2d');
        const trends = this.data.query_trends || [];
        
        if (this.charts.trends) {
            this.charts.trends.destroy();
        }
        
        const labels = trends.map(t => new Date(t.date).toLocaleDateString());
        const data = trends.map(t => t.total_queries);
        
        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Total Queries',
                    data: data,
                    borderColor: '#6366F1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#6366F1',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#6366F1',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#E5E7EB',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: '#E5E7EB',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    updateInputMethodsChart() {
        const ctx = document.getElementById('input-methods-chart').getContext('2d');
        const inputMethods = this.data.input_methods || [];
        
        if (this.charts.inputMethods) {
            this.charts.inputMethods.destroy();
        }
        
        const colors = {
            voice: '#6366F1',
            text: '#10B981',
            vision: '#F59E0B'
        };
        
        this.charts.inputMethods = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: inputMethods.map(im => im.input_method.charAt(0).toUpperCase() + im.input_method.slice(1)),
                datasets: [{
                    data: inputMethods.map(im => im.count),
                    backgroundColor: inputMethods.map(im => colors[im.input_method] || '#6B7280'),
                    borderWidth: 0,
                    cutout: '60%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const percentage = inputMethods[context.dataIndex]?.percentage || 0;
                                return `${context.label}: ${context.parsed} (${percentage.toFixed(1)}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Update legend
        this.updateChartLegend('input-methods-legend', inputMethods.map(im => ({
            label: im.input_method.charAt(0).toUpperCase() + im.input_method.slice(1),
            color: colors[im.input_method] || '#6B7280',
            value: `${im.count} (${(im.percentage || 0).toFixed(1)}%)`
        })));
    }
    
    updateQueryTypesChart() {
        const ctx = document.getElementById('query-types-chart').getContext('2d');
        
        // Calculate query type distribution from success rates data
        const successRates = this.data.success_rates?.by_query_type || [];
        
        if (this.charts.queryTypes) {
            this.charts.queryTypes.destroy();
        }
        
        const colors = {
            location: '#6366F1',
            information: '#10B981',
            general: '#F59E0B'
        };
        
        this.charts.queryTypes = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: successRates.map(qt => qt.query_type.charAt(0).toUpperCase() + qt.query_type.slice(1)),
                datasets: [{
                    data: successRates.map(qt => qt.total),
                    backgroundColor: successRates.map(qt => colors[qt.query_type] || '#6B7280'),
                    borderWidth: 0,
                    cutout: '60%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = successRates.reduce((sum, qt) => sum + qt.total, 0);
                                const percentage = total > 0 ? (context.parsed / total * 100) : 0;
                                return `${context.label}: ${context.parsed} (${percentage.toFixed(1)}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Update legend
        const total = successRates.reduce((sum, qt) => sum + qt.total, 0);
        this.updateChartLegend('query-types-legend', successRates.map(qt => ({
            label: qt.query_type.charAt(0).toUpperCase() + qt.query_type.slice(1),
            color: colors[qt.query_type] || '#6B7280',
            value: `${qt.total} (${total > 0 ? (qt.total / total * 100).toFixed(1) : 0}%)`
        })));
    }
    
    updatePeakHoursChart() {
        const ctx = document.getElementById('peak-hours-chart').getContext('2d');
        const peakHours = this.data.peak_hours || [];
        
        if (this.charts.peakHours) {
            this.charts.peakHours.destroy();
        }
        
        // Fill missing hours with 0
        const hourlyData = new Array(24).fill(0);
        peakHours.forEach(ph => {
            hourlyData[ph.hour] = ph.query_count;
        });
        
        this.charts.peakHours = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                datasets: [{
                    label: 'Queries',
                    data: hourlyData,
                    backgroundColor: hourlyData.map((count, hour) => {
                        // Highlight business hours (9-17) with different color
                        return hour >= 9 && hour <= 17 ? '#6366F1' : '#D1D5DB';
                    }),
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 10
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: '#E5E7EB',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateResponseTimeDistributionChart() {
        const ctx = document.getElementById('response-time-dist-chart').getContext('2d');
        const distribution = this.data.performance_metrics?.response_time_distribution || [];
        
        if (this.charts.responseTimeDist) {
            this.charts.responseTimeDist.destroy();
        }
        
        this.charts.responseTimeDist = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: distribution.map(d => d.time_range),
                datasets: [{
                    label: 'Queries',
                    data: distribution.map(d => d.count),
                    backgroundColor: '#10B981',
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: '#E5E7EB',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateChartLegend(elementId, items) {
        const legendElement = document.getElementById(elementId);
        if (!legendElement) return;
        
        legendElement.innerHTML = items.map(item => `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${item.color}"></div>
                <span>${item.label}: ${item.value}</span>
            </div>
        `).join('');
    }
    
    switchTrendsChart(chartType) {
        // This would switch between different trend views
        // For now, we'll just update the existing chart
        const trends = this.data.query_trends || [];
        let data, label, color;
        
        switch (chartType) {
            case 'response-time':
                data = trends.map(t => t.avg_response_time || 0);
                label = 'Avg Response Time (ms)';
                color = '#F59E0B';
                break;
            case 'success-rate':
                data = trends.map(t => {
                    const total = t.total_queries || 1;
                    const successful = t.total_queries - (t.location_queries + t.information_queries);
                    return (successful / total * 100);
                });
                label = 'Success Rate (%)';
                color = '#10B981';
                break;
            default:
                data = trends.map(t => t.total_queries);
                label = 'Total Queries';
                color = '#6366F1';
        }
        
        if (this.charts.trends) {
            this.charts.trends.data.datasets[0].data = data;
            this.charts.trends.data.datasets[0].label = label;
            this.charts.trends.data.datasets[0].borderColor = color;
            this.charts.trends.data.datasets[0].backgroundColor = color + '20';
            this.charts.trends.data.datasets[0].pointBackgroundColor = color;
            this.charts.trends.update();
        }
    }
    
    updateTables() {
        this.updatePopularProductsTable();
        this.updateBusiestLocationsTable();
        this.updateRecentActivitiesTable();
    }
    
    updatePopularProductsTable() {
        const container = document.getElementById('popular-products-table');
        const products = this.data.popular_products || [];
        
        if (products.length === 0) {
            container.innerHTML = '<div class="loading-spinner">No product data available</div>';
            return;
        }
        
        const table = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Searches</th>
                        <th>Found Rate</th>
                        <th>Avg Confidence</th>
                        <th>Last Searched</th>
                    </tr>
                </thead>
                <tbody>
                    ${products.slice(0, 20).map(product => `
                        <tr>
                            <td><strong>${product.normalized_product}</strong></td>
                            <td>${product.search_count}</td>
                            <td>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${(product.found_count / product.search_count * 100)}%"></div>
                                </div>
                                ${(product.found_count / product.search_count * 100).toFixed(1)}%
                            </td>
                            <td>${((product.avg_confidence || 0) * 100).toFixed(1)}%</td>
                            <td>${new Date(product.last_searched).toLocaleDateString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = table;
    }
    
    updateBusiestLocationsTable() {
        const container = document.getElementById('busiest-locations-table');
        const locations = this.data.location_analytics?.busiest_aisles || [];
        
        if (locations.length === 0) {
            container.innerHTML = '<div class="loading-spinner">No location data available</div>';
            return;
        }
        
        const table = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Aisle</th>
                        <th>Queries</th>
                        <th>Avg Confidence</th>
                    </tr>
                </thead>
                <tbody>
                    ${locations.slice(0, 15).map(location => `
                        <tr>
                            <td><strong>Aisle ${location.aisle}</strong></td>
                            <td>${location.query_count}</td>
                            <td>${((location.avg_confidence || 0) * 100).toFixed(1)}%</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = table;
    }
    
    updateRecentActivitiesTable() {
        const container = document.getElementById('recent-activities-table');
        const activities = this.data.recent_activities || [];
        
        if (activities.length === 0) {
            container.innerHTML = '<div class="loading-spinner">No recent activities</div>';
            return;
        }
        
        const table = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Query</th>
                        <th>Type</th>
                        <th>Method</th>
                        <th>Product</th>
                        <th>Response Time</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${activities.slice(0, 50).map(activity => `
                        <tr>
                            <td>${new Date(activity.timestamp).toLocaleString()}</td>
                            <td title="${activity.query_text}">
                                ${activity.query_text.length > 50 ? activity.query_text.substring(0, 50) + '...' : activity.query_text}
                            </td>
                            <td>${activity.query_type}</td>
                            <td>
                                <span class="input-method-badge ${activity.input_method}">
                                    ${activity.input_method}
                                </span>
                            </td>
                            <td>${activity.product || '-'}</td>
                            <td>${activity.response_time_ms}ms</td>
                            <td>
                                <span class="status-badge ${activity.success ? 'success' : 'error'}">
                                    ${activity.success ? 'Success' : 'Error'}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = table;
    }
    
    filterProductsTable(searchTerm) {
        const table = document.querySelector('#popular-products-table table');
        if (!table) return;
        
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const productName = row.cells[0].textContent.toLowerCase();
            const matches = productName.includes(searchTerm.toLowerCase());
            row.style.display = matches ? '' : 'none';
        });
    }
    
    filterActivitiesTable(filter) {
        const table = document.querySelector('#recent-activities-table table');
        if (!table) return;
        
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            if (filter === 'all') {
                row.style.display = '';
            } else {
                const methodCell = row.cells[3];
                const method = methodCell.textContent.trim().toLowerCase();
                const matches = method.includes(filter);
                row.style.display = matches ? '' : 'none';
            }
        });
    }
    
    async loadRecentActivities() {
        try {
            document.getElementById('activities-refresh').querySelector('i').classList.add('fa-spin');
            
            const response = await fetch(`${this.apiBase}/recent?limit=100`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            this.data.recent_activities = result.data.activities;
            this.updateRecentActivitiesTable();
            
        } catch (error) {
            console.error('Failed to load recent activities:', error);
            this.showError('Failed to refresh activities');
        } finally {
            document.getElementById('activities-refresh').querySelector('i').classList.remove('fa-spin');
        }
    }
    
    async checkSystemHealth() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            const result = await response.json();
            
            const healthElement = document.getElementById('health-status');
            if (result.status === 'healthy') {
                healthElement.textContent = 'Healthy';
                healthElement.style.color = '#10B981';
            } else {
                healthElement.textContent = 'Issues Detected';
                healthElement.style.color = '#EF4444';
            }
        } catch (error) {
            const healthElement = document.getElementById('health-status');
            healthElement.textContent = 'Offline';
            healthElement.style.color = '#EF4444';
        }
    }
    
    updateLastUpdated() {
        const now = new Date();
        document.getElementById('update-time').textContent = now.toLocaleTimeString();
    }
    
    startAutoRefresh() {
        // Refresh real-time metrics every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadRealTimeMetrics();
        }, 30000);
    }
    
    async loadRealTimeMetrics() {
        try {
            const response = await fetch(`${this.apiBase}/real-time`);
            if (!response.ok) return;
            
            const result = await response.json();
            const data = result.data;
            
            // Update real-time indicators
            this.updateLastUpdated();
            
            // Update some key metrics if they've changed significantly
            const currentQueries = parseInt(document.getElementById('total-queries').textContent) || 0;
            if (Math.abs(data.queries_today - currentQueries) > 5) {
                this.loadDashboardData();
            }
            
        } catch (error) {
            console.error('Failed to load real-time metrics:', error);
        }
    }
    
    showExportModal() {
        document.getElementById('export-modal').classList.remove('hidden');
    }
    
    hideExportModal() {
        document.getElementById('export-modal').classList.add('hidden');
    }
    
    async exportData() {
        try {
            const timeRange = document.getElementById('export-time-range').value;
            const format = document.getElementById('export-format').value;
            
            this.hideExportModal();
            this.showLoading('Preparing export...');
            
            const response = await fetch(`${this.apiBase}/export?days=${timeRange}&format=${format}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            
            // Create and download file
            const dataStr = JSON.stringify(result.data, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `shelfsense-analytics-${timeRange}days-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Failed to export data:', error);
            this.showError('Failed to export analytics data');
        } finally {
            this.hideLoading();
        }
    }
    
    showLoading(message = 'Loading Analytics...') {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.remove('hidden');
        if (message) {
            overlay.querySelector('h3').textContent = message;
        }
    }
    
    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }
    
    showError(message) {
        const toast = document.getElementById('error-toast');
        const messageElement = document.getElementById('error-message');
        messageElement.textContent = message;
        toast.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => this.hideError(), 5000);
    }
    
    hideError() {
        document.getElementById('error-toast').classList.add('hidden');
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Destroy all charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.analyticsDashboard = new AnalyticsDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.analyticsDashboard) {
        window.analyticsDashboard.destroy();
    }
});