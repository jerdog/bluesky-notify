// Add passive event listener support
let supportsPassive = false;
try {
    window.addEventListener("test", null, Object.defineProperty({}, 'passive', {
        get: function () { 
            supportsPassive = true; 
        } 
    }));
} catch(e) {}

// Force passive event listeners for touch events
document.addEventListener('touchstart', function(){}, supportsPassive ? {passive: true} : false);
document.addEventListener('touchmove', function(){}, supportsPassive ? {passive: true} : false);
document.addEventListener('wheel', function(){}, supportsPassive ? {passive: true} : false);

const API_BASE_URL = '/api';
let toast;

// Initialize Bootstrap toast
function showNotification(message, type = 'success') {
    const toastEl = document.getElementById('toast');
    const toastBody = toastEl.querySelector('.toast-body');
    toastBody.textContent = message;
    toastEl.classList.remove('success', 'error');
    toastEl.classList.add(type);
    const bsToast = new bootstrap.Toast(toastEl);
    bsToast.show();
}

document.addEventListener('DOMContentLoaded', () => {
    // Add event listeners
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('addAccountForm').addEventListener('submit', handleAddAccount);
    
    // Check if user is already logged in
    checkAuthStatus();
});

async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            showMainContent();
            await loadAccounts();
        } else {
            showLoginForm();
        }
    } catch (error) {
        showLoginForm();
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Login successful', 'success');
            showMainContent();
            await loadAccounts();
        } else {
            showNotification(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showNotification('Login failed', 'error');
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE_URL}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        showLoginForm();
    } catch (error) {
        showNotification('Logout failed', 'error');
    }
}

async function handleAddAccount(event) {
    event.preventDefault();
    
    const handle = document.getElementById('handle').value;
    const desktop = document.getElementById('desktopNotif').checked;
    const email = document.getElementById('emailNotif').checked;
    
    try {
        const response = await fetch(`${API_BASE_URL}/accounts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                handle,
                notification_preferences: {
                    desktop,
                    email
                }
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Account added successfully', 'success');
            document.getElementById('addAccountForm').reset();
            await loadAccounts();
        } else {
            showNotification(data.error || 'Failed to add account', 'error');
        }
    } catch (error) {
        showNotification('Failed to add account', 'error');
    }
}

async function loadAccounts() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts`);
        const data = await response.json();
        const accountsTable = document.getElementById('accountsTable');
        accountsTable.innerHTML = '';

        if (data.success && data.accounts) {
            data.accounts.forEach(account => {
                const handle = account.handle.startsWith('@') ? account.handle.substring(1) : account.handle;
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <div class="d-flex align-items-center">
                            <img src="${account.avatar_url || 'https://i.imgur.com/8ZZE4Sa.png'}" 
                                 alt="@${handle}'s avatar"
                                 class="rounded-circle me-2"
                                 width="40" height="40"
                                 onerror="this.src='https://i.imgur.com/8ZZE4Sa.png'">
                            <div>
                                <div class="fw-bold">${account.display_name || handle}</div>
                                <a href="https://bsky.app/profile/${handle}" 
                                   target="_blank" 
                                   rel="noopener noreferrer" 
                                   class="text-muted text-decoration-none">
                                    @${handle}
                                </a>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="badge ${account.is_active ? 'bg-success' : 'bg-danger'}">
                            ${account.is_active ? 'Active' : 'Paused'}
                        </span>
                    </td>
                    <td>
                        <div class="form-check form-switch">
                            <input class="form-check-input notification-toggle" type="checkbox" role="switch" 
                                   id="desktop-${handle}" 
                                   data-handle="${handle}"
                                   data-type="desktop"
                                   ${account.notification_preferences.desktop ? 'checked' : ''}>
                            <label class="form-check-label" for="desktop-${handle}">
                                <i class="bi bi-laptop"></i>
                            </label>
                        </div>
                    </td>
                    <td>
                        <div class="form-check form-switch">
                            <input class="form-check-input notification-toggle" type="checkbox" role="switch" 
                                   id="email-${handle}"
                                   data-handle="${handle}"
                                   data-type="email"
                                   ${account.notification_preferences.email ? 'checked' : ''}>
                            <label class="form-check-label" for="email-${handle}">
                                <i class="bi bi-envelope"></i>
                            </label>
                        </div>
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-${account.is_active ? 'warning' : 'success'}" onclick="toggleAccount('${handle}')">
                                <i class="bi bi-${account.is_active ? 'pause-fill' : 'play-fill'}"></i>
                                ${account.is_active ? 'Pause' : 'Resume'}
                            </button>
                            <button class="btn btn-danger" onclick="removeAccount('${handle}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                accountsTable.appendChild(row);

                // Add event listeners to the notification toggles
                const desktopToggle = document.getElementById(`desktop-${handle}`);
                const emailToggle = document.getElementById(`email-${handle}`);

                desktopToggle.addEventListener('change', async (e) => {
                    await toggleNotification(handle, 'desktop', e.target.checked);
                });

                emailToggle.addEventListener('change', async (e) => {
                    await toggleNotification(handle, 'email', e.target.checked);
                });
            });
        }
    } catch (error) {
        console.error('Error loading accounts:', error);
        showNotification('Error loading accounts', 'error');
    }
}

async function toggleAccount(handle) {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/${handle}/toggle`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`Account ${data.is_active ? 'activated' : 'paused'} successfully`, 'success');
            await loadAccounts();
        } else {
            showNotification(data.error || 'Failed to toggle account', 'error');
        }
    } catch (error) {
        showNotification('Failed to toggle account', 'error');
    }
}

async function toggleNotification(handle, type, enabled) {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/${handle}/preferences`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                desktop: type === 'desktop' ? enabled : document.getElementById(`desktop-${handle}`).checked,
                email: type === 'email' ? enabled : document.getElementById(`email-${handle}`).checked
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`${type.charAt(0).toUpperCase() + type.slice(1)} notifications ${enabled ? 'enabled' : 'disabled'}`, 'success');
        } else {
            showNotification(data.error || `Failed to update ${type} notifications`, 'error');
            // Revert the toggle if there was an error
            document.getElementById(`${type}-${handle}`).checked = !enabled;
        }
    } catch (error) {
        console.error(`Error updating ${type} notifications:`, error);
        showNotification(`Failed to update ${type} notifications`, 'error');
        // Revert the toggle if there was an error
        document.getElementById(`${type}-${handle}`).checked = !enabled;
    }
}

async function removeAccount(handle) {
    if (!confirm(`Are you sure you want to remove ${handle}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/${handle}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Account removed successfully', 'success');
            await loadAccounts();
        } else {
            const data = await response.json();
            showNotification(data.error || 'Failed to remove account', 'error');
        }
    } catch (error) {
        showNotification('Failed to remove account', 'error');
    }
}

function showMainContent() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('mainContent').style.display = 'block';
}

function showLoginForm() {
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('mainContent').style.display = 'none';
    document.getElementById('loginForm').reset();
}
