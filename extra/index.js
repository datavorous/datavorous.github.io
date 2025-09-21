document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
        target.scrollIntoView({
    behavior: 'smooth',
    block: 'start'
        });
    }
        });
});
document.querySelectorAll('.item').forEach(item => {
    item.addEventListener('mouseenter', function() {
    this.style.transform = 'translateX(4px)';
    this.style.transition = 'transform 0.2s ease';
});

    item.addEventListener('mouseleave', function() {
    this.style.transform = 'translateX(0)';
    });
});
