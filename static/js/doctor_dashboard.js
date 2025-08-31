class DoctorDashboard {
    constructor() {
        this.doctorToken = localStorage.getItem('doctor_token');
        this.doctorData = JSON.parse(localStorage.getItem('doctor_data') || '{}');
        this.currentFilter = 'all';
    }

    async checkAuthentication() {
        if (!this.doctorToken) {
            window.location.href = '/';
            return;
        }

        try {
            const response = await fetch('/doctor/api/profile', {
                headers: {
                    'Authorization': `Bearer ${this.doctorToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.doctorData = data.doctor;
                localStorage.setItem('doctor_data', JSON.stringify(data.doctor));
                this.updateUI();
                this.loadAppointments();
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Authentication check failed:', error);
            this.logout();
        }
    }

    updateUI() {
        document.getElementById('doctorName').textContent = this.doctorData.name || 'Doctor';
        document.getElementById('profileName').textContent = `Dr. ${this.doctorData.name}`;
        document.getElementById('profileSpecialization').textContent = this.doctorData.specialization || 'General Medicine';
        document.getElementById('profileQualification').textContent = this.doctorData.qualification || 'Medical Qualification';
        document.getElementById('profileExperience').textContent = this.doctorData.experience_years || '0';
        document.getElementById('profileHospital').textContent = this.doctorData.current_hospital || 'Hospital';
    }

    async loadAppointments(status = 'all') {
        this.currentFilter = status;
        
        try {
            const response = await fetch(`/doctor/api/appointments?status=${status}`, {
                headers: {
                    'Authorization': `Bearer ${this.doctorToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayAppointments(data.appointments);
                this.updateStats(data.stats);
            } else {
                console.error('Failed to load appointments');
            }
        } catch (error) {
            console.error('Error loading appointments:', error);
        }
    }

    displayAppointments(appointments) {
        const container = document.getElementById('appointmentsList');
        
        if (appointments.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-calendar-alt fa-3x text-muted mb-3"></i>
                    <h6 class="text-muted">No appointments found</h6>
                    <p class="text-muted">No appointments matching the current filter.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = appointments.map(appointment => `
            <div class="card appointment-card appointment-${appointment.approval_status || appointment.status} mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h6 class="mb-1">${appointment.patient_name}</h6>
                            <p class="text-muted mb-1">
                                <i class="fas fa-calendar me-1"></i>
                                ${this.formatDate(appointment.appointment_date)} 
                                ${this.formatTime(appointment.starts_at)}
                            </p>
                            <p class="text-muted mb-0">
                                <i class="fas fa-phone me-1"></i>
                                ${appointment.patient_phone || 'N/A'}
                            </p>
                        </div>
                        <div class="col-md-4">
                            <p class="mb-1"><strong>Symptoms:</strong></p>
                            <p class="text-muted small">${appointment.symptoms || 'No symptoms provided'}</p>
                            ${appointment.note ? `<p class="text-muted small"><strong>Note:</strong> ${appointment.note}</p>` : ''}
                        </div>
                        <div class="col-md-2 text-end">
                            <span class="badge bg-${this.getStatusColor(appointment.approval_status, appointment.status)}">
                                ${this.getStatusText(appointment.approval_status, appointment.status)}
                            </span>
                            <div class="mt-2">
                                ${this.getActionButtons(appointment)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateStats(stats) {
        document.getElementById('totalAppointments').textContent = stats.total || 0;
        document.getElementById('pendingAppointments').textContent = stats.pending || 0;
        document.getElementById('scheduledAppointments').textContent = stats.scheduled || 0;
        document.getElementById('completedAppointments').textContent = stats.completed || 0;
    }

    getStatusColor(approvalStatus, status) {
        if (approvalStatus === 'pending') return 'warning';
        if (approvalStatus === 'approved' && status === 'scheduled') return 'success';
        if (status === 'completed') return 'secondary';
        if (status === 'cancelled') return 'danger';
        return 'primary';
    }

    getStatusText(approvalStatus, status) {
        if (approvalStatus === 'pending') return 'Pending Approval';
        if (approvalStatus === 'approved' && status === 'scheduled') return 'Scheduled';
        if (status === 'completed') return 'Completed';
        if (status === 'cancelled') return 'Cancelled';
        return status || 'Unknown';
    }

    getActionButtons(appointment) {
        if (appointment.approval_status === 'approved' && appointment.status === 'scheduled') {
            return `
                <button class="btn btn-success btn-sm me-1" onclick="completeAppointment(${appointment.id})">
                    <i class="fas fa-check"></i> Complete
                </button>
                ${appointment.google_meet_link ? `
                    <a href="${appointment.google_meet_link}" target="_blank" class="btn btn-primary btn-sm">
                        <i class="fas fa-video"></i> Join
                    </a>
                ` : ''}
            `;
        }
        return '';
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString();
    }

    formatTime(timeString) {
        if (!timeString) return '';
        return new Date(timeString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    logout() {
        localStorage.removeItem('doctor_token');
        localStorage.removeItem('doctor_data');
        window.location.href = '/';
    }

    // Time Slot Management Methods
    async loadTimeSlots(date = null) {
        try {
            const dateParam = date || document.getElementById('slotDateFilter').value;
            const url = dateParam 
                ? `/doctor/api/time-slots?date=${dateParam}` 
                : '/doctor/api/time-slots';
            
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${this.doctorToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayTimeSlots(data.slots);
                this.updateSlotStats(data.stats);
            } else {
                console.error('Failed to load time slots');
            }
        } catch (error) {
            console.error('Error loading time slots:', error);
        }
    }

    displayTimeSlots(slots) {
        const container = document.getElementById('timeSlotsList');
        
        if (slots.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-clock fa-3x text-muted mb-3"></i>
                    <h6 class="text-muted">No time slots found</h6>
                    <p class="text-muted">Create your first time slot to start accepting appointments.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = slots.map(slot => `
            <div class="card mb-2 ${slot.is_booked ? 'border-danger' : 'border-success'}">
                <div class="card-body py-2">
                    <div class="row align-items-center">
                        <div class="col-md-4">
                            <strong>${this.formatDate(slot.appointment_date)}</strong>
                        </div>
                        <div class="col-md-4">
                            <span class="badge ${slot.is_booked ? 'bg-danger' : 'bg-success'}">
                                ${slot.start_time} - ${slot.end_time}
                            </span>
                        </div>
                        <div class="col-md-2">
                            <span class="badge ${slot.is_booked ? 'bg-danger' : 'bg-success'}">
                                ${slot.is_booked ? 'Booked' : 'Available'}
                            </span>
                        </div>
                        <div class="col-md-2 text-end">
                            ${slot.can_delete ? `
                                <button class="btn btn-sm btn-outline-danger" onclick="doctorDashboard.deleteTimeSlot(${slot.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateSlotStats(stats) {
        document.getElementById('totalSlots').textContent = stats.total;
        document.getElementById('availableSlots').textContent = stats.available;
        document.getElementById('bookedSlots').textContent = stats.booked;
    }

    async createTimeSlot() {
        const form = document.getElementById('createSlotForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch('/doctor/api/time-slots', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.doctorToken}`
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('createSlotModal'));
                modal.hide();
                
                // Reset form
                form.reset();
                
                // Reload slots
                this.loadTimeSlots();
                
                // Show success message
                this.showAlert('Time slot created successfully!', 'success');
            } else {
                this.showAlert(result.error || 'Failed to create time slot', 'danger');
            }
        } catch (error) {
            console.error('Error creating time slot:', error);
            this.showAlert('An error occurred while creating the time slot', 'danger');
        }
    }

    async deleteTimeSlot(slotId) {
        if (!confirm('Are you sure you want to delete this time slot?')) {
            return;
        }

        try {
            const response = await fetch(`/doctor/api/time-slots/${slotId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.doctorToken}`
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.loadTimeSlots();
                this.showAlert('Time slot deleted successfully!', 'success');
            } else {
                this.showAlert(result.error || 'Failed to delete time slot', 'danger');
            }
        } catch (error) {
            console.error('Error deleting time slot:', error);
            this.showAlert('An error occurred while deleting the time slot', 'danger');
        }
    }

    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of main content
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }
}

// Global functions
async function loadAppointments(status) {
    if (window.doctorDashboard) {
        window.doctorDashboard.loadAppointments(status);
    }
}

function showProfileModal() {
    if (!window.doctorDashboard || !window.doctorDashboard.doctorData) return;
    
    const doctor = window.doctorDashboard.doctorData;
    
    document.getElementById('editName').value = doctor.name || '';
    document.getElementById('editPhone').value = doctor.phone || '';
    document.getElementById('editSpecialization').value = doctor.specialization || '';
    document.getElementById('editQualification').value = doctor.qualification || '';
    document.getElementById('editExperience').value = doctor.experience_years || '';
    document.getElementById('editHospital').value = doctor.current_hospital || '';
    document.getElementById('editPassword').value = '';
    document.getElementById('editConfirmPassword').value = '';
    
    new bootstrap.Modal(document.getElementById('editProfileModal')).show();
}

async function updateProfile() {
    const form = document.getElementById('editProfileForm');
    const formData = new FormData(form);
    
    const password = formData.get('password');
    const confirmPassword = document.getElementById('editConfirmPassword').value;
    
    if (password && password !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }
    
    const updateData = {
        name: formData.get('name'),
        phone: formData.get('phone'),
        specialization: formData.get('specialization'),
        qualification: formData.get('qualification'),
        experience_years: parseInt(formData.get('experience_years')),
        current_hospital: formData.get('current_hospital')
    };
    
    if (password) {
        updateData.password = password;
    }
    
    try {
        const response = await fetch('/doctor/api/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.doctorDashboard.doctorToken}`
            },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Profile updated successfully!');
            window.doctorDashboard.doctorData = result.doctor;
            localStorage.setItem('doctor_data', JSON.stringify(result.doctor));
            window.doctorDashboard.updateUI();
            bootstrap.Modal.getInstance(document.getElementById('editProfileModal')).hide();
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        alert('Failed to update profile');
    }
}

async function completeAppointment(appointmentId) {
    if (!confirm('Mark this appointment as completed?')) {
        return;
    }
    
    try {
        const response = await fetch(`/doctor/api/appointments/${appointmentId}/complete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.doctorDashboard.doctorToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Appointment marked as completed!');
            window.doctorDashboard.loadAppointments(window.doctorDashboard.currentFilter);
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error completing appointment:', error);
        alert('Failed to complete appointment');
    }
}

function doctorLogout() {
    if (confirm('Are you sure you want to logout?')) {
        window.doctorDashboard.logout();
    }
}

// Global functions for slot management
function showCreateSlotModal() {
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('slotDate').min = today;
    
    new bootstrap.Modal(document.getElementById('createSlotModal')).show();
}

function createTimeSlot() {
    if (window.doctorDashboard) {
        window.doctorDashboard.createTimeSlot();
    }
}

function loadTimeSlots() {
    if (window.doctorDashboard) {
        window.doctorDashboard.loadTimeSlots();
    }
}