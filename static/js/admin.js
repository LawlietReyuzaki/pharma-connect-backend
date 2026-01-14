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
            case 'payments':
                loadPayments();
                loadPaymentMethods();
                loadBankingDetails();
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

    async loadMedicinesFiltered(search = '', status = '', category = '') {
        try {
            let url = '/admin/api/medicines?';
            if (search) url += `search=${encodeURIComponent(search)}&`;
            if (status) url += `status=${encodeURIComponent(status)}&`;
            if (category) url += `category=${encodeURIComponent(category)}&`;
            
            const response = await fetch(url, {
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
            if (!this.authToken) {
                console.warn('No auth token available for orders');
                return;
            }
            
            const response = await fetch('/admin/api/orders', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.orders) {
                    this.renderOrdersTable(data.orders);
                    
                    // Update order count if element exists
                    const orderCountEl = document.getElementById('totalOrdersCount');
                    if (orderCountEl) {
                        orderCountEl.textContent = data.total_count || data.orders.length;
                    }
                } else {
                    console.warn('Orders API returned unexpected format:', data);
                }
            } else {
                console.error('Orders API failed with status:', response.status);
            }
        } catch (error) {
            console.error('Error loading orders:', error.message || error);
        }
    }

    renderOrdersTable(orders) {
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) {
            console.warn('ordersTableBody element not found');
            return;
        }

        tbody.innerHTML = '';
        
        if (!orders || orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No orders found</td></tr>';
            return;
        }

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
            if (!this.authToken) {
                console.warn('No auth token available for appointments');
                return;
            }
            
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
                
                if (data.success && data.appointments) {
                    this.renderAppointmentsTable(data.appointments);
                    
                    // Update counters with null checks
                    const pendingEl = document.getElementById('pendingAppointmentsCount');
                    const approvedEl = document.getElementById('approvedAppointmentsCount');
                    
                    if (pendingEl) pendingEl.textContent = data.pending_count || 0;
                    if (approvedEl) approvedEl.textContent = data.approved_count || 0;
                } else {
                    console.warn('Appointments API returned unexpected format:', data);
                }
            } else {
                console.error('Appointments API failed with status:', response.status);
            }
        } catch (error) {
            console.error('Error loading appointments:', error.message || error);
        }
    }

    renderAppointmentsTable(appointments) {
        const tbody = document.getElementById('appointmentsTableBody');
        if (!tbody) {
            console.warn('appointmentsTableBody element not found');
            return;
        }

        tbody.innerHTML = '';
        
        if (!appointments || appointments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No appointments found</td></tr>';
            return;
        }

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
            'confirmed': 'info',
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

async function editMedicine(medicineId) {
    try {
        const token = localStorage.getItem('admin_token');
        const response = await fetch(`/admin/api/medicines/${medicineId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch medicine details');
        }
        
        const data = await response.json();
        const medicine = data.medicine;
        
        // Populate the edit form
        document.getElementById('editMedicineId').value = medicine.id;
        document.getElementById('editMedicineName').value = medicine.name;
        document.getElementById('editMedicineChemical').value = medicine.chemical || '';
        document.getElementById('editMedicinePrice').value = medicine.price;
        document.getElementById('editMedicineStock').value = medicine.stock_quantity;
        document.getElementById('editMedicineCategory').value = medicine.category || 'General';
        document.getElementById('editMedicineStatus').value = medicine.status;
        document.getElementById('editMedicineDescription').value = medicine.description || '';
        
        // Show current image
        const currentImage = document.getElementById('editCurrentImage');
        currentImage.src = medicine.image_path || '/static/images/default-medicine.png';
        
        // Reset file input and preview
        document.getElementById('editImageFile').value = '';
        document.getElementById('editImagePreviewContainer').style.display = 'none';
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('editMedicineModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading medicine:', error);
        if (adminDashboard && adminDashboard.showAlert) {
            adminDashboard.showAlert('Failed to load medicine details', 'danger');
        } else {
            alert('Failed to load medicine details');
        }
    }
}

function previewEditImage(input) {
    const previewContainer = document.getElementById('editImagePreviewContainer');
    const preview = document.getElementById('editImagePreview');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    } else {
        previewContainer.style.display = 'none';
    }
}

async function saveMedicineEdit() {
    try {
        const medicineId = document.getElementById('editMedicineId').value;
        const form = document.getElementById('editMedicineForm');
        const formData = new FormData(form);
        
        const token = localStorage.getItem('admin_token');
        
        const response = await fetch(`/admin/api/medicines/${medicineId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editMedicineModal'));
            modal.hide();
            
            // Show success message
            if (adminDashboard && adminDashboard.showAlert) {
                adminDashboard.showAlert('Medicine updated successfully!', 'success');
            } else {
                alert('Medicine updated successfully!');
            }
            
            // Reload medicines list
            if (adminDashboard) {
                adminDashboard.loadMedicines();
            }
        } else {
            throw new Error(data.error || 'Failed to update medicine');
        }
        
    } catch (error) {
        console.error('Error updating medicine:', error);
        if (adminDashboard && adminDashboard.showAlert) {
            adminDashboard.showAlert(error.message || 'Failed to update medicine', 'danger');
        } else {
            alert(error.message || 'Failed to update medicine');
        }
    }
}

function filterMedicines() {
    const search = document.getElementById('medicineSearchInput').value;
    const status = document.getElementById('medicineStatusFilter').value;
    const category = document.getElementById('medicineCategoryFilter').value;
    
    if (adminDashboard) {
        adminDashboard.loadMedicinesFiltered(search, status, category);
    }
}

// ============ OTHER CRUD OPERATIONS ============

async function viewOrder(id) {
    try {
        const response = await fetch(`/admin/api/orders/${id}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const order = data.order;
            
            // Build items list HTML - use medicine_image from API
            let itemsHtml = order.items.map(item => `
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <img src="${item.medicine_image || '/static/images/default-medicine.png'}" 
                                 alt="${item.medicine_name}" class="rounded me-2" 
                                 style="width: 40px; height: 40px; object-fit: cover;"
                                 onerror="this.src='/static/images/default-medicine.png'">
                            <span>${item.medicine_name}</span>
                        </div>
                    </td>
                    <td>PKR ${item.price_each}</td>
                    <td>${item.quantity}</td>
                    <td>PKR ${item.total}</td>
                </tr>
            `).join('');
            
            const statusColor = adminDashboard.getStatusColor(order.status);
            const orderDate = new Date(order.created_at).toLocaleString();
            
            // Get customer info - use customer object from API
            const customerName = order.customer ? order.customer.name : 'Unknown';
            const customerEmail = order.customer ? order.customer.email : 'N/A';
            const customerPhone = order.customer ? order.customer.phone : order.phone || 'N/A';
            
            // Create modal HTML
            const modalHtml = `
                <div class="modal fade" id="orderDetailModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-shopping-cart text-danger me-2"></i>Order #${order.id} Details
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row mb-4">
                                    <div class="col-md-6">
                                        <div class="card">
                                            <div class="card-header bg-light">
                                                <h6 class="mb-0"><i class="fas fa-user text-danger me-2"></i>Customer Information</h6>
                                            </div>
                                            <div class="card-body">
                                                <p class="mb-2"><strong>Name:</strong> ${customerName}</p>
                                                <p class="mb-2"><strong>Email:</strong> ${customerEmail}</p>
                                                <p class="mb-2"><strong>Phone:</strong> ${customerPhone}</p>
                                                <p class="mb-0"><strong>Address:</strong> ${order.address}</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="card">
                                            <div class="card-header bg-light">
                                                <h6 class="mb-0"><i class="fas fa-info-circle text-danger me-2"></i>Order Information</h6>
                                            </div>
                                            <div class="card-body">
                                                <p class="mb-2"><strong>Order Date:</strong> ${orderDate}</p>
                                                <p class="mb-2"><strong>Status:</strong> <span class="badge bg-${statusColor}">${order.status}</span></p>
                                                <p class="mb-2"><strong>Payment:</strong> ${order.payment_method}</p>
                                                <p class="mb-0"><strong>Notes:</strong> ${order.notes || 'None'}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <h6 class="mb-3"><i class="fas fa-pills text-danger me-2"></i>Order Items</h6>
                                <table class="table table-bordered">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Medicine</th>
                                            <th>Price</th>
                                            <th>Quantity</th>
                                            <th>Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${itemsHtml}
                                    </tbody>
                                    <tfoot class="table-light">
                                        <tr>
                                            <td colspan="3" class="text-end"><strong>Subtotal:</strong></td>
                                            <td>PKR ${order.total_amount - order.delivery_fee}</td>
                                        </tr>
                                        <tr>
                                            <td colspan="3" class="text-end"><strong>Delivery Fee:</strong></td>
                                            <td>PKR ${order.delivery_fee}</td>
                                        </tr>
                                        <tr>
                                            <td colspan="3" class="text-end"><strong>Total:</strong></td>
                                            <td><strong>PKR ${order.total_amount}</strong></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                <button type="button" class="btn btn-primary" onclick="updateOrderStatus(${order.id})">
                                    <i class="fas fa-edit me-1"></i>Update Status
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('orderDetailModal');
            if (existingModal) existingModal.remove();
            
            // Add and show modal
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = new bootstrap.Modal(document.getElementById('orderDetailModal'));
            modal.show();
        } else {
            alert('Failed to load order details');
        }
    } catch (error) {
        console.error('Error viewing order:', error);
        alert('Failed to load order details');
    }
}

async function updateOrderStatus(id) {
    // Create status update modal
    const modalHtml = `
        <div class="modal fade" id="updateOrderStatusModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-edit text-primary me-2"></i>Update Order #${id} Status
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">New Status</label>
                            <select class="form-select" id="newOrderStatus">
                                <option value="pending">Pending</option>
                                <option value="confirmed">Confirmed</option>
                                <option value="processing">Processing</option>
                                <option value="out_for_delivery">Out for Delivery</option>
                                <option value="delivered">Delivered</option>
                                <option value="cancelled">Cancelled</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notes (optional)</label>
                            <textarea class="form-control" id="orderStatusNotes" rows="3" placeholder="Add notes about this status update..."></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="submitOrderStatusUpdate(${id})">
                            <i class="fas fa-save me-1"></i>Update Status
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('updateOrderStatusModal');
    if (existingModal) existingModal.remove();
    
    // Hide order detail modal if open
    const detailModal = document.getElementById('orderDetailModal');
    if (detailModal) {
        const bsDetailModal = bootstrap.Modal.getInstance(detailModal);
        if (bsDetailModal) bsDetailModal.hide();
    }
    
    // Add and show modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('updateOrderStatusModal'));
    modal.show();
}

async function submitOrderStatusUpdate(id) {
    const status = document.getElementById('newOrderStatus').value;
    const notes = document.getElementById('orderStatusNotes').value;
    
    try {
        const response = await fetch(`/admin/api/orders/${id}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
            },
            body: JSON.stringify({ status, notes })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('updateOrderStatusModal'));
            if (modal) modal.hide();
            
            // Show success message
            alert(`Order status updated to ${status}`);
            
            // Reload orders
            if (adminDashboard) {
                adminDashboard.loadOrders();
            }
        } else {
            alert(data.error || 'Failed to update order status');
        }
    } catch (error) {
        console.error('Error updating order status:', error);
        alert('Failed to update order status');
    }
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

