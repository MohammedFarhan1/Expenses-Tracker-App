// Mobile menu functionality
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu functionality
    const menuToggle = document.getElementById('menu-toggle');
    const navbarNav = document.getElementById('navbar-nav');
    const overlay = document.getElementById('mobile-menu-overlay');
    
    if (menuToggle && navbarNav && overlay) {
        menuToggle.addEventListener('click', function() {
            navbarNav.classList.toggle('active');
            overlay.style.display = navbarNav.classList.contains('active') ? 'block' : 'none';
            
            // Change icon based on menu state
            const menuIcon = menuToggle.querySelector('i');
            if (menuIcon) {
                if (navbarNav.classList.contains('active')) {
                    menuIcon.classList.replace('fa-bars', 'fa-times');
                } else {
                    menuIcon.classList.replace('fa-times', 'fa-bars');
                }
            }
        });
        
        // Close menu when clicking on overlay
        overlay.addEventListener('click', function() {
            navbarNav.classList.remove('active');
            overlay.style.display = 'none';
            const menuIcon = menuToggle.querySelector('i');
            if (menuIcon) {
                menuIcon.classList.replace('fa-times', 'fa-bars');
            }
        });
        
        // Close menu when clicking on a link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    navbarNav.classList.remove('active');
                    overlay.style.display = 'none';
                    const menuIcon = menuToggle.querySelector('i');
                    if (menuIcon) {
                        menuIcon.classList.replace('fa-times', 'fa-bars');
                    }
                }
            });
        });
    }
});