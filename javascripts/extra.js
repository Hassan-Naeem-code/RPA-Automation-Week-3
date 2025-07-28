// Custom JavaScript for RPA Documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add performance metrics animation
    const performanceMetrics = document.querySelectorAll('.performance-metric');
    performanceMetrics.forEach(metric => {
        metric.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.transition = 'transform 0.2s ease';
        });
        
        metric.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Add copy button functionality to API examples
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        const pre = block.parentElement;
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.innerHTML = '📋 Copy';
        button.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            background: #1976d2;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        `;
        
        pre.style.position = 'relative';
        pre.appendChild(button);
        
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent).then(() => {
                button.innerHTML = '✅ Copied!';
                setTimeout(() => {
                    button.innerHTML = '📋 Copy';
                }, 2000);
            });
        });
    });

    // Add smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add status indicator for API functions
    const apiFunctions = document.querySelectorAll('.api-function');
    apiFunctions.forEach(func => {
        const statusBadge = document.createElement('span');
        statusBadge.className = 'status-badge status-success';
        statusBadge.textContent = 'Active';
        statusBadge.style.float = 'right';
        
        const header = func.querySelector('h3');
        if (header) {
            header.appendChild(statusBadge);
        }
    });
});