// ============ PAYMENT MANAGEMENT ============

let allPayments = [];

async function loadPayments() {
    try {
        const response = await fetch('/admin/api/payments', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            allPayments = data.payments || [];
            renderPaymentsTable(allPayments);
        }
    } catch (error) {
        console.error('Error loading payments:', error);
    }
}

function renderPaymentsTable(payments) {
    const tbody = document.getElementById('paymentsTableBody');
    if (!tbody) return;

    if (payments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">No payments found</td></tr>';
        return;
    }

    tbody.innerHTML = payments.map(payment => {
        const paymentDate = new Date(payment.created_at).toLocaleDateString();
        const statusColor = getPaymentStatusColor(payment.payment_status);
        const methodDisplay = formatPaymentMethod(payment.payment_method);
        const rejectionReason = payment.rejection_reason ? 
            `<br><small class="text-danger"><i class="fas fa-exclamation-circle me-1"></i>${payment.rejection_reason}</small>` : '';
        const receiptUploaded = payment.receipt_uploaded_at ? 
            `<br><small class="text-muted"><i class="fas fa-clock me-1"></i>${new Date(payment.receipt_uploaded_at).toLocaleString()}</small>` : '';
        
        const isPDF = payment.receipt_path && payment.receipt_path.toLowerCase().endsWith('.pdf');
        const receiptIcon = isPDF ? 'fa-file-pdf' : 'fa-image';
        const receiptText = isPDF ? 'PDF' : 'View';
        
        return `
            <tr class="${payment.payment_status === 'pending' ? 'table-warning' : ''}">
                <td><strong>#${payment.order_id}</strong></td>
                <td>
                    <div>${payment.customer_name}</div>
                    <small class="text-muted">${payment.customer_email}</small>
                    <br><small class="text-muted">${payment.customer_phone || 'N/A'}</small>
                </td>
                <td><strong>PKR ${payment.amount.toLocaleString()}</strong></td>
                <td>
                    <span class="badge bg-secondary">${methodDisplay}</span>
                </td>
                <td>
                    <span class="badge bg-${statusColor}">${payment.payment_status.toUpperCase()}</span>
                    ${rejectionReason}
                </td>
                <td>
                    ${payment.receipt_path ? 
                        `<button class="btn btn-sm btn-outline-primary" onclick="viewReceipt('${payment.receipt_path}', ${payment.order_id})">
                            <i class="fas ${receiptIcon} me-1"></i>${receiptText}
                        </button>
                        <a href="${payment.receipt_path}" download class="btn btn-sm btn-outline-secondary ms-1" title="Download">
                            <i class="fas fa-download"></i>
                        </a>
                        ${receiptUploaded}` : 
                        '<span class="text-muted">N/A</span>'}
                </td>
                <td>${paymentDate}</td>
                <td>
                    ${payment.payment_method !== 'cash_on_delivery' ? `
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-success" onclick="acceptPayment(${payment.order_id})" 
                                    title="Accept Payment" ${payment.payment_status === 'accepted' ? 'disabled' : ''}>
                                <i class="fas fa-check"></i>
                            </button>
                            <button class="btn btn-danger" onclick="showRejectPaymentModal(${payment.order_id})" 
                                    title="Reject Payment" ${payment.payment_status === 'declined' ? 'disabled' : ''}>
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    ` : '<span class="text-muted">COD</span>'}
                </td>
            </tr>
        `;
    }).join('');
}

