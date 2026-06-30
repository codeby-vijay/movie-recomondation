/**
 * CineAI - Main Application JavaScript
 * =======================================
 * Handles search, AJAX interactions, ratings, favorites,
 * watchlist, pagination, and dynamic UI updates.
 */

'use strict';

// ---- Namespace ----
const CineAI = {
    /**
     * Initialize the application.
     */
    init() {
        this.setupNavbar();
        this.setupSearch();
        this.setupFlashMessages();
        this.setupMovieCards();
        this.setupRating();
        this.setupFavorites();
        this.setupWatchlist();
        this.setupScrollAnimations();
    },

    // ========== NAVBAR ==========
    setupNavbar() {
        const navbar = document.querySelector('.navbar-cineai');
        if (!navbar) return;

        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }, { passive: true });
    },

    // ========== SEARCH ==========
    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        const suggestionsBox = document.getElementById('searchSuggestions');

        if (!searchInput || !suggestionsBox) return;

        let debounceTimer = null;

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            clearTimeout(debounceTimer);

            if (query.length < 2) {
                suggestionsBox.classList.remove('active');
                suggestionsBox.innerHTML = '';
                return;
            }

            debounceTimer = setTimeout(() => {
                this.fetchSuggestions(query, suggestionsBox);
            }, 300);
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = searchInput.value.trim();
                if (query) {
                    window.location.href = `/movies/search?q=${encodeURIComponent(query)}`;
                }
            }
            if (e.key === 'Escape') {
                suggestionsBox.classList.remove('active');
            }
        });

        // Close suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                suggestionsBox.classList.remove('active');
            }
        });
    },

    /**
     * Fetch search suggestions via AJAX.
     * @param {string} query - Search query.
     * @param {HTMLElement} container - Suggestions container.
     */
    async fetchSuggestions(query, container) {
        try {
            const response = await fetch(
                `/movies/search/suggestions?q=${encodeURIComponent(query)}`
            );
            const data = await response.json();

            if (data.length === 0) {
                container.classList.remove('active');
                container.innerHTML = '';
                return;
            }

            container.innerHTML = data.map(movie => `
                <a href="/movies/${movie.id}" class="suggestion-item">
                    <img src="${movie.poster_url}"
                         alt="${movie.title}"
                         class="suggestion-poster"
                         onerror="this.src='/static/images/no-poster.png'">
                    <div class="suggestion-info">
                        <div class="suggestion-title">${this.escapeHtml(movie.title)}</div>
                        <div class="suggestion-year">${movie.year || ''}</div>
                    </div>
                </a>
            `).join('');

            container.classList.add('active');
        } catch (error) {
            console.error('Search suggestion error:', error);
        }
    },

    // ========== FLASH MESSAGES ==========
    setupFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(msg => {
            setTimeout(() => {
                msg.style.transition = 'all 0.3s ease';
                msg.style.opacity = '0';
                msg.style.transform = 'translateX(100%)';
                setTimeout(() => msg.remove(), 300);
            }, 4000);
        });
    },

    // ========== MOVIE CARDS ==========
    setupMovieCards() {
        // Make movie cards clickable
        document.querySelectorAll('.movie-card[data-movie-id]').forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't navigate if clicking action buttons
                if (e.target.closest('.btn-icon') || e.target.closest('.movie-card-actions')) {
                    return;
                }
                const movieId = card.dataset.movieId;
                window.location.href = `/movies/${movieId}`;
            });
        });
    },

    // ========== RATING ==========
    setupRating() {
        const ratingInputs = document.querySelectorAll('.star-rating input');
        ratingInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const movieId = e.target.closest('.star-rating').dataset.movieId;
                const rating = e.target.value;
                this.submitRating(movieId, rating);
            });
        });
    },

    /**
     * Submit a movie rating via AJAX.
     * @param {number} movieId - Movie ID.
     * @param {number} rating - Rating value.
     */
    async submitRating(movieId, rating) {
        try {
            const response = await fetch('/movies/rate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ movie_id: movieId, rating: parseFloat(rating) }),
            });
            const data = await response.json();
            this.showToast(data.message, data.success ? 'success' : 'danger');
        } catch (error) {
            this.showToast('Failed to save rating', 'danger');
        }
    },

    // ========== FAVORITES ==========
    setupFavorites() {
        document.querySelectorAll('.btn-favorite').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const movieId = btn.dataset.movieId;
                this.toggleFavorite(movieId, btn);
            });
        });
    },

    /**
     * Toggle favorite status via AJAX.
     * @param {number} movieId - Movie ID.
     * @param {HTMLElement} btn - Button element.
     */
    async toggleFavorite(movieId, btn) {
        try {
            const response = await fetch('/movies/favorite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ movie_id: movieId }),
            });
            const data = await response.json();

            if (data.success) {
                btn.classList.toggle('active', data.is_favorited);
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.className = data.is_favorited ? 'bi bi-heart-fill' : 'bi bi-heart';
                }
                this.showToast(data.message, 'success');
            }
        } catch (error) {
            this.showToast('Please login to add favorites', 'info');
        }
    },

    // ========== WATCHLIST ==========
    setupWatchlist() {
        document.querySelectorAll('.btn-watchlist').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const movieId = btn.dataset.movieId;
                this.toggleWatchlist(movieId, btn);
            });
        });
    },

    /**
     * Toggle watchlist status via AJAX.
     * @param {number} movieId - Movie ID.
     * @param {HTMLElement} btn - Button element.
     */
    async toggleWatchlist(movieId, btn) {
        try {
            const response = await fetch('/movies/watchlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ movie_id: movieId }),
            });
            const data = await response.json();

            if (data.success) {
                btn.classList.toggle('active', data.is_in_watchlist);
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.className = data.is_in_watchlist
                        ? 'bi bi-bookmark-fill' : 'bi bi-bookmark';
                }
                this.showToast(data.message, 'success');
            }
        } catch (error) {
            this.showToast('Please login to manage watchlist', 'info');
        }
    },

    // ========== SCROLL ANIMATIONS ==========
    setupScrollAnimations() {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('fade-in-up');
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
        );

        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    },

    // ========== TOAST NOTIFICATIONS ==========
    /**
     * Show a toast notification.
     * @param {string} message - Notification message.
     * @param {string} type - Notification type (success, danger, info, warning).
     */
    showToast(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `flash-message ${type}`;
        toast.innerHTML = `
            <i class="bi bi-${this.getToastIcon(type)}"></i>
            <span>${this.escapeHtml(message)}</span>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.transition = 'all 0.3s ease';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    },

    /**
     * Get Bootstrap icon name for toast type.
     * @param {string} type - Toast type.
     * @returns {string} Icon name.
     */
    getToastIcon(type) {
        const icons = {
            success: 'check-circle-fill',
            danger: 'exclamation-circle-fill',
            warning: 'exclamation-triangle-fill',
            info: 'info-circle-fill',
        };
        return icons[type] || 'info-circle-fill';
    },

    // ========== UTILITIES ==========
    /**
     * Escape HTML entities to prevent XSS.
     * @param {string} text - Raw text.
     * @returns {string} Escaped text.
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Load more movies via AJAX (infinite scroll or pagination).
     * @param {string} url - API endpoint.
     * @param {HTMLElement} container - Movies container.
     */
    async loadMoreMovies(url, container) {
        try {
            container.insertAdjacentHTML('beforeend',
                '<div class="col-12 text-center py-3"><div class="spinner-border text-danger" role="status"></div></div>'
            );

            const response = await fetch(url);
            const data = await response.json();

            // Remove spinner
            const spinner = container.querySelector('.spinner-border');
            if (spinner) spinner.closest('.col-12').remove();

            if (data.movies && data.movies.length > 0) {
                data.movies.forEach(movie => {
                    container.insertAdjacentHTML('beforeend',
                        this.createMovieCardHtml(movie)
                    );
                });
            }

            return data;
        } catch (error) {
            console.error('Load more error:', error);
            return null;
        }
    },

    /**
     * Create movie card HTML.
     * @param {Object} movie - Movie data object.
     * @returns {string} HTML string.
     */
    createMovieCardHtml(movie) {
        return `
            <div class="movie-card" data-movie-id="${movie.id}">
                <div class="movie-card-poster">
                    <img src="${movie.poster_url || '/static/images/no-poster.png'}"
                         alt="${this.escapeHtml(movie.title)}"
                         loading="lazy"
                         onerror="this.src='/static/images/no-poster.png'">
                    <div class="movie-card-overlay">
                        <div class="movie-card-actions">
                            <button class="btn-icon btn-favorite" data-movie-id="${movie.id}">
                                <i class="bi bi-heart"></i>
                            </button>
                            <button class="btn-icon btn-watchlist" data-movie-id="${movie.id}">
                                <i class="bi bi-bookmark"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="movie-card-info">
                    <div class="movie-card-title">${this.escapeHtml(movie.title)}</div>
                    <div class="movie-card-meta">
                        <span class="movie-card-rating">
                            <i class="bi bi-star-fill"></i>
                            ${movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A'}
                        </span>
                        <span class="movie-card-year">${movie.year || ''}</span>
                    </div>
                </div>
            </div>
        `;
    },
};

// ---- Initialize on DOM ready ----
document.addEventListener('DOMContentLoaded', () => {
    CineAI.init();
});
