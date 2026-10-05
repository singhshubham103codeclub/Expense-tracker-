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
