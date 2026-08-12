// static/script.js - Enhanced with Dark Mode & Budget

document.addEventListener('DOMContentLoaded', function() {

  // ===== DARK MODE TOGGLE =====
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    const currentTheme = localStorage.getItem('theme') || 'light';
    if (currentTheme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      themeToggle.textContent = '☀️';
    }
    themeToggle.addEventListener('click', function() {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      if (isDark) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        this.textContent = '🌙';
      } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        this.textContent = '☀️';
      }
    });
  }

  // ===== BUDGET MANAGEMENT =====
  const BUDGET_KEY = 'monthly_budget';
  const budgetInput = document.getElementById('budget-input');
  const setBudgetBtn = document.getElementById('set-budget-btn');
  if (budgetInput && setBudgetBtn) {
    const saved = parseFloat(localStorage.getItem(BUDGET_KEY)) || 0;
    if (saved > 0) budgetInput.value = saved;
    setBudgetBtn.addEventListener('click', function() {
      const val = parseFloat(budgetInput.value);
      if (!isNaN(val) && val >= 0) {
        localStorage.setItem(BUDGET_KEY, val);
        alert('Budget set to ₹' + val.toFixed(2));
        location.reload();
      } else {
        alert('Please enter a valid positive number.');
      }
    });
  }

  // ===== DAILY REMINDER =====
  const notifBtn = document.getElementById('notif-btn');
  if (!('Notification' in window)) {
    if (notifBtn) notifBtn.style.display = 'none';
  } else {
    function checkReminder() {
      fetch('/api/reminder-status')
        .then(r => r.json())
        .then(data => {
          if (!data.logged_today && Notification.permission === 'granted') {
            new Notification('⏰ Daily Expense Reminder', {
              body: `You haven't logged any expenses for ${data.date}. Add them now!`,
              icon: 'https://cdn.jsdelivr.net/npm/emoji-datasource-apple/img/apple/64/1f4b0.png'
            });
          }
        })
        .catch(err => console.error('Reminder check failed:', err));
    }
    if (notifBtn) {
      notifBtn.addEventListener('click', function() {
        if (Notification.permission === 'granted') {
          checkReminder();
          this.textContent = '✅ Reminders Enabled';
          this.style.background = '#22c55e';
        } else if (Notification.permission === 'denied') {
          alert('Notifications are blocked. Please allow them in your browser settings.');
        } else {
          Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
              this.textContent = '✅ Reminders Enabled';
              this.style.background = '#22c55e';
              checkReminder();
            } else {
              alert('Permission denied.');
            }
          });
        }
      });
      if (Notification.permission === 'granted') {
        notifBtn.textContent = '✅ Reminders Enabled';
        notifBtn.style.background = '#22c55e';
        checkReminder();
        setInterval(checkReminder, 300000);
      }
    }
  }

  // ===== QUICK ADD =====
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
      .then(r => r.json())
      .then(data => {
        if (data.success) window.location.reload();
        else alert('Failed: ' + (data.error || 'Unknown error'));
      })
      .catch(err => alert('Error: ' + err));
    });
  });

  // ===== AUTO-DISMISS FLASH MESSAGES =====
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach((flash, index) => {
    setTimeout(() => {
      flash.style.transition = 'opacity 0.5s ease';
      flash.style.opacity = '0';
      setTimeout(() => flash.remove(), 500);
    }, 4000 + (index * 200));
  });
});