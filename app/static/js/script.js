document.addEventListener('DOMContentLoaded', function() {
    const body = document.body;
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const menuToggle = document.getElementById('menuToggle'); // Hamburger in top navbar
    const themeToggleSwitch = document.getElementById('theme-toggle-switch');
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));


    // --- Theme Handling (Keep as is from your last working version) ---
    const defaultTheme = 'dark';
    function applyTheme(theme) { /* ... same as your last working version ... */
        if (!theme || (theme !== 'light' && theme !== 'dark')) theme = defaultTheme;
        document.documentElement.setAttribute('data-bs-theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
        if (themeToggleSwitch) themeToggleSwitch.checked = theme === 'dark';
        const themeButtons = document.querySelectorAll('.theme-option-button');
        themeButtons.forEach(button => {
            const isActive = button.getAttribute('value') === theme;
            button.classList.toggle('active', isActive);
            button.classList.toggle('btn-primary', isActive);
            button.classList.toggle('btn-outline-secondary', !isActive);
        });
    }
    let serverSetTheme = document.documentElement.getAttribute('data-bs-theme');
    let themeToApplyOnInit;
    if (serverSetTheme && (serverSetTheme === 'light' || serverSetTheme === 'dark')) {
        themeToApplyOnInit = serverSetTheme;
        if (localStorage.getItem('theme') !== serverSetTheme) localStorage.setItem('theme', serverSetTheme);
    } else {
        themeToApplyOnInit = localStorage.getItem('theme') || defaultTheme;
    }
    applyTheme(themeToApplyOnInit);
    if (themeToggleSwitch) {
        themeToggleSwitch.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }


    // --- Sidebar Logic for Advanced Behavior ---
    if (sidebar && mainContent) {
        const isMobile = () => window.innerWidth < 992;

        function applyDesktopClasses(desktopState) {
            sidebar.classList.remove('desktop-full-open', 'desktop-icon-only');
            mainContent.classList.remove('sidebar-desktop-full-open', 'sidebar-desktop-icon-only');
            if (desktopState === 'full') {
                sidebar.classList.add('desktop-full-open');
                mainContent.classList.add('sidebar-desktop-full-open');
            } else { // 'icons'
                sidebar.classList.add('desktop-icon-only');
                mainContent.classList.add('sidebar-desktop-icon-only');
            }
        }

        function applyMobileClasses(isOpen) {
            sidebar.classList.remove('desktop-full-open', 'desktop-icon-only', 'hover-expanded');
            mainContent.classList.remove('sidebar-desktop-full-open', 'sidebar-desktop-icon-only');
            if (isOpen) {
                sidebar.classList.add('mobile-overlay-open');
                sidebar.classList.remove('mobile-collapsed');
                mainContent.classList.remove('sidebar-mobile-hidden'); // Assuming overlay doesn't push content
            } else {
                sidebar.classList.remove('mobile-overlay-open');
                sidebar.classList.add('mobile-collapsed');
                mainContent.classList.add('sidebar-mobile-hidden'); // Or ensure it's full width
            }
        }

        function initializeSidebar() {
            if (isMobile()) {
                applyMobileClasses(false); // Start closed on mobile
            } else {
                // Default to icon-only on desktop if no preference, or read preference
                let desktopState = localStorage.getItem('desktopSidebarState') || 'icons';
                applyDesktopClasses(desktopState);
            }
            // Remove initializing class to make sidebar visible AFTER correct state classes are applied
            sidebar.classList.remove('sidebar-initializing');
        }

        // Call initializeSidebar only if sidebar is part of the page (e.g. user is authenticated)
        if (document.body.contains(sidebar)) { // Check if sidebar element is in the DOM
            initializeSidebar();
        }


        if (menuToggle) {
            menuToggle.addEventListener('click', function(event) {
                event.stopPropagation();
                if (isMobile()) {
                    const isOpen = sidebar.classList.contains('mobile-overlay-open');
                    applyMobileClasses(!isOpen);
                } else {
                    let currentDesktopState = sidebar.classList.contains('desktop-icon-only') ? 'icons' : 'full';
                    let newDesktopState = (currentDesktopState === 'full') ? 'icons' : 'full';
                    localStorage.setItem('desktopSidebarState', newDesktopState);
                    applyDesktopClasses(newDesktopState);
                }
            });
        }

        sidebar.addEventListener('mouseenter', function() {
            if (!isMobile() && sidebar.classList.contains('desktop-icon-only')) {
                sidebar.classList.add('hover-expanded');
            }
        });
        sidebar.addEventListener('mouseleave', function() {
            if (!isMobile() && sidebar.classList.contains('desktop-icon-only')) {
                sidebar.classList.remove('hover-expanded');
            }
            // Collapse open submenus when mouse leaves sidebar (from previous confirmed update)
            const openSubmenus = sidebar.querySelectorAll('.sidebar-nav .submenu.open');
            openSubmenus.forEach(function(submenu) {
                submenu.classList.remove('open');
                const parentLink = submenu.parentElement.querySelector('a');
                if (parentLink) {
                    const arrowIcon = parentLink.querySelector('.arrow .fas');
                    if (arrowIcon && arrowIcon.classList.contains('fa-chevron-down')) {
                        arrowIcon.classList.remove('fa-chevron-down');
                        arrowIcon.classList.add('fa-chevron-right');
                    }
                }
            });
        });

        document.addEventListener('click', function(event) {
            if (isMobile() && sidebar.classList.contains('mobile-overlay-open')) {
                if (!sidebar.contains(event.target) && (menuToggle && !menuToggle.contains(event.target))) {
                    applyMobileClasses(false);
                }
            }
        });

        window.addEventListener('resize', function() {
            if (document.body.contains(sidebar)) { // Check if sidebar exists before re-initializing
                initializeSidebar();
            }
        });

    }

    // --- Sidebar Submenu Toggle Functionality ---
    const submenuToggles = document.querySelectorAll('.sidebar-nav .has-submenu > a');
    submenuToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function(event) {
            const parentLi = this.parentElement;
            if (parentLi.classList.contains('has-submenu')) {
                event.preventDefault();
                const submenu = parentLi.querySelector('.submenu');
                const arrowIcon = this.querySelector('.arrow .fas');
                if (submenu) {
                    const isCurrentlyOpen = submenu.classList.contains('open');
                    submenu.classList.toggle('open', !isCurrentlyOpen);
                    if (arrowIcon) {
                        arrowIcon.classList.toggle('fa-chevron-down', !isCurrentlyOpen);
                        arrowIcon.classList.toggle('fa-chevron-right', isCurrentlyOpen);
                    }
                }
            }
        });
    });

    // --- Flash Message Handling ---
    const flashCloseButtons = document.querySelectorAll('.alert .btn-close');
    flashCloseButtons.forEach(function(button) { /* ... same as before ... */ });
    const autoDismissMessages = document.querySelectorAll('.alert-dismissible.fade.show');
    autoDismissMessages.forEach(function(message) { /* ... same as before ... */ });

});