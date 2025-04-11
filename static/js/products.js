// Products management functionality

document.addEventListener('DOMContentLoaded', function() {
    
    // Handle product activation/deactivation toggle
    const activeToggles = document.querySelectorAll('.product-active-toggle');
    
    activeToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const productId = this.getAttribute('data-product-id');
            const isActive = this.checked;
            
            // Create form data
            const formData = new FormData();
            formData.append('active', isActive ? 'on' : 'off');
            
            // Send update request
            fetch(`/admin/products/${productId}/update`, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Product update failed');
                }
                return response.text();
            })
            .then(() => {
                // Show success message
                const statusBadge = document.querySelector(`.product-status-badge[data-product-id="${productId}"]`);
                if (statusBadge) {
                    statusBadge.textContent = isActive ? 'Active' : 'Inactive';
                    statusBadge.className = isActive ? 
                        'badge bg-success product-status-badge' : 
                        'badge bg-danger product-status-badge';
                    statusBadge.setAttribute('data-product-id', productId);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Revert toggle to original state on error
                this.checked = !this.checked;
                
                alert('Failed to update product status. Please try again.');
            });
        });
    });
    
    // Handle product form validation
    const productForm = document.querySelector('form[action*="/products/"]');
    
    if (productForm) {
        productForm.addEventListener('submit', function(e) {
            const nameInput = document.getElementById('name');
            const nameArInput = document.getElementById('name_ar');
            const priceInput = document.getElementById('price');
            const categoryInput = document.getElementById('category');
            const categoryArInput = document.getElementById('category_ar');
            
            let isValid = true;
            
            // Validate required fields
            if (!nameInput.value.trim()) {
                markInvalid(nameInput, 'Product name is required');
                isValid = false;
            } else {
                markValid(nameInput);
            }
            
            if (!nameArInput.value.trim()) {
                markInvalid(nameArInput, 'Arabic product name is required');
                isValid = false;
            } else {
                markValid(nameArInput);
            }
            
            if (!priceInput.value || parseFloat(priceInput.value) <= 0) {
                markInvalid(priceInput, 'Please enter a valid price');
                isValid = false;
            } else {
                markValid(priceInput);
            }
            
            if (!categoryInput.value.trim()) {
                markInvalid(categoryInput, 'Category is required');
                isValid = false;
            } else {
                markValid(categoryInput);
            }
            
            if (!categoryArInput.value.trim()) {
                markInvalid(categoryArInput, 'Arabic category is required');
                isValid = false;
            } else {
                markValid(categoryArInput);
            }
            
            if (!isValid) {
                e.preventDefault();
                // Scroll to the first invalid field
                document.querySelector('.is-invalid').scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }
    
    // Helper functions for form validation
    function markInvalid(element, message) {
        element.classList.add('is-invalid');
        
        // Create or update feedback message
        let feedback = element.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            element.parentNode.insertBefore(feedback, element.nextSibling);
        }
        
        feedback.textContent = message;
    }
    
    function markValid(element) {
        element.classList.remove('is-invalid');
        element.classList.add('is-valid');
        
        // Remove any existing feedback
        const feedback = element.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.remove();
        }
    }
    
    // Handle category selection and auto-fill pairs
    const categoryInput = document.getElementById('category');
    const categoryArInput = document.getElementById('category_ar');
    
    if (categoryInput && categoryArInput) {
        // Store the category pairs
        const categoryPairs = [];
        
        // Populate category pairs from datalist options
        const categoryList = document.getElementById('category-list');
        const categoryListAr = document.getElementById('category-list-ar');
        
        if (categoryList && categoryListAr) {
            const enOptions = categoryList.querySelectorAll('option');
            const arOptions = categoryListAr.querySelectorAll('option');
            
            for (let i = 0; i < Math.min(enOptions.length, arOptions.length); i++) {
                categoryPairs.push({
                    en: enOptions[i].value,
                    ar: arOptions[i].value
                });
            }
        }
        
        // Auto-fill the corresponding category when one is selected
        categoryInput.addEventListener('change', function() {
            const selectedCat = this.value;
            const matchingPair = categoryPairs.find(pair => pair.en === selectedCat);
            
            if (matchingPair && !categoryArInput.value) {
                categoryArInput.value = matchingPair.ar;
            }
        });
        
        categoryArInput.addEventListener('change', function() {
            const selectedCat = this.value;
            const matchingPair = categoryPairs.find(pair => pair.ar === selectedCat);
            
            if (matchingPair && !categoryInput.value) {
                categoryInput.value = matchingPair.en;
            }
        });
    }
    
    // Handle product image preview if there's an image upload
    const productImageInput = document.getElementById('product-image');
    const imagePreview = document.getElementById('image-preview');
    
    if (productImageInput && imagePreview) {
        productImageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
});
