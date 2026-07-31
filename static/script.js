// Sticky navbar background on scroll
document.addEventListener('DOMContentLoaded', function () {
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    const onScroll = () => {
      if (window.scrollY > 40) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    };
    window.addEventListener('scroll', onScroll);
    onScroll();
  }

  // Prediction form validation + loading state
  const form = document.getElementById('prediction-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      let valid = true;

      form.querySelectorAll('[data-field]').forEach((field) => {
        const input = field.querySelector('input, select');
        if (!input || input.value === '' || input.value === null) {
          field.classList.add('invalid');
          valid = false;
        } else {
          field.classList.remove('invalid');
        }
      });

      if (!valid) {
        e.preventDefault();
        const firstInvalid = form.querySelector('.invalid');
        if (firstInvalid) {
          firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.classList.add('loading');
        submitBtn.setAttribute('disabled', 'true');
      }
    });
  }
});
