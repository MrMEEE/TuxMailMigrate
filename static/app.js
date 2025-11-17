// Global state
let servers = [];
let accounts = [];
let syncJobs = [];
let currentLogJobId = null;

// Modal instances
let addServerModal;
let editServerModal;
let addAccountModal;
let editAccountModal;
let addSyncModal;
let editSyncModal;
let syncLogsModal;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap modals
    addServerModal = new bootstrap.Modal(document.getElementById('addServerModal'));
    editServerModal = new bootstrap.Modal(document.getElementById('editServerModal'));
    addAccountModal = new bootstrap.Modal(document.getElementById('addAccountModal'));
    editAccountModal = new bootstrap.Modal(document.getElementById('editAccountModal'));
    addSyncModal = new bootstrap.Modal(document.getElementById('addSyncModal'));
    editSyncModal = new bootstrap.Modal(document.getElementById('editSyncModal'));
    syncLogsModal = new bootstrap.Modal(document.getElementById('syncLogsModal'));
    
    // Load initial data
    loadServers();
    loadAccounts();
    loadSyncJobs();
    updateWorkerStatus();
    
    // Start polling for updates
    setInterval(updateWorkerStatus, 3000);
    setInterval(loadSyncJobs, 5000);
});

// ==================== Servers ====================

async function loadServers() {
    try {
        const response = await fetch('/api/servers');
        servers = await response.json();
        renderServers();
        updateAccountServerSelects();
    } catch (error) {
        console.error('Error loading servers:', error);
        showAlert('Failed to load servers', 'danger');
    }
}

