// Admin Dashboard JavaScript
let adminDashboard;

class AdminDashboard {
    constructor() {
        this.authToken = localStorage.getItem('admin_token');
        this.adminData = null;
        this.currentSection = 'dashboard';
        this.pendingAppointmentsCount = 0;
    }

    // ============ AUTHENTICATION ============
    
    async checkAdminAuth() {
        // Refresh token from localStorage in case it was just set
        this.authToken = localStorage.getItem('admin_token');
        
        if (!this.authToken) {
            console.warn('No auth token found, redirecting to home');
            setTimeout(() => {
                window.location.href = '/';
            }, 100);
            return;
        }
        
        try {
            const response = await fetch('/admin/auth/verify', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.adminData = data.admin;
                
                if (!data.valid || data.admin.role !== 'admin') {
                    alert('Access denied. Admin privileges required.');
                    window.location.href = '/';
                    return;
                }
                
                // Update admin name in UI
                const adminNameElement = document.getElementById('adminName');
                if (adminNameElement) {
                    adminNameElement.textContent = data.admin.name;
                }
                
                this.loadPendingNotifications();
            } else {
                throw new Error('Authentication failed');
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            
            // Be more specific about the error
            if (error.message.includes('Failed to fetch')) {
                console.error('Network error during auth check');
                // Don't redirect immediately on network errors - might be temporary
                setTimeout(() => {
                    if (!this.adminData) {
                        alert('Network error. Please check your connection and try again.');
                        window.location.href = '/';
                    }
                }, 2000);
                return;
            }
            
            // Clear auth data and redirect for authentication failures
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin_data');
            alert('Admin session expired. Please login again.');
            window.location.href = '/';
        }
    }

    // ============ SECTION MANAGEMENT ============
    
    showSection(sectionName) {
        // Check if auth token is available before switching sections
        if (!this.authToken) {
            console.warn('Auth token not ready, deferring section switch');
            // Retry after a short delay
            setTimeout(() => this.showSection(sectionName), 100);
            return;
        }

        // Hide all sections
        const sections = document.querySelectorAll('.admin-section');
        sections.forEach(section => {
            section.style.display = 'none';
        });

        // Show selected section
        const targetSection = document.getElementById(sectionName + 'Section');
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        // Update navigation
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        this.currentSection = sectionName;

        // Load section-specific data
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboardStats();
                this.loadPendingNotifications();
                break;
            case 'medicines':
                this.loadMedicines();
                break;
            case 'orders':
                this.loadOrders();
                break;
            case 'appointments':
                this.loadAppointments();
                this.loadPendingNotifications();
                break;
            case 'timeslots':
                this.loadTimeSlots();
                break;
            case 'doctors':
                this.loadDoctors();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'chats':
                this.loadChatLogs();
                break;
        }
    }

    // ============ DASHBOARD STATS ============
    