function viewReceipt(receiptPath, orderId) {
    const isPDF = receiptPath.toLowerCase().endsWith('.pdf');
    
    const modalHtml = `
        <div class="modal fade" id="receiptViewModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-receipt me-2"></i>Payment Receipt - Order #${orderId}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center" style="min-height: 400px;">
                        ${isPDF ? 
                            `<embed src="${receiptPath}" type="application/pdf" width="100%" height="500px" />` :
                            `<img src="${receiptPath}" alt="Payment Receipt" class="img-fluid" style="max-height: 500px;" />`
                        }
                    </div>
                    <div class="modal-footer">
                        <a href="${receiptPath}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt me-1"></i>Open in New Tab
                        </a>
                        <a href="${receiptPath}" download class="btn btn-success">
                            <i class="fas fa-download me-1"></i>Download
                        </a>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('receiptViewModal');
    if (existingModal) existingModal.remove();
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('receiptViewModal'));
    modal.show();
}

function showRejectPaymentModal(orderId) {
    const modalHtml = `
        <div class="modal fade" id="rejectPaymentModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-times-circle me-2"></i>Reject Payment - Order #${orderId}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to reject this payment? The customer will be notified and can re-upload a new receipt.</p>
                        <div class="mb-3">
                            <label class="form-label"><strong>Rejection Reason</strong></label>
                            <select class="form-select mb-2" id="rejectionReasonSelect" onchange="toggleCustomReason()">
                                <option value="Receipt is unclear or unreadable">Receipt is unclear or unreadable</option>
                                <option value="Amount does not match order total">Amount does not match order total</option>
                                <option value="Transaction ID not visible">Transaction ID not visible</option>
                                <option value="Receipt appears to be fake or edited">Receipt appears to be fake or edited</option>
                                <option value="Wrong account number used">Wrong account number used</option>
                                <option value="custom">Other (specify below)</option>
                            </select>
                            <textarea class="form-control" id="customRejectionReason" rows="2" 
                                      placeholder="Enter custom rejection reason..." style="display:none;"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" onclick="confirmRejectPayment(${orderId})">
                            <i class="fas fa-times me-1"></i>Reject Payment
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('rejectPaymentModal');
    if (existingModal) existingModal.remove();
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('rejectPaymentModal'));
    modal.show();
}

