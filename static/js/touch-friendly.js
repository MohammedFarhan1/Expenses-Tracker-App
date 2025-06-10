// Touch-friendly enhancements for mobile devices
document.addEventListener('DOMContentLoaded', function() {
    // Add touch-friendly classes to interactive elements
    function enhanceTouchElements() {
        // Add touch-friendly class to all buttons
        const buttons = document.querySelectorAll('button, .btn');
        buttons.forEach(button => {
            button.classList.add('touch-friendly');
        });
        
        // Add touch-friendly class to all form inputs
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.classList.add('touch-friendly');
        });
        
        // Add touch-friendly class to all links
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            link.classList.add('touch-friendly');
        });
        
        // Add touch-friendly class to all table cells
        const tableCells = document.querySelectorAll('td, th');
        tableCells.forEach(cell => {
            cell.classList.add('touch-friendly');
        });
    }
    
    // Add fastclick to eliminate 300ms delay on touch devices
    function eliminateTouchDelay() {
        // Simple implementation to reduce touch delay
        document.addEventListener('touchstart', function() {}, {passive: true});
    }
    
    // Improve scrolling on touch devices
    function improveScrolling() {
        // Add momentum scrolling to elements that need it
        const scrollableElements = document.querySelectorAll('.table-responsive, .modal-body');
        scrollableElements.forEach(element => {
            element.style.webkitOverflowScrolling = 'touch';
        });
    }
    
    // Prevent zooming on form fields (iOS)
    function preventZoom() {
        // Set font-size to 16px or larger on all input fields to prevent zoom
        const formInputs = document.querySelectorAll('input, select, textarea');
        formInputs.forEach(input => {
            input.style.fontSize = '16px';
        });
    }
    
    // Run all enhancements
    enhanceTouchElements();
    eliminateTouchDelay();
    improveScrolling();
    preventZoom();
});