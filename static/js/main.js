// Global Utilities for the Admin Dashboard

document.addEventListener('DOMContentLoaded', function() {
    
    // Add the current year to the footer
    const yearElement = document.querySelector('.footer .text-muted');
    if (yearElement) {
        const currentYear = new Date().getFullYear();
        yearElement.textContent = yearElement.textContent.replace('{{ now.year }}', currentYear);
    }
    
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alertList = [].slice.call(document.querySelectorAll('.alert.alert-success, .alert.alert-info'));
        alertList.forEach(function(alert) {
            if (alert) {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    });
    
    // Handle RTL text inputs
    const rtlInputs = document.querySelectorAll('[dir="rtl"]');
    rtlInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Check if contains Arabic characters
            const arabicPattern = /[\u0600-\u06FF]/;
            if (arabicPattern.test(this.value) && !this.hasAttribute('dir')) {
                this.setAttribute('dir', 'rtl');
            }
        });
    });
    
    // Confirmation for delete actions
    const confirmDeleteForms = document.querySelectorAll('form[data-confirm]');
    confirmDeleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });
    
    // Prevent double form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Disable all buttons
            const buttons = this.querySelectorAll('button[type="submit"]');
            buttons.forEach(button => {
                button.disabled = true;
                
                // Add spinner to indicate loading
                if (!button.querySelector('.spinner-border')) {
                    const originalText = button.innerHTML;
                    button.setAttribute('data-original-text', originalText);
                    button.innerHTML = `
                        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        Loading...
                    `;
                }
            });
        });
    });
    
    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            // Format to 2 decimal places if there's a value
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
});

// Helper function to format currency
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

// Helper function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Function to toggle RTL mode
function toggleRTL() {
    document.body.classList.toggle('rtl');
    
    // Store preference in localStorage
    if (document.body.classList.contains('rtl')) {
        localStorage.setItem('rtl', 'enabled');
    } else {
        localStorage.setItem('rtl', 'disabled');
    }
}

// Check if user has notifications
function checkNotifications() {
    // This would typically be an API call to check for new notifications
    // For now, we'll just simulate it
    return new Promise((resolve) => {
        setTimeout(() => {
            // Simulating 2 notifications
            resolve(2);
        }, 1000);
    });
}

// Function to display notification badge
function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('d-none');
        } else {
            badge.classList.add('d-none');
        }
    }
}

// Check for new orders periodically (every 60 seconds)
let notificationInterval;
function startNotificationChecking() {
    // Check immediately
    checkNotifications().then(updateNotificationBadge);
    
    // Then check every 60 seconds
    notificationInterval = setInterval(() => {
        checkNotifications().then(updateNotificationBadge);
    }, 60000);
}

// Only start notification checking if user is logged in
if (document.querySelector('.navbar-nav')) {
    startNotificationChecking();
}
