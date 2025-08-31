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
        
        this.initializeEventListeners();
        this.updateCartDisplay();
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
                    setTimeout(() => {
                        window.location.href = '/admin';
                    }, 1500);
                } else {
                    this.showSuccess('Login successful! Welcome back, ' + data.user.name);
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
                        <img src="${medicine.image_url || 'https://pixabay.com/get/g7f4583c94af9a1854eb8b3aa95302ecc29bfb74ed9e4a49eda99a8d292810723fe0fa0624331e0b8a0976b75b535ad2cea69e85568e6e30d421d9e3ac8f3dfd1_1280.png'}" 
                             class="card-img-top medicine-image" 
                             alt="${medicine.name}"
                             onerror="this.src='https://pixabay.com/get/g7f4583c94af9a1854eb8b3aa95302ecc29bfb74ed9e4a49eda99a8d292810723fe0fa0624331e0b8a0976b75b535ad2cea69e85568e6e30d421d9e3ac8f3dfd1_1280.png'">
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
                                    <img src="${medicine.image_url || 'https://pixabay.com/get/g7f4583c94af9a1854eb8b3aa95302ecc29bfb74ed9e4a49eda99a8d292810723fe0fa0624331e0b8a0976b75b535ad2cea69e85568e6e30d421d9e3ac8f3dfd1_1280.png'}" 
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
                image_url: medicine.image_url
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
        const modalHtml = `
            <div class="modal fade" id="quickCheckoutModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-bolt text-success me-2"></i>Quick Checkout
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Order Summary -->
                            <div class="mb-4">
                                <h6>Order Summary</h6>
                                <div class="card">
                                    <div class="card-body">
                                        <div class="row align-items-center">
                                            <div class="col-3">
                                                <img src="${medicine.image_url || 'https://pixabay.com/get/g7f4583c94af9a1854eb8b3aa95302ecc29bfb74ed9e4a49eda99a8d292810723fe0fa0624331e0b8a0976b75b535ad2cea69e85568e6e30d421d9e3ac8f3dfd1_1280.png'}" 
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
                                    <label class="form-label">Delivery Address *</label>
                                    <textarea class="form-control" id="quickDeliveryAddress" rows="3" 
                                              placeholder="Enter your complete delivery address..." required></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Contact Number *</label>
                                    <input type="tel" class="form-control" id="quickDeliveryPhone" 
                                           placeholder="Enter your contact number" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Payment Method</label>
                                    <select class="form-select" id="quickPaymentMethod">
                                        <option value="cash_on_delivery">Cash on Delivery</option>
                                    </select>
                                </div>
                            </form>
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
    }

    async processQuickOrder(medicineId) {
        const medicine = this.medicines.find(m => m.id === medicineId);
        if (!medicine) {
            this.showError('Medicine not found');
            return;
        }

        const address = document.getElementById('quickDeliveryAddress')?.value?.trim();
        const phone = document.getElementById('quickDeliveryPhone')?.value?.trim();
        const paymentMethod = document.getElementById('quickPaymentMethod')?.value || 'cash_on_delivery';

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
                payment_method: paymentMethod,
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
                
                this.showSuccess(`Order placed successfully! Order ID: #${data.order.id}. Expected delivery: ${data.order.estimated_delivery}`);
                
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
                        <img src="${item.image_url || 'https://pixabay.com/get/g7f4583c94af9a1854eb8b3aa95302ecc29bfb74ed9e4a49eda99a8d292810723fe0fa0624331e0b8a0976b75b535ad2cea69e85568e6e30d421d9e3ac8f3dfd1_1280.png'}" 
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
                        <div class="doctor-avatar">
                            <i class="fas fa-user-md"></i>
                        </div>
                        <h6 class="card-title">${doctor.name}</h6>
                        <p class="text-muted mb-2">${doctor.email}</p>
                        ${doctor.phone ? `<p class="text-muted mb-2"><i class="fas fa-phone me-1"></i>${doctor.phone}</p>` : ''}
                        <p class="text-muted small">
                            <i class="fas fa-calendar me-1"></i>
                            ${doctor.upcoming_appointments} upcoming appointments
                        </p>
                        <button class="btn btn-danger btn-sm w-100" onclick="app.selectDoctor(${doctor.id})">
                            <i class="fas fa-calendar-plus me-1"></i>Book Appointment
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    populateDoctorSelect(doctors) {
        const select = document.getElementById('doctorSelect');
        if (!select) return;

        select.innerHTML = '<option value="">Choose a doctor...</option>' +
            doctors.map(doctor => `<option value="${doctor.id}">${doctor.name}</option>`).join('');
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
                 onclick="${slot.available ? `app.selectTimeSlot('${slot.start_time}', '${slot.display_time}')` : ''}"
                 data-time="${slot.start_time}">
                ${slot.display_time}
            </div>
        `).join('');
    }

    selectTimeSlot(startTime, displayTime) {
        // Remove previous selection
        document.querySelectorAll('.time-slot').forEach(slot => {
            slot.classList.remove('selected');
        });
        
        // Add selection to clicked slot
        event.target.classList.add('selected');
        this.selectedTimeSlot = startTime;
    }

    async bookAppointment(formData) {
        if (!this.authToken) {
            this.showError('Please login to book an appointment');
            this.showLogin();
            return;
        }

        if (!this.selectedTimeSlot) {
            this.showError('Please select a time slot');
            return;
        }

        try {
            this.showLoading();

            const appointmentData = {
                doctor_id: parseInt(formData.get('doctor_id')),
                start_time: this.selectedTimeSlot,
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
                this.selectedTimeSlot = null;
                document.querySelectorAll('.time-slot').forEach(slot => {
                    slot.classList.remove('selected');
                });
                
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

    displayOrdersModal(orders) {
        const ordersHtml = orders.length === 0 ? 
            '<p class="text-muted text-center py-4">No orders found</p>' :
            orders.map(order => `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h6>Order #${order.id}</h6>
                                <p class="text-muted mb-1">${order.item_count} items • PKR ${order.total_amount}</p>
                                <p class="text-muted mb-1">${new Date(order.created_at).toLocaleString()}</p>
                                <span class="badge bg-${this.getOrderStatusColor(order.status)}">${order.status.replace('_', ' ').toUpperCase()}</span>
                            </div>
                            <div class="col-md-4 text-end">
                                <button class="btn btn-outline-danger btn-sm" onclick="app.viewOrderDetails(${order.id})">
                                    View Details
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

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

    // ============ UTILITY METHODS ============
    
    getOrderStatusColor(status) {
        const colors = {
            'pending': 'warning',
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
    if (typeof initializeChatbot === 'function') {
        initializeChatbot();
    }
    
    // Initialize voice assistant
    if (typeof initializeVoiceAssistant === 'function') {
        initializeVoiceAssistant();
    }
});
