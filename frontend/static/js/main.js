/**
 * CarePlus Hospital - Core Application & Public Homepage Script
 * Handles navigation, mobile navbar collapse, scrollspy, interactive contact form, and back-to-top.
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Navbar Auto-Collapse on Link Click
  const navLinks = document.querySelectorAll('.cp-nav-link');
  const navbarCollapse = document.getElementById('careplusNavbar');

  navLinks.forEach(function (link) {
    link.addEventListener('click', function () {
      if (navbarCollapse && navbarCollapse.classList.contains('show')) {
        const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
        if (bsCollapse) {
          bsCollapse.hide();
        }
      }
    });
  });

  // 2. Active Navigation Highlight based on Scroll Position (ScrollSpy)
  const sections = document.querySelectorAll('section[id], header[id]');
  
  function highlightNavOnScroll() {
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;
    
    sections.forEach(function (section) {
      const sectionHeight = section.offsetHeight;
      const sectionTop = section.offsetTop - 120;
      const sectionId = section.getAttribute('id');
      
      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        navLinks.forEach(function (link) {
          link.classList.remove('active');
          if (link.getAttribute('href').includes('#' + sectionId)) {
            link.classList.add('active');
          }
        });
      }
    });
  }

  window.addEventListener('scroll', highlightNavOnScroll, { passive: true });

  // 3. Back to Top Button
  const backToTopBtn = document.getElementById('backToTopBtn');
  if (backToTopBtn) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 400) {
        backToTopBtn.classList.add('show');
      } else {
        backToTopBtn.classList.remove('show');
      }
    }, { passive: true });

    backToTopBtn.addEventListener('click', function () {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // 4. Contact Form Submission Handler (Mock feedback without backend mutation)
  const contactForm = document.getElementById('hospitalContactForm');
  const contactSuccessAlert = document.getElementById('contactSuccessAlert');

  if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
      e.preventDefault();

      const name = document.getElementById('contactName').value.trim();
      const email = document.getElementById('contactEmail').value.trim();
      const message = document.getElementById('contactMessage').value.trim();

      if (!name || !email || !message) {
        alert('Please fill in all mandatory fields before sending your message.');
        return;
      }

      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Transmitting message...';

      // Simulate instantaneous client-side acknowledgment
      setTimeout(function () {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        contactForm.reset();

        if (contactSuccessAlert) {
          contactSuccessAlert.classList.remove('d-none');
          contactSuccessAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
          setTimeout(function () {
            contactSuccessAlert.classList.add('d-none');
          }, 8000);
        }
      }, 700);
    });
  }

  // 5. Doctor Profile Details Modal Handler
  const doctorModalEl = document.getElementById('doctorDetailModal');
  if (doctorModalEl) {
    doctorModalEl.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      if (!button) return;

      const name = button.getAttribute('data-doctor-name') || 'Doctor Profile';
      const spec = button.getAttribute('data-doctor-spec') || '';
      const qual = button.getAttribute('data-doctor-qual') || '';
      const dept = button.getAttribute('data-doctor-dept') || '';
      const room = button.getAttribute('data-doctor-room') || '';
      const fee = button.getAttribute('data-doctor-fee') || '500';
      const bio = button.getAttribute('data-doctor-bio') || '';
      const img = button.getAttribute('data-doctor-img') || '';

      const nameEl = document.getElementById('modalDoctorName');
      const specEl = document.getElementById('modalDoctorSpec');
      const qualEl = document.getElementById('modalDoctorQual');
      const deptEl = document.getElementById('modalDoctorDept');
      const roomEl = document.getElementById('modalDoctorRoom');
      const feeEl = document.getElementById('modalDoctorFee');
      const bioEl = document.getElementById('modalDoctorBio');
      const modalImg = document.getElementById('modalDoctorImg');

      if (nameEl) nameEl.textContent = name;
      if (specEl) specEl.textContent = spec;
      if (qualEl) qualEl.textContent = qual;
      if (deptEl) deptEl.textContent = dept;
      if (roomEl) roomEl.textContent = room;
      if (feeEl) feeEl.textContent = '$' + fee;
      if (bioEl) bioEl.textContent = bio;
      if (modalImg && img) {
        modalImg.src = img;
        modalImg.alt = name;
      }
    });
  }

  // 6. Auto-dismiss Flash Alert Messages after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alertEl) {
    setTimeout(function () {
      if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
        if (bsAlert) {
          bsAlert.close();
        }
      }
    }, 5000);
  });

  // 7. Interactive Confirmation Modal/Dialog for Dangerous Actions
  const confirmButtons = document.querySelectorAll('[data-confirm]');
  confirmButtons.forEach(function (button) {
    button.addEventListener('click', function (e) {
      const message = button.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
});
