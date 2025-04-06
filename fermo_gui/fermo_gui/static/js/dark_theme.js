const toggleButton = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');
const html = document.documentElement;

const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    html.setAttribute('data-bs-theme', savedTheme);
    // Update the icon based on the saved theme
    themeIcon.classList.replace(savedTheme === 'dark' ? 'bi-moon-stars' : 'bi-sun', savedTheme === 'dark' ? 'bi-moon-stars' : 'bi-sun');
}

// Toggle theme on button click
toggleButton.addEventListener('click', function () {
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    // Toggle the theme
    html.setAttribute('data-bs-theme', newTheme);

    // Save the theme to localStorage
    localStorage.setItem('theme', newTheme);

    // Update the icon based on the new theme
    themeIcon.classList.replace(currentTheme === 'dark' ? 'bi-moon-stars' : 'bi-sun', newTheme === 'dark' ? 'bi-moon-stars' : 'bi-sun');
});