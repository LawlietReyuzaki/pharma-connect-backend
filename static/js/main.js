// Red Dot Pharmacy - Main JavaScript Application
// Handles authentication, medicine browsing, cart, appointments, and general UI interactions

class RedDotPharmacy {
    constructor() {
        this.authToken = localStorage.getItem('auth_token');
        this.userData = JSON.parse(localStorage.getItem('user_data') || '{}');
        this.cart = JSON.parse(localStorage.getItem('cart') || '[]');
        this.medicines = [];
        this.doctors = [];
        this.selectedTimeSlot = null;
        this.pendingAppointments = 0;
        this.paymentMethods = [];
        this.uploadedReceiptPath = null;
        
        this.initializeEventListeners();
        this.updateCartDisplay();
        this.loadPaymentMethods();
    }

    async loadPaymentMethods() {
        try {
            const response = await fetch('/api/payments/methods');
            if (response.ok) {
                const data = await response.json();
                this.paymentMethods = data.payment_methods || [];
            }
        } catch (error) {
            console.error('Error loading payment methods:', error);
            this.paymentMethods = [{
                slug: 'cash_on_delivery',
                name: 'Cash on Delivery',
                logo_path: '/static/images/payment-logos/cash-on-delivery.svg',
                requires_receipt: false
            }];
        }
    }

    getPaymentMethodsHtml() {
        if (this.paymentMethods.length === 0) {
            return `
                <div class="payment-method-option">
                    <input type="radio" name="paymentMethod" id="pm_cod" value="cash_on_delivery" checked>
                    <label for="pm_cod" class="d-flex align-items-center p-2 border rounded mb-2 cursor-pointer">
                        <img src="/static/images/payment-logos/cash-on-delivery.svg" alt="Cash on Delivery" class="me-2" style="height: 30px;">
                        <span>Cash on Delivery</span>
                    </label>
                </div>
            `;
        }

        return this.paymentMethods.map((method, index) => `
            <div class="payment-method-option mb-2">
                <input type="radio" name="paymentMethod" id="pm_${method.slug}" value="${method.slug}" 
                       ${index === 0 ? 'checked' : ''} 
                       data-requires-receipt="${method.requires_receipt}"
                       data-account-title="${method.account_title || ''}"
                       data-account-number="${method.account_number || ''}"
                       data-account-details="${method.account_details || ''}"
                       data-method-name="${method.name}"
                       data-logo-path="${method.logo_path}"
                       onchange="app.onPaymentMethodChange()">
                <label for="pm_${method.slug}" class="d-flex align-items-center p-2 border rounded cursor-pointer w-100" style="cursor: pointer;">
                    <img src="${method.logo_path}" alt="${method.name}" class="me-2" 
                         style="height: 35px; width: 50px; object-fit: contain;"
                         onerror="this.src='/static/images/payment-logos/cash-on-delivery.svg'">
                    <span>${method.name}</span>
                </label>
            </div>
        `).join('');
    }