    async loadDashboardStats() {
        try {
            const response = await fetch('/admin/api/stats', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const stats = await response.json();
                this.updateDashboardUI(stats);
            } else {
                console.error('Failed to load dashboard stats');
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }

    updateDashboardUI(stats) {
        // Update stat cards
        document.getElementById('totalUsers').textContent = stats.total_users || 0;
        document.getElementById('totalOrders').textContent = stats.total_orders || 0;
        document.getElementById('totalAppointments').textContent = stats.total_appointments || 0;
        document.getElementById('totalRevenue').textContent = `PKR ${stats.total_revenue || 0}`;
    }

    // ============ NOTIFICATIONS ============
    
    async loadPendingNotifications() {
        try {
            const response = await fetch('/admin/api/appointments?approval_status=pending', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.pendingAppointmentsCount = data.appointments?.length || 0;
                this.updateNotificationUI();
            }
        } catch (error) {
            console.error('Error loading pending notifications:', error);
        }
    }

    updateNotificationUI() {
        // Update badge in navigation
        const badge = document.getElementById('pendingAppointmentsBadge');
        if (badge) {
            if (this.pendingAppointmentsCount > 0) {
                badge.textContent = this.pendingAppointmentsCount;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        }

        // Update dashboard alert
        const alert = document.getElementById('pendingAppointmentsAlert');
        const alertText = document.getElementById('pendingAppointmentsText');
        
        if (alert && alertText) {
            if (this.pendingAppointmentsCount > 0) {
                alert.classList.remove('d-none');
                alertText.textContent = `You have ${this.pendingAppointmentsCount} appointment${this.pendingAppointmentsCount > 1 ? 's' : ''} waiting for approval`;
            } else {
                alert.classList.add('d-none');
            }
        }
    }

    // ============ MEDICINES MANAGEMENT ============
    
    async loadMedicines() {
        try {
            const response = await fetch('/admin/api/medicines', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderMedicinesTable(data);
            } else {
                console.error('Failed to load medicines:', response.status);
                this.showAlert('Failed to load medicines', 'danger');
            }
        } catch (error) {
            console.error('Error loading medicines:', error);
            this.showAlert('Error loading medicines', 'danger');
        }
    }

    renderMedicinesTable(data) {
        const tbody = document.getElementById('medicinesTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        // Handle both old format (array) and new format (object with medicines array)
        const medicines = data.medicines || data;
        
        if (medicines && medicines.length > 0) {
            medicines.forEach(medicine => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${medicine.id}</td>
                    <td>
                        <div class="d-flex align-items-center">
                            <img src="${medicine.image_path || '/static/images/default-medicine.png'}" 
                                 alt="${medicine.name}" class="rounded me-2" 
                                 style="width: 40px; height: 40px; object-fit: cover;">
                            <span>${medicine.name}</span>
                        </div>
                    </td>
                    <td>${medicine.chemical || '-'}</td>
                    <td>${medicine.category || '-'}</td>
                    <td>PKR ${medicine.price}</td>
                    <td>${medicine.stock_quantity}</td>
                    <td><span class="badge bg-${medicine.status === 'in_stock' ? 'success' : 'danger'}">${medicine.status.replace('_', ' ')}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="editMedicine(${medicine.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteMedicine(${medicine.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">No medicines found</td></tr>';
        }
    }

    // ============ ORDERS MANAGEMENT ============
    
    async loadOrders() {
        try {
            const response = await fetch('/admin/api/orders', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const orders = await response.json();
                this.renderOrdersTable(orders);
            }
        } catch (error) {
            console.error('Error loading orders:', error);
        }
    }

    renderOrdersTable(orders) {
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        orders.forEach(order => {
            const row = document.createElement('tr');
            const orderDate = new Date(order.created_at).toLocaleDateString();
            
            row.innerHTML = `
                <td>#${order.id}</td>
                <td>${order.customer_name || 'Unknown'}</td>
                <td>${order.total_items || 0} items</td>
                <td>PKR ${order.total_amount}</td>
                <td><span class="badge bg-${this.getStatusColor(order.status)}">${order.status}</span></td>
                <td>${orderDate}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewOrder(${order.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="updateOrderStatus(${order.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // ============ APPOINTMENTS MANAGEMENT ============
    
    async loadAppointments(filter = 'all') {
        try {
            let url = '/admin/api/appointments';
            if (filter !== 'all') {
                url += `?approval_status=${filter}`;
            }
            
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderAppointmentsTable(data.appointments);
                
                // Update counters
                document.getElementById('pendingAppointmentsCount').textContent = data.pending_count || 0;
                document.getElementById('approvedAppointmentsCount').textContent = data.approved_count || 0;
            }
        } catch (error) {
            console.error('Error loading appointments:', error);
        }
    }

    renderAppointmentsTable(appointments) {
        const tbody = document.getElementById('appointmentsTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        appointments.forEach(appointment => {
            const row = document.createElement('tr');
            const appointmentDate = new Date(appointment.starts_at).toLocaleString();
            const isApprovalPending = appointment.approval_status === 'pending';
            
            row.innerHTML = `
                <td>${appointment.id}</td>
                <td>${appointment.patient_name || 'Unknown'}<br><small class="text-muted">${appointment.patient_email}</small></td>
                <td>${appointment.doctor_name || 'Unknown'}</td>
                <td>${appointmentDate}<br><small class="text-muted">${appointment.appointment_date}</small></td>
                <td><span class="badge bg-${this.getApprovalStatusColor(appointment.approval_status)}">${appointment.approval_status}</span></td>
                <td><span class="badge bg-${this.getStatusColor(appointment.status)}">${appointment.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="viewAppointment(${appointment.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${isApprovalPending ? `
                        <button class="btn btn-sm btn-outline-success me-1" onclick="approveAppointment(${appointment.id})" title="Approve">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="declineAppointment(${appointment.id})" title="Decline">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : `
                        <button class="btn btn-sm btn-outline-warning" onclick="cancelAppointment(${appointment.id})" title="Cancel">
                            <i class="fas fa-ban"></i>
                        </button>
                    `}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // ============ DOCTOR AVAILABILITY MANAGEMENT ============
    
    async loadTimeSlots() {
        try {
            const response = await fetch('/admin/api/availability', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentAvailabilities = data.availabilities || [];
                this.renderAvailabilityTable(this.currentAvailabilities);
                this.loadDoctorsForSlots();
            }
        } catch (error) {
            console.error('Error loading availabilities:', error);
        }
    }

    async loadDoctorsForSlots() {
        try {
            const response = await fetch('/admin/api/users?role=doctor', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                const doctorSelect = document.getElementById('slotDoctorId');
                if (doctorSelect) {
                    doctorSelect.innerHTML = '<option value="">Select Doctor</option>';
                    data.users.forEach(doctor => {
                        doctorSelect.innerHTML += `<option value="${doctor.id}">${doctor.name} - ${doctor.specialization || 'General'}</option>`;
                    });
                }
            }
        } catch (error) {
            console.error('Error loading doctors:', error);
        }
    }

    renderAvailabilityTable(availabilities) {
        const tbody = document.getElementById('timeSlotsTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (availabilities.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        <i class="fas fa-calendar-plus fa-3x mb-3 d-block"></i>
                        No doctor availability schedules found. Add one above to get started.
                    </td>
                </tr>
            `;
            return;
        }

        availabilities.forEach(avail => {
            const row = document.createElement('tr');
            const statusBadge = avail.is_active ? 
                '<span class="badge bg-success">Active</span>' : 
                '<span class="badge bg-secondary">Inactive</span>';
            
            row.innerHTML = `
                <td><strong>${avail.doctor_name}</strong></td>
                <td><span class="badge bg-primary">${avail.day_name}</span></td>
                <td>${avail.start_time} - ${avail.end_time}</td>
                <td>${avail.slot_duration} min</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteAvailability(${avail.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    renderTimeSlotsTable(data) {
        // Alias for compatibility
        this.renderAvailabilityTable(data);
    }

    // ============ DOCTORS MANAGEMENT ============
    
    async loadDoctors() {
        try {
            const response = await fetch('/admin/api/doctors', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayDoctors(data.doctors);
            } else {
                console.error('Failed to load doctors');
            }
        } catch (error) {
            console.error('Error loading doctors:', error);
        }
    }

    displayDoctors(doctors) {
        const tbody = document.getElementById('doctorsTableBody');
        
        if (doctors.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">No doctors found</td></tr>';
            return;
        }

        tbody.innerHTML = doctors.map(doctor => `
            <tr>
                <td>${doctor.id}</td>
                <td>${doctor.name}</td>
                <td>${doctor.email}</td>
                <td>${doctor.specialization || 'N/A'}</td>
                <td>${doctor.experience_years ? doctor.experience_years + ' years' : 'N/A'}</td>
                <td>${doctor.current_hospital || 'N/A'}</td>
                <td>${doctor.phone || 'N/A'}</td>
                <td>${doctor.appointment_count}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editDoctor(${doctor.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteDoctor(${doctor.id}, '${doctor.name}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // ============ USERS MANAGEMENT ============
    
    async loadUsers() {
        try {
            const response = await fetch('/admin/api/users', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const users = await response.json();
                this.renderUsersTable(users);
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    renderUsersTable(users) {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        users.forEach(user => {
            const row = document.createElement('tr');
            const joinDate = new Date(user.created_at).toLocaleDateString();
            
            row.innerHTML = `
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td><span class="badge bg-${this.getRoleColor(user.role)}">${user.role}</span></td>
                <td>${user.phone || '-'}</td>
                <td>${joinDate}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="editUser(${user.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // ============ CHAT LOGS ============
    
    async loadChatLogs() {
        try {
            const response = await fetch('/admin/api/chatlogs', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const chatLogs = await response.json();
                this.renderChatLogs(chatLogs);
            }
        } catch (error) {
            console.error('Error loading chat logs:', error);
        }
    }

    renderChatLogs(chatLogs) {
        const container = document.getElementById('chatLogsList');
        if (!container) return;

        container.innerHTML = '';

        chatLogs.forEach(log => {
            const logElement = document.createElement('div');
            logElement.className = `chat-log-item mb-3 p-3 border rounded ${log.flagged ? 'border-danger' : 'border-light'}`;
            
            const logDate = new Date(log.created_at).toLocaleString();
            
            logElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <small class="text-muted">Session: ${log.session_id}</small>
                    <div>
                        <span class="badge bg-${log.language === 'ur' ? 'info' : 'secondary'}">${log.language.toUpperCase()}</span>
                        ${log.flagged ? '<span class="badge bg-danger ms-1">Flagged</span>' : ''}
                    </div>
                </div>
                <div class="mb-2">
                    <strong>User:</strong> ${log.message}
                </div>
                <div class="mb-2">
                    <strong>Bot:</strong> ${log.response}
                </div>
                <small class="text-muted">${logDate}</small>
            `;
            
            container.appendChild(logElement);
        });
    }

    // ============ UTILITY FUNCTIONS ============
    
    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'processing': 'info',
            'out_for_delivery': 'primary',
            'delivered': 'success',
            'cancelled': 'danger',
            'scheduled': 'info',
            'ongoing': 'warning',
            'completed': 'success'
        };
        return colors[status] || 'secondary';
    }

    getApprovalStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'approved': 'success',
            'declined': 'danger'
        };
        return colors[status] || 'secondary';
    }

    getRoleColor(role) {
        const colors = {
            'admin': 'danger',
            'doctor': 'success',
            'patient': 'primary'
        };
        return colors[role] || 'secondary';
    }

    // ============ LOGOUT ============
    
    adminLogout() {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_data');
        window.location.href = '/';
    }

    // ============ CHARTS INITIALIZATION ============
    
    initializeCharts() {
        // Revenue Chart
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            new Chart(revenueCtx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Revenue (PKR)',
                        data: [12000, 19000, 15000, 25000, 22000, 30000],
                        borderColor: '#dc3545',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Order Status Chart
        const orderStatusCtx = document.getElementById('orderStatusChart');
        if (orderStatusCtx) {
            new Chart(orderStatusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Pending', 'Processing', 'Delivered', 'Cancelled'],
                    datasets: [{
                        data: [20, 35, 40, 5],
                        backgroundColor: ['#ffc107', '#17a2b8', '#28a745', '#dc3545']
                    }]
                },
                options: {
                    responsive: true
                }
            });
        }
    }
}

// Global functions for template onclick handlers

function checkAdminAuth() {
    if (adminDashboard) {
        adminDashboard.checkAdminAuth();
    }
}

function showSection(sectionName) {
    if (adminDashboard && adminDashboard.showSection) {
        adminDashboard.showSection(sectionName);
    } else {
        console.error('Admin dashboard not initialized or showSection method not available');
    }
}

function loadDashboardStats() {
    if (adminDashboard) {
        adminDashboard.loadDashboardStats();
    }
}

function initializeCharts() {
    if (adminDashboard) {
        adminDashboard.initializeCharts();
    }
}

function adminLogout() {
    if (adminDashboard) {
        adminDashboard.adminLogout();
    }
}

// ============ TIME SLOT FUNCTIONS ============

async function addTimeSlot(event) {
    event.preventDefault();
    
    const doctorId = document.getElementById('slotDoctorId').value;
    const dayOfWeek = document.getElementById('slotDayOfWeek').value;
    const startTime = document.getElementById('slotStartTime').value;
    const endTime = document.getElementById('slotEndTime').value;
    const slotDuration = document.getElementById('slotDuration').value;
    
    if (!doctorId || !startTime || !endTime) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('/admin/api/availability', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                doctor_id: parseInt(doctorId),
                day_of_week: parseInt(dayOfWeek),
                start_time: startTime,
                end_time: endTime,
                slot_duration: parseInt(slotDuration)
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Doctor availability added successfully! Time slots will be auto-generated.');
            document.getElementById('addTimeSlotForm').reset();
            adminDashboard.loadTimeSlots();
        } else {
            alert(result.error || 'Failed to add availability');
        }
    } catch (error) {
        console.error('Error adding availability:', error);
        alert('Failed to add availability');
    }
}

async function deleteAvailability(availId) {
    if (!confirm('Are you sure you want to delete this availability schedule?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/availability/${availId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Availability deleted successfully!');
            adminDashboard.loadTimeSlots();
        } else {
            alert(result.error || 'Failed to delete availability');
        }
    } catch (error) {
        console.error('Error deleting availability:', error);
        alert('Failed to delete availability');
    }
}

function filterAvailabilityByDay(dayOfWeek) {
    // Update active tab
    const tabs = document.querySelectorAll('#dayTabs .nav-link');
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
    
    // Filter the current availabilities
    if (!adminDashboard.currentAvailabilities) {
        return;
    }
    
    const filtered = dayOfWeek === -1 ? 
        adminDashboard.currentAvailabilities :
        adminDashboard.currentAvailabilities.filter(a => a.day_of_week === dayOfWeek);
    
    adminDashboard.renderAvailabilityTable(filtered);
}

async function generateTimeSlots() {
    if (!confirm('This will generate time slots for all active doctor availabilities for the next 30 days. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch('/admin/api/availability/generate-slots', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(result.message || 'Time slots generated successfully!');
        } else {
            alert(result.error || 'Failed to generate time slots');
        }
    } catch (error) {
        console.error('Error generating time slots:', error);
        alert('Failed to generate time slots');
    }
}

async function toggleSlotAvailability(slotId, isAvailable) {
    try {
        const response = await fetch(`/admin/api/timeslots/${slotId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_available: isAvailable
            })
        });
        
        if (!response.ok) {
            const result = await response.json();
            alert(result.error || 'Failed to update time slot');
            adminDashboard.loadTimeSlots(); // Refresh to revert changes
        }
    } catch (error) {
        console.error('Error updating time slot:', error);
        adminDashboard.loadTimeSlots(); // Refresh to revert changes
    }
}

async function updateSlotMaxAppointments(slotId, maxAppointments) {
    try {
        const response = await fetch(`/admin/api/timeslots/${slotId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                max_appointments: parseInt(maxAppointments)
            })
        });
        
        if (!response.ok) {
            const result = await response.json();
            alert(result.error || 'Failed to update time slot');
            adminDashboard.loadTimeSlots(); // Refresh to revert changes
        }
    } catch (error) {
        console.error('Error updating time slot:', error);
        adminDashboard.loadTimeSlots(); // Refresh to revert changes
    }
}

async function deleteTimeSlot(slotId) {
    if (!confirm('Are you sure you want to delete this time slot?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/timeslots/${slotId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Time slot deleted successfully!');
            adminDashboard.loadTimeSlots();
        } else {
            alert(result.error || 'Failed to delete time slot');
        }
    } catch (error) {
        console.error('Error deleting time slot:', error);
        alert('Failed to delete time slot');
    }
}

function filterSlotsByDay(dayOfWeek) {
    // Update active tab
    const tabs = document.querySelectorAll('#dayTabs .nav-link');
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
    
    // Filter table rows
    const rows = document.querySelectorAll('#timeSlotsTableBody tr');
    rows.forEach(row => {
        if (dayOfWeek === -1) {
            row.style.display = ''; // Show all
        } else {
            const dayCell = row.children[1]; // Day column
            const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
            const shouldShow = dayCell.textContent.trim() === dayNames[dayOfWeek];
            row.style.display = shouldShow ? '' : 'none';
        }
    });
}

// ============ APPOINTMENT FUNCTIONS ============

async function approveAppointment(appointmentId) {
    if (!confirm('Are you sure you want to approve this appointment?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/appointments/${appointmentId}/approve`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Appointment approved successfully!');
            adminDashboard.loadAppointments();
            adminDashboard.loadPendingNotifications();
        } else {
            alert(result.error || 'Failed to approve appointment');
        }
    } catch (error) {
        console.error('Error approving appointment:', error);
        alert('Failed to approve appointment');
    }
}

async function declineAppointment(appointmentId) {
    const reason = prompt('Please provide a reason for declining this appointment:');
    if (reason === null) return; // User cancelled
    
    try {
        const response = await fetch(`/admin/api/appointments/${appointmentId}/decline`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reason: reason || 'No reason provided'
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Appointment declined successfully!');
            adminDashboard.loadAppointments();
            adminDashboard.loadPendingNotifications();
        } else {
            alert(result.error || 'Failed to decline appointment');
        }
    } catch (error) {
        console.error('Error declining appointment:', error);
        alert('Failed to decline appointment');
    }
}

async function cancelAppointment(appointmentId) {
    if (!confirm('Are you sure you want to cancel this appointment?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/appointments/${appointmentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Appointment cancelled successfully!');
            adminDashboard.loadAppointments();
        } else {
            alert(result.error || 'Failed to cancel appointment');
        }
    } catch (error) {
        console.error('Error cancelling appointment:', error);
        alert('Failed to cancel appointment');
    }
}

function filterAppointments(filter) {
    // Update active tab
    const tabs = document.querySelectorAll('.nav-tabs .nav-link');
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
    
    // Load appointments with filter
    adminDashboard.loadAppointments(filter);
}

async function viewAppointment(id) {
    try {
        // Show the modal with loading state
        const modal = new bootstrap.Modal(document.getElementById('appointmentDetailsModal'));
        const contentDiv = document.getElementById('appointmentDetailsContent');
        
        contentDiv.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-danger" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">Loading appointment details...</p>
            </div>
        `;
        
        modal.show();
        
        // Fetch appointment details
        const response = await fetch(`/admin/api/appointments/${id}`, {
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load appointment details');
        }
        
        const data = await response.json();
        const appt = data.appointment;
        
        // Format dates
        const appointmentDate = appt.starts_at ? new Date(appt.starts_at).toLocaleString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }) : 'N/A';
        
        const createdAt = appt.created_at ? new Date(appt.created_at).toLocaleString() : 'N/A';
        
        // Get status badge colors
        const approvalBadgeColor = adminDashboard.getApprovalStatusColor(appt.approval_status);
        const statusBadgeColor = adminDashboard.getStatusColor(appt.status);
        
        // Build the details HTML
        contentDiv.innerHTML = `
            <div class="row">
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-user text-danger me-2"></i>Patient Information</h6>
                        </div>
                        <div class="card-body">
                            <p class="mb-2"><strong>Name:</strong> ${appt.patient.name}</p>
                            <p class="mb-2"><strong>Email:</strong> ${appt.patient.email}</p>
                            <p class="mb-0"><strong>Phone:</strong> ${appt.patient.phone}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-user-md text-danger me-2"></i>Doctor Information</h6>
                        </div>
                        <div class="card-body">
                            <p class="mb-2"><strong>Name:</strong> ${appt.doctor.name}</p>
                            <p class="mb-2"><strong>Specialization:</strong> ${appt.doctor.specialization}</p>
                            <p class="mb-2"><strong>Qualification:</strong> ${appt.doctor.qualification}</p>
                            <p class="mb-0"><strong>Phone:</strong> ${appt.doctor.phone}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12 mb-3">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-calendar-alt text-danger me-2"></i>Appointment Details</h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p class="mb-2"><strong>Appointment ID:</strong> #${appt.id}</p>
                                    <p class="mb-2"><strong>Date & Time:</strong> ${appointmentDate}</p>
                                    <p class="mb-2"><strong>Created:</strong> ${createdAt}</p>
                                </div>
                                <div class="col-md-6">
                                    <p class="mb-2"><strong>Approval Status:</strong> <span class="badge bg-${approvalBadgeColor}">${appt.approval_status}</span></p>
                                    <p class="mb-2"><strong>Appointment Status:</strong> <span class="badge bg-${statusBadgeColor}">${appt.status}</span></p>
                                    ${appt.meet_link ? `<p class="mb-0"><strong>Meet Link:</strong> <a href="${appt.meet_link}" target="_blank" class="text-decoration-none">${appt.meet_link}</a></p>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            ${appt.symptoms ? `
            <div class="row">
                <div class="col-12 mb-3">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-notes-medical text-danger me-2"></i>Patient Symptoms</h6>
                        </div>
                        <div class="card-body">
                            <p class="mb-0">${appt.symptoms}</p>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${appt.note ? `
            <div class="row">
                <div class="col-12 mb-3">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-sticky-note text-danger me-2"></i>Notes</h6>
                        </div>
                        <div class="card-body">
                            <p class="mb-0">${appt.note}</p>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
        `;
        
    } catch (error) {
        console.error('Error loading appointment details:', error);
        const contentDiv = document.getElementById('appointmentDetailsContent');
        contentDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong>Error:</strong> Failed to load appointment details. Please try again.
            </div>
        `;
    }
}

// ============ DOCTOR MANAGEMENT FUNCTIONS ============

function showAddDoctorModal() {
    document.getElementById('addDoctorForm').reset();
    new bootstrap.Modal(document.getElementById('addDoctorModal')).show();
}

async function createDoctor() {
    const form = document.getElementById('addDoctorForm');
    const formData = new FormData(form);
    
    const doctorData = {
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        specialization: formData.get('specialization'),
        qualification: formData.get('qualification'),
        experience_years: parseInt(formData.get('experience_years')),
        current_hospital: formData.get('current_hospital')
    };
    
    try {
        const response = await fetch('/admin/api/doctors', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminDashboard.authToken}`
            },
            body: JSON.stringify(doctorData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(`Doctor created successfully! Default password is: ${result.doctor.default_password}`);
            bootstrap.Modal.getInstance(document.getElementById('addDoctorModal')).hide();
            adminDashboard.loadDoctors();
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error creating doctor:', error);
        alert('Failed to create doctor');
    }
}

async function editDoctor(id) {
    try {
        // Fetch doctor details from the server
        const response = await fetch(`/admin/api/doctors/${id}`, {
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const doctor = data.doctor;
            
            document.getElementById('editDoctorId').value = doctor.id;
            document.getElementById('editDoctorName').value = doctor.name;
            document.getElementById('editDoctorEmail').value = doctor.email;
            document.getElementById('editDoctorPhone').value = doctor.phone || '';
            document.getElementById('editDoctorSpecialization').value = doctor.specialization || '';
            document.getElementById('editDoctorQualification').value = doctor.qualification || '';
            document.getElementById('editDoctorExperience').value = doctor.experience_years || '';
            document.getElementById('editDoctorHospital').value = doctor.current_hospital || '';
            
            new bootstrap.Modal(document.getElementById('editDoctorModal')).show();
        } else {
            alert('Failed to load doctor details');
        }
    } catch (error) {
        console.error('Error loading doctor details:', error);
        alert('Failed to load doctor details');
    }
}

async function updateDoctor() {
    const doctorId = document.getElementById('editDoctorId').value;
    const form = document.getElementById('editDoctorForm');
    const formData = new FormData(form);
    
    const doctorData = {
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        specialization: formData.get('specialization'),
        qualification: formData.get('qualification'),
        experience_years: parseInt(formData.get('experience_years')),
        current_hospital: formData.get('current_hospital')
    };
    
    try {
        const response = await fetch(`/admin/api/doctors/${doctorId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminDashboard.authToken}`
            },
            body: JSON.stringify(doctorData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Doctor updated successfully!');
            bootstrap.Modal.getInstance(document.getElementById('editDoctorModal')).hide();
            adminDashboard.loadDoctors();
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error updating doctor:', error);
        alert('Failed to update doctor');
    }
}

async function deleteDoctor(id, name) {
    if (!confirm(`Are you sure you want to delete Dr. ${name}? This will also delete their time slots.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/doctors/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Doctor deleted successfully!');
            adminDashboard.loadDoctors();
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error deleting doctor:', error);
        alert('Failed to delete doctor');
    }
}

// ============ MEDICINE MANAGEMENT FUNCTIONS ============

function showAddMedicineModal() {
    const modal = new bootstrap.Modal(document.getElementById('addMedicineModal'));
    
    // Reset form
    document.getElementById('addMedicineForm').reset();
    
    // Hide image preview
    const previewContainer = document.getElementById('imagePreviewContainer');
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }
    
    modal.show();
}

async function addMedicine() {
    const form = document.getElementById('addMedicineForm');
    const formData = new FormData(form);
    const addBtn = document.getElementById('addMedicineBtn');
    let originalText = '';
    
    // Validate required fields
    if (!formData.get('name') || !formData.get('price') || !formData.get('stock_quantity') || !formData.get('category')) {
        if (adminDashboard && adminDashboard.showAlert) {
            adminDashboard.showAlert('Please fill in all required fields', 'danger');
        } else {
            alert('Please fill in all required fields');
        }
        return;
    }
    
    // Disable button and show loading
    if (addBtn) {
        addBtn.disabled = true;
        originalText = addBtn.innerHTML;
        addBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Adding...';
    }
    
    try {
        const response = await fetch('/admin/api/medicines', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`
            },
            body: formData
        });

        const result = await response.json();
        
        if (response.ok) {
            if (adminDashboard && adminDashboard.showAlert) {
                adminDashboard.showAlert(result.message || 'Medicine added successfully', 'success');
            } else {
                alert(result.message || 'Medicine added successfully');
            }
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addMedicineModal'));
            modal.hide();
            
            // Reload medicines table
            if (adminDashboard && adminDashboard.loadMedicines) {
                adminDashboard.loadMedicines();
            }
            
            // Reload dashboard stats
            if (adminDashboard && adminDashboard.loadDashboardStats) {
                adminDashboard.loadDashboardStats();
            }
            
        } else {
            if (adminDashboard && adminDashboard.showAlert) {
                adminDashboard.showAlert(result.error || 'Failed to add medicine', 'danger');
            } else {
                alert(result.error || 'Failed to add medicine');
            }
        }
    } catch (error) {
        console.error('Error adding medicine:', error);
        if (adminDashboard && adminDashboard.showAlert) {
            adminDashboard.showAlert('Error adding medicine', 'danger');
        } else {
            alert('Error adding medicine');
        }
    } finally {
        // Re-enable button
        if (addBtn) {
            addBtn.disabled = false;
            addBtn.innerHTML = originalText;
        }
    }
}

function previewImage(input) {
    const file = input.files[0];
    const previewContainer = document.getElementById('imagePreviewContainer');
    const previewImage = document.getElementById('imagePreview');
    
    if (file) {
        // Validate file type - only accept jpg, jpeg, png
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (!allowedTypes.includes(file.type.toLowerCase())) {
            if (adminDashboard && adminDashboard.showAlert) {
                adminDashboard.showAlert('Please select a JPG, JPEG, or PNG image file', 'danger');
            } else {
                alert('Please select a JPG, JPEG, or PNG image file');
            }
            input.value = '';
            previewContainer.style.display = 'none';
            return;
        }
        
        // Validate file size (2MB max as specified)
        if (file.size > 2 * 1024 * 1024) {
            if (adminDashboard && adminDashboard.showAlert) {
                adminDashboard.showAlert('Image file size should be less than 2MB', 'danger');
            } else {
                alert('Image file size should be less than 2MB');
            }
            input.value = '';
            previewContainer.style.display = 'none';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        previewContainer.style.display = 'none';
    }
}

async function deleteMedicine(medicineId) {
    if (!confirm('Are you sure you want to delete this medicine? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/medicines/${medicineId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${adminDashboard.authToken}`,
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        
        if (response.ok) {
            if (adminDashboard && adminDashboard.showAlert) {
                adminDashboard.showAlert(result.message || 'Medicine deleted successfully', 'success');
            } else {
                alert(result.message || 'Medicine deleted successfully');
            }
            if (adminDashboard && adminDashboard.loadMedicines) {
                adminDashboard.loadMedicines();
            }
            if (adminDashboard && adminDashboard.loadDashboardStats) {
                adminDashboard.loadDashboardStats();
            }
        } else {
            if (adminDashboard && adminDashboard.showAlert) {
                adminDashboard.showAlert(result.error || 'Failed to delete medicine', 'danger');
            } else {
                alert(result.error || 'Failed to delete medicine');
            }
        }
    } catch (error) {
        console.error('Error deleting medicine:', error);
        if (adminDashboard && adminDashboard.showAlert) {
            adminDashboard.showAlert('Error deleting medicine', 'danger');
        } else {
            alert('Error deleting medicine');
        }
    }
}

function editMedicine(medicineId) {
    // TODO: Implement edit medicine functionality
    if (adminDashboard && adminDashboard.showAlert) {
        adminDashboard.showAlert('Edit medicine functionality coming soon', 'info');
    } else {
        alert('Edit medicine functionality coming soon');
    }
}

function filterMedicines() {
    // TODO: Implement medicine filtering
    console.log('Filter medicines functionality coming soon');
}

// ============ OTHER CRUD OPERATIONS ============

function viewOrder(id) {
    console.log('View order:', id);
}

function updateOrderStatus(id) {
    console.log('Update order status:', id);
}

function editUser(id) {
    console.log('Edit user:', id);
}

function deleteUser(id) {
    console.log('Delete user:', id);
}

function showAddUserModal() {
    console.log('Show add user modal');
}

function filterOrders() {
    console.log('Filter orders');
}

function filterChatLogs() {
    console.log('Filter chat logs');
}

// Initialize admin dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    adminDashboard = new AdminDashboard();
    
    // Add form submission handler for time slots
    const timeSlotForm = document.getElementById('addTimeSlotForm');
    if (timeSlotForm) {
        timeSlotForm.addEventListener('submit', addTimeSlot);
    }
});