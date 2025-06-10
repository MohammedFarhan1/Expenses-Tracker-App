// Responsive Charts Configuration
document.addEventListener('DOMContentLoaded', function() {
    // Function to update chart options based on screen size
    function getResponsiveChartOptions(chartType) {
        const isMobile = window.innerWidth < 768;
        
        // Common options for all charts
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: isMobile ? 'bottom' : 'right',
                    labels: {
                        boxWidth: isMobile ? 12 : 20,
                        padding: isMobile ? 10 : 20,
                        font: {
                            size: isMobile ? 10 : 12
                        }
                    }
                },
                tooltip: {
                    bodyFont: {
                        size: isMobile ? 12 : 14
                    },
                    titleFont: {
                        size: isMobile ? 12 : 14
                    }
                }
            }
        };
        
        // Chart-specific options
        if (chartType === 'pie') {
            return {
                ...commonOptions,
                cutout: isMobile ? '40%' : '0%',
                radius: isMobile ? '90%' : '100%'
            };
        } else if (chartType === 'bar') {
            return {
                ...commonOptions,
                scales: {
                    x: {
                        ticks: {
                            font: {
                                size: isMobile ? 8 : 12
                            },
                            maxRotation: isMobile ? 45 : 0,
                            minRotation: isMobile ? 45 : 0
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: isMobile ? 10 : 12
                            }
                        }
                    }
                }
            };
        }
        
        return commonOptions;
    }
    
    // Function to create or update charts
    window.createOrUpdateChart = function(chartId, chartType, chartData) {
        const ctx = document.getElementById(chartId);
        if (!ctx) return null;
        
        // Destroy existing chart if it exists
        if (window[chartId + 'Chart']) {
            window[chartId + 'Chart'].destroy();
        }
        
        // Get responsive options
        const options = getResponsiveChartOptions(chartType);
        
        // Create new chart
        window[chartId + 'Chart'] = new Chart(ctx, {
            type: chartType,
            data: chartData,
            options: options
        });
        
        return window[chartId + 'Chart'];
    };
    
    // Handle window resize to make charts responsive
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // Recreate charts with new options when window is resized
            if (window.recreateChartsOnResize) {
                window.recreateChartsOnResize();
            }
        }, 250);
    });
});