    async onPaymentMethodChange() {
        const selectedRadio = document.querySelector('input[name="paymentMethod"]:checked');
        const receiptSection = document.getElementById('receiptUploadSection');
        const accountDetailsDiv = document.getElementById('paymentAccountDetails');
        
        if (!selectedRadio || !receiptSection) return;
        
        const requiresReceipt = selectedRadio.dataset.requiresReceipt === 'true';
        const methodSlug = selectedRadio.value;
        const methodName = selectedRadio.dataset.methodName;
        
        if (requiresReceipt) {
            receiptSection.style.display = 'block';
            
            if (accountDetailsDiv) {
                accountDetailsDiv.innerHTML = '<div class="text-center py-2"><i class="fas fa-spinner fa-spin"></i> Loading payment details...</div>';
                accountDetailsDiv.style.display = 'block';
                
                try {
                    const response = await fetch('/api/payments/banking-details');
                    const data = await response.json();
                    const banking = data.banking_details;
                    
                    if (banking) {
                        let detailsHtml = `
                            <div class="card border-success mb-3">
                                <div class="card-header bg-success text-white py-2">
                                    <i class="fas fa-university me-1"></i>Payment Details - Send Payment To
                                </div>
                                <div class="card-body">
                        `;
                        
                        if (methodSlug === 'easypaisa' && banking.easypaisa_number) {
                            detailsHtml += `
                                <div class="mb-3 p-3 bg-light rounded border-start border-success border-4">
                                    <div class="d-flex align-items-center mb-2">
                                        <i class="fas fa-mobile-alt text-success me-2 fa-lg"></i>
                                        <strong class="text-success">EasyPaisa</strong>
                                    </div>
                                    ${banking.account_title ? `<div class="mb-1"><small class="text-muted">Account Title:</small> <strong>${banking.account_title}</strong></div>` : ''}
                                    <div>
                                        <small class="text-muted">Number:</small>
                                        <span class="fw-bold text-primary" style="font-family: monospace; font-size: 1.2rem;">${banking.easypaisa_number}</span>
                                        <button type="button" class="btn btn-sm btn-outline-success ms-2" 
                                                onclick="navigator.clipboard.writeText('${banking.easypaisa_number}'); app.showSuccess('Number copied!')">
                                            <i class="fas fa-copy"></i>
                                        </button>
                                    </div>
                                </div>
                            `;
                        } else if (methodSlug === 'jazzcash' && banking.jazzcash_number) {
                            detailsHtml += `
                                <div class="mb-3 p-3 bg-light rounded border-start border-danger border-4">
                                    <div class="d-flex align-items-center mb-2">
                                        <i class="fas fa-mobile-alt text-danger me-2 fa-lg"></i>
                                        <strong class="text-danger">JazzCash</strong>
                                    </div>
                                    ${banking.account_title ? `<div class="mb-1"><small class="text-muted">Account Title:</small> <strong>${banking.account_title}</strong></div>` : ''}
                                    <div>
                                        <small class="text-muted">Number:</small>
                                        <span class="fw-bold text-primary" style="font-family: monospace; font-size: 1.2rem;">${banking.jazzcash_number}</span>
                                        <button type="button" class="btn btn-sm btn-outline-danger ms-2" 
                                                onclick="navigator.clipboard.writeText('${banking.jazzcash_number}'); app.showSuccess('Number copied!')">
                                            <i class="fas fa-copy"></i>
                                        </button>
                                    </div>
                                </div>
                            `;
                        } else if (banking.bank_name || banking.account_number) {
                            detailsHtml += `
                                <div class="mb-3 p-3 bg-light rounded border-start border-primary border-4">
                                    <div class="d-flex align-items-center mb-2">
                                        <i class="fas fa-university text-primary me-2 fa-lg"></i>
                                        <strong class="text-primary">${banking.bank_name || 'Bank Transfer'}</strong>
                                    </div>
                                    ${banking.account_title ? `<div class="mb-1"><small class="text-muted">Account Title:</small> <strong>${banking.account_title}</strong></div>` : ''}
                                    ${banking.account_number ? `
                                        <div class="mb-1">
                                            <small class="text-muted">Account Number:</small>
                                            <span class="fw-bold text-primary" style="font-family: monospace;">${banking.account_number}</span>
                                            <button type="button" class="btn btn-sm btn-outline-primary ms-1" 
                                                    onclick="navigator.clipboard.writeText('${banking.account_number}'); app.showSuccess('Account number copied!')">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    ` : ''}
                                    ${banking.iban ? `
                                        <div>
                                            <small class="text-muted">IBAN:</small>
                                            <span class="fw-bold" style="font-family: monospace; font-size: 0.9rem;">${banking.iban}</span>
                                            <button type="button" class="btn btn-sm btn-outline-secondary ms-1" 
                                                    onclick="navigator.clipboard.writeText('${banking.iban}'); app.showSuccess('IBAN copied!')">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        }
                        
                        if (banking.additional_instructions) {
                            detailsHtml += `
                                <div class="alert alert-info py-2 mb-0">
                                    <i class="fas fa-info-circle me-1"></i>
                                    <small>${banking.additional_instructions}</small>
                                </div>
                            `;
                        }
                        
                        detailsHtml += '</div></div>';
                        accountDetailsDiv.innerHTML = detailsHtml;
                    } else {
                        accountDetailsDiv.innerHTML = `
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle me-1"></i>
                                Payment details not configured. Please contact the pharmacy.
                            </div>
                        `;
                    }
                } catch (error) {
                    console.error('Error loading banking details:', error);
                    accountDetailsDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle me-1"></i>
                            Failed to load payment details. Please try again.
                        </div>
                    `;
                }
            }
        } else {
            receiptSection.style.display = 'none';
            if (accountDetailsDiv) accountDetailsDiv.style.display = 'none';
            this.uploadedReceiptPath = null;
        }
    }

    async uploadReceipt(inputElement) {
        const file = inputElement.files[0];
        if (!file) return;

        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
        if (!validTypes.includes(file.type)) {
            this.showError('Invalid file type. Please upload PNG, JPG, JPEG, or PDF only.');
            inputElement.value = '';
            return;
        }
        
        // Check file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            this.showError('File too large. Maximum size is 5MB.');
            inputElement.value = '';
            return;
        }

        const formData = new FormData();
        formData.append('receipt', file);

        try {
            this.showLoading();
            
            const response = await fetch('/api/payments/upload-receipt', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.uploadedReceiptPath = data.receipt_path;
                const preview = document.getElementById('receiptPreview');
                if (preview) {
                    const isPdf = file.type === 'application/pdf';
                    preview.innerHTML = `
                        <div class="mt-2">
                            ${isPdf ? `
                                <div class="p-3 bg-light rounded border">
                                    <i class="fas fa-file-pdf text-danger fa-2x me-2"></i>
                                    <span>${file.name}</span>
                                </div>
                            ` : `
                                <img src="${data.receipt_path}" alt="Receipt" class="img-thumbnail" style="max-height: 150px;">
                            `}
                            <p class="text-success mb-0 mt-2"><i class="fas fa-check-circle me-1"></i>Receipt uploaded successfully</p>
                        </div>
                    `;
                }
                this.showSuccess('Receipt uploaded successfully');
            } else {
                this.showError(data.error || 'Failed to upload receipt');
                inputElement.value = '';
            }
        } catch (error) {
            console.error('Error uploading receipt:', error);
            this.showError('Failed to upload receipt. Please try again.');
            inputElement.value = '';
        } finally {
            this.hideLoading();
        }
    }

    showOrderConfirmationModal(order, paymentMethod, medicine) {
        const formatPaymentMethod = (method) => {
            const methods = {
                'cash_on_delivery': 'Cash on Delivery',
                'easypaisa': 'EasyPaisa',
                'jazzcash': 'JazzCash',
                'meezan_bank': 'Meezan Bank',
                'nayapay': 'NayaPay'
            };
            return methods[method] || method;
        };

        const modalHtml = `
            <div class="modal fade" id="orderConfirmationModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-check-circle me-2"></i>Order Placed Successfully!
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="text-center mb-4">
                                <i class="fas fa-check-circle text-success" style="font-size: 4rem;"></i>
                                <h4 class="mt-3">Thank You for Your Order!</h4>
                                <p class="text-muted">Order ID: <strong>#${order.id}</strong></p>
                            </div>
                            
                            <div class="card mb-3">
                                <div class="card-header bg-light">
                                    <i class="fas fa-shopping-bag me-1"></i>Order Details
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-8">
                                            <strong>${medicine ? medicine.name : 'Order Items'}</strong>
                                            ${medicine ? `<br><small class="text-muted">${medicine.chemical || ''}</small>` : ''}
                                        </div>
                                        <div class="col-4 text-end">
                                            <strong class="text-danger">PKR ${order.total_amount}</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card mb-3">
                                <div class="card-header bg-light">
                                    <i class="fas fa-credit-card me-1"></i>Payment Method
                                </div>
                                <div class="card-body">
                                    <div class="d-flex align-items-center">
                                        ${paymentMethod.logo_path ? `
                                            <img src="${paymentMethod.logo_path}" alt="${paymentMethod.name}" 
                                                 style="height: 35px; width: 50px; object-fit: contain;" class="me-2"
                                                 onerror="this.style.display='none'">
                                        ` : ''}
                                        <div>
                                            <strong>${paymentMethod.name || formatPaymentMethod(order.payment_method)}</strong>
                                            ${paymentMethod.account_title ? `<br><small class="text-muted">Account: ${paymentMethod.account_title}</small>` : ''}
                                            ${paymentMethod.account_number ? `<br><small class="text-primary fw-bold">${paymentMethod.account_number}</small>` : ''}
                                        </div>
                                    </div>
                                    ${order.payment_method !== 'cash_on_delivery' ? `
                                        <div class="mt-2">
                                            <span class="badge bg-warning text-dark">
                                                <i class="fas fa-clock me-1"></i>Payment Verification Pending
                                            </span>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                            
                            <div class="card">
                                <div class="card-header bg-light">
                                    <i class="fas fa-truck me-1"></i>Delivery Information
                                </div>
                                <div class="card-body">
                                    <p class="mb-1"><i class="fas fa-calendar-alt text-primary me-2"></i>Expected Delivery: <strong>${order.estimated_delivery || '2-3 Days'}</strong></p>
                                    <p class="mb-0"><i class="fas fa-info-circle text-muted me-2"></i>Status: <span class="badge bg-info">Pending</span></p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" onclick="app.showOrders()">
                                <i class="fas fa-list me-1"></i>View My Orders
                            </button>
                            <button type="button" class="btn btn-success" data-bs-dismiss="modal">
                                <i class="fas fa-shopping-cart me-1"></i>Continue Shopping
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('orderConfirmationModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('orderConfirmationModal'));
        modal.show();
    }

    // ============ AUTHENTICATION METHODS ============
    
    async checkAuthStatus() {
        if (this.authToken) {
            try {
                const response = await fetch('/api/auth/verify', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    this.userData = data.user;
                    localStorage.setItem('user_data', JSON.stringify(data.user));
                    this.updateAuthUI(true);
                    this.loadPendingAppointments();
                } else {
                    this.logout(false);
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                this.logout(false);
            }
        } else {
            this.updateAuthUI(false);
        }
    }

    updateAuthUI(isAuthenticated) {
        const authButtons = document.getElementById('authButtons');
        const userDropdown = document.getElementById('userDropdown');
        const userName = document.getElementById('userName');
        const adminLink = document.getElementById('adminLink');

        if (isAuthenticated && this.userData.name) {
            authButtons.style.display = 'none';
            userDropdown.style.display = 'block';
            userName.textContent = this.userData.name;
            
            // Show admin link for admin users
            if (adminLink && this.userData.role === 'admin') {
                adminLink.style.display = 'block';
            }
        } else {
            authButtons.style.display = 'block';
            userDropdown.style.display = 'none';
        }
    }

    async login(email, password) {
        try {
            this.showLoading();
            
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.authToken = data.token;
                this.userData = data.user;
                
                localStorage.setItem('auth_token', data.token);
                localStorage.setItem('user_data', JSON.stringify(data.user));
                
                this.updateAuthUI(true);
                this.hideAllModals();
                
                // Redirect admin users to admin dashboard
                if (data.user.role === 'admin') {
                    this.showSuccess('Login successful! Welcome back, ' + data.user.name + '. Redirecting to admin dashboard...');
                    // Ensure token is saved before redirect
                    setTimeout(() => {
                        // Double-check token is saved
                        localStorage.setItem('auth_token', data.token);
                        localStorage.setItem('user_data', JSON.stringify(data.user));
                        window.location.href = '/admin';
                    }, 1000);
                } else {
                    this.showSuccess('Login successful! Welcome back, ' + data.user.name);
                    this.loadPendingAppointments();
                }
                
                return true;
            } else {
                this.showError(data.error || 'Login failed');
                return false;
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Login failed. Please check your connection.');
            return false;
        } finally {
            this.hideLoading();
        }
    }

    async register(userData) {
        try {
            this.showLoading();
            
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (response.ok) {
                this.authToken = data.token;
                this.userData = data.user;
                
                localStorage.setItem('auth_token', data.token);
                localStorage.setItem('user_data', JSON.stringify(data.user));
                
                this.updateAuthUI(true);
                this.hideAllModals();
                this.showSuccess('Registration successful! Welcome to Red Dot Pharmacy, ' + data.user.name);
                
                return true;
            } else {
                this.showError(data.error || 'Registration failed');
                return false;
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showError('Registration failed. Please check your connection.');
            return false;
        } finally {
            this.hideLoading();
        }
    }

    logout(showMessage = true) {
        this.authToken = null;
        this.userData = {};
        this.cart = [];
        
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('cart');
        
        this.updateAuthUI(false);
        this.updateCartDisplay();
        
        if (showMessage) {
            this.showSuccess('You have been logged out successfully.');
        }
        
        // Redirect to home if on admin page
        if (window.location.pathname.includes('/admin')) {
            window.location.href = '/';
        }
    }

    // ============ MEDICINE MANAGEMENT ============
    
    async loadMedicines(params = {}) {
        try {
            const queryParams = new URLSearchParams(params);
            const response = await fetch(`/api/store/medicines?${queryParams}`);
            
            if (response.ok) {
                const data = await response.json();
                this.medicines = data.medicines;
                this.displayMedicines(data.medicines);
                
                // Update medicine count in hero
                const countElement = document.getElementById('medicineCount');
                if (countElement) {
                    countElement.textContent = `${data.total_count}+`;
                }
                
                return data;
            } else {
                throw new Error('Failed to load medicines');
            }
        } catch (error) {
            console.error('Error loading medicines:', error);
            this.showError('Failed to load medicines. Please try again.');
            return null;
        }
    }

    displayMedicines(medicines) {
        const grid = document.getElementById('medicineGrid');
        if (!grid) return;

        if (medicines.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-pills fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">No medicines found</h5>
                    <p class="text-muted">Try adjusting your search criteria</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = medicines.map(medicine => `
            <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
                <div class="card medicine-card h-100">
                    <div class="position-relative">
                        <img src="${medicine.image_path || '/static/images/default-medicine.png'}" 
                             class="card-img-top medicine-image" 
                             alt="${medicine.name}"
                             onerror="this.src='/static/images/default-medicine.png'"
                             style="height: 180px; object-fit: cover;">
                        <span class="badge stock-badge ${medicine.status === 'in_stock' ? 'bg-success' : 'bg-danger'}">
                            ${medicine.status === 'in_stock' ? 'In Stock' : 'Out of Stock'}
                        </span>
                    </div>
                    <div class="card-body medicine-info d-flex flex-column">
                        <h6 class="card-title">${medicine.name}</h6>
                        <p class="text-muted small mb-2">${medicine.chemical || 'Generic Medicine'}</p>
                        ${medicine.description ? `<p class="text-muted small mb-3">${medicine.description.substring(0, 80)}${medicine.description.length > 80 ? '...' : ''}</p>` : ''}
                        <div class="mt-auto">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <span class="medicine-price">PKR ${medicine.price}</span>
                                <small class="text-muted">${medicine.category || 'General'}</small>
                            </div>
                            <div class="d-flex gap-2 mb-2">
                                <button class="btn btn-outline-danger btn-sm flex-fill" 
                                        onclick="app.viewMedicine(${medicine.id})"
                                        title="View Details">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-danger btn-sm flex-fill ${medicine.status !== 'in_stock' ? 'disabled' : ''}" 
                                        onclick="app.addToCart(${medicine.id})"
                                        ${medicine.status !== 'in_stock' ? 'disabled' : ''}
                                        title="Add to Cart">
                                    <i class="fas fa-cart-plus me-1"></i>Add to Cart
                                </button>
                            </div>
                            <button class="btn btn-success btn-sm w-100 ${medicine.status !== 'in_stock' ? 'disabled' : ''}" 
                                    onclick="app.buyNow(${medicine.id})"
                                    ${medicine.status !== 'in_stock' ? 'disabled' : ''}
                                    title="Buy Now">
                                <i class="fas fa-bolt me-1"></i>Buy Now
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async searchMedicines(query = '') {
        const searchParams = {
            search: query,
            limit: 20
        };
        return this.loadMedicines(searchParams);
    }

    async filterByCategory(category) {
        // Update category filter buttons
        document.querySelectorAll('.category-filter .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        event.target.classList.add('active');
        
        const filterParams = category ? { category } : {};
        return this.loadMedicines(filterParams);
    }

    async viewMedicine(medicineId) {
        try {
            const response = await fetch(`/api/store/medicines/${medicineId}`);
            
            if (response.ok) {
                const data = await response.json();
                this.showMedicineModal(data.medicine);
            } else {
                throw new Error('Failed to load medicine details');
            }
        } catch (error) {
            console.error('Error loading medicine details:', error);
            this.showError('Failed to load medicine details.');
        }
    }

    showMedicineModal(medicine) {
        const modalHtml = `
            <div class="modal fade" id="medicineModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${medicine.name}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-4">
                                    <img src="${medicine.image_path || '/static/images/default-medicine.png'}" 
                                         class="img-fluid rounded" alt="${medicine.name}">
                                </div>
                                <div class="col-md-8">
                                    <h6>Chemical Name: <span class="text-muted">${medicine.chemical || 'Not specified'}</span></h6>
                                    <h6>Category: <span class="text-muted">${medicine.category || 'General'}</span></h6>
                                    <h6>Price: <span class="text-danger">PKR ${medicine.price}</span></h6>
                                    <h6>Status: <span class="badge ${medicine.status === 'in_stock' ? 'bg-success' : 'bg-danger'}">${medicine.status === 'in_stock' ? 'In Stock' : 'Out of Stock'}</span></h6>
                                    ${medicine.stock_quantity !== undefined ? `<h6>Available: <span class="text-muted">${medicine.stock_quantity} units</span></h6>` : ''}
                                    ${medicine.description ? `<p class="mt-3">${medicine.description}</p>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-danger ${medicine.status !== 'in_stock' ? 'disabled' : ''}" 
                                    onclick="app.addToCart(${medicine.id}); bootstrap.Modal.getInstance(document.getElementById('medicineModal')).hide();"
                                    ${medicine.status !== 'in_stock' ? 'disabled' : ''}>
                                <i class="fas fa-cart-plus me-2"></i>Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('medicineModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('medicineModal'));
        modal.show();
    }

    // ============ SHOPPING CART MANAGEMENT ============
    
    addToCart(medicineId, quantity = 1) {
        const medicine = this.medicines.find(m => m.id === medicineId);
        if (!medicine) {
            this.showError('Medicine not found');
            return;
        }

        if (medicine.status !== 'in_stock') {
            this.showError('This medicine is currently out of stock');
            return;
        }

        const existingItem = this.cart.find(item => item.medicine_id === medicineId);
        
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.cart.push({
                medicine_id: medicineId,
                medicine_name: medicine.name,
                price: medicine.price,
                quantity: quantity,
                image_path: medicine.image_path
            });
        }

        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.updateCartDisplay();
        this.showSuccess(`${medicine.name} added to cart!`);
    }

    buyNow(medicineId) {
        const medicine = this.medicines.find(m => m.id === medicineId);
        if (!medicine) {
            this.showError('Medicine not found');
            return;
        }

        if (medicine.status !== 'in_stock') {
            this.showError('This medicine is currently out of stock');
            return;
        }

        // Check if user is logged in
        if (!this.authToken) {
            this.showError('Please login to place an order');
            this.showLogin();
            return;
        }

        // Show quick checkout modal for this specific medicine
        this.showQuickCheckoutModal(medicine);
    }

    showQuickCheckoutModal(medicine) {
        this.uploadedReceiptPath = null;
        
        const modalHtml = `
            <div class="modal fade" id="quickCheckoutModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-bolt text-success me-2"></i>Quick Checkout
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <!-- Order Summary -->
                                    <div class="mb-4">
                                        <h6><i class="fas fa-shopping-bag text-danger me-2"></i>Order Summary</h6>
                                        <div class="card">
                                            <div class="card-body">
                                                <div class="row align-items-center">
                                                    <div class="col-3">
                                                        <img src="${medicine.image_path || '/static/images/default-medicine.png'}" 
                                                             alt="${medicine.name}" class="img-fluid rounded">
                                                    </div>
                                                    <div class="col-6">
                                                        <h6 class="mb-1">${medicine.name}</h6>
                                                        <small class="text-muted">${medicine.chemical || 'Generic Medicine'}</small>
                                                        <br><small class="text-muted">Quantity: 1</small>
                                                    </div>
                                                    <div class="col-3 text-end">
                                                        <strong class="text-danger">PKR ${medicine.price}</strong>
                                                    </div>
                                                </div>
                                                <hr>
                                                <div class="d-flex justify-content-between">
                                                    <span>Subtotal:</span>
                                                    <span>PKR ${medicine.price}</span>
                                                </div>
                                                <div class="d-flex justify-content-between">
                                                    <span>Delivery:</span>
                                                    <span>PKR 100</span>
                                                </div>
                                                <hr>
                                                <div class="d-flex justify-content-between">
                                                    <strong>Total:</strong>
                                                    <strong class="text-danger">PKR ${medicine.price + 100}</strong>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Delivery Details -->
                                    <form id="quickCheckoutForm">
                                        <div class="mb-3">
                                            <label class="form-label"><i class="fas fa-map-marker-alt me-1"></i>Delivery Address *</label>
                                            <textarea class="form-control" id="quickDeliveryAddress" rows="2" 
                                                      placeholder="Enter your complete delivery address..." required></textarea>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label"><i class="fas fa-phone me-1"></i>Contact Number *</label>
                                            <input type="tel" class="form-control" id="quickDeliveryPhone" 
                                                   placeholder="Enter your contact number" required>
                                        </div>
                                    </form>
                                </div>
                                
                                <div class="col-md-6">
                                    <!-- Payment Method Selection -->
                                    <div class="mb-3">
                                        <h6><i class="fas fa-credit-card text-danger me-2"></i>Payment Method</h6>
                                        <div id="paymentMethodsContainer">
                                            ${this.getPaymentMethodsHtml()}
                                        </div>
                                    </div>
                                    
                                    <!-- Account Details for online payment -->
                                    <div id="paymentAccountDetails" style="display: none;"></div>
                                    
                                    <!-- Receipt Upload Section -->
                                    <div id="receiptUploadSection" style="display: none;">
                                        <div class="card border-warning">
                                            <div class="card-body">
                                                <h6 class="card-title"><i class="fas fa-upload text-warning me-2"></i>Upload Payment Receipt *</h6>
                                                <p class="small text-muted mb-2">Please upload your payment screenshot/receipt to confirm your order.</p>
                                                <input type="file" class="form-control" id="receiptUpload" 
                                                       accept="image/png,image/jpeg,image/jpg,application/pdf"
                                                       onchange="app.uploadReceipt(this)">
                                                <small class="text-muted">Accepted: PNG, JPG, JPEG, PDF (Max 5MB)</small>
                                                <div id="receiptPreview"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-success" onclick="app.processQuickOrder(${medicine.id})">
                                <i class="fas fa-bolt me-1"></i>Place Order - PKR ${medicine.price + 100}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('quickCheckoutModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('quickCheckoutModal'));
        modal.show();
        
        // Trigger payment method change to set initial state
        setTimeout(() => this.onPaymentMethodChange(), 100);
    }

    async processQuickOrder(medicineId) {
        const medicine = this.medicines.find(m => m.id === medicineId);
        if (!medicine) {
            this.showError('Medicine not found');
            return;
        }

        const address = document.getElementById('quickDeliveryAddress')?.value?.trim();
        const phone = document.getElementById('quickDeliveryPhone')?.value?.trim();
        
        const selectedRadio = document.querySelector('input[name="paymentMethod"]:checked');
        const paymentMethod = selectedRadio?.value || 'cash_on_delivery';
        const requiresReceipt = selectedRadio?.dataset.requiresReceipt === 'true';

        if (!address) {
            this.showError('Please enter your delivery address');
            return;
        }

        if (!phone) {
            this.showError('Please enter your contact number');
            return;
        }

        if (requiresReceipt && !this.uploadedReceiptPath) {
            this.showError('Please upload your payment receipt before placing the order');
            return;
        }

        try {
            this.showLoading();

            const orderData = {
                address: address,
                phone: phone,
                payment_method: paymentMethod,
                payment_receipt_path: this.uploadedReceiptPath,
                items: [{
                    medicine_id: medicineId,
                    quantity: 1,
                    price_each: medicine.price
                }]
            };

            const response = await fetch('/api/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify(orderData)
            });

            const data = await response.json();

            if (response.ok) {
                // Hide the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('quickCheckoutModal'));
                if (modal) {
                    modal.hide();
                }
                
                // Get the selected payment method info for confirmation
                const selectedMethod = this.paymentMethods.find(m => m.slug === paymentMethod) || {};
                
                // Clear the receipt path
                this.uploadedReceiptPath = null;
                
                // Show order confirmation modal
                this.showOrderConfirmationModal(data.order, selectedMethod, medicine);
                
                // Reload medicines to update stock display
                this.loadMedicines();
            } else {
                this.showError(data.error || 'Failed to place order');
            }
        } catch (error) {
            console.error('Error placing quick order:', error);
            this.showError('Failed to place order. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    removeFromCart(medicineId) {
        this.cart = this.cart.filter(item => item.medicine_id !== medicineId);
        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.updateCartDisplay();
        this.displayCartItems();
    }

    updateCartQuantity(medicineId, newQuantity) {
        const item = this.cart.find(item => item.medicine_id === medicineId);
        if (item) {
            if (newQuantity <= 0) {
                this.removeFromCart(medicineId);
            } else {
                item.quantity = newQuantity;
                localStorage.setItem('cart', JSON.stringify(this.cart));
                this.updateCartDisplay();
                this.displayCartItems();
            }
        }
    }

    updateCartDisplay() {
        const cartCount = document.getElementById('cartCount');
        if (cartCount) {
            const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.textContent = totalItems;
        }
    }

    updateNotificationCount(count = null) {
        if (count !== null) {
            this.pendingAppointments = count;
        }
        
        const notificationCount = document.getElementById('notificationCount');
        if (notificationCount) {
            notificationCount.textContent = this.pendingAppointments;
            notificationCount.style.display = this.pendingAppointments > 0 ? 'inline' : 'none';
        }
    }

    async loadPendingAppointments() {
        if (!this.authToken) return;
        
        try {
            const response = await fetch('/api/appointments?status=pending', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                const pendingCount = data.appointments?.filter(apt => apt.approval_status === 'pending').length || 0;
                this.updateNotificationCount(pendingCount);
            }
        } catch (error) {
            console.error('Error loading pending appointments:', error);
        }
    }

    showNotifications() {
        if (!this.authToken) {
            this.showError('Please login to view notifications');
            this.showLogin();
            return;
        }
        
        if (this.pendingAppointments > 0) {
            const message = `You have ${this.pendingAppointments} appointment${this.pendingAppointments > 1 ? 's' : ''} waiting for doctor approval.`;
            this.showSuccess(message + ' <a href="/appointments" class="text-white"><u>View Appointments</u></a>');
        } else {
            this.showSuccess('No pending notifications');
        }
    }

    displayCartItems() {
        const cartItems = document.getElementById('cartItems');
        const cartSubtotal = document.getElementById('cartSubtotal');
        const cartTotal = document.getElementById('cartTotal');
        
        if (!cartItems) return;

        if (this.cart.length === 0) {
            cartItems.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-shopping-cart fa-3x text-muted mb-3"></i>
                    <h6 class="text-muted">Your cart is empty</h6>
                    <p class="text-muted">Add some medicines to get started</p>
                </div>
            `;
            if (cartSubtotal) cartSubtotal.textContent = 'PKR 0';
            if (cartTotal) cartTotal.textContent = 'PKR 100';
            return;
        }

        const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const total = subtotal + 100; // Add delivery fee

        cartItems.innerHTML = this.cart.map(item => `
            <div class="cart-item">
                <div class="row align-items-center">
                    <div class="col-2">
                        <img src="${item.image_path || '/static/images/default-medicine.png'}" 
                             alt="${item.medicine_name}" class="img-fluid rounded">
                    </div>
                    <div class="col-4">
                        <h6 class="mb-1">${item.medicine_name}</h6>
                        <small class="text-muted">PKR ${item.price} each</small>
                    </div>
                    <div class="col-3">
                        <div class="quantity-controls">
                            <button onclick="app.updateCartQuantity(${item.medicine_id}, ${item.quantity - 1})">-</button>
                            <span class="mx-2">${item.quantity}</span>
                            <button onclick="app.updateCartQuantity(${item.medicine_id}, ${item.quantity + 1})">+</button>
                        </div>
                    </div>
                    <div class="col-2">
                        <strong>PKR ${item.price * item.quantity}</strong>
                    </div>
                    <div class="col-1">
                        <button class="btn btn-outline-danger btn-sm" onclick="app.removeFromCart(${item.medicine_id})" title="Remove">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        if (cartSubtotal) cartSubtotal.textContent = `PKR ${subtotal}`;
        if (cartTotal) cartTotal.textContent = `PKR ${total}`;
    }

    async placeOrder() {
        if (!this.authToken) {
            this.showError('Please login to place an order');
            this.showLogin();
            return;
        }

        if (this.cart.length === 0) {
            this.showError('Your cart is empty');
            return;
        }

        const address = document.getElementById('deliveryAddress')?.value?.trim();
        const phone = document.getElementById('deliveryPhone')?.value?.trim();

        if (!address) {
            this.showError('Please enter your delivery address');
            return;
        }

        if (!phone) {
            this.showError('Please enter your contact number');
            return;
        }

        try {
            this.showLoading();

            const orderData = {
                address: address,
                phone: phone,
                items: this.cart.map(item => ({
                    medicine_id: item.medicine_id,
                    quantity: item.quantity,
                    price_each: item.price
                }))
            };

            const response = await fetch('/api/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify(orderData)
            });

            const data = await response.json();

            if (response.ok) {
                this.cart = [];
                localStorage.removeItem('cart');
                this.updateCartDisplay();
                this.hideAllModals();
                
                this.showSuccess(`Order placed successfully! Order ID: #${data.order.id}. Expected delivery: ${data.order.estimated_delivery}`);
            } else {
                this.showError(data.error || 'Failed to place order');
            }
        } catch (error) {
            console.error('Error placing order:', error);
            this.showError('Failed to place order. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    // ============ APPOINTMENT MANAGEMENT ============
    
    async loadDoctors() {
        try {
            const response = await fetch('/api/appointments/doctors');
            
            if (response.ok) {
                const data = await response.json();
                this.doctors = data.doctors;
                this.displayDoctors(data.doctors);
                this.populateDoctorSelect(data.doctors);
                return data;
            } else {
                throw new Error('Failed to load doctors');
            }
        } catch (error) {
            console.error('Error loading doctors:', error);
            this.showError('Failed to load doctors.');
            return null;
        }
    }

    displayDoctors(doctors) {
        const grid = document.getElementById('doctorGrid');
        if (!grid) return;

        if (doctors.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-4">
                    <i class="fas fa-user-md fa-3x text-muted mb-3"></i>
                    <h6 class="text-muted">No doctors available</h6>
                </div>
            `;
            return;
        }

        grid.innerHTML = doctors.map(doctor => `
            <div class="col-lg-4 col-md-6 mb-4">
                <div class="card doctor-card h-100">
                    <div class="card-body">
                        <div class="text-center mb-3">
                            <div class="doctor-avatar mb-3">
                                <i class="fas fa-user-md fa-3x text-primary"></i>
                            </div>
                            <h5 class="card-title mb-1">${doctor.name}</h5>
                            <p class="text-primary fw-bold mb-2">${doctor.specialization || 'General Medicine'}</p>
                        </div>
                        
                        <div class="doctor-details mb-3">
                            <div class="row text-center">
                                <div class="col-6">
                                    <small class="text-muted d-block">Experience</small>
                                    <strong>${doctor.experience_years || 0} years</strong>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted d-block">Qualification</small>
                                    <strong class="small">${(doctor.qualification || 'MBBS').substring(0, 15)}${(doctor.qualification || '').length > 15 ? '...' : ''}</strong>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <small class="text-muted d-block"><i class="fas fa-hospital me-1"></i>Currently at</small>
                            <p class="mb-0 small fw-bold">${doctor.current_hospital || 'Red Dot Medical Center'}</p>
                        </div>
                        
                        ${doctor.phone ? `<div class="mb-3"><small class="text-muted"><i class="fas fa-phone me-1"></i>${doctor.phone}</small></div>` : ''}
                        
                        <div class="text-center">
                            <button class="btn btn-danger btn-sm w-100" onclick="app.selectDoctor(${doctor.id})">
                                <i class="fas fa-calendar-plus me-1"></i>Book Appointment
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    populateDoctorSelect(doctors) {
        const select = document.getElementById('doctorSelect');
        if (!select) return;

        select.innerHTML = '<option value="">Choose a doctor...</option>' +
            doctors.map(doctor => `<option value="${doctor.id}">${doctor.name} - ${doctor.specialization || 'General Medicine'}</option>`).join('');
    }

    selectDoctor(doctorId) {
        const doctorSelect = document.getElementById('doctorSelect');
        if (doctorSelect) {
            doctorSelect.value = doctorId;
            this.loadTimeSlots();
        }
        
        // Scroll to consultation form
        document.getElementById('consultation')?.scrollIntoView({ behavior: 'smooth' });
    }

    async loadTimeSlots() {
        const doctorId = document.getElementById('doctorSelect')?.value;
        const date = document.getElementById('consultationDate')?.value;
        const timeSlotsContainer = document.getElementById('timeSlots');
        
        if (!doctorId || !date || !timeSlotsContainer) return;

        try {
            const response = await fetch(`/api/appointments/available-slots/${doctorId}?date=${date}`);
            
            if (response.ok) {
                const data = await response.json();
                this.displayTimeSlots(data.slots);
            } else {
                throw new Error('Failed to load time slots');
            }
        } catch (error) {
            console.error('Error loading time slots:', error);
            timeSlotsContainer.innerHTML = '<p class="text-danger">Failed to load available time slots</p>';
        }
    }

    displayTimeSlots(slots) {
        const container = document.getElementById('timeSlots');
        if (!container) return;

        if (slots.length === 0) {
            container.innerHTML = '<p class="text-muted">No time slots available for selected date</p>';
            return;
        }

        container.innerHTML = slots.map(slot => `
            <div class="time-slot ${slot.available ? '' : 'unavailable'}" 
                 onclick="${slot.available ? `app.selectTimeSlot('${slot.slot_id}', '${slot.display_time}')` : ''}"
                 data-slot-id="${slot.slot_id}">
                ${slot.display_time}
            </div>
        `).join('');
    }

    selectTimeSlot(slotId, displayTime) {
        // Remove previous selection
        document.querySelectorAll('.time-slot').forEach(slot => {
            slot.classList.remove('selected');
        });
        
        // Add selection to clicked slot
        event.target.classList.add('selected');
        this.selectedSlotId = slotId;
    }

    async bookAppointment(formData) {
        if (!this.authToken) {
            this.showError('Please login to book an appointment');
            this.showLogin();
            return;
        }

        if (!this.selectedSlotId) {
            this.showError('Please select a time slot');
            return;
        }

        try {
            this.showLoading();

            const appointmentData = {
                doctor_id: parseInt(formData.get('doctor_id')),
                slot_id: this.selectedSlotId,
                symptoms: formData.get('symptoms'),
                note: formData.get('note') || ''
            };

            const response = await fetch('/api/appointments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify(appointmentData)
            });

            const data = await response.json();

            if (response.ok) {
                const doctor = this.doctors.find(d => d.id === appointmentData.doctor_id);
                this.showSuccess(`Your consultation request has been sent to ${doctor?.name || 'doctor'} and is waiting for approval. You will receive an email with the consultation link once the doctor approves your request.`);
                
                // Reset form
                document.getElementById('consultationForm')?.reset();
                this.selectedSlotId = null;
                document.querySelectorAll('.time-slot').forEach(slot => {
                    slot.classList.remove('selected');
                });
                
                // Update pending appointments count
                this.loadPendingAppointments();
                
                return data;
            } else {
                this.showError(data.error || 'Failed to book appointment');
            }
        } catch (error) {
            console.error('Error booking appointment:', error);
            this.showError('Failed to book appointment. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    // ============ USER PROFILE MANAGEMENT ============
    
    async showProfile() {
        if (!this.userData.name) {
            this.showError('Please login to view profile');
            return;
        }

        const modalHtml = `
            <div class="modal fade" id="profileModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-user-edit text-danger me-2"></i>My Profile
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="profileForm">
                                <div class="mb-3">
                                    <label class="form-label">Full Name</label>
                                    <input type="text" class="form-control" name="name" value="${this.userData.name || ''}" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Email Address</label>
                                    <input type="email" class="form-control" value="${this.userData.email || ''}" disabled>
                                    <small class="text-muted">Email cannot be changed</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Phone Number</label>
                                    <input type="tel" class="form-control" name="phone" value="${this.userData.phone || ''}" placeholder="03XX-XXXXXXX">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">New Password (optional)</label>
                                    <input type="password" class="form-control" name="password" placeholder="Leave blank to keep current password">
                                </div>
                                <button type="submit" class="btn btn-danger w-100">
                                    <i class="fas fa-save me-2"></i>Update Profile
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('profileModal');
        if (existingModal) existingModal.remove();
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Setup form handler
        document.getElementById('profileForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const profileData = Object.fromEntries(formData.entries());
            
            // Remove empty password
            if (!profileData.password) {
                delete profileData.password;
            }
            
            await this.updateProfile(profileData);
        });
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('profileModal'));
        modal.show();
    }

    async updateProfile(profileData) {
        try {
            this.showLoading();
            
            const response = await fetch('/api/auth/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify(profileData)
            });

            const data = await response.json();

            if (response.ok) {
                this.userData = data.user;
                localStorage.setItem('user_data', JSON.stringify(data.user));
                this.updateAuthUI(true);
                this.hideAllModals();
                this.showSuccess('Profile updated successfully!');
            } else {
                this.showError(data.error || 'Failed to update profile');
            }
        } catch (error) {
            console.error('Error updating profile:', error);
            this.showError('Failed to update profile. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async showOrders() {
        if (!this.authToken) {
            this.showError('Please login to view orders');
            return;
        }

        try {
            this.showLoading();
            
            const response = await fetch('/api/orders', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayOrdersModal(data.orders);
            } else {
                throw new Error('Failed to load orders');
            }
        } catch (error) {
            console.error('Error loading orders:', error);
            this.showError('Failed to load orders.');
        } finally {
            this.hideLoading();
        }
    }

    getPaymentStatusBadge(paymentStatus, paymentMethod) {
        if (paymentMethod === 'cash_on_delivery') {
            return '<span class="badge bg-success">Cash on Delivery</span>';
        }
        const statusColors = {
            'pending': 'warning',
            'accepted': 'success',
            'declined': 'danger'
        };
        const statusLabels = {
            'pending': 'Payment Pending',
            'accepted': 'Payment Verified',
            'declined': 'Payment Rejected'
        };
        const color = statusColors[paymentStatus] || 'secondary';
        const label = statusLabels[paymentStatus] || paymentStatus;
        return `<span class="badge bg-${color}">${label}</span>`;
    }

    displayOrdersModal(orders) {
        const ordersHtml = orders.length === 0 ? 
            '<p class="text-muted text-center py-4">No orders found</p>' :
            orders.map(order => {
                const paymentBadge = this.getPaymentStatusBadge(order.payment_status, order.payment_method);
                const showReupload = order.payment_status === 'declined' && order.payment_method !== 'cash_on_delivery';
                const rejectionNote = order.payment_rejection_reason ? 
                    `<div class="alert alert-danger py-2 mb-2 small"><i class="fas fa-exclamation-circle me-1"></i>Rejection reason: ${order.payment_rejection_reason}</div>` : '';
                
                return `
                <div class="card mb-3 ${order.payment_status === 'declined' ? 'border-danger' : ''}">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h6>Order #${order.id}</h6>
                                <p class="text-muted mb-1">${order.item_count} items • PKR ${order.total_amount}</p>
                                <p class="text-muted mb-1">${new Date(order.created_at).toLocaleString()}</p>
                                <div class="mb-2">
                                    <span class="badge bg-${this.getOrderStatusColor(order.status)} me-1">${order.status.replace('_', ' ').toUpperCase()}</span>
                                    ${paymentBadge}
                                </div>
                                ${rejectionNote}
                            </div>
                            <div class="col-md-4 text-end">
                                <button class="btn btn-outline-danger btn-sm mb-1" onclick="app.viewOrderDetails(${order.id})">
                                    <i class="fas fa-eye me-1"></i>View Details
                                </button>
                                ${showReupload ? `
                                    <br><button class="btn btn-warning btn-sm mt-1" onclick="app.showReuploadReceiptModal(${order.id})">
                                        <i class="fas fa-upload me-1"></i>Re-upload Receipt
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `}).join('');

        const modalHtml = `
            <div class="modal fade" id="ordersModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-shopping-bag text-danger me-2"></i>My Orders
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${ordersHtml}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('ordersModal');
        if (existingModal) existingModal.remove();
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('ordersModal'));
        modal.show();
    }

    async viewOrderDetails(orderId) {
        try {
            this.showLoading();
            
            const response = await fetch(`/api/orders/${orderId}`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                const order = data.order;
                
                // Build items list HTML
                let itemsHtml = order.items.map(item => `
                    <tr>
                        <td>
                            <div class="d-flex align-items-center">
                                <img src="${item.medicine.image_path || '/static/images/default-medicine.png'}" 
                                     alt="${item.medicine.name}" class="rounded me-2" 
                                     style="width: 40px; height: 40px; object-fit: cover;">
                                <span>${item.medicine.name}</span>
                            </div>
                        </td>
                        <td>PKR ${item.price_each}</td>
                        <td>${item.quantity}</td>
                        <td>PKR ${item.total}</td>
                    </tr>
                `).join('');
                
                const statusColor = this.getOrderStatusColor(order.status);
                const orderDate = new Date(order.created_at).toLocaleString();
                
                // Create modal HTML
                const modalHtml = `
                    <div class="modal fade" id="orderDetailModal" tabindex="-1">
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">
                                        <i class="fas fa-shopping-bag text-danger me-2"></i>Order #${order.id} Details
                                    </h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="row mb-4">
                                        <div class="col-md-6">
                                            <h6><i class="fas fa-truck text-muted me-2"></i>Delivery Address</h6>
                                            <p class="text-muted">${order.address}</p>
                                        </div>
                                        <div class="col-md-6">
                                            <h6><i class="fas fa-info-circle text-muted me-2"></i>Order Info</h6>
                                            <p class="mb-1"><strong>Date:</strong> ${orderDate}</p>
                                            <p class="mb-1"><strong>Order Status:</strong> <span class="badge bg-${statusColor}">${order.status.replace('_', ' ').toUpperCase()}</span></p>
                                            <p class="mb-1"><strong>Payment Method:</strong> ${order.payment_method.replace('_', ' ')}</p>
                                            <p class="mb-0"><strong>Payment Status:</strong> ${this.getPaymentStatusBadge(order.payment_status, order.payment_method)}</p>
                                            ${order.payment_rejection_reason ? `
                                                <div class="alert alert-danger py-2 mt-2 small">
                                                    <i class="fas fa-exclamation-circle me-1"></i>Rejection: ${order.payment_rejection_reason}
                                                </div>
                                            ` : ''}
                                            ${order.receipt_uploaded_at ? `
                                                <p class="mb-0 mt-2 text-muted small"><i class="fas fa-upload me-1"></i>Receipt uploaded: ${new Date(order.receipt_uploaded_at).toLocaleString()}</p>
                                            ` : ''}
                                        </div>
                                    </div>
                                    
                                    <h6 class="mb-3"><i class="fas fa-pills text-muted me-2"></i>Order Items</h6>
                                    <table class="table table-bordered">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Medicine</th>
                                                <th>Price</th>
                                                <th>Qty</th>
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
                throw new Error('Failed to load order details');
            }
        } catch (error) {
            console.error('Error viewing order details:', error);
            this.showError('Failed to load order details');
        } finally {
            this.hideLoading();
        }
    }

    showReuploadReceiptModal(orderId) {
        const modalHtml = `
            <div class="modal fade" id="reuploadReceiptModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title">
                                <i class="fas fa-upload me-2"></i>Re-upload Payment Receipt
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                Your previous payment receipt was rejected. Please upload a new, clearer receipt.
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-file-image me-1"></i>Select Receipt File</label>
                                <input type="file" class="form-control" id="reuploadReceiptFile" 
                                       accept="image/png,image/jpeg,image/jpg,application/pdf">
                                <small class="text-muted">Accepted formats: PNG, JPG, JPEG, PDF (Max 5MB)</small>
                            </div>
                            
                            <div id="reuploadPreview" class="mb-3"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-warning" onclick="app.submitReuploadReceipt(${orderId})">
                                <i class="fas fa-upload me-1"></i>Upload Receipt
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const existingModal = document.getElementById('reuploadReceiptModal');
        if (existingModal) existingModal.remove();
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const fileInput = document.getElementById('reuploadReceiptFile');
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const preview = document.getElementById('reuploadPreview');
                if (file.type === 'application/pdf') {
                    preview.innerHTML = `
                        <div class="p-3 bg-light rounded border">
                            <i class="fas fa-file-pdf text-danger fa-2x me-2"></i>
                            <span>${file.name}</span>
                        </div>
                    `;
                } else {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        preview.innerHTML = `<img src="${e.target.result}" class="img-thumbnail" style="max-height: 150px;">`;
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
        
        const modal = new bootstrap.Modal(document.getElementById('reuploadReceiptModal'));
        modal.show();
    }

    async submitReuploadReceipt(orderId) {
        const fileInput = document.getElementById('reuploadReceiptFile');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showError('Please select a receipt file');
            return;
        }
        
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
        if (!validTypes.includes(file.type)) {
            this.showError('Invalid file type. Please upload PNG, JPG, JPEG, or PDF only.');
            return;
        }
        
        if (file.size > 5 * 1024 * 1024) {
            this.showError('File too large. Maximum size is 5MB.');
            return;
        }
        
        const formData = new FormData();
        formData.append('receipt', file);
        
        try {
            this.showLoading();
            
            const response = await fetch(`/api/payments/reupload-receipt/${orderId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('reuploadReceiptModal'));
                if (modal) modal.hide();
                
                this.showSuccess('Receipt uploaded successfully! Your payment will be reviewed.');
                
                // Refresh orders modal
                this.showOrders();
            } else {
                this.showError(data.error || 'Failed to upload receipt');
            }
        } catch (error) {
            console.error('Error re-uploading receipt:', error);
            this.showError('Failed to upload receipt. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async showAppointments() {
        if (!this.authToken) {
            this.showError('Please login to view appointments');
            return;
        }

        try {
            this.showLoading();
            
            const response = await fetch('/api/appointments', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayAppointmentsModal(data.appointments);
            } else {
                throw new Error('Failed to load appointments');
            }
        } catch (error) {
            console.error('Error loading appointments:', error);
            this.showError('Failed to load appointments.');
        } finally {
            this.hideLoading();
        }
    }

    displayAppointmentsModal(appointments) {
        const appointmentsHtml = appointments.length === 0 ? 
            '<p class="text-muted text-center py-4">No appointments found</p>' :
            appointments.map(appt => `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h6>Consultation with ${appt.doctor_name}</h6>
                                <p class="text-muted mb-1">${new Date(appt.start_time).toLocaleString()}</p>
                                <p class="text-muted mb-1">${appt.symptoms}</p>
                                <span class="badge bg-${this.getAppointmentStatusColor(appt.status)}">${appt.status.toUpperCase()}</span>
                            </div>
                            <div class="col-md-4 text-end">
                                ${appt.google_meet_link && appt.status === 'scheduled' ? 
                                    `<a href="${appt.google_meet_link}" class="btn btn-success btn-sm mb-2" target="_blank">
                                        <i class="fas fa-video me-1"></i>Join Meeting
                                    </a><br>` : ''}
                                <button class="btn btn-outline-danger btn-sm" onclick="app.viewAppointmentDetails(${appt.id})">
                                    View Details
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

        const modalHtml = `
            <div class="modal fade" id="appointmentsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-calendar text-danger me-2"></i>My Appointments
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${appointmentsHtml}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('appointmentsModal');
        if (existingModal) existingModal.remove();
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('appointmentsModal'));
        modal.show();
    }

    async viewAppointmentDetails(appointmentId) {
        if (!this.authToken) {
            this.showError('Please login to view appointment details');
            return;
        }

        try {
            this.showLoading();
            
            const response = await fetch(`/api/appointments/${appointmentId}`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayAppointmentDetailsModal(data.appointment);
            } else {
                throw new Error('Failed to load appointment details');
            }
        } catch (error) {
            console.error('Error loading appointment details:', error);
            this.showError('Failed to load appointment details.');
        } finally {
            this.hideLoading();
        }
    }

    displayAppointmentDetailsModal(appointment) {
        const statusColor = this.getAppointmentStatusColor(appointment.status);
        const meetLinkHtml = appointment.google_meet_link ? 
            `<div class="alert alert-success mt-3">
                <i class="fas fa-video me-2"></i>
                <strong>Google Meet Link:</strong>
                <a href="${appointment.google_meet_link}" target="_blank" class="ms-2">
                    ${appointment.google_meet_link}
                </a>
            </div>` : '';

        const modalHtml = `
            <div class="modal fade" id="appointmentDetailsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-calendar-check text-danger me-2"></i>Appointment Details
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <strong>Doctor:</strong> ${appointment.doctor?.name || 'N/A'}
                            </div>
                            <div class="mb-3">
                                <strong>Email:</strong> ${appointment.doctor?.email || 'N/A'}
                            </div>
                            <div class="mb-3">
                                <strong>Date & Time:</strong> ${new Date(appointment.start_time).toLocaleString()}
                            </div>
                            <div class="mb-3">
                                <strong>Symptoms:</strong> ${appointment.symptoms || 'Not specified'}
                            </div>
                            <div class="mb-3">
                                <strong>Notes:</strong> ${appointment.note || 'No additional notes'}
                            </div>
                            <div class="mb-3">
                                <strong>Status:</strong> 
                                <span class="badge bg-${statusColor}">${appointment.status?.toUpperCase() || 'PENDING'}</span>
                            </div>
                            ${meetLinkHtml}
                        </div>
                        <div class="modal-footer">
                            ${appointment.google_meet_link && appointment.status === 'scheduled' ? 
                                `<a href="${appointment.google_meet_link}" class="btn btn-success" target="_blank">
                                    <i class="fas fa-video me-1"></i>Join Google Meet
                                </a>` : ''}
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('appointmentDetailsModal');
        if (existingModal) existingModal.remove();
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('appointmentDetailsModal'));
        modal.show();
    }

    // ============ UTILITY METHODS ============
    
    getOrderStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'info',
            'out_for_delivery': 'primary',
            'delivered': 'success',
            'cancelled': 'danger'
        };
        return colors[status] || 'secondary';
    }

    getAppointmentStatusColor(status) {
        const colors = {
            'scheduled': 'primary',
            'ongoing': 'success',
            'completed': 'success',
            'cancelled': 'danger'
        };
        return colors[status] || 'secondary';
    }

    // ============ EVENT LISTENERS ============
    
    initializeEventListeners() {
        // Login form
        document.addEventListener('submit', async (e) => {
            if (e.target.id === 'loginForm') {
                e.preventDefault();
                const email = document.getElementById('loginEmail').value;
                const password = document.getElementById('loginPassword').value;
                await this.login(email, password);
            }
            
            if (e.target.id === 'registerForm') {
                e.preventDefault();
                const formData = new FormData(e.target);
                
                // Validate password confirmation
                if (formData.get('password') !== formData.get('confirmPassword')) {
                    this.showError('Passwords do not match');
                    return;
                }
                
                const userData = {
                    name: formData.get('name'),
                    email: formData.get('email'),
                    phone: formData.get('phone'),
                    password: formData.get('password')
                };
                
                await this.register(userData);
            }
            
            if (e.target.id === 'consultationForm') {
                e.preventDefault();
                const formData = new FormData(e.target);
                await this.bookAppointment(formData);
            }
        });

        // Search functionality
        document.addEventListener('keypress', (e) => {
            if (e.target.id === 'medicineSearch' && e.key === 'Enter') {
                this.searchMedicines(e.target.value);
            }
        });

        // Date change for time slots
        document.addEventListener('change', (e) => {
            if (e.target.id === 'consultationDate') {
                this.loadTimeSlots();
            }
            if (e.target.id === 'doctorSelect') {
                this.loadTimeSlots();
            }
        });
    }

    // ============ UI HELPER METHODS ============
    
    showLoading() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) spinner.style.display = 'flex';
    }

    hideLoading() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) spinner.style.display = 'none';
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        // Remove existing alerts
        document.querySelectorAll('.app-alert').forEach(alert => alert.remove());
        
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show app-alert" role="alert" style="position: fixed; top: 100px; right: 20px; z-index: 9999; min-width: 300px;">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.querySelector('.app-alert');
            if (alert) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 5000);
    }

    hideAllModals() {
        document.querySelectorAll('.modal.show').forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }

    showLogin() {
        const modal = new bootstrap.Modal(document.getElementById('loginModal'));
        modal.show();
    }

    showRegister() {
        this.hideAllModals();
        const modal = new bootstrap.Modal(document.getElementById('registerModal'));
        modal.show();
    }

    showCart() {
        this.displayCartItems();
        const modal = new bootstrap.Modal(document.getElementById('cartModal'));
        modal.show();
    }
}

// Global functions for HTML onclick handlers
function showLogin() {
    app.showLogin();
}

function showRegister() {
    app.showRegister();
}

function hideAllModals() {
    document.querySelectorAll('.modal.show').forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
}

function showDoctorLogin() {
    hideAllModals();
    new bootstrap.Modal(document.getElementById('doctorLoginModal')).show();
}

function showPasswordSetup() {
    hideAllModals();
    new bootstrap.Modal(document.getElementById('passwordSetupModal')).show();
}

function showAdminLogin() {
    hideAllModals();
    new bootstrap.Modal(document.getElementById('adminLoginModal')).show();
}

function showCart() {
    app.showCart();
}

function logout() {
    app.logout();
}

function showProfile() {
    app.showProfile();
}

function showOrders() {
    app.showOrders();
}

function showAppointments() {
    app.showAppointments();
}

function searchMedicines() {
    const query = document.getElementById('medicineSearch')?.value || '';
    app.searchMedicines(query);
}

function filterByCategory(category) {
    app.filterByCategory(category);
}

function loadMoreMedicines() {
    // Load more medicines with pagination
    app.loadMedicines({ offset: app.medicines.length });
}

function placeOrder() {
    app.placeOrder();
}

function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// Initialize app
const app = new RedDotPharmacy();

// Initialize forms
function initializeForms() {
    // Set minimum date for appointment booking
    const dateInput = document.getElementById('consultationDate');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
    }
}

// Check authentication on page load
function checkAuthStatus() {
    app.checkAuthStatus();
}

// Load initial data
function loadMedicines() {
    app.loadMedicines();
}

function loadDoctors() {
    app.loadDoctors();
}

function loadTimeSlots() {
    app.loadTimeSlots();
}

// Doctor authentication functions
async function handleDoctorLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('doctorLoginEmail').value;
    const password = document.getElementById('doctorLoginPassword').value;
    
    if (!email || !password) {
        alert('Please enter both email and password');
        return;
    }
    
    try {
        const response = await fetch('/doctor/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('doctor_token', data.token);
            localStorage.setItem('doctor_data', JSON.stringify(data.doctor));
            hideAllModals();
            alert('Login successful! Redirecting to doctor dashboard...');
            window.location.href = '/doctor/dashboard';
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Doctor login error:', error);
        alert('Login failed. Please try again.');
    }
}

async function handlePasswordSetup(event) {
    event.preventDefault();
    
    const email = document.getElementById('setupEmail').value;
    const password = document.getElementById('setupPassword').value;
    const confirmPassword = document.getElementById('setupConfirmPassword').value;
    
    if (!email || !password || !confirmPassword) {
        alert('Please fill in all fields');
        return;
    }
    
    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }
    
    if (password.length < 6) {
        alert('Password must be at least 6 characters long');
        return;
    }
    
    try {
        const response = await fetch('/doctor/api/setup-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                email, 
                password, 
                confirm_password: confirmPassword 
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('doctor_token', data.token);
            localStorage.setItem('doctor_data', JSON.stringify(data.doctor));
            hideAllModals();
            alert('Password set successfully! Redirecting to doctor dashboard...');
            window.location.href = '/doctor/dashboard';
        } else {
            alert(data.error || 'Failed to set password');
        }
    } catch (error) {
        console.error('Password setup error:', error);
        alert('Failed to set password. Please try again.');
    }
}

// Initialize all components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize forms
    initializeForms();
    
    // Check authentication status
    checkAuthStatus();
    
    // Load initial data if we're on specific pages
    if (document.getElementById('medicineGrid')) {
        loadMedicines();
    }
    
    if (document.getElementById('doctorGrid')) {
        loadDoctors();
    }
    
    // Initialize chatbot
    // Initialize chatbot if we're on the assistant page
    if (window.location.pathname === '/assistant') {
        // Chat initialization is handled by voice.js and assistant page scripts
        console.log('Chat initialized with language:', window.currentLanguage || 'en');
    }
    
    // Initialize voice assistant
    if (typeof initializeVoiceAssistant === 'function') {
        initializeVoiceAssistant();
    }
    
    // Initialize doctor forms
    const doctorLoginForm = document.getElementById('doctorLoginForm');
    if (doctorLoginForm) {
        doctorLoginForm.addEventListener('submit', handleDoctorLogin);
    }
    
    const passwordSetupForm = document.getElementById('passwordSetupForm');
    if (passwordSetupForm) {
        passwordSetupForm.addEventListener('submit', handlePasswordSetup);
    }
    
    // Initialize admin forms
    const adminLoginForm = document.getElementById('adminLoginForm');
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', handleAdminLogin);
    }
});

// Admin authentication functions
async function handleAdminLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('adminLoginEmail').value;
    const password = document.getElementById('adminLoginPassword').value;
    
    if (!email || !password) {
        alert('Please enter both email and password');
        return;
    }
    
    try {
        const response = await fetch('/admin/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('admin_token', data.token);
            localStorage.setItem('admin_data', JSON.stringify(data.admin));
            hideAllModals();
            alert('Admin login successful! Redirecting to admin dashboard...');
            window.location.href = '/admin';
        } else {
            alert(data.error || 'Admin login failed');
        }
    } catch (error) {
        console.error('Admin login error:', error);
        alert('Admin login failed. Please try again.');
    }
}
