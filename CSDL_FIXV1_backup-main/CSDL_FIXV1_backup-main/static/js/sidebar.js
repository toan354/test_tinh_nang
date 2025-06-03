// Lấy các phần tử DOM cần thiết
const links = document.querySelectorAll('.sidebar a');
const rightSection = document.querySelector('.right-section');
const container = document.querySelector('.container');

// Duyệt qua tất cả các thẻ a và thêm sự kiện click
links.forEach(link => {
    link.addEventListener('click', function(event) {
        // Only prevent default for submenu toggles
        const submenu = this.nextElementSibling;
        if (submenu && submenu.classList && submenu.classList.contains('submenu')) {
            event.preventDefault();
            
            // Toggle submenu visibility
            const isOpen = submenu.classList.contains('open');
            document.querySelectorAll('.submenu').forEach(sub => {
                if (sub && sub.classList) sub.classList.remove('open');
            });
            if (!isOpen) {
                submenu.classList.add('open');
            }
        }

        // Remove active class from all links
        links.forEach(l => l.classList.remove('active'));
        // Add active class to clicked link
        this.classList.add('active');

        // Handle layout changes if needed
        const href = this.getAttribute('href');
        if (href && (href.includes('stock') || href.includes('analytics'))) {
            if (rightSection) rightSection.style.display = 'none';
            if (container) container.classList.add('two-column');
        } else {
            if (rightSection) rightSection.style.display = 'block';
            if (container) container.classList.remove('two-column');
        }
    });
});

// Add event listener for submenu toggle and active state
document.querySelectorAll('.sidebar > li > a').forEach(link => {
    link.addEventListener('click', function(event) {
        const submenu = this.nextElementSibling;
        
        // Add null check before accessing submenu
        if (submenu && submenu.classList && submenu.classList.contains('submenu')) {
            event.preventDefault(); // Prevent default link behavior

            // Toggle submenu visibility
            const isOpen = submenu.classList.contains('open');
            document.querySelectorAll('.submenu').forEach(sub => {
                if (sub && sub.classList) sub.classList.remove('open');
            });
            if (!isOpen) {
                submenu.classList.add('open');
            }

            // Activate "Tổng quan" when "Stock" is clicked
            const stockLink = submenu.querySelector('a[href*="stock"]');
            if (stockLink && stockLink.classList) {
                stockLink.classList.add('active');
            }
            
        } else {
            // Hide all submenus when another main menu item is clicked
            document.querySelectorAll('.submenu').forEach(sub => {
                if (sub && sub.classList) sub.classList.remove('open');
            });
            document.querySelectorAll('.submenu a').forEach(subLink => {
                if (subLink && subLink.classList) subLink.classList.remove('active');
            });
        }
    });
});

// Ensure submenu remains open when clicking on its items
document.querySelectorAll('.submenu a')?.forEach(subLink => {
    if (subLink) {
        subLink.addEventListener('click', function(event) {
            event.stopPropagation(); // Prevent event from bubbling up to parent
            document.querySelectorAll('.submenu a')?.forEach(link => {
                if (link) link.classList.remove('active');
            });
            this.classList.add('active');
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Lấy tất cả các links trong sidebar
    const sidebarLinks = document.querySelectorAll('#navbar .sidebar a');
    
    // Xác định trang hiện tại từ URL
    const currentPath = window.location.pathname;

    // Hàm kiểm tra path match (hỗ trợ cả exact và partial match)
    function isPathMatch(linkPath, currentPath) {
        // Exact match
        if (linkPath === currentPath) return true;
        
        // Special case for home page
        if (linkPath === '/' && currentPath === '/priceboard') return true;
        
        // Check if current path starts with link path (for sub-pages)
        if (linkPath !== '/' && currentPath.startsWith(linkPath)) return true;
        
        return false;
    }

    // Đánh dấu active cho trang hiện tại
    sidebarLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        
        // Đánh dấu active nếu path match
        if (isPathMatch(linkPath, currentPath)) {
            link.classList.add('active');
            // Thêm class active cho parent li nếu có
            const parentLi = link.closest('li');
            if (parentLi) {
                parentLi.classList.add('active');
            }
        }
    });

    // Xử lý menu button trên mobile (nếu có)
    const menuBtn = document.querySelector('#menu-btn');
    const closeBtn = document.querySelector('#close-btn');
    const sidebar = document.querySelector('#navbar');

    if (menuBtn && sidebar) {
        menuBtn.addEventListener('click', () => {
            sidebar.style.display = 'block';
        });
    }

    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => {
            sidebar.style.display = 'none';
        });
    }
});
