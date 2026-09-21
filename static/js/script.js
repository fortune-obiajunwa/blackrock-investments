// =========================================
// FORTUNE CAPITAL
// MAIN JAVASCRIPT
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    // Mobile menu
    const menuToggle = document.querySelector(".menu-toggle");
    const mobileNav = document.querySelector(".mobile-nav");

    if (menuToggle && mobileNav) {
        menuToggle.addEventListener("click", () => {
            mobileNav.classList.toggle("active");
        });
    }

});