function toggleCustomReason() {
    const select = document.getElementById('rejectionReasonSelect');
    const customInput = document.getElementById('customRejectionReason');
    customInput.style.display = select.value === 'custom' ? 'block' : 'none';
}

async function confirmRejectPayment(orderId) {
    const select = document.getElementById('rejectionReasonSelect');
    const customInput = document.getElementById('customRejectionReason');
    
    let reason = select.value;
    if (reason === 'custom') {
        reason = customInput.value.trim();
        if (!reason) {
            alert('Please enter a rejection reason');
            return;
        }
    }
    
    await updatePaymentStatus(orderId, 'declined', reason);
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('rejectPaymentModal'));
    if (modal) modal.hide();
}

async function acceptPayment(orderId) {
    if (!confirm('Accept this payment? This will confirm the order.')) return;
    await updatePaymentStatus(orderId, 'accepted');
}

function getPaymentStatusColor(status) {
    switch(status) {
        case 'accepted': return 'success';
        case 'declined': return 'danger';
        case 'pending': return 'warning';
        default: return 'secondary';
    }
}

function formatPaymentMethod(method) {
    const methods = {
        'cash_on_delivery': 'Cash on Delivery',
        'easypaisa': 'EasyPaisa',
        'jazzcash': 'JazzCash',
        'meezan_bank': 'Meezan Bank',
        'nayapay': 'NayaPay'
    };
    return methods[method] || method;
}

