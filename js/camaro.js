/**
 * BUMBLEBEE — Chevrolet Camaro 6.2 V8 2SS ZL1
 * Scroll reveals, lightbox, video autoplay, sticky CTA, countUp
 */

(function () {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isTouchDevice = window.matchMedia('(hover: none)').matches;

  // ── Preloader ──────────────────────────────────────────────
  function initPreloader() {
    const preloader = document.querySelector('.preloader');
    if (!preloader) return;

    const heroImg = document.querySelector('.hero__img');
    const timeout = new Promise(resolve => setTimeout(resolve, 3000));
    const heroLoad = heroImg
      ? new Promise(resolve => {
          if (heroImg.complete) resolve();
          else {
            heroImg.addEventListener('load', resolve, { once: true });
            heroImg.addEventListener('error', resolve, { once: true });
          }
        })
      : Promise.resolve();

    Promise.race([heroLoad, timeout]).then(() => {
      preloader.classList.add('preloader--hidden');
      document.body.classList.add('loaded');
      preloader.addEventListener('transitionend', () => preloader.remove(), { once: true });
    });
  }

  // ── Scroll Reveal + Blur-Up (shared observer) ─────────────
  function initScrollReveal() {
    if (prefersReducedMotion) {
      document.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'));
      document.querySelectorAll('.blur-up').forEach(img => img.classList.add('loaded'));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          const el = entry.target;

          if (el.classList.contains('reveal')) {
            el.classList.add('visible');
          }

          if (el.classList.contains('blur-up')) {
            if (el.complete) {
              el.classList.add('loaded');
            } else {
              el.addEventListener('load', () => el.classList.add('loaded'), { once: true });
              el.addEventListener('error', () => el.classList.add('loaded'), { once: true });
            }
          }

          observer.unobserve(el);
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );

    document.querySelectorAll('.reveal, .blur-up').forEach(el => observer.observe(el));
  }

  // ── Scroll Effects (parallax + indicator) ──────────────────
  function initScrollEffects() {
    const hero = document.querySelector('.hero');
    const heroImg = (!prefersReducedMotion && !isTouchDevice)
      ? document.querySelector('.hero__img-wrap--desktop .hero__img')
      : null;
    const indicator = document.querySelector('.hero__scroll');
    if (!hero && !indicator) return;

    let indicatorHidden = false;
    let ticking = false;

    function onScroll() {
      const scrollY = window.scrollY;
      const heroH = hero ? hero.offsetHeight : 0;

      if (heroImg && scrollY < heroH) {
        heroImg.style.transform = `translate3d(0, ${scrollY * 0.3}px, 0) scale(1.05)`;
      }

      if (indicator && !indicatorHidden && scrollY > 100) {
        indicator.style.opacity = '0';
        indicatorHidden = true;
      }

      // Unregister when parallax is past and indicator is hidden
      if (indicatorHidden && (!heroImg || scrollY >= heroH)) {
        window.removeEventListener('scroll', scrollHandler);
      }

      ticking = false;
    }

    function scrollHandler() {
      if (!ticking) {
        requestAnimationFrame(onScroll);
        ticking = true;
      }
    }

    window.addEventListener('scroll', scrollHandler, { passive: true });
  }

  // ── CountUp Animation ─────────────────────────────────────
  function initCountUp() {
    if (prefersReducedMotion) {
      document.querySelectorAll('[data-countup]').forEach(el => {
        el.textContent = el.dataset.countup;
      });
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseFloat(el.dataset.countup);
        const suffix = el.dataset.suffix || '';
        const duration = 1500;
        const start = performance.now();

        function step(now) {
          const elapsed = now - start;
          const progress = Math.min(elapsed / duration, 1);
          // easeOutExpo
          const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
          const current = Math.round(eased * target);
          el.textContent = current.toLocaleString('bg-BG') + suffix;
          if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
        observer.unobserve(el);
      });
    }, { threshold: 0.3 });

    document.querySelectorAll('[data-countup]').forEach(el => observer.observe(el));
  }

  // ── Lightbox ──────────────────────────────────────────────
  function initLightbox() {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.setAttribute('role', 'dialog');
    lightbox.setAttribute('aria-label', 'Преглед на изображение');
    lightbox.setAttribute('aria-hidden', 'true');
    lightbox.innerHTML = `
      <button class="lightbox__close" aria-label="Затвори">&times;</button>
      <button class="lightbox__nav lightbox__nav--prev" aria-label="Предишна">&#8249;</button>
      <img class="lightbox__img" alt="" />
      <button class="lightbox__nav lightbox__nav--next" aria-label="Следваща">&#8250;</button>
    `;
    document.body.appendChild(lightbox);

    const lbImg = lightbox.querySelector('.lightbox__img');
    const closeBtn = lightbox.querySelector('.lightbox__close');
    const prevBtn = lightbox.querySelector('.lightbox__nav--prev');
    const nextBtn = lightbox.querySelector('.lightbox__nav--next');
    const items = Array.from(document.querySelectorAll('[data-lightbox]'));
    let currentIndex = -1;
    let lastTrigger = null;
    let touchStartX = 0;
    let touchStartY = 0;

    function showImage(index) {
      currentIndex = index;
      const el = items[index];
      lastTrigger = el;
      lbImg.src = el.dataset.lightbox;
      lbImg.alt = el.querySelector('img')?.alt || '';
      prevBtn.style.display = index > 0 ? '' : 'none';
      nextBtn.style.display = index < items.length - 1 ? '' : 'none';
    }

    function openLightbox(index) {
      showImage(index);
      lightbox.classList.add('active');
      lightbox.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      closeBtn.focus();
    }

    function closeLightbox() {
      lightbox.classList.remove('active');
      lightbox.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
      lbImg.src = '';
      if (lastTrigger) {
        lastTrigger.focus();
        lastTrigger = null;
      }
    }

    function navigate(delta) {
      const next = currentIndex + delta;
      if (next >= 0 && next < items.length) showImage(next);
    }

    items.forEach((el, i) => {
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('aria-label', (el.querySelector('img')?.alt || '') + ' — натисни за увеличение');

      function activate() { openLightbox(i); }

      el.addEventListener('click', activate);
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          activate();
        }
      });
    });

    prevBtn.addEventListener('click', (e) => { e.stopPropagation(); navigate(-1); });
    nextBtn.addEventListener('click', (e) => { e.stopPropagation(); navigate(1); });
    closeBtn.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox) closeLightbox();
    });
    document.addEventListener('keydown', (e) => {
      if (!lightbox.classList.contains('active')) return;
      if (e.key === 'Escape') closeLightbox();
      else if (e.key === 'ArrowLeft') navigate(-1);
      else if (e.key === 'ArrowRight') navigate(1);
    });

    lightbox.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    }, { passive: true });

    lightbox.addEventListener('touchend', (e) => {
      const deltaX = e.changedTouches[0].clientX - touchStartX;
      const deltaY = e.changedTouches[0].clientY - touchStartY;
      if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 60) {
        navigate(deltaX < 0 ? 1 : -1);
      } else if (deltaY > 80) {
        closeLightbox();
      }
    }, { passive: true });
  }

  // ── Video Autoplay ────────────────────────────────────────
  function initVideo() {
    const video = document.querySelector('.cinema__video');
    if (!video) return;

    const playBtn = document.querySelector('.cinema__play');

    if (!isTouchDevice) {
      // Desktop: autoplay muted when in view
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            video.play().catch(() => {});
            if (playBtn) playBtn.style.display = 'none';
          } else {
            video.pause();
          }
        });
      }, { threshold: 0.3 });
      observer.observe(video);
    } else {
      // Mobile: tap to play
      if (playBtn) {
        playBtn.addEventListener('click', () => {
          if (video.paused) {
            video.play().catch(() => {});
            playBtn.style.display = 'none';
          }
        });
        video.addEventListener('pause', () => {
          playBtn.style.display = '';
        });
      }
    }
  }

  // ── Sticky CTA ────────────────────────────────────────────
  function initStickyCta() {
    const stickyCta = document.querySelector('.sticky-cta');
    const ctaSection = document.querySelector('.price');
    const hero = document.querySelector('.hero');
    if (!stickyCta) return;

    let ctaVisible = false;
    let pastHero = false;

    // Watch CTA section
    if (ctaSection) {
      const ctaObserver = new IntersectionObserver((entries) => {
        ctaVisible = entries[0].isIntersecting;
        updateSticky();
      }, { threshold: 0.1 });
      ctaObserver.observe(ctaSection);
    }

    // Watch hero
    if (hero) {
      const heroObserver = new IntersectionObserver((entries) => {
        pastHero = !entries[0].isIntersecting;
        updateSticky();
      }, { threshold: 0 });
      heroObserver.observe(hero);
    }

    function updateSticky() {
      if (pastHero && !ctaVisible) {
        stickyCta.classList.add('sticky-cta--visible');
      } else {
        stickyCta.classList.remove('sticky-cta--visible');
      }
    }
  }

  // ── Init ───────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    initPreloader();
    initScrollReveal();
    initScrollEffects();
    initCountUp();
    initLightbox();
    initVideo();
    initStickyCta();
  });
})();
