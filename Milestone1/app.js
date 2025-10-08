// Application State
let currentUser = null;
let users = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadUsers();
    checkAuthStatus();
});

// Initialize application data
function initializeApp() {
    // Create sample user if not exists
    const sampleUser = {
        id: 1,
        username: 'admin',
        email: 'admin@crowdcount.com',
        password: 'password123',
        createdAt: new Date().toISOString()
    };

    // Load users from localStorage or create sample user
    const storedUsers = localStorage.getItem('crowdcount_users');
    if (storedUsers) {
        users = JSON.parse(storedUsers);
    } else {
        users = [sampleUser];
        saveUsers();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Auth tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', handleTabSwitch);
    });

    // Form submissions
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // Dashboard navigation
    const navItems = document.querySelectorAll('.nav-item:not(.logout-btn)');
    navItems.forEach(item => {
        item.addEventListener('click', handleNavigation);
    });

    // Logout button - fixed event listener
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            handleLogout(e);
        });
    }
}

// Handle tab switching between login and register
function handleTabSwitch(e) {
    e.preventDefault();
    const targetTab = e.target.dataset.tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    
    // Update forms
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
    });
    document.getElementById(`${targetTab}-form`).classList.add('active');
    
    // Clear error messages
    clearErrorMessages();
}

// Handle login form submission
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    
    // Clear previous errors
    clearErrorMessages();
    
    // Validate inputs
    if (!email || !password) {
        showError('login-error', 'Please fill in all fields.');
        return;
    }
    
    if (!isValidEmail(email)) {
        showError('login-error', 'Please enter a valid email address.');
        return;
    }
    
    showLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
        const user = authenticateUser(email, password);
        
        if (user) {
            currentUser = user;
            saveCurrentUser();
            showDashboard();
            showSuccess('Login successful!');
        } else {
            showError('login-error', 'Invalid email or password.');
        }
        
        showLoading(false);
    }, 1000);
}

// Handle register form submission
async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm').value;
    
    // Clear previous errors
    clearErrorMessages();
    
    // Validate inputs
    const validation = validateRegistration(username, email, password, confirmPassword);
    if (!validation.isValid) {
        showError('register-error', validation.message);
        return;
    }
    
    showLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
        const existingUser = users.find(u => u.email === email || u.username === username);
        
        if (existingUser) {
            showError('register-error', 'User with this email or username already exists.');
            showLoading(false);
            return;
        }
        
        // Create new user
        const newUser = {
            id: users.length + 1,
            username: username,
            email: email,
            password: password, // In real app, this would be hashed
            createdAt: new Date().toISOString()
        };
        
        users.push(newUser);
        saveUsers();
        
        currentUser = newUser;
        saveCurrentUser();
        showDashboard();
        showSuccess('Registration successful!');
        showLoading(false);
    }, 1000);
}

// Validate registration inputs
function validateRegistration(username, email, password, confirmPassword) {
    if (!username || !email || !password || !confirmPassword) {
        return { isValid: false, message: 'Please fill in all fields.' };
    }
    
    if (username.length < 3) {
        return { isValid: false, message: 'Username must be at least 3 characters long.' };
    }
    
    if (!isValidEmail(email)) {
        return { isValid: false, message: 'Please enter a valid email address.' };
    }
    
    if (password.length < 6) {
        return { isValid: false, message: 'Password must be at least 6 characters long.' };
    }
    
    if (password !== confirmPassword) {
        return { isValid: false, message: 'Passwords do not match.' };
    }
    
    return { isValid: true };
}

// Authenticate user
function authenticateUser(email, password) {
    return users.find(u => u.email === email && u.password === password);
}

// Validate email format
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Handle dashboard navigation
function handleNavigation(e) {
    e.preventDefault();
    
    const section = e.currentTarget.dataset.section;
    if (!section) return;
    
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    e.currentTarget.classList.add('active');
    
    // Show corresponding content view
    document.querySelectorAll('.content-view').forEach(view => {
        view.classList.remove('active');
    });
    
    const targetView = document.getElementById(`${section}-view`);
    if (targetView) {
        targetView.classList.add('active');
    }
}

// Handle logout - fixed implementation
function handleLogout(e) {
    e.preventDefault();
    e.stopPropagation();
    
    // Show confirmation dialog
    const shouldLogout = confirm('Are you sure you want to logout?');
    
    if (shouldLogout) {
        // Clear current user
        currentUser = null;
        localStorage.removeItem('crowdcount_current_user');
        
        // Show auth page
        showAuthPage();
        
        // Show success message
        showSuccess('Logged out successfully!');
        
        // Reset forms
        resetAllForms();
    }
}

// Reset all forms
function resetAllForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        if (form.reset) {
            form.reset();
        }
    });
    clearErrorMessages();
}

