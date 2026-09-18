/**
 * AttendTrack Enterprise UI - Interactive Frontend Script
 * Handles real-time clock ticker, responsive sidebar drawer,
 * alert dismissal, form submission protection, and demo autofill.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Drawer Toggle
  const sidebar = document.querySelector('.app-sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle');
  const backdrop = document.getElementById('sidebar-backdrop');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (backdrop) backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (sidebar && sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', closeSidebar);
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  });

  // 2. Real-time Digital Clock Ticker
  function updateLiveClock() {
    const now = new Date();

    // Topbar Clock
    const topbarClock = document.getElementById('topbar-live-clock');
    if (topbarClock) {
      topbarClock.textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
    }

    // Large Terminal Clock
    const bigClock = document.getElementById('big-terminal-clock');
    if (bigClock) {
      bigClock.textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
    }

    // Terminal Date Display
    const terminalDate = document.getElementById('big-terminal-date');
    if (terminalDate) {
      terminalDate.textContent = now.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    }
  }

  setInterval(updateLiveClock, 1000);
  updateLiveClock();

  // 3. Auto-dismiss Alert Toasts (after 5 seconds)
  const alerts = document.querySelectorAll('.alert-box');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 400);
    }, 5500);
  });

  // 4. Punch Action Confirmation & Double-Click Protection
  const clockInForm = document.getElementById('clock-in-form');
  if (clockInForm) {
    clockInForm.addEventListener('submit', function (e) {
      const btn = this.querySelector('button[type="submit"]');
      if (btn && btn.disabled) {
        e.preventDefault();
        return;
      }
      if (!confirm('Confirm Time-In punch for today?')) {
        e.preventDefault();
      } else if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> RECORDING...';
      }
    });
  }

  const clockOutForm = document.getElementById('clock-out-form');
  if (clockOutForm) {
    clockOutForm.addEventListener('submit', function (e) {
      const btn = this.querySelector('button[type="submit"]');
      if (btn && btn.disabled) {
        e.preventDefault();
        return;
      }
      if (!confirm('Confirm Time-Out punch for today?')) {
        e.preventDefault();
      } else if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> RECORDING...';
      }
    });
  }

  // 5. Quick Demo Credentials Autofill Helper
  window.fillLogin = function (username, password) {
    const userField = document.getElementById('id_username');
    const passField = document.getElementById('id_password');
    if (userField && passField) {
      userField.value = username;
      passField.value = password;
      userField.style.borderColor = '#3b82f6';
      passField.style.borderColor = '#3b82f6';
      setTimeout(() => {
        userField.style.borderColor = '';
        passField.style.borderColor = '';
      }, 800);
    }
  };
});
