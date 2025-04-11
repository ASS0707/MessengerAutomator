// Orders management functionality

document.addEventListener('DOMContentLoaded', function() {
    // Update order status with AJAX
    const statusSelects = document.querySelectorAll('.order-status-select');
    
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            const orderId = this.getAttribute('data-order-id');
            const newStatus = this.value;
            
            // Confirm status change
            if (confirm(`Are you sure you want to change the order status to ${newStatus}?`)) {
                updateOrderStatus(orderId, newStatus, this);
            } else {
                // Reset to previous value if canceled
                this.value = this.getAttribute('data-original-status');
            }
        });
        
        // Store original value for cancel case
        select.setAttribute('data-original-status', select.value);
    });
    
    // Function to update order status
    function updateOrderStatus(orderId, status, selectElement) {
        // Show loading state
        const originalBgColor = selectElement.style.backgroundColor;
        selectElement.style.backgroundColor = '#e9ecef';
        selectElement.disabled = true;
        
        // Create form data
        const formData = new FormData();
        formData.append('status', status);
        
        // Send update request
        fetch(`/admin/orders/${orderId}/update`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Status update failed');
            }
            return response.text();
        })
        .then(() => {
            // Show success indicator
            selectElement.style.backgroundColor = '#d1e7dd';
            
            // Update data-original-status
            selectElement.setAttribute('data-original-status', status);
            
            // Reset after delay
            setTimeout(() => {
                selectElement.style.backgroundColor = originalBgColor;
                selectElement.disabled = false;
            }, 1000);
            
            // Update badge if it exists
            const statusBadge = document.querySelector(`.order-status-badge[data-order-id="${orderId}"]`);
            if (statusBadge) {
                // Remove all badge classes and add the correct one
                statusBadge.classList.remove('bg-primary', 'bg-warning', 'bg-info', 'bg-success', 'bg-danger', 'bg-secondary');
                
                let badgeClass = 'bg-secondary';
                let statusText = status.charAt(0).toUpperCase() + status.slice(1);
                
                switch(status) {
                    case 'new':
                        badgeClass = 'bg-primary';
                        break;
                    case 'processing':
                        badgeClass = 'bg-warning text-dark';
                        break;
                    case 'shipped':
                        badgeClass = 'bg-info text-dark';
                        break;
                    case 'delivered':
                        badgeClass = 'bg-success';
                        break;
                    case 'cancelled':
                        badgeClass = 'bg-danger';
                        break;
                }
                
                statusBadge.className = `badge ${badgeClass} order-badge`;
                statusBadge.textContent = statusText;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Show error state
            selectElement.style.backgroundColor = '#f8d7da';
            
            // Reset after delay
            setTimeout(() => {
                selectElement.style.backgroundColor = originalBgColor;
                selectElement.disabled = false;
                // Reset to original value on error
                selectElement.value = selectElement.getAttribute('data-original-status');
            }, 1000);
            
            alert('Failed to update order status. Please try again.');
        });
    }
    
    // Filter orders by date range if date pickers exist
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const filterButton = document.getElementById('filter-date-btn');
    
    if (startDateInput && endDateInput && filterButton) {
        filterButton.addEventListener('click', function() {
            const startDate = startDateInput.value;
            const endDate = endDateInput.value;
            
            if (!startDate || !endDate) {
                alert('Please select both start and end dates');
                return;
            }
            
            // Get current URL and params
            const url = new URL(window.location.href);
            
            // Update or add date filter params
            url.searchParams.set('start_date', startDate);
            url.searchParams.set('end_date', endDate);
            
            // Navigate to filtered URL
            window.location.href = url.toString();
        });
    }
    
    // Clear date filters if clear button exists
    const clearFilterButton = document.getElementById('clear-date-filter');
    if (clearFilterButton) {
        clearFilterButton.addEventListener('click', function() {
            // Get current URL and params
            const url = new URL(window.location.href);
            
            // Remove date filter params
            url.searchParams.delete('start_date');
            url.searchParams.delete('end_date');
            
            // Navigate to URL without date filters
            window.location.href = url.toString();
        });
    }
    
    // Handle bulk actions if bulk action form exists
    const bulkActionForm = document.getElementById('bulk-action-form');
    const bulkActionSelect = document.getElementById('bulk-action');
    const bulkActionButton = document.getElementById('apply-bulk-action');
    
    if (bulkActionForm && bulkActionSelect && bulkActionButton) {
        bulkActionButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const action = bulkActionSelect.value;
            if (!action) {
                alert('Please select an action');
                return;
            }
            
            // Check if any orders are selected
            const selectedOrders = document.querySelectorAll('input[name="order_ids"]:checked');
            if (selectedOrders.length === 0) {
                alert('Please select at least one order');
                return;
            }
            
            // Confirm action
            if (confirm(`Are you sure you want to ${action} the selected orders?`)) {
                bulkActionForm.submit();
            }
        });
    }
    
    // Add invoice previewer if print button exists
    const printInvoiceButtons = document.querySelectorAll('.print-invoice-btn');
    
    if (printInvoiceButtons.length > 0) {
        printInvoiceButtons.forEach(button => {
            button.addEventListener('click', function() {
                const orderId = this.getAttribute('data-order-id');
                // Open invoice in new window for printing
                window.open(`/admin/orders/${orderId}/invoice`, '_blank');
            });
        });
    }
});
