document.addEventListener('DOMContentLoaded', () => {
  // 1. Scroll Reveal Animation
  const revealElements = document.querySelectorAll('.reveal');
  
  if ('IntersectionObserver' in window) {
    const revealOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px"
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          
          if (entry.target.classList.contains('features-grid') || 
              entry.target.classList.contains('steps-flow') ||
              entry.target.classList.contains('qs-grid')) {
            
            const children = entry.target.children;
            Array.from(children).forEach((child, index) => {
              child.style.transitionDelay = `${index * 100}ms`;
            });
          }
          
          observer.unobserve(entry.target);
        }
      });
    }, revealOptions);

    revealElements.forEach(el => revealObserver.observe(el));
  } else {
    revealElements.forEach(el => el.classList.add('visible'));
  }

  // 2. Terminal Typing Animation (Hero)
  const heroTerminal = document.getElementById('hero-terminal');
  if (heroTerminal) {
    const typeLines = heroTerminal.querySelectorAll('.type-line');
    const resultLines = heroTerminal.querySelectorAll('.result-lines');
    
    // Check for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
      typeLines.forEach(line => {
        line.textContent = line.getAttribute('data-text');
        line.classList.add('done');
      });
      resultLines.forEach(res => res.classList.add('visible'));
    } else {
      let currentLineIndex = 0;
      
      const typeText = (element, text, speed, callback) => {
        let i = 0;
        element.textContent = '';
        
        const typeChar = () => {
          if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(typeChar, speed + (Math.random() * 20)); // slight randomness
          } else {
            element.classList.add('done');
            if (callback) setTimeout(callback, 200);
          }
        };
        typeChar();
      };

      const animateTerminal = () => {
        if (currentLineIndex < typeLines.length) {
          const currentLine = typeLines[currentLineIndex];
          const text = currentLine.getAttribute('data-text');
          
          typeText(currentLine, text, 30, () => {
            // Show corresponding results instantly
            if (resultLines[currentLineIndex]) {
              resultLines[currentLineIndex].classList.add('visible');
            }
            currentLineIndex++;
            setTimeout(animateTerminal, 600);
          });
        }
      };

      // Start animation with a slight delay
      setTimeout(animateTerminal, 1000);
    }
  }

  // 3. Copy to Clipboard
  const copyButtons = document.querySelectorAll('.copy-btn');
  copyButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const textToCopy = btn.getAttribute('data-clipboard');
      
      navigator.clipboard.writeText(textToCopy).then(() => {
        const originalText = btn.textContent;
        btn.textContent = '已复制 ✓';
        btn.style.backgroundColor = '#D97757';
        btn.style.color = '#FAFAF8';
        btn.style.borderColor = '#D97757';
        
        setTimeout(() => {
          btn.textContent = originalText;
          btn.style.backgroundColor = '';
          btn.style.color = '';
          btn.style.borderColor = '';
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy: ', err);
      });
    });
  });

  // 4. Mobile Navigation
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  const navLinksItems = document.querySelectorAll('.nav-link, .nav-cta');
  
  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      const isOpen = navLinks.classList.toggle('active');
      menuToggle.setAttribute('aria-expanded', isOpen);
    });

    // Close menu when clicking links
    navLinksItems.forEach(item => {
      item.addEventListener('click', () => {
        navLinks.classList.remove('active');
        menuToggle.setAttribute('aria-expanded', 'false');
      });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.navbar')) {
        navLinks.classList.remove('active');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // 5. Smooth Scroll for anchors
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      if (targetId === '#') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return;
      }
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        // Account for sticky navbar height (approx 70px)
        const headerOffset = 70;
        const elementPosition = targetElement.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
  
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
});