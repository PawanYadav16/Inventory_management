// Main Javascript - Inventory Management System

document.addEventListener('DOMContentLoaded', function () {
    // Explicitly initialize Bootstrap 5 dropdowns if present and bootstrap is loaded
    if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
        const dropdownElementList = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        dropdownElementList.forEach(function (dropdownToggleEl) {
            new bootstrap.Dropdown(dropdownToggleEl);
        });
    }

    // Immediate dismissal of flash message alerts on close button (×) click
    document.addEventListener('click', function (event) {
        const dismissBtn = event.target.closest('[data-bs-dismiss="alert"]');
        if (dismissBtn) {
            const alertBox = dismissBtn.closest('.alert');
            if (alertBox) {
                alertBox.remove();
            }
        }
    });

    // Reload page if retrieved from Back/Forward cache (BFCache) after logout
    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            window.location.reload();
        }
    });

    // Auto-dismiss alert notifications after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                if (document.body.contains(alert)) {
                    alert.remove();
                }
            } catch (e) {
                // Ignore if alert already dismissed by user
            }
        }, 6000);
    });
});
