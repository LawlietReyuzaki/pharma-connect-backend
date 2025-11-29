/**
 * Wikipedia Sources Display Component
 * Renders Wikipedia images with proper attribution under chatbot responses
 */

function renderWikiResults(wikiData, containerElement) {
    if (!wikiData || !wikiData.title) {
        return;
    }

    clearPreviousWikiResults(containerElement);

    const wikiSection = document.createElement('div');
    wikiSection.className = 'wiki-sources-section';
    wikiSection.innerHTML = `
        <div class="wiki-sources-header">
            <i class="fab fa-wikipedia-w"></i>
            <span>Wikipedia Sources</span>
            <a href="${escapeHtml(wikiData.page_url)}" target="_blank" rel="noopener noreferrer" class="wiki-link">
                View Article <i class="fas fa-external-link-alt"></i>
            </a>
        </div>
        <div class="wiki-title">${escapeHtml(wikiData.title)}</div>
        ${wikiData.summary ? `<div class="wiki-summary">${escapeHtml(wikiData.summary)}</div>` : ''}
        <div class="wiki-images-grid"></div>
    `;

    const imagesGrid = wikiSection.querySelector('.wiki-images-grid');
    
    if (wikiData.images && wikiData.images.length > 0) {
        wikiData.images.forEach(image => {
            const card = createImageCard(image);
            imagesGrid.appendChild(card);
        });
    }

    containerElement.appendChild(wikiSection);
    
    wikiSection.style.opacity = '0';
    wikiSection.style.transform = 'translateY(10px)';
    requestAnimationFrame(() => {
        wikiSection.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        wikiSection.style.opacity = '1';
        wikiSection.style.transform = 'translateY(0)';
    });
}

function createImageCard(imageData) {
    const card = document.createElement('div');
    card.className = 'wiki-image-card';
    
    const imageUrl = imageData.thumb_url || imageData.url;
    const artist = imageData.artist || 'Unknown';
    const license = imageData.license || 'Unknown License';
    const licenseUrl = imageData.license_url || '#';
    const credit = imageData.credit || 'Wikimedia Commons';
    
    card.innerHTML = `
        <div class="wiki-image-container">
            <img src="${escapeHtml(imageUrl)}" alt="Wikipedia image" loading="lazy" 
                 onerror="this.parentElement.innerHTML='<div class=\\'wiki-image-placeholder\\'><i class=\\'fas fa-image\\'></i></div>'"
                 onclick="openImageModal('${escapeHtml(imageData.url)}')">
        </div>
        <div class="wiki-image-info">
            <div class="wiki-artist" title="${escapeHtml(artist)}">
                <i class="fas fa-user"></i>
                <span>${escapeHtml(truncateText(artist, 30))}</span>
            </div>
            <div class="wiki-license">
                <i class="fas fa-balance-scale"></i>
                <a href="${escapeHtml(licenseUrl)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(license)}">
                    ${escapeHtml(truncateText(license, 20))}
                </a>
            </div>
            <div class="wiki-credit">
                <i class="fab fa-wikipedia-w"></i>
                <span>${escapeHtml(credit)}</span>
            </div>
        </div>
    `;
    
    return card;
}

function clearPreviousWikiResults(containerElement) {
    const existingWiki = containerElement.querySelector('.wiki-sources-section');
    if (existingWiki) {
        existingWiki.remove();
    }
}

function openImageModal(imageUrl) {
    const existingModal = document.getElementById('wikiImageModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = 'wikiImageModal';
    modal.className = 'wiki-image-modal';
    modal.innerHTML = `
        <div class="wiki-modal-overlay" onclick="closeImageModal()"></div>
        <div class="wiki-modal-content">
            <button class="wiki-modal-close" onclick="closeImageModal()">
                <i class="fas fa-times"></i>
            </button>
            <img src="${escapeHtml(imageUrl)}" alt="Full size image" loading="lazy">
        </div>
    `;
    
    document.body.appendChild(modal);
    
    requestAnimationFrame(() => {
        modal.classList.add('active');
    });
    
    document.addEventListener('keydown', handleModalEscape);
}

function closeImageModal() {
    const modal = document.getElementById('wikiImageModal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
    document.removeEventListener('keydown', handleModalEscape);
}

function handleModalEscape(e) {
    if (e.key === 'Escape') {
        closeImageModal();
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
}

function addWikiStyles() {
    if (document.getElementById('wikiDisplayStyles')) return;
    
    const style = document.createElement('style');
    style.id = 'wikiDisplayStyles';
    style.textContent = `
        .wiki-sources-section {
            margin-top: 20px;
            padding: 16px;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            border-left: 4px solid #1e3a5f;
        }
        
        .wiki-sources-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
            font-weight: 600;
            color: #1e3a5f;
            font-size: 15px;
        }
        
        .wiki-sources-header .fab {
            font-size: 18px;
        }
        
        .wiki-link {
            margin-left: auto;
            font-size: 13px;
            color: #2563eb;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 4px;
            font-weight: 500;
        }
        
        .wiki-link:hover {
            text-decoration: underline;
        }
        
        .wiki-title {
            font-size: 16px;
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 8px;
        }
        
        .wiki-summary {
            font-size: 14px;
            color: #475569;
            line-height: 1.6;
            margin-bottom: 16px;
        }
        
        .wiki-images-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 12px;
        }
        
        .wiki-image-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .wiki-image-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .wiki-image-container {
            position: relative;
            padding-top: 75%;
            overflow: hidden;
            background: #f1f5f9;
        }
        
        .wiki-image-container img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        
        .wiki-image-container img:hover {
            transform: scale(1.05);
        }
        
        .wiki-image-placeholder {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #94a3b8;
            font-size: 24px;
        }
        
        .wiki-image-info {
            padding: 10px;
            font-size: 11px;
        }
        
        .wiki-artist,
        .wiki-license,
        .wiki-credit {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
            color: #64748b;
        }
        
        .wiki-artist i,
        .wiki-license i,
        .wiki-credit i {
            width: 12px;
            font-size: 10px;
            color: #94a3b8;
        }
        
        .wiki-license a {
            color: #2563eb;
            text-decoration: none;
        }
        
        .wiki-license a:hover {
            text-decoration: underline;
        }
        
        .wiki-image-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        
        .wiki-image-modal.active {
            opacity: 1;
            pointer-events: all;
        }
        
        .wiki-modal-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
        }
        
        .wiki-modal-content {
            position: relative;
            max-width: 90vw;
            max-height: 90vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .wiki-modal-content img {
            max-width: 100%;
            max-height: 90vh;
            object-fit: contain;
            border-radius: 8px;
        }
        
        .wiki-modal-close {
            position: absolute;
            top: -40px;
            right: 0;
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s ease;
        }
        
        .wiki-modal-close:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        @media (max-width: 768px) {
            .wiki-images-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }
            
            .wiki-sources-section {
                padding: 12px;
            }
            
            .wiki-sources-header {
                flex-wrap: wrap;
            }
            
            .wiki-link {
                width: 100%;
                margin-left: 0;
                margin-top: 8px;
            }
        }
    `;
    
    document.head.appendChild(style);
}

document.addEventListener('DOMContentLoaded', addWikiStyles);

if (typeof window !== 'undefined') {
    window.renderWikiResults = renderWikiResults;
    window.clearPreviousWikiResults = clearPreviousWikiResults;
    window.openImageModal = openImageModal;
    window.closeImageModal = closeImageModal;
}
