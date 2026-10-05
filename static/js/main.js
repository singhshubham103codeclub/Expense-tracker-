// main.js — Spendly Client Interactions

document.addEventListener('DOMContentLoaded', () => {
    initModals();
});

function initModals() {
    let activeModal = null;
    let lastActiveTrigger = null;

    function openModal(modalId, triggerElement) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        // If opening video modal, mount player or empty state
        if (modalId === 'videoModal') {
            setupVideoPlayer(modal);
        }

        // If another modal is currently active, close it immediately
        if (activeModal && activeModal !== modal) {
            closeModal(activeModal, false);
        }

        lastActiveTrigger = triggerElement || document.activeElement;
        activeModal = modal;

        modal.removeAttribute('hidden');
        document.body.classList.add('modal-open');

        // Force browser reflow to trigger smooth CSS transition
        void modal.offsetWidth;
        modal.classList.add('is-open');

        // Accessible focus management: focus modal close button or container
        const closeBtn = modal.querySelector('.modal-close-btn');
        if (closeBtn) {
            closeBtn.focus();
        }
    }

    function closeModal(modalToClose, shouldAnimate = true) {
        const modal = modalToClose || activeModal;
        if (!modal) return;

        // If closing video modal, completely tear down iframe so playback stops immediately
        if (modal.id === 'videoModal') {
            teardownVideoPlayer(modal);
        }

        modal.classList.remove('is-open');
        document.body.classList.remove('modal-open');

        const finishClosing = () => {
            modal.setAttribute('hidden', '');
            if (activeModal === modal) {
                activeModal = null;
            }
            if (lastActiveTrigger && typeof lastActiveTrigger.focus === 'function') {
                lastActiveTrigger.focus();
                lastActiveTrigger = null;
            }
        };

        if (shouldAnimate) {
            setTimeout(finishClosing, 250);
        } else {
            finishClosing();
        }
    }

    function formatYouTubeEmbedUrl(url) {
        if (!url) return '';
        const trimmed = url.trim();
        if (!trimmed) return '';

        // If already an embed URL, append autoplay if not present
        if (trimmed.includes('youtube.com/embed/')) {
            const separator = trimmed.includes('?') ? '&' : '?';
            return trimmed.includes('autoplay=') ? trimmed : `${trimmed}${separator}autoplay=1`;
        }

        // Extract YouTube ID from standard watch URL or youtu.be short URL
        const regExp = /(?:youtube\.com\/(?:watch\?.*v=|embed\/|v\/)|youtu\.be\/)([\w-]{11})/;
        const match = trimmed.match(regExp);

        if (match && match[1]) {
            const videoId = match[1];
            return `https://www.youtube.com/embed/${videoId}?autoplay=1`;
        }

        // Return trimmed URL if it's already a direct source URL
        return trimmed;
    }

    function setupVideoPlayer(modal) {
        const container = modal.querySelector('#videoPlayerContainer');
        if (!container) return;

        const rawUrl = modal.dataset.videoUrl || '';
        const embedUrl = formatYouTubeEmbedUrl(rawUrl);

        if (embedUrl) {
            container.innerHTML = `<iframe class="video-iframe" src="${embedUrl}" title="Spendly Demo Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`;
        } else {
            container.innerHTML = `
                <div class="video-empty-state">
                    <div class="video-empty-icon">▶</div>
                    <h3>Demo Video Coming Soon</h3>
                    <p>A video walkthrough of Spendly will be available here soon.</p>
                </div>
            `;
        }
    }

    function teardownVideoPlayer(modal) {
        const container = modal.querySelector('#videoPlayerContainer');
        if (container) {
            container.innerHTML = '';
        }
    }

    // Modal Trigger Buttons in Hero
    const videoBtn = document.getElementById('openVideoBtn');
    if (videoBtn) {
        videoBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openModal('videoModal', videoBtn);
        });
    }

    // Modal Trigger Buttons in Footer
    const termsBtn = document.getElementById('openTermsBtn');
    if (termsBtn) {
        termsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openModal('termsModal', termsBtn);
        });
    }

    const privacyBtn = document.getElementById('openPrivacyBtn');
    if (privacyBtn) {
        privacyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openModal('privacyModal', privacyBtn);
        });
    }

    // Close actions via click (close buttons or clicking outside on backdrop)
    document.addEventListener('click', (e) => {
        const closeTrigger = e.target.closest('[data-close-modal]');
        if (closeTrigger) {
            e.preventDefault();
            const modal = closeTrigger.closest('.modal-overlay');
            closeModal(modal);
            return;
        }

        if (e.target.classList && e.target.classList.contains('modal-overlay')) {
            closeModal(e.target);
        }
    });

    // Keyboard accessibility: Escape to close & Tab focus trap
    document.addEventListener('keydown', (e) => {
        if (!activeModal) return;

        if (e.key === 'Escape' || e.key === 'Esc') {
            e.preventDefault();
            closeModal(activeModal);
            return;
        }

        if (e.key === 'Tab') {
            const focusable = activeModal.querySelectorAll(
                'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
            );
            if (focusable.length === 0) return;

            const firstEl = focusable[0];
            const lastEl = focusable[focusable.length - 1];

            if (e.shiftKey) {
                if (document.activeElement === firstEl) {
                    e.preventDefault();
                    lastEl.focus();
                }
            } else {
                if (document.activeElement === lastEl) {
                    e.preventDefault();
                    firstEl.focus();
                }
            }
        }
    });
}
