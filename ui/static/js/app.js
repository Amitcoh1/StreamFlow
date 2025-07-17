/**
 * StreamFlow Dashboard Application
 * Main JavaScript functionality for the dashboard
 */

class StreamFlowApp {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.notificationQueue = [];
        this.charts = {};
        this.init();
    }

    init() {
        this.setupGlobalErrorHandling();
        this.setupAPIInterceptors();
        this.setupNotificationSystem();
        this.highlightActiveNavigation();
    }

    /**
     * Setup global error handling
     */
    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.showNotification('An unexpected error occurred', 'error');
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showNotification('An unexpected error occurred', 'error');
        });
    }

    /**
     * Setup API interceptors for authentication
     */
    setupAPIInterceptors() {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const [url, options = {}] = args;
            
            // Add authorization header if token exists
            const token = localStorage.getItem('token');
            if (token && !options.headers?.Authorization) {
                options.headers = {
                    ...options.headers,
                    'Authorization': `Bearer ${token}`
                };
            }

            try {
                const response = await originalFetch(url, options);
                
                // Handle unauthorized responses
                if (response.status === 401) {
                    await this.handleUnauthorized();
                    return response;
                }

                return response;
            } catch (error) {
                console.error('Fetch error:', error);
                throw error;
            }
        };
    }

    /**
     * Handle unauthorized responses
     */
    async handleUnauthorized() {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
            try {
                const response = await fetch('/api/v1/auth/refresh', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        refresh_token: refreshToken
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('token', data.access_token);
                    if (data.refresh_token) {
                        localStorage.setItem('refresh_token', data.refresh_token);
                    }
                    return;
                }
            } catch (error) {
                console.error('Token refresh failed:', error);
            }
        }

        // Redirect to login if refresh fails
        this.logout();
    }

    /**
     * Logout user
     */
    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
    }

    /**
     * Setup notification system
     */
    setupNotificationSystem() {
        // Create notification container if it doesn't exist
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification notification-${type} fadeIn`;
        
        const icon = this.getNotificationIcon(type);
        
        notification.innerHTML = `
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <i class="${icon}"></i>
                    </div>
                    <div class="ml-3 w-0 flex-1">
                        <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
                            ${message}
                        </p>
                    </div>
                    <div class="ml-4 flex-shrink-0 flex">
                        <button class="notification-close bg-white dark:bg-gray-800 rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add close functionality
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.removeNotification(notification);
        });

        container.appendChild(notification);

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification);
            }, duration);
        }

        return notification;
    }

    /**
     * Remove notification
     */
    removeNotification(notification) {
        if (notification && notification.parentNode) {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }

    /**
     * Get notification icon
     */
    getNotificationIcon(type) {
        const icons = {
            success: 'fas fa-check-circle text-green-500',
            error: 'fas fa-exclamation-circle text-red-500',
            warning: 'fas fa-exclamation-triangle text-yellow-500',
            info: 'fas fa-info-circle text-blue-500'
        };
        return icons[type] || icons.info;
    }

    /**
     * Highlight active navigation
     */
    highlightActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    /**
     * Format numbers for display
     */
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    /**
     * Format bytes for display
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Format duration for display
     */
    formatDuration(ms) {
        if (ms < 1000) return ms + 'ms';
        if (ms < 60000) return (ms / 1000).toFixed(1) + 's';
        if (ms < 3600000) return Math.floor(ms / 60000) + 'm';
        return Math.floor(ms / 3600000) + 'h';
    }

    /**
     * Debounce function
     */
    debounce(func, wait) {
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

    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Make API request with error handling
     */
    async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            this.showNotification(`API Error: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Export data as CSV
     */
    exportToCSV(data, filename = 'data.csv') {
        const csvContent = this.arrayToCSV(data);
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        
        const link = document.createElement('a');
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    /**
     * Convert array to CSV
     */
    arrayToCSV(data) {
        if (!data || data.length === 0) return '';
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => 
                headers.map(header => {
                    const value = row[header];
                    return typeof value === 'string' && value.includes(',') 
                        ? `"${value}"` 
                        : value;
                }).join(',')
            )
        ].join('\n');
        
        return csvContent;
    }
}

// Initialize the application
const streamFlow = new StreamFlowApp();

// Export for global access
window.streamFlow = streamFlow;

// Utility functions for templates
window.formatNumber = streamFlow.formatNumber.bind(streamFlow);
window.formatBytes = streamFlow.formatBytes.bind(streamFlow);
window.formatDuration = streamFlow.formatDuration.bind(streamFlow);
window.showNotification = streamFlow.showNotification.bind(streamFlow);
window.apiRequest = streamFlow.apiRequest.bind(streamFlow);
window.exportToCSV = streamFlow.exportToCSV.bind(streamFlow);