// static/script.js

// ----------------------------------------------------------------
// 1. Daily Reminder Notification System
// ----------------------------------------------------------------
document.addEventListener('DOMContentLoaded', function() {
    const notifBtn = document.getElementById('notif-btn');
    
    // Check if the browser supports notifications
    if (!('Notification' in window)) {
        if (notifBtn) notifBtn.style.display = 'none';
        return;
    }

    // Function to check reminder status and notify
    function checkReminder() {
        fetch('/api/reminder-status')
            .then(response => response.json())
            .then(data => {
                if (!data.logged_today) {
                    // Show browser notification
                    if (Notification.permission === 'granted') {
                        new Notification('⏰ Daily Expense Reminder', {
                            body: `You haven't logged any expenses for ${data.date}. Add them now!`,
                            icon: 'https://cdn.jsdelivr.net/npm/emoji-datasource-apple/img/apple/64/1f4b0.png'
                        });
                    }
                }
            })
            .catch(err => console.error('Reminder check failed:', err));
    }

    // Handle the "Enable Reminders" button
    if (notifBtn) {
        notifBtn.addEventListener('click', function() {
            if (Notification.permission === 'granted') {
                // Already granted, just check
                checkReminder();
                this.textContent = '✅ Reminders Enabled';
                this.style.background = '#22c55e';
            } else if (Notification.permission === 'denied') {
                alert('Notifications are blocked. Please allow them in your browser settings.');
            } else {
                // Request permission
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        this.textContent = '✅ Reminders Enabled';
                        this.style.background = '#22c55e';
                        checkReminder();
                    } else {
                        alert('Permission denied. You won\'t receive daily reminders.');
                    }
                });
            }
        });

        // Auto-check permission status on load
        if (Notification.permission === 'granted') {
            notifBtn.textContent = '✅ Reminders Enabled';
            notifBtn.style.background = '#22c55e';
            // Check reminder status every 5 minutes (300,000 ms)
            checkReminder(); // initial check
            setInterval(checkReminder, 300000);
        }
    }
});

// ----------------------------------------------------------------
// 2. Quick Add Expense (AJAX)
// ----------------------------------------------------------------
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.quick-add-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const category = this.dataset.category;
            const amount = this.dataset.amount;
            const description = this.dataset.description || `Quick ${category}`;
            
            fetch('/api/quick-add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category, amount, description })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload the page to reflect changes
                    window.location.reload();
                } else {
                    alert('Failed to add expense: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(err => alert('Error: ' + err));
        });
    });
});

// ----------------------------------------------------------------
// 3. Auto-dismiss flash messages after 4 seconds
// ----------------------------------------------------------------
document.addEventListener('DOMContentLoaded', function() {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach((flash, index) => {
        setTimeout(() => {
            flash.style.transition = 'opacity 0.5s ease';
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 500);
        }, 4000 + (index * 200));
    });
});