async function updatePaymentStatus(orderId, status, rejectionReason = null) {
    try {
        const payload = { payment_status: status };
        if (rejectionReason) {
            payload.rejection_reason = rejectionReason;
        }
        
        const response = await fetch(`/admin/api/payments/${orderId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            const statusLabel = status === 'accepted' ? 'accepted' : 'rejected';
            alert(`Payment ${statusLabel} successfully`);
            loadPayments();
            if (window.adminDashboard) {
                window.adminDashboard.loadOrders();
            }
        } else {
            alert(data.error || 'Failed to update payment status');
        }
    } catch (error) {
        console.error('Error updating payment status:', error);
        alert('Failed to update payment status');
    }
}

function filterPayments() {
    const statusFilter = document.getElementById('paymentStatusFilter')?.value;
    
    let filtered = allPayments;
    if (statusFilter) {
        filtered = allPayments.filter(p => p.payment_status === statusFilter);
    }
    
    renderPaymentsTable(filtered);
}

async function loadPaymentMethods() {
    try {
        const response = await fetch('/admin/api/payment-methods', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            renderPaymentMethodsControls(data.payment_methods || []);
        }
    } catch (error) {
        console.error('Error loading payment methods:', error);
    }
}

function renderPaymentMethodsControls(methods) {
    const container = document.getElementById('paymentMethodsControls');
    if (!container) return;

    if (methods.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-3">
                <p class="text-muted">No payment methods configured.</p>
                <button class="btn btn-primary" onclick="initPaymentMethods()">
                    <i class="fas fa-plus me-1"></i>Initialize Payment Methods
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = methods.map(method => `
        <div class="col-md-4 col-lg-2 mb-3">
            <div class="card h-100 ${method.is_active ? 'border-success' : 'border-secondary'}">
                <div class="card-body text-center">
                    <img src="${method.logo_path}" alt="${method.name}" class="mb-2" 
                         style="height: 40px; width: auto; max-width: 80px; object-fit: contain;"
                         onerror="this.src='/static/images/payment-logos/cash-on-delivery.svg'">
                    <h6 class="card-title mb-2">${method.name}</h6>
                    <div class="form-check form-switch d-flex justify-content-center">
                        <input class="form-check-input" type="checkbox" id="pm_toggle_${method.id}" 
                               ${method.is_active ? 'checked' : ''} 
                               onchange="togglePaymentMethod(${method.id})">
                        <label class="form-check-label ms-2" for="pm_toggle_${method.id}">
                            ${method.is_active ? 'Active' : 'Inactive'}
                        </label>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

async function togglePaymentMethod(methodId) {
    try {
        const response = await fetch(`/admin/api/payment-methods/${methodId}/toggle`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            loadPaymentMethods();
        } else {
            alert(data.error || 'Failed to toggle payment method');
            loadPaymentMethods();
        }
    } catch (error) {
        console.error('Error toggling payment method:', error);
        alert('Failed to toggle payment method');
    }
}

async function initPaymentMethods() {
    try {
        const response = await fetch('/api/payments/init-methods', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert('Payment methods initialized successfully');
            loadPaymentMethods();
        } else {
            alert(data.message || data.error || 'Failed to initialize payment methods');
        }
    } catch (error) {
        console.error('Error initializing payment methods:', error);
        alert('Failed to initialize payment methods');
    }
}

// ============ BANKING DETAILS MANAGEMENT ============

async function loadBankingDetails() {
    try {
        const response = await fetch('/admin/api/banking-details', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            populateBankingDetailsForm(data.banking_details);
        }
    } catch (error) {
        console.error('Error loading banking details:', error);
    }
}

function populateBankingDetailsForm(details) {
    if (!details) return;
    
    const fields = ['bank_name', 'account_title', 'account_number', 'iban', 'easypaisa_number', 'jazzcash_number', 'additional_instructions'];
    fields.forEach(field => {
        const input = document.getElementById(`banking_${field}`);
        if (input && details[field]) {
            input.value = details[field];
        }
    });
}

async function saveBankingDetails() {
    const saveBtn = document.getElementById('saveBankingBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Saving...';
    saveBtn.disabled = true;

    try {
        const data = {
            bank_name: document.getElementById('banking_bank_name')?.value || '',
            account_title: document.getElementById('banking_account_title')?.value || '',
            account_number: document.getElementById('banking_account_number')?.value || '',
            iban: document.getElementById('banking_iban')?.value || '',
            easypaisa_number: document.getElementById('banking_easypaisa_number')?.value || '',
            jazzcash_number: document.getElementById('banking_jazzcash_number')?.value || '',
            additional_instructions: document.getElementById('banking_additional_instructions')?.value || ''
        };

        const response = await fetch('/admin/api/banking-details', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            showBankingAlert('Banking details saved successfully!', 'success');
        } else {
            showBankingAlert(result.error || 'Failed to save banking details', 'danger');
        }
    } catch (error) {
        console.error('Error saving banking details:', error);
        showBankingAlert('Failed to save banking details', 'danger');
    } finally {
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }
}

function showBankingAlert(message, type) {
    const alertDiv = document.getElementById('bankingAlert');
    if (alertDiv) {
        alertDiv.className = `alert alert-${type}`;
        alertDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>${message}`;
        alertDiv.classList.remove('d-none');
        setTimeout(() => alertDiv.classList.add('d-none'), 5000);
    }
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