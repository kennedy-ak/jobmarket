// Language Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Set initial language from server
    const currentLang = document.body.getAttribute('data-language') || 'en';
    
    // Language toggle buttons
    document.querySelectorAll('.lang-btn').forEach(button => {
        button.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            
            // Update active button
            document.querySelectorAll('.lang-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            // Send language change to server
            fetch('/api/set-language/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ language: lang })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show selected language content
                    document.querySelectorAll('.lang-en, .lang-nl').forEach(element => {
                        element.classList.remove('active');
                    });
                    document.querySelectorAll(`.lang-${lang}`).forEach(element => {
                        element.classList.add('active');
                    });
                    
                    // Reload page to apply language changes
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
    
    // FAQ Functionality
    document.querySelectorAll('.faq-question').forEach(question => {
        question.addEventListener('click', () => {
            const item = question.parentNode;
            item.classList.toggle('active');
            
            // Change + to - and vice versa
            const icon = question.querySelector('span:last-child');
            icon.textContent = item.classList.contains('active') ? '−' : '+';
        });
    });
    
    // Mobile Menu Functionality
    const mobileMenu = document.querySelector('.mobile-menu');
    const nav = document.querySelector('nav');
    const overlay = document.querySelector('.overlay');
    const closeMenu = document.querySelector('.close-menu');
    
    if (mobileMenu) {
        mobileMenu.addEventListener('click', function() {
            nav.classList.add('active');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }
    
    if (closeMenu) {
        closeMenu.addEventListener('click', function() {
            nav.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = 'auto';
        });
    }
    
    if (overlay) {
        overlay.addEventListener('click', function() {
            nav.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = 'auto';
        });
    }
    
    // Close menu when clicking on a link
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', function() {
            nav.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = 'auto';
        });
    });
    
    // Back to top button
    const backToTopButton = document.querySelector('.back-to-top');
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.classList.add('visible');
        } else {
            backToTopButton.classList.remove('visible');
        }
    });
    
    if (backToTopButton) {
        backToTopButton.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Form submission with AJAX
    const registrationForm = document.getElementById('registrationForm');
    if (registrationForm) {
        registrationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/registration/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => {
                if (response.ok) {
                    // Redirect to success page
                    window.location.href = '/registration/success/';
                } else {
                    return response.json();
                }
            })
            .then(data => {
                if (data && data.errors) {
                    // Display form errors
                    displayFormErrors(data.errors);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            });
        });
    }
});

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Helper function to display form errors
function displayFormErrors(errors) {
    // Clear previous errors
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    
    // Display new errors
    Object.keys(errors).forEach(field => {
        const fieldElement = document.querySelector(`[name="${field}"]`);
        if (fieldElement) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.color = 'red';
            errorDiv.style.fontSize = '14px';
            errorDiv.style.marginTop = '5px';
            errorDiv.textContent = errors[field][0];
            fieldElement.parentNode.appendChild(errorDiv);
        }
    });
}

// Improve touch experience on mobile
document.addEventListener('touchstart', function() {}, {passive: true});