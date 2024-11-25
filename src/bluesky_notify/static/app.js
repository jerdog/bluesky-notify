// Constants and Utilities
const BSKY_BASE_URL = 'https://bsky.app/profile/';
const API_BASE_URL = '/api';
const REFRESH_INTERVAL = 5000; // 5 seconds

// Check if the browser supports passive event listeners
let supportsPassive = false;
try {
    window.addEventListener("test", null, Object.defineProperty({}, 'passive', {
        get: function () { supportsPassive = true; }
    }));
} catch(e) {}

// Add passive event listeners for better scrolling performance
document.addEventListener('touchstart', function(){}, supportsPassive ? {passive: true} : false);
document.addEventListener('touchmove', function(){}, supportsPassive ? {passive: true} : false);
document.addEventListener('wheel', function(){}, supportsPassive ? {passive: true} : false);

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadAccounts();
    startPeriodicRefresh();
    
    // Add account form submission
    const addAccountForm = document.getElementById('addAccountForm');
    if (addAccountForm) {
        addAccountForm.addEventListener('submit', handleAddAccount);
    }
});

// Toast notification handler
function showNotification(message, type = 'success') {
    const toastEl = document.getElementById('toast');
    const toastBody = toastEl.querySelector('.toast-body');
    const toastTitle = toastEl.querySelector('.toast-header strong');
    
    toastTitle.textContent = type.charAt(0).toUpperCase() + type.slice(1);
    toastBody.textContent = message;
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// Handle adding a new account
async function handleAddAccount(event) {
    event.preventDefault();
    
    let handle = document.getElementById('handle').value.trim();
    const desktopNotif = document.getElementById('desktopNotif').checked;
    const emailNotif = document.getElementById('emailNotif').checked;

    // Remove @ if present and clean invisible characters
    if (handle.startsWith('@')) {
        handle = handle.substring(1);
    }
    // Clean invisible characters and normalize
    handle = handle.replace(/[\u200B-\u200D\u202A-\u202E\uFEFF]/g, '').normalize();

    // Basic handle validation
    if (!handle) {
        showNotification('Please enter a Bluesky handle', 'error');
        return;
    }

    // Validate handle format
    const handleRegex = /^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9](\.[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9])*$/;
    if (!handleRegex.test(handle)) {
        showNotification('Please enter a valid Bluesky handle (e.g., user.bsky.social)', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/accounts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                handle,
                notification_preferences: {
                    desktop: desktopNotif,
                    email: emailNotif
                }
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to add account');
        }

        document.getElementById('handle').value = '';
        await loadAccounts();
        showNotification('Account added successfully');
    } catch (error) {
        console.error('Error adding account:', error);
        showNotification(error.message || 'Failed to add account', 'error');
    }
}

// Load and display accounts
async function loadAccounts() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load accounts');
        }
        
        const accounts = data?.data?.accounts || [];
        const accountsTable = document.getElementById('accountsTable');
        accountsTable.innerHTML = '';
        
        if (accounts.length === 0) {
            accountsTable.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        No accounts added yet. Add an account above to start monitoring.
                    </td>
                </tr>
            `;
            return;
        }
        
        accounts.forEach(account => {
            const row = document.createElement('tr');
            row.dataset.handle = account.handle;
            
            // Account info cell
            const accountCell = document.createElement('td');
            accountCell.innerHTML = `
                <div class="d-flex align-items-center">
                    ${account.avatar_url ? `<img src="${account.avatar_url}" class="rounded-circle me-2" width="32" height="32" alt="${account.handle}'s avatar">` : ''}
                    <div>
                        <div class="fw-bold"><a href="${BSKY_BASE_URL}${account.handle}" target="_blank">${account.display_name || account.handle}</a></div>
                        <div class="text-muted">@${account.handle}</div>
                    </div>
                </div>
            `;
            
            // Status cell
            const statusCell = document.createElement('td');
            statusCell.innerHTML = `
                <span class="badge ${account.is_active ? 'bg-success' : 'bg-secondary'}">
                    ${account.is_active ? 'Active' : 'Inactive'}
                </span>
            `;
            
            // Desktop notifications cell
            const desktopCell = document.createElement('td');
            const desktopEnabled = account.notification_preferences?.desktop ?? false;
            desktopCell.innerHTML = `
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" role="switch" data-type="desktop" 
                           ${desktopEnabled ? 'checked' : ''} 
                           onchange="toggleNotification('${account.handle}', 'desktop', this.checked)">
                </div>
            `;
            
            // Email notifications cell
            const emailCell = document.createElement('td');
            const emailEnabled = account.notification_preferences?.email ?? false;
            emailCell.innerHTML = `
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" role="switch" data-type="email" 
                           ${emailEnabled ? 'checked' : ''} 
                           onchange="toggleNotification('${account.handle}', 'email', this.checked)">
                </div>
            `;
            
            // Actions cell
            const actionsCell = document.createElement('td');
            actionsCell.innerHTML = `
                <button class="btn btn-sm btn-outline-danger" onclick="removeAccount('${account.did}')">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            
            row.appendChild(accountCell);
            row.appendChild(statusCell);
            row.appendChild(desktopCell);
            row.appendChild(emailCell);
            row.appendChild(actionsCell);
            
            accountsTable.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading accounts:', error);
        showNotification('Failed to load accounts', 'error');
    }
}

