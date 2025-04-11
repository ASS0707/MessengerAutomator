// Dark Mode Toggle Functionality

document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const darkModeText = document.getElementById('dark-mode-text');
    const darkModeStyles = document.getElementById('dark-mode-styles');
    
    // Function to enable dark mode
    function enableDarkMode() {
        document.body.setAttribute('data-bs-theme', 'dark');
        darkModeStyles.disabled = false;
        localStorage.setItem('darkMode', 'enabled');
        if (darkModeText) {
            darkModeText.textContent = 'Light Mode';
        }
    }
    
    // Function to disable dark mode
    function disableDarkMode() {
        document.body.removeAttribute('data-bs-theme');
        darkModeStyles.disabled = true;
        localStorage.setItem('darkMode', 'disabled');
        if (darkModeText) {
            darkModeText.textContent = 'Dark Mode';
        }
    }
    
    // Check if the user previously enabled dark mode
    const darkMode = localStorage.getItem('darkMode');
    
    // If dark mode was previously enabled, turn it on
    if (darkMode === 'enabled') {
        enableDarkMode();
    }
    
    // Add event listener to toggle button if it exists
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            // Toggle dark mode
            if (localStorage.getItem('darkMode') !== 'enabled') {
                enableDarkMode();
            } else {
                disableDarkMode();
            }
        });
    }
    
    // Add custom events for enabling/disabling dark mode
    document.addEventListener('enableDarkMode', function() {
        enableDarkMode();
    });
    
    document.addEventListener('disableDarkMode', function() {
        disableDarkMode();
    });
    
    // Listen for system preference changes
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)');
    
    prefersDarkMode.addEventListener('change', function(e) {
        // Only change if the user hasn't manually set a preference
        if (!localStorage.getItem('darkMode')) {
            if (e.matches) {
                enableDarkMode();
            } else {
                disableDarkMode();
            }
        }
    });
    
    // Check system preference on initial load if no manual preference is set
    if (!localStorage.getItem('darkMode')) {
        if (prefersDarkMode.matches) {
            enableDarkMode();
        } else {
            disableDarkMode();
        }
    }
    
    // Add support for keyboard shortcut (Alt+D) to toggle dark mode
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === 'd') {
            if (localStorage.getItem('darkMode') !== 'enabled') {
                enableDarkMode();
            } else {
                disableDarkMode();
            }
        }
    });
});