function renderServers() {
    const container = document.getElementById('serversList');
    
    if (servers.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="bi bi-server" style="font-size: 3rem;"></i>
                <p class="mt-2">No server configurations yet. Add your first server to get started.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = servers.map(server => `
        <div class="list-group-item account-item d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-1">
                    ${escapeHtml(server.name)}
                    ${server.server_type ? `<span class="badge bg-secondary ms-2">${escapeHtml(server.server_type)}</span>` : ''}
                </h6>
                <small class="text-muted">
                    <i class="bi bi-link-45deg"></i> ${escapeHtml(server.url)}
                    ${server.principal_path ? `<br><i class="bi bi-diagram-3"></i> ${escapeHtml(server.principal_path)}` : ''}
                    <br><i class="bi bi-people"></i> ${server.account_count} account(s)
                </small>
                ${server.description ? `<div class="small text-muted mt-1">${escapeHtml(server.description)}</div>` : ''}
            </div>
            <div>
                <button class="btn btn-sm btn-primary me-1" onclick="showEditServerModal(${server.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteServer(${server.id}, '${escapeHtml(server.name)}', ${server.account_count})" ${server.account_count > 0 ? 'title="Remove all accounts first"' : ''}>
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function updateServerDefaults(mode) {
    // No longer needed - defaults are handled in the backend
    // Keeping function for backward compatibility with HTML onchange events
}

function showAddServerModal() {
    document.getElementById('addServerForm').reset();
    addServerModal.show();
}

async function addServer() {
    const data = {
        name: document.getElementById('serverName').value,
        url: document.getElementById('serverUrl').value,
        server_type: document.getElementById('serverType').value || null,
        principal_path: document.getElementById('serverPrincipalPath').value || null,
        description: document.getElementById('serverDescription').value || null,
        verify_ssl: document.getElementById('serverVerifySSL').checked
    };
    
    try {
        const response = await fetch('/api/servers', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to add server');
        }
        
        addServerModal.hide();
        showAlert('Server configuration added successfully', 'success');
        loadServers();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function showEditServerModal(id) {
    const server = servers.find(s => s.id === id);
    if (!server) return;
    
    document.getElementById('editServerId').value = server.id;
    document.getElementById('editServerName').value = server.name;
    document.getElementById('editServerUrl').value = server.url;
    document.getElementById('editServerType').value = server.server_type || '';
    document.getElementById('editServerPrincipalPath').value = server.principal_path || '';
    document.getElementById('editServerDescription').value = server.description || '';
    document.getElementById('editServerVerifySSL').checked = server.verify_ssl !== false;
    
    editServerModal.show();
}

async function updateServer() {
    const id = document.getElementById('editServerId').value;
    const data = {
        name: document.getElementById('editServerName').value,
        url: document.getElementById('editServerUrl').value,
        server_type: document.getElementById('editServerType').value || null,
        principal_path: document.getElementById('editServerPrincipalPath').value || null,
        description: document.getElementById('editServerDescription').value || null,
        verify_ssl: document.getElementById('editServerVerifySSL').checked
    };
    
    try {
        const response = await fetch(`/api/servers/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update server');
        }
        
        editServerModal.hide();
        showAlert('Server configuration updated successfully', 'success');
        loadServers();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function deleteServer(id, name, accountCount) {
    if (accountCount > 0) {
        showAlert(`Cannot delete server "${name}" because it has ${accountCount} account(s). Delete those accounts first.`, 'warning');
        return;
    }
    
    if (!confirm(`Delete server configuration "${name}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/servers/${id}`, {method: 'DELETE'});
        
        if (!response.ok) {
            throw new Error('Failed to delete server');
        }
        
        showAlert('Server configuration deleted', 'success');
        loadServers();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

function updateAccountServerSelects() {
    const select = document.getElementById('accountServerId');
    if (!select) return;
    
    const options = servers.map(server => 
        `<option value="${server.id}">${escapeHtml(server.name)} (${escapeHtml(server.url)})</option>`
    ).join('');
    
    select.innerHTML = '<option value="">Select server...</option>' + options;
}

function updateEditAccountServerSelects() {
    const select = document.getElementById('editAccountServerId');
    if (!select) return;
    
    const options = servers.map(server => 
        `<option value="${server.id}">${escapeHtml(server.name)} (${escapeHtml(server.url)})</option>`
    ).join('');
    
    select.innerHTML = '<option value="">Select server...</option>' + options;
}

// ==================== Accounts ====================

async function loadAccounts() {
    try {
        const response = await fetch('/api/accounts');
        accounts = await response.json();
        renderAccounts();
        updateSyncAccountSelects();
    } catch (error) {
        console.error('Error loading accounts:', error);
        showAlert('Failed to load accounts', 'danger');
    }
}

function renderAccounts() {
    const container = document.getElementById('accountsList');
    
    if (accounts.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="bi bi-inbox" style="font-size: 3rem;"></i>
                <p class="mt-2">No accounts yet. Add your first account to get started.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = accounts.map(account => `
        <div class="list-group-item account-item d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-1">${escapeHtml(account.name)}</h6>
                <small class="text-muted">
                    <i class="bi bi-server"></i> ${escapeHtml(account.server_name || 'Unknown')}
                    <br>
                    <i class="bi bi-link-45deg"></i> ${escapeHtml(account.server_url || 'N/A')}
                    <br>
                    <i class="bi bi-person"></i> ${escapeHtml(account.username)}
                </small>
            </div>
            <div>
                <button class="btn btn-sm btn-primary me-1" onclick="showEditAccountModal(${account.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteAccount(${account.id}, '${escapeHtml(account.name)}')">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function showAddAccountModal() {
    if (servers.length === 0) {
        showAlert('Please add a server configuration first', 'warning');
        return;
    }
    
    document.getElementById('addAccountForm').reset();
    updateAccountServerSelects();
    addAccountModal.show();
}

async function addAccount() {
    const serverId = parseInt(document.getElementById('accountServerId').value);
    
    if (!serverId) {
        showAlert('Please select a server', 'warning');
        return;
    }
    
    const data = {
        name: document.getElementById('accountName').value,
        server_id: serverId,
        username: document.getElementById('accountUsername').value,
        password: document.getElementById('accountPassword').value
    };
    
    try {
        const response = await fetch('/api/accounts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to add account');
        }
        
        addAccountModal.hide();
        showAlert('Account added successfully', 'success');
        loadAccounts();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function showEditAccountModal(id) {
    const account = accounts.find(a => a.id === id);
    if (!account) return;
    
    document.getElementById('editAccountId').value = account.id;
    document.getElementById('editAccountName').value = account.name;
    document.getElementById('editAccountServerId').value = account.server_id;
    document.getElementById('editAccountUsername').value = account.username;
    document.getElementById('editAccountPassword').value = ''; // Don't show password
    
    updateEditAccountServerSelects();
    editAccountModal.show();
}

async function updateAccount() {
    const id = document.getElementById('editAccountId').value;
    const serverId = parseInt(document.getElementById('editAccountServerId').value);
    
    if (!serverId) {
        showAlert('Please select a server', 'warning');
        return;
    }
    
    const data = {
        name: document.getElementById('editAccountName').value,
        server_id: serverId,
        username: document.getElementById('editAccountUsername').value
    };
    
    // Only update password if it's not empty
    const password = document.getElementById('editAccountPassword').value;
    if (password) {
        data.password = password;
    }
    
    try {
        const response = await fetch(`/api/accounts/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update account');
        }
        
        editAccountModal.hide();
        showAlert('Account updated successfully', 'success');
        loadAccounts();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function deleteAccount(id, name) {
    if (!confirm(`Delete account "${name}"? This will also delete all associated sync jobs.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/accounts/${id}`, {method: 'DELETE'});
        
        if (!response.ok) {
            throw new Error('Failed to delete account');
        }
        
        showAlert('Account deleted', 'success');
        loadAccounts();
        loadSyncJobs();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

// ==================== Sync Jobs ====================

async function loadSyncJobs() {
    try {
        const response = await fetch('/api/sync-jobs');
        syncJobs = await response.json();
        renderSyncJobs();
    } catch (error) {
        console.error('Error loading sync jobs:', error);
    }
}

function renderSyncJobs() {
    const container = document.getElementById('syncJobsList');
    
    if (syncJobs.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="bi bi-calendar-x" style="font-size: 3rem;"></i>
                <p class="mt-2">No sync jobs yet. Create your first synchronization job.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = syncJobs.map(job => renderSyncJobCard(job)).join('');
}

function renderSyncJobCard(job) {
    const statusClass = getStatusClass(job.status);
    const statusIcon = getStatusIcon(job.status);
    const statusBadge = `<span class="badge bg-${statusClass}">${statusIcon} ${job.status.toUpperCase()}</span>`;
    
    const stats = job.stats || {};
    const hasStats = Object.keys(stats).length > 0;
    
    return `
        <div class="card sync-job-card sync-job-${job.status}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h5 class="card-title mb-1">${escapeHtml(job.name)}</h5>
                        <small class="text-muted">
                            <i class="bi bi-box-arrow-right"></i> ${escapeHtml(job.source_name || 'Unknown')}
                            <i class="bi bi-arrow-right mx-2"></i>
                            <i class="bi bi-box-arrow-in-left"></i> ${escapeHtml(job.destination_name || 'Unknown')}
                        </small>
                    </div>
                    <div>
                        ${statusBadge}
                    </div>
                </div>
                
                ${job.status === 'running' || job.status === 'queued' ? `
                    <div class="progress mb-3">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" 
                             style="width: ${job.progress}%"
                             aria-valuenow="${job.progress}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                            ${job.progress}%
                        </div>
                    </div>
                ` : ''}
                
                ${job.error_message ? `
                    <div class="alert alert-danger mb-3" role="alert">
                        <i class="bi bi-exclamation-triangle"></i> ${escapeHtml(job.error_message)}
                    </div>
                ` : ''}
                
                ${hasStats ? `
                    <div class="row text-center mb-3">
                        ${job.migrate_calendars ? `
                            <div class="col-6">
                                <small class="text-muted">Calendars</small>
                                <div><strong>${stats.calendars_migrated || 0}</strong> / ${(stats.calendars_migrated || 0) + (stats.calendars_failed || 0)}</div>
                                ${stats.dry_run_details && stats.dry_run_details.calendars && stats.dry_run_details.calendars.length > 0 ? `
                                    <small class="text-muted" style="font-size: 0.75rem;">
                                        ${stats.dry_run_details.calendars.map(cal => escapeHtml(cal.name)).join(', ')}
                                    </small>
                                ` : ''}
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Events</small>
                                ${stats.dry_run_details && stats.dry_run_details.calendars && stats.dry_run_details.calendars.length > 0 ? `
                                    <div><strong>${stats.dry_run_details.calendars.reduce((sum, cal) => sum + (cal.event_count || 0), 0)}</strong> total</div>
                                    ${(() => {
                                        const totalDummy = stats.dry_run_details.calendars.reduce((sum, cal) => sum + (cal.dummy_count || 0), 0);
                                        return totalDummy > 0 ? `<small class="text-warning" style="font-size: 0.75rem;">⏭️ ${totalDummy} "Dummy" event(s) would be skipped</small>` : '';
                                    })()}
                                ` : `
                                    <div><strong>${stats.events_migrated || 0}</strong> / ${(stats.events_migrated || 0) + (stats.events_failed || 0)}</div>
                                `}
                            </div>
                        ` : ''}
                        ${job.migrate_contacts ? `
                            <div class="col-6">
                                <small class="text-muted">Address Books</small>
                                <div><strong>${stats.addressbooks_migrated || 0}</strong> / ${(stats.addressbooks_migrated || 0) + (stats.addressbooks_failed || 0)}</div>
                                ${stats.dry_run_details && stats.dry_run_details.addressbooks && stats.dry_run_details.addressbooks.length > 0 ? `
                                    <small class="text-muted" style="font-size: 0.75rem;">
                                        ${stats.dry_run_details.addressbooks.map(ab => escapeHtml(ab.name)).join(', ')}
                                    </small>
                                ` : ''}
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Contacts</small>
                                ${stats.dry_run_details && stats.dry_run_details.addressbooks && stats.dry_run_details.addressbooks.length > 0 ? `
                                    <div><strong>${stats.dry_run_details.addressbooks.reduce((sum, ab) => sum + (ab.contact_count || 0), 0)}</strong> total</div>
                                ` : `
                                    <div><strong>${stats.contacts_migrated || 0}</strong> / ${(stats.contacts_migrated || 0) + (stats.contacts_failed || 0)}</div>
                                `}
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
                
                <div class="d-flex justify-content-between align-items-center">
                    <div class="btn-group btn-group-sm" role="group">
                        ${job.status === 'pending' || job.status === 'completed' || job.status === 'failed' ? `
                            <button class="btn btn-success" onclick="startSyncJob(${job.id}, false)" title="Start full sync">
                                <i class="bi bi-play-fill"></i> Start
                            </button>
                            <button class="btn btn-outline-info" onclick="startSyncJob(${job.id}, true)" title="Dry run - analyze without copying">
                                <i class="bi bi-eye"></i> Dry Run
                            </button>
                            ${job.migrate_calendars ? `
                                <button class="btn btn-outline-success" onclick="startSyncJob(${job.id}, false, 'calendars')" title="Sync calendars only">
                                    <i class="bi bi-calendar"></i> Events
                                </button>
                            ` : ''}
                            ${job.migrate_contacts ? `
                                <button class="btn btn-outline-success" onclick="startSyncJob(${job.id}, false, 'contacts')" title="Sync contacts only">
                                    <i class="bi bi-person"></i> Contacts
                                </button>
                            ` : ''}
                        ` : ''}
                        ${job.status === 'running' ? `
                            <button class="btn btn-warning" onclick="pauseSyncJob(${job.id})">
                                <i class="bi bi-pause-fill"></i> Pause
                            </button>
                            <button class="btn btn-danger" onclick="cancelSyncJob(${job.id})" title="Cancel running sync">
                                <i class="bi bi-x-circle"></i> Cancel
                            </button>
                        ` : ''}
                        ${job.status === 'paused' ? `
                            <button class="btn btn-info" onclick="resumeSyncJob(${job.id})">
                                <i class="bi bi-play-fill"></i> Resume
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary" onclick="showSyncLogs(${job.id})">
                            <i class="bi bi-file-text"></i> Logs
                        </button>
                        ${job.status !== 'running' && job.status !== 'queued' ? `
                            <button class="btn btn-primary" onclick="showEditSyncModal(${job.id})">
                                <i class="bi bi-pencil"></i> Edit
                            </button>
                        ` : ''}
                        ${job.status !== 'running' ? `
                            <button class="btn btn-danger" onclick="deleteSyncJob(${job.id}, '${escapeHtml(job.name)}')">
                                <i class="bi bi-trash"></i> Delete
                            </button>
                        ` : ''}
                    </div>
                    <small class="text-muted">
                        ${job.created_at ? `Created: ${formatDate(job.created_at)}` : ''}
                    </small>
                </div>
            </div>
        </div>
    `;
}

function showAddSyncModal() {
    if (accounts.length < 2) {
        showAlert('You need at least 2 accounts to create a sync job', 'warning');
        return;
    }
    
    document.getElementById('addSyncForm').reset();
    updateSyncAccountSelects();
    addSyncModal.show();
}

function updateSyncAccountSelects() {
    const sourceSelect = document.getElementById('syncSourceId');
    const destSelect = document.getElementById('syncDestinationId');
    
    if (!sourceSelect || !destSelect) return;
    
    const options = accounts.map(acc => 
        `<option value="${acc.id}">${escapeHtml(acc.name)}</option>`
    ).join('');
    
    sourceSelect.innerHTML = '<option value="">Select source...</option>' + options;
    destSelect.innerHTML = '<option value="">Select destination...</option>' + options;
}

function updateEditSyncAccountSelects() {
    const sourceSelect = document.getElementById('editSyncSourceId');
    const destSelect = document.getElementById('editSyncDestinationId');
    
    if (!sourceSelect || !destSelect) return;
    
    const options = accounts.map(acc => 
        `<option value="${acc.id}">${escapeHtml(acc.name)}</option>`
    ).join('');
    
    sourceSelect.innerHTML = '<option value="">Select source...</option>' + options;
    destSelect.innerHTML = '<option value="">Select destination...</option>' + options;
}

async function addSyncJob() {
    const data = {
        name: document.getElementById('syncName').value,
        source_id: parseInt(document.getElementById('syncSourceId').value),
        destination_id: parseInt(document.getElementById('syncDestinationId').value),
        migrate_calendars: document.getElementById('syncMigrateCalendars').checked,
        migrate_contacts: document.getElementById('syncMigrateContacts').checked,
        create_collections: document.getElementById('syncCreateCollections').checked,
        skip_dummy_events: document.getElementById('syncSkipDummy').checked
    };
    
    if (!data.source_id || !data.destination_id) {
        showAlert('Please select both source and destination accounts', 'warning');
        return;
    }
    
    if (data.source_id === data.destination_id) {
        showAlert('Source and destination must be different', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/sync-jobs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create sync job');
        }
        
        addSyncModal.hide();
        showAlert('Sync job created successfully', 'success');
        loadSyncJobs();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function showEditSyncModal(id) {
    const job = syncJobs.find(j => j.id === id);
    if (!job) return;
    
    document.getElementById('editSyncId').value = job.id;
    document.getElementById('editSyncName').value = job.name;
    document.getElementById('editSyncSourceId').value = job.source_id;
    document.getElementById('editSyncDestinationId').value = job.destination_id;
    document.getElementById('editSyncMigrateCalendars').checked = job.migrate_calendars;
    document.getElementById('editSyncMigrateContacts').checked = job.migrate_contacts;
    document.getElementById('editSyncCreateCollections').checked = job.create_collections;
    document.getElementById('editSyncSkipDummy').checked = job.skip_dummy_events || false;
    
    updateEditSyncAccountSelects();
    editSyncModal.show();
}

async function updateSyncJob() {
    const id = document.getElementById('editSyncId').value;
    const data = {
        name: document.getElementById('editSyncName').value,
        source_id: parseInt(document.getElementById('editSyncSourceId').value),
        destination_id: parseInt(document.getElementById('editSyncDestinationId').value),
        migrate_calendars: document.getElementById('editSyncMigrateCalendars').checked,
        migrate_contacts: document.getElementById('editSyncMigrateContacts').checked,
        create_collections: document.getElementById('editSyncCreateCollections').checked,
        skip_dummy_events: document.getElementById('editSyncSkipDummy').checked
    };
    
    if (!data.source_id || !data.destination_id) {
        showAlert('Please select both source and destination accounts', 'warning');
        return;
    }
    
    if (data.source_id === data.destination_id) {
        showAlert('Source and destination must be different', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/sync-jobs/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update sync job');
        }
        
        editSyncModal.hide();
        showAlert('Sync job updated successfully', 'success');
        loadSyncJobs();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function startSyncJob(id, dryRun = false, mode = 'full') {
    try {
        // First update the job with dry_run setting
        if (dryRun) {
            const updateResponse = await fetch(`/api/sync-jobs/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dry_run: true})
            });
            if (!updateResponse.ok) {
                throw new Error('Failed to set dry-run mode');
            }
        } else {
            // Make sure dry_run is false for normal start
            const updateResponse = await fetch(`/api/sync-jobs/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dry_run: false})
            });
        }
        
        // Prepare request body for selective sync
        const requestBody = {};
        if (mode === 'calendars') {
            requestBody.calendars_only = true;
        } else if (mode === 'contacts') {
            requestBody.contacts_only = true;
        }
        
        const response = await fetch(`/api/sync-jobs/${id}/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start job');
        }
        
        let message = 'Sync job started';
        if (dryRun) {
            message = 'Dry run started - analyzing data';
        } else if (mode === 'calendars') {
            message = 'Calendar sync started';
        } else if (mode === 'contacts') {
            message = 'Contact sync started';
        }
        
        showAlert(message, 'success');
        loadSyncJobs();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function cancelSyncJob(id) {
    try {
        const response = await fetch(`/api/sync-jobs/${id}/cancel`, {method: 'POST'});
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to cancel job');
        }
        
        showAlert('Cancellation requested', 'warning');
        loadSyncJobs();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function pauseSyncJob(id) {
    try {
        const response = await fetch(`/api/sync-jobs/${id}/pause`, {method: 'POST'});
        
        if (!response.ok) {
            throw new Error('Failed to pause job');
        }
        
        showAlert('Sync job paused', 'info');
        loadSyncJobs();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function resumeSyncJob(id) {
    try {
        const response = await fetch(`/api/sync-jobs/${id}/resume`, {method: 'POST'});
        
        if (!response.ok) {
            throw new Error('Failed to resume job');
        }
        
        showAlert('Sync job resumed', 'success');
        loadSyncJobs();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function deleteSyncJob(id, name) {
    if (!confirm(`Delete sync job "${name}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sync-jobs/${id}`, {method: 'DELETE'});
        
        if (!response.ok) {
            throw new Error('Failed to delete sync job');
        }
        
        showAlert('Sync job deleted', 'success');
        loadSyncJobs();
    } catch (error) {
        showAlert(error.message, 'danger');
    }
}

async function showSyncLogs(jobId) {
    currentLogJobId = jobId;
    syncLogsModal.show();
    
    const container = document.getElementById('syncLogsContent');
    container.innerHTML = '<div class="text-center p-4"><div class="spinner-border"></div></div>';
    
    try {
        const response = await fetch(`/api/sync-jobs/${jobId}/logs`);
        const logs = await response.json();
        
        if (logs.length === 0) {
            container.innerHTML = '<div class="text-center text-muted p-4">No logs yet</div>';
            return;
        }
        
        container.innerHTML = logs.map(log => `
            <div class="log-entry ${log.level}">
                <strong>[${log.level}]</strong> 
                <small class="text-muted">${formatDate(log.timestamp)}</small>
                <br>
                ${escapeHtml(log.message)}
            </div>
        `).join('');
        
    } catch (error) {
        container.innerHTML = '<div class="alert alert-danger">Failed to load logs</div>';
    }
}

// ==================== Worker Status ====================

async function updateWorkerStatus() {
    try {
        const response = await fetch('/api/worker/status');
        const status = await response.json();
        
        const indicator = document.getElementById('workerIndicator');
        const text = document.getElementById('workerText');
        
        if (status.running && !status.paused) {
            indicator.className = 'bi bi-circle-fill text-success pulse';
            if (status.current_job_id) {
                text.textContent = `Running Job #${status.current_job_id}`;
            } else {
                text.textContent = 'Worker Ready';
            }
        } else if (status.paused) {
            indicator.className = 'bi bi-circle-fill text-warning';
            text.textContent = 'Worker Paused';
        } else {
            indicator.className = 'bi bi-circle-fill text-secondary';
            text.textContent = 'Worker Stopped';
        }
    } catch (error) {
        console.error('Failed to update worker status:', error);
    }
}

// ==================== Utilities ====================

function getStatusClass(status) {
    const classes = {
        'pending': 'secondary',
        'queued': 'info',
        'running': 'primary',
        'paused': 'warning',
        'completed': 'success',
        'failed': 'danger'
    };
    return classes[status] || 'secondary';
}

function getStatusIcon(status) {
    const icons = {
        'pending': '<i class="bi bi-clock"></i>',
        'queued': '<i class="bi bi-hourglass-split"></i>',
        'running': '<i class="bi bi-arrow-repeat"></i>',
        'paused': '<i class="bi bi-pause"></i>',
        'completed': '<i class="bi bi-check-circle"></i>',
        'failed': '<i class="bi bi-x-circle"></i>'
    };
    return icons[status] || '<i class="bi bi-question"></i>';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