// Show dashboard
function showDashboard() {
    const authSection = document.getElementById('auth-section');
    const dashboardSection = document.getElementById('dashboard-section');
    
    if (authSection) {
        authSection.classList.add('hidden');
    }
    
    if (dashboardSection) {
        dashboardSection.classList.remove('hidden');
    }
    
    // Update username display
    const usernameDisplay = document.getElementById('username-display');
    if (usernameDisplay && currentUser) {
        usernameDisplay.textContent = currentUser.username;
    }
    
    // Reset to dashboard view
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const dashboardNav = document.querySelector('.nav-item[data-section="dashboard"]');
    if (dashboardNav) {
        dashboardNav.classList.add('active');
    }
    
    document.querySelectorAll('.content-view').forEach(view => {
        view.classList.remove('active');
    });
    
    const dashboardView = document.getElementById('dashboard-view');
    if (dashboardView) {
        dashboardView.classList.add('active');
    }
}

// Show auth page
function showAuthPage() {
    const authSection = document.getElementById('auth-section');
    const dashboardSection = document.getElementById('dashboard-section');
    
    if (dashboardSection) {
        dashboardSection.classList.add('hidden');
    }
    
    if (authSection) {
        authSection.classList.remove('hidden');
    }
    
    // Reset forms
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => {
        if (form.reset) {
            form.reset();
        }
    });
    clearErrorMessages();
    
    // Reset to login tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const loginTab = document.querySelector('.tab-btn[data-tab="login"]');
    if (loginTab) {
        loginTab.classList.add('active');
    }
    
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
    });
    
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.classList.add('active');
    }
}

// Check authentication status on page load
function checkAuthStatus() {
    const savedUser = localStorage.getItem('crowdcount_current_user');
    if (savedUser) {
        try {
            currentUser = JSON.parse(savedUser);
            
            // Verify user still exists in users array
            const userExists = users.find(u => u.id === currentUser.id);
            if (userExists) {
                showDashboard();
            } else {
                localStorage.removeItem('crowdcount_current_user');
                currentUser = null;
                showAuthPage();
            }
        } catch (e) {
            localStorage.removeItem('crowdcount_current_user');
            currentUser = null;
            showAuthPage();
        }
    } else {
        showAuthPage();
    }
}

// Save current user to localStorage
function saveCurrentUser() {
    if (currentUser) {
        localStorage.setItem('crowdcount_current_user', JSON.stringify(currentUser));
    }
}

// Save users to localStorage
function saveUsers() {
    localStorage.setItem('crowdcount_users', JSON.stringify(users));
}

// Load users from localStorage
function loadUsers() {
    const storedUsers = localStorage.getItem('crowdcount_users');
    if (storedUsers) {
        try {
            users = JSON.parse(storedUsers);
        } catch (e) {
            users = [];
        }
    }
}

// Show error message
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }
}

// Clear all error messages
function clearErrorMessages() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.classList.add('hidden');
        element.textContent = '';
    });
}

// Show success message (temporary notification)
function showSuccess(message) {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.success-notification');
    existingNotifications.forEach(notification => {
        document.body.removeChild(notification);
    });
    
    // Create temporary success notification
    const notification = document.createElement('div');
    notification.className = 'success-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--color-success);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        font-weight: 500;
        transition: all 0.3s ease;
        transform: translateX(100%);
        opacity: 0;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
        notification.style.opacity = '1';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Show/hide loading overlay
function showLoading(show) {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        if (show) {
            loadingOverlay.classList.remove('hidden');
        } else {
            loadingOverlay.classList.add('hidden');
        }
    }
}

// Utility function to simulate API delays
function simulateApiCall(callback, delay = 1000) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const result = callback();
            resolve(result);
        }, delay);
    });
}

// Mobile sidebar toggle (for future enhancement)
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// Add mobile sidebar button if needed
function addMobileSidebarButton() {
    if (window.innerWidth <= 768) {
        let toggleButton = document.querySelector('.mobile-sidebar-toggle');
        if (!toggleButton) {
            toggleButton = document.createElement('button');
            toggleButton.className = 'mobile-sidebar-toggle';
            toggleButton.innerHTML = '☰';
            toggleButton.addEventListener('click', toggleSidebar);
            document.body.appendChild(toggleButton);
        }
    }
}

// Handle window resize for responsive design
window.addEventListener('resize', function() {
    addMobileSidebarButton();
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape key to close modals or return to dashboard
    if (e.key === 'Escape') {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay && !loadingOverlay.classList.contains('hidden')) {
            // Don't allow escape during loading
            return;
        }
    }
    
    // Enter key in forms
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        const form = e.target.closest('form');
        if (form) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    }
});

// Form validation helpers
function addRealTimeValidation() {
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            // Clear error state on input
            this.classList.remove('error');
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    
    if (field.hasAttribute('required') && !value) {
        isValid = false;
    }
    
    if (field.type === 'email' && value && !isValidEmail(value)) {
        isValid = false;
    }
    
    if (field.type === 'password' && value && value.length < 6) {
        isValid = false;
    }
    
    field.classList.toggle('error', !isValid);
    return isValid;
}

// Initialize real-time validation after DOM is loaded
setTimeout(() => {
    addRealTimeValidation();
}, 100);

// Export functions for potential external use
window.CrowdCountApp = {
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    getCurrentUser: () => currentUser,
    showDashboard,
    showAuthPage
};