/**
 * Platform Homepage — Pharmacy Discovery & Search
 */

let currentOffset = 0;
const PAGE_SIZE = 12;
let currentSearch = '';
let currentCity = '';

// ─── Location ───────────────────────────────────────────────────────────────

function requestLocation() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
    }
    navigator.geolocation.getCurrentPosition(
        position => {
            const { latitude, longitude } = position.coords;
            loadNearbyPharmacies(latitude, longitude);
        },
        () => {
            alert('Location access denied. You can search by city instead.');
        }
    );
}

async function loadNearbyPharmacies(lat, lng) {
    try {
        const res = await fetch(`/pharmacy/api/nearby?lat=${lat}&lng=${lng}&limit=6`);
        const data = await res.json();

        if (data.success && data.pharmacies.length > 0) {
            const grid = document.getElementById('nearbyGrid');
            grid.innerHTML = '';
            data.pharmacies.forEach(p => {
                grid.innerHTML += createPharmacyCard(p, true);
            });
            document.getElementById('nearbySection').style.display = 'block';
        }
    } catch (err) {
        console.error('Nearby pharmacies error:', err);
    }
}

// ─── Search & Filter ────────────────────────────────────────────────────────

function searchPharmacies() {
    currentSearch = document.getElementById('searchInput').value.trim();
    currentOffset = 0;
    loadPharmacies();
}

function filterByCity(city) {
    currentCity = city;
    currentOffset = 0;
    // Update active button
    document.querySelectorAll('.filter-pills .btn').forEach(b => b.classList.remove('active'));
    event.currentTarget.classList.add('active');
    loadPharmacies();
}

async function loadPharmacies() {
    try {
        let url = `/pharmacy/api/list?limit=${PAGE_SIZE}&offset=${currentOffset}`;
        if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;
        if (currentCity) url += `&city=${encodeURIComponent(currentCity)}`;

        const res = await fetch(url);
        const data = await res.json();
        const grid = document.getElementById('pharmacyGrid');
        const noResults = document.getElementById('noResults');
        const loadMoreBtn = document.getElementById('loadMoreBtn');

        if (currentOffset === 0) grid.innerHTML = '';

        if (data.pharmacies && data.pharmacies.length > 0) {
            noResults.style.display = 'none';
            data.pharmacies.forEach(p => {
                grid.innerHTML += createPharmacyCard(p);
            });
            loadMoreBtn.style.display = data.pharmacies.length >= PAGE_SIZE ? 'inline-block' : 'none';
        } else {
            if (currentOffset === 0) {
                noResults.style.display = 'block';
            }
            loadMoreBtn.style.display = 'none';
        }
    } catch (err) {
        console.error('Load pharmacies error:', err);
    }
}

function loadMore() {
    currentOffset += PAGE_SIZE;
    loadPharmacies();
}

// ─── Card Renderer ──────────────────────────────────────────────────────────

function createPharmacyCard(pharmacy, showDistance = false) {
    const photo = pharmacy.pharmacy_photo_path || 'https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=400&q=60';
    const stars = renderStars(pharmacy.avg_rating || 0);
    const distance = showDistance && pharmacy.distance_km !== undefined
        ? `<span class="badge bg-primary">${pharmacy.distance_km} km away</span>`
        : '';

    return `
        <div class="col-lg-3 col-md-4 col-sm-6">
            <div class="pharmacy-card">
                <img src="${photo}" alt="${pharmacy.name}"
                     onerror="this.src='https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=400&q=60'">
                <div class="card-body">
                    <h6 class="fw-bold mb-1">${pharmacy.name}</h6>
                    <p class="text-muted small mb-2">
                        <i class="fas fa-map-marker-alt me-1"></i>${pharmacy.city || 'Pakistan'}
                    </p>
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <span class="badge-rating badge">
                            ${stars} ${(pharmacy.avg_rating || 0).toFixed(1)}
                        </span>
                        <small class="text-muted">(${pharmacy.review_count || 0})</small>
                        ${distance}
                    </div>
                    <div class="d-flex align-items-center justify-content-between">
                        <small class="text-muted">
                            <i class="fas fa-user-md me-1"></i>${pharmacy.doctor_count || 0} doctors
                        </small>
                        <a href="/pharmacy/${pharmacy.slug}" class="btn btn-sm btn-outline-primary">
                            Visit <i class="fas fa-arrow-right ms-1"></i>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderStars(rating) {
    let html = '';
    for (let i = 1; i <= 5; i++) {
        html += `<i class="fas fa-star" style="color:${i <= Math.round(rating) ? '#f59e0b' : '#d1d5db'};font-size:0.75rem;"></i>`;
    }
    return html;
}

// ─── Load Cities ────────────────────────────────────────────────────────────

async function loadCities() {
    try {
        const res = await fetch('/pharmacy/api/cities');
        const data = await res.json();
        const container = document.getElementById('cityFilters');
        if (data.cities && data.cities.length > 0) {
            data.cities.forEach(c => {
                const btn = document.createElement('button');
                btn.className = 'btn btn-outline-secondary';
                btn.textContent = `${c.name} (${c.count})`;
                btn.onclick = function () { filterByCity(c.name); };
                container.appendChild(btn);
            });
        }
    } catch (err) {
        console.error('Load cities error:', err);
    }
}

// ─── Search on Enter ────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadPharmacies();
    loadCities();

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchPharmacies();
        });
    }
});
