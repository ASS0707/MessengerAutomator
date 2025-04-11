// Analytics Dashboard Functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers if they exist
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const applyDateFilterBtn = document.getElementById('apply-date-filter');
    
    if (startDateInput && endDateInput && applyDateFilterBtn) {
        // Set default values if not already set
        if (!startDateInput.value) {
            const defaultStart = new Date();
            defaultStart.setDate(defaultStart.getDate() - 30); // Last 30 days
            startDateInput.valueAsDate = defaultStart;
        }
        
        if (!endDateInput.value) {
            endDateInput.valueAsDate = new Date();
        }
        
        // Apply date filter
        applyDateFilterBtn.addEventListener('click', function() {
            if (!startDateInput.value || !endDateInput.value) {
                alert('Please select both start and end dates');
                return;
            }
            
            // Get current URL and params
            const url = new URL(window.location.href);
            
            // Update or add date filter params
            url.searchParams.set('start_date', startDateInput.value);
            url.searchParams.set('end_date', endDateInput.value);
            
            // Navigate to filtered URL
            window.location.href = url.toString();
        });
    }
    
    // Handle period selection
    const periodButtons = document.querySelectorAll('.period-btn');
    if (periodButtons.length > 0) {
        periodButtons.forEach(button => {
            button.addEventListener('click', function() {
                const period = this.getAttribute('data-period');
                
                // Get current URL and params
                const url = new URL(window.location.href);
                
                // Update or add period param
                url.searchParams.set('period', period);
                
                // Remove any date range filters when switching to period view
                url.searchParams.delete('start_date');
                url.searchParams.delete('end_date');
                
                // Navigate to filtered URL
                window.location.href = url.toString();
            });
        });
    }
    
    // Export analytics data if export button exists
    const exportButtons = document.querySelectorAll('.export-analytics-btn');
    
    if (exportButtons.length > 0) {
        exportButtons.forEach(button => {
            button.addEventListener('click', function() {
                const format = this.getAttribute('data-format');
                const chartId = this.getAttribute('data-chart');
                const chartTitle = this.getAttribute('data-title') || 'Chart';
                
                if (format === 'csv') {
                    exportChartDataCSV(chartId, chartTitle);
                } else if (format === 'png') {
                    exportChartAsPNG(chartId, chartTitle);
                }
            });
        });
    }
    
    // Function to export chart data as CSV
    function exportChartDataCSV(chartId, title) {
        const chart = Chart.getChart(chartId);
        if (!chart) return;
        
        // Prepare CSV content
        let csvContent = 'data:text/csv;charset=utf-8,';
        
        // Add headers
        let headers = ['Label'];
        chart.data.datasets.forEach(dataset => {
            headers.push(dataset.label);
        });
        csvContent += headers.join(',') + '\r\n';
        
        // Add data rows
        chart.data.labels.forEach((label, i) => {
            let row = [label];
            chart.data.datasets.forEach(dataset => {
                row.push(dataset.data[i]);
            });
            csvContent += row.join(',') + '\r\n';
        });
        
        // Create download link
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `${title.replace(/\s+/g, '_')}_${formatDate(new Date())}.csv`);
        document.body.appendChild(link);
        
        // Trigger download
        link.click();
        document.body.removeChild(link);
    }
    
    // Function to export chart as PNG
    function exportChartAsPNG(chartId, title) {
        const chart = Chart.getChart(chartId);
        if (!chart) return;
        
        // Create a temporary link for download
        const link = document.createElement('a');
        link.href = chart.toBase64Image();
        link.download = `${title.replace(/\s+/g, '_')}_${formatDate(new Date())}.png`;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Helper function to format date as YYYYMMDD
    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}${month}${day}`;
    }
    
    // Dynamic chart color themes based on dark mode
    function updateChartColors() {
        const isDarkMode = localStorage.getItem('darkMode') === 'enabled';
        
        // Define color schemes for light and dark modes
        const colorSchemes = {
            light: {
                backgroundColor: [
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(255, 159, 64, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                gridColor: 'rgba(0, 0, 0, 0.1)',
                textColor: '#666'
            },
            dark: {
                backgroundColor: [
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(153, 102, 255, 0.7)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                gridColor: 'rgba(255, 255, 255, 0.1)',
                textColor: '#ccc'
            }
        };
        
        // Get all charts on the page
        const chartIds = ['salesChart', 'statusChart', 'productsChart'];
        const scheme = isDarkMode ? colorSchemes.dark : colorSchemes.light;
        
        chartIds.forEach(id => {
            const chart = Chart.getChart(id);
            if (!chart) return;
            
            // Update chart colors
            chart.options.scales.x.grid.color = scheme.gridColor;
            chart.options.scales.x.ticks.color = scheme.textColor;
            
            // Update y-axis scales if they exist
            if (chart.options.scales.y) {
                chart.options.scales.y.grid.color = scheme.gridColor;
                chart.options.scales.y.ticks.color = scheme.textColor;
            }
            
            if (chart.options.scales.y1) {
                chart.options.scales.y1.grid.color = scheme.gridColor;
                chart.options.scales.y1.ticks.color = scheme.textColor;
            }
            
            // Update dataset colors for bar and line charts
            if (chart.config.type === 'bar' || chart.config.type === 'line') {
                chart.data.datasets.forEach((dataset, i) => {
                    dataset.backgroundColor = scheme.backgroundColor[i % scheme.backgroundColor.length];
                    dataset.borderColor = scheme.borderColor[i % scheme.borderColor.length];
                });
            }
            
            // Update for doughnut/pie charts
            if (chart.config.type === 'doughnut' || chart.config.type === 'pie') {
                chart.data.datasets[0].backgroundColor = scheme.backgroundColor;
                chart.data.datasets[0].borderColor = scheme.borderColor;
            }
            
            // Update chart
            chart.update();
        });
    }
    
    // Update chart colors on initial load
    updateChartColors();
    
    // Listen for dark mode toggle events
    document.addEventListener('enableDarkMode', updateChartColors);
    document.addEventListener('disableDarkMode', updateChartColors);
    
    // Handle comparison toggle if it exists
    const comparisonToggle = document.getElementById('comparison-toggle');
    if (comparisonToggle) {
        comparisonToggle.addEventListener('change', function() {
            const showComparison = this.checked;
            
            // Get all comparison elements
            const comparisonElements = document.querySelectorAll('.comparison-data');
            comparisonElements.forEach(element => {
                if (showComparison) {
                    element.classList.remove('d-none');
                } else {
                    element.classList.add('d-none');
                }
            });
            
            // Store preference
            localStorage.setItem('showComparison', showComparison ? 'true' : 'false');
        });
        
        // Set initial state based on stored preference
        const showComparison = localStorage.getItem('showComparison') === 'true';
        comparisonToggle.checked = showComparison;
        
        // Trigger change event to update UI
        const event = new Event('change');
        comparisonToggle.dispatchEvent(event);
    }
    
    // Handle metrics toggle if it exists
    const metricsToggles = document.querySelectorAll('.metric-toggle');
    if (metricsToggles.length > 0) {
        metricsToggles.forEach(toggle => {
            toggle.addEventListener('change', function() {
                const metricType = this.getAttribute('data-metric');
                const chartId = this.getAttribute('data-chart');
                const isVisible = this.checked;
                
                // Update chart visibility
                const chart = Chart.getChart(chartId);
                if (chart) {
                    // Find the dataset with the matching label
                    const datasetIndex = chart.data.datasets.findIndex(ds => ds.label.toLowerCase() === metricType.toLowerCase());
                    if (datasetIndex !== -1) {
                        chart.setDatasetVisibility(datasetIndex, isVisible);
                        chart.update();
                    }
                }
                
                // Store preference
                localStorage.setItem(`metric_${metricType}`, isVisible ? 'true' : 'false');
            });
            
            // Set initial state based on stored preference
            const metricType = toggle.getAttribute('data-metric');
            const showMetric = localStorage.getItem(`metric_${metricType}`) !== 'false'; // Default to true
            toggle.checked = showMetric;
            
            // Trigger change event to update UI
            const event = new Event('change');
            toggle.dispatchEvent(event);
        });
    }
    
    // Handle real-time analytics update
    let realtimeUpdateInterval;
    const realtimeToggle = document.getElementById('realtime-toggle');
    
    if (realtimeToggle) {
        realtimeToggle.addEventListener('change', function() {
            const isRealtime = this.checked;
            
            if (isRealtime) {
                // Start polling for updates every 30 seconds
                realtimeUpdateInterval = setInterval(fetchLatestAnalytics, 30000);
                fetchLatestAnalytics(); // Fetch immediately
            } else {
                // Stop polling
                clearInterval(realtimeUpdateInterval);
            }
            
            // Store preference
            localStorage.setItem('realtimeAnalytics', isRealtime ? 'true' : 'false');
        });
        
        // Set initial state based on stored preference
        const isRealtime = localStorage.getItem('realtimeAnalytics') === 'true';
        realtimeToggle.checked = isRealtime;
        
        // Trigger change event to update UI
        const event = new Event('change');
        realtimeToggle.dispatchEvent(event);
    }
    
    // Function to fetch latest analytics data
    function fetchLatestAnalytics() {
        // This would typically be an API call to get the latest data
        // For now, we'll just reload the page
        // In a real implementation, you would use fetch() to get JSON data
        // and update the charts without reloading
        
        // Example of how it would be implemented:
        // const url = new URL(window.location.href);
        // fetch(`/api/analytics/latest${url.search}`)
        //     .then(response => response.json())
        //     .then(data => {
        //         updateChartsWithNewData(data);
        //     })
        //     .catch(error => {
        //         console.error('Error fetching real-time analytics:', error);
        //     });
    }
    
    // Function to update charts with new data
    function updateChartsWithNewData(data) {
        // Update sales chart
        const salesChart = Chart.getChart('salesChart');
        if (salesChart && data.sales) {
            salesChart.data.labels = data.sales.labels;
            salesChart.data.datasets[0].data = data.sales.orders;
            salesChart.data.datasets[1].data = data.sales.revenue;
            salesChart.update();
        }
        
        // Update status chart
        const statusChart = Chart.getChart('statusChart');
        if (statusChart && data.statuses) {
            statusChart.data.labels = data.statuses.labels;
            statusChart.data.datasets[0].data = data.statuses.counts;
            statusChart.update();
        }
        
        // Update products chart
        const productsChart = Chart.getChart('productsChart');
        if (productsChart && data.products) {
            productsChart.data.labels = data.products.labels;
            productsChart.data.datasets[0].data = data.products.quantities;
            productsChart.data.datasets[1].data = data.products.revenue;
            productsChart.update();
        }
        
        // Update summary cards
        if (data.summary) {
            updateSummaryCards(data.summary);
        }
    }
    
    // Function to update summary cards
    function updateSummaryCards(summary) {
        // Update total orders
        const totalOrdersElement = document.getElementById('total-orders');
        if (totalOrdersElement && summary.totalOrders) {
            totalOrdersElement.textContent = summary.totalOrders;
        }
        
        // Update total revenue
        const totalRevenueElement = document.getElementById('total-revenue');
        if (totalRevenueElement && summary.totalRevenue) {
            totalRevenueElement.textContent = formatCurrency(summary.totalRevenue);
        }
        
        // Update total customers
        const totalCustomersElement = document.getElementById('total-customers');
        if (totalCustomersElement && summary.totalCustomers) {
            totalCustomersElement.textContent = summary.totalCustomers;
        }
        
        // Update average order value
        const avgOrderElement = document.getElementById('avg-order');
        if (avgOrderElement && summary.avgOrderValue) {
            avgOrderElement.textContent = formatCurrency(summary.avgOrderValue);
        }
        
        // Update growth indicators
        updateGrowthIndicator('order-growth', summary.orderGrowth);
        updateGrowthIndicator('revenue-growth', summary.revenueGrowth);
    }
    
    // Function to update growth indicators
    function updateGrowthIndicator(elementId, growthValue) {
        const growthElement = document.getElementById(elementId);
        if (!growthElement || growthValue === undefined) return;
        
        const isPositive = growthValue >= 0;
        const absGrowth = Math.abs(growthValue);
        
        growthElement.textContent = `${isPositive ? '↑' : '↓'} ${absGrowth.toFixed(1)}%`;
        growthElement.className = `growth-indicator ${isPositive ? 'growth-positive' : 'growth-negative'}`;
    }
    
    // Helper function to format currency
    function formatCurrency(amount) {
        return '$' + parseFloat(amount).toFixed(2);
    }
});
