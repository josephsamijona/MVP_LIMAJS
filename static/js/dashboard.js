// static/js/dashboard.js

// Gestion du DOM
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des composants
    initializeSidebar();
    initializeTooltips();
    initializeScrollAnimations();
    setupAccessibility();
 });
 
 // ========== SIDEBAR MANAGEMENT ==========
 function initializeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    const submenus = document.querySelectorAll('.submenu-trigger');
 
    // Toggle du sidebar
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            
            // Mise à jour des attributs ARIA
            const isExpanded = sidebar.classList.contains('collapsed');
            toggleBtn.setAttribute('aria-expanded', !isExpanded);
            
            // Animation fluide
            if (isExpanded) {
                sidebar.style.transform = 'translateX(-100%)';
            } else {
                sidebar.style.transform = 'translateX(0)';
            }
        });
 
        // Gestion du clic en dehors du sidebar pour le fermer
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.add('collapsed');
                toggleBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }
 
    // Gestion des sous-menus
    submenus.forEach(submenu => {
        submenu.addEventListener('click', (e) => {
            e.preventDefault();
            const parent = submenu.parentElement;
            const submenuContent = parent.querySelector('.submenu-content');
            
            // Toggle avec animation
            if (submenuContent) {
                const isExpanded = submenuContent.classList.contains('expanded');
                
                submenuContent.style.height = isExpanded ? '0' : `${submenuContent.scrollHeight}px`;
                submenuContent.classList.toggle('expanded');
                
                // Mise à jour ARIA
                submenu.setAttribute('aria-expanded', !isExpanded);
            }
        });
    });
 }
 
 // ========== TOOLTIPS ==========
 function initializeTooltips() {
    const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
    
    tooltipTriggers.forEach(trigger => {
        const tooltipText = trigger.getAttribute('data-tooltip');
        let tooltip = null;
        
        // Création du tooltip
        trigger.addEventListener('mouseenter', (e) => {
            tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            document.body.appendChild(tooltip);
            
            // Positionnement
            const rect = trigger.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
            tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
            
            // Animation d'apparition
            requestAnimationFrame(() => {
                tooltip.style.opacity = '1';
                tooltip.style.transform = 'translateY(0)';
            });
        });
        
        // Suppression du tooltip
        trigger.addEventListener('mouseleave', () => {
            if (tooltip) {
                tooltip.remove();
                tooltip = null;
            }
        });
    });
 }
 
 // ========== SCROLL ANIMATIONS ==========
 function initializeScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '50px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
 }
 
 // ========== ACCESSIBILITY ==========
 function setupAccessibility() {
    // Gestion de la navigation au clavier
    const focusableElements = document.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    
    focusableElements.forEach(element => {
        element.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                element.click();
            }
        });
    });
 
    // Trap focus dans le sidebar quand il est ouvert
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        const firstFocusable = sidebar.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        const lastFocusable = Array.from(sidebar.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')).pop();
        
        if (firstFocusable && lastFocusable) {
            lastFocusable.addEventListener('keydown', (e) => {
                if (e.key === 'Tab' && !e.shiftKey) {
                    e.preventDefault();
                    firstFocusable.focus();
                }
            });
 
            firstFocusable.addEventListener('keydown', (e) => {
                if (e.key === 'Tab' && e.shiftKey) {
                    e.preventDefault();
                    lastFocusable.focus();
                }
            });
        }
    }
 }
 
 // ========== UTILITAIRES ==========
 // Fonction de debounce pour optimiser les performances
 function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
 }
 
 // Fonction pour vérifier les préférences de réduction de mouvement
 function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 }
 
 // ========== ÉCOUTEURS D'ÉVÉNEMENTS GLOBAUX ==========
 // Gestion du redimensionnement
 window.addEventListener('resize', debounce(() => {
    // Réajuster les éléments si nécessaire
    const sidebar = document.querySelector('.sidebar');
    if (window.innerWidth > 768) {
        sidebar?.classList.remove('collapsed');
    }
 }, 250));
 
 // Gestion des préférences de réduction de mouvement
 window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', () => {
    // Adapter les animations en fonction des préférences
    if (prefersReducedMotion()) {
        document.body.classList.add('reduce-motion');
    } else {
        document.body.classList.remove('reduce-motion');
    }
 });