// Add periodic refresh of accounts
function startPeriodicRefresh() {
    setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/accounts`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to refresh accounts');
            }
            
            if (data.data && data.data.accounts) {
                updateAccountsTable(data.data.accounts);
            }
        } catch (error) {
            console.error('Error refreshing accounts:', error);
        }
    }, REFRESH_INTERVAL);
}

// Update accounts table without full reload
function updateAccountsTable(accounts) {
    const accountsTable = document.getElementById('accountsTableBody');
    if (!accountsTable) return;

    accounts.forEach(account => {
        const existingRow = document.querySelector(`tr[data-handle="${account.handle}"]`);
        if (existingRow) {
            // Update preferences in existing row
            const desktopCheckbox = existingRow.querySelector('input[data-type="desktop"]');
            const emailCheckbox = existingRow.querySelector('input[data-type="email"]');
            
            if (desktopCheckbox && account.notification_preferences) {
                desktopCheckbox.checked = account.notification_preferences.desktop || false;
            }
            if (emailCheckbox && account.notification_preferences) {
                emailCheckbox.checked = account.notification_preferences.email || false;
            }
        }
    });
}

// Toggle notification settings
async function toggleNotification(handle, type, enabled) {
    try {
        // Get the current state of both checkboxes
        const row = document.querySelector(`tr[data-handle="${handle}"]`);
        const desktopCheckbox = row.querySelector('input[data-type="desktop"]');
        const emailCheckbox = row.querySelector('input[data-type="email"]');
        
        // Create preferences object with both settings
        const preferences = {
            desktop: desktopCheckbox.checked,
            email: emailCheckbox.checked
        };
        
        // Override the toggled preference
        preferences[type] = enabled;
        
        console.log(`Updating preferences for ${handle}:`, preferences);
        
        const response = await fetch(`${API_BASE_URL}/accounts/${handle}/preferences`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(preferences)
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to update notification settings');
        }

        // Update UI with the returned data
        if (data.data && data.data.account && data.data.account.notification_preferences) {
            const prefs = data.data.account.notification_preferences;
            desktopCheckbox.checked = prefs.desktop || false;
            emailCheckbox.checked = prefs.email || false;
            console.log('Updated UI with preferences:', prefs);
        } else {
            console.warn('No preference data in response:', data);
        }

        showNotification('Notification settings updated');
    } catch (error) {
        console.error('Error updating notification settings:', error);
        showNotification(error.message || 'Failed to update notification settings', 'error');
        
        // Revert checkbox state
        const checkbox = row.querySelector(`input[data-type="${type}"]`);
        if (checkbox) {
            checkbox.checked = !enabled;
        }
    }
}

// Remove an account
async function removeAccount(did) {
    // Add confirmation dialog
    if (!confirm('Are you sure you want to remove this account?')) {
        return;
    }

    try {
        const response = await fetch(`/api/accounts/did/${did}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to remove account');
        }

        // Show success message
        showNotification('Account removed successfully');
        
        // Refresh the accounts list
        await loadAccounts();
    } catch (error) {
        console.error('Error removing account:', error);
        showNotification(error.message, 'error');
    }
}
