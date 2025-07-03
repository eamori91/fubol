// Sistema de Gestión de Temas y Funcionalidades Interactivas

class FootballAnalyzerApp {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.favorites = JSON.parse(localStorage.getItem('favorites')) || [];
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.setupLoadingStates();
        this.setupEventListeners();
        this.setupSearchFunctionality();
        this.setupNotifications();
        this.setupAnimations();
        this.setupPWA();
        this.setupMobileNavigation();
        this.setupFavorites();
        this.setupTeamComparator();
        this.loadDashboardData();
        
        // Marcar elementos con loading state
        document.querySelectorAll('.with-loading').forEach(el => {
            el.setAttribute('data-loading', 'true');
        });
    }

    // Sistema de Temas
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.currentTheme = theme;
        
        // Actualizar iconos del toggle
        const sunIcon = document.querySelector('.theme-toggle .fa-sun');
        const moonIcon = document.querySelector('.theme-toggle .fa-moon');
        
        if (theme === 'dark') {
            if (sunIcon) sunIcon.style.opacity = '1';
            if (moonIcon) moonIcon.style.opacity = '0.3';
        } else {
            if (sunIcon) sunIcon.style.opacity = '0.3';
            if (moonIcon) moonIcon.style.opacity = '1';
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        this.showNotification(
            `Tema ${newTheme === 'dark' ? 'oscuro' : 'claro'} activado`,
            'success'
        );
    }

    // Sistema de Loading States
    setupLoadingStates() {
        // Crear un contenedor global para loader overlay
        const loaderOverlay = document.createElement('div');
        loaderOverlay.classList.add('loader-overlay');
        loaderOverlay.innerHTML = `
            <div class="loader-content">
                <div class="loading-spinner-large"></div>
                <p class="loader-message">Cargando...</p>
            </div>
        `;
        document.body.appendChild(loaderOverlay);
        
        // Configurar el API para usar el loading
        this.setupFetchWithLoading();
    }

    setupFetchWithLoading() {
        // Interceptar fetch original para mostrar/ocultar loading
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const [resource, config = {}] = args;
            
            // No mostrar loading para algunas peticiones
            const skipLoadingUrls = [
                '/api/dashboard/stats',
                '/api/teams/trending'
            ];
            
            const shouldShowLoading = !skipLoadingUrls.some(url => resource.includes(url));
            
            // Mostrar loading si es necesario
            if (shouldShowLoading && !config.headers?.['X-No-Loading']) {
                this.showLoading(config.loadingMessage || 'Cargando datos...');
            }
            
            try {
                const response = await originalFetch(resource, config);
                
                // Verificar si el fetch fue exitoso
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`);
                }
                
                // Simular una pequeña latencia para mejor UX con loaders rápidos
                if (shouldShowLoading) {
                    const loadingTime = Math.random() * 300 + 300; // 300-600ms para loaders rápidos
                    await new Promise(resolve => setTimeout(resolve, loadingTime));
                }
                
                return response;
            } catch (error) {
                this.showNotification(error.message, 'error');
                throw error;
            } finally {
                // Ocultar loading si estaba mostrado
                if (shouldShowLoading && !config.headers?.['X-No-Loading']) {
                    this.hideLoading();
                }
            }
        };
    }

    showLoading(message = 'Cargando...') {
        const loader = document.querySelector('.loader-overlay');
        if (loader) {
            loader.querySelector('.loader-message').textContent = message;
            loader.classList.add('active');
            
            // Añadir clase al body para prevenir scroll
            document.body.classList.add('loading-active');
        }
        
        // También activar mini loaders específicos
        document.querySelectorAll('[data-loading]').forEach(el => {
            const container = el;
            const content = container.querySelector('.content-to-load');
            const loader = container.querySelector('.element-loader') || this.createMiniLoader(container);
            
            if (content) content.style.opacity = '0.3';
            if (loader) loader.style.display = 'flex';
        });
    }

    hideLoading() {
        const loader = document.querySelector('.loader-overlay');
        if (loader) {
            loader.classList.remove('active');
            
            // Remover clase del body
            document.body.classList.remove('loading-active');
        }
        
        // También desactivar mini loaders específicos
        document.querySelectorAll('[data-loading]').forEach(el => {
            const container = el;
            const content = container.querySelector('.content-to-load');
            const loader = container.querySelector('.element-loader');
            
            if (content) content.style.opacity = '1';
            if (loader) loader.style.display = 'none';
        });
    }

    createMiniLoader(container) {
        // Crear un mini loader para elementos específicos
        const loader = document.createElement('div');
        loader.classList.add('element-loader');
        loader.innerHTML = '<div class="loading-spinner"></div>';
        container.appendChild(loader);
        return loader;
    }

    // Event Listeners
    setupEventListeners() {
        // Theme toggle
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Búsqueda global
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleGlobalSearch(e.target.value));
            searchInput.addEventListener('focus', () => this.showSearchSuggestions());
        }

        // Widgets interactivos
        document.querySelectorAll('.widget-card').forEach(widget => {
            widget.addEventListener('click', () => this.handleWidgetClick(widget));
        });

        // Botones de acción rápida
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickAction(e.target.dataset.action));
        });
    }

    // Búsqueda Global
    async handleGlobalSearch(query) {
        if (query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        try {
            const response = await fetch(`/api/search/teams?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.showSearchResults(data);
        } catch (error) {
            console.error('Error en búsqueda:', error);
        }
    }

    showSearchResults(results) {
        let suggestionsDiv = document.querySelector('.search-suggestions');
        if (!suggestionsDiv) {
            suggestionsDiv = document.createElement('div');
            suggestionsDiv.className = 'search-suggestions';
            document.querySelector('.search-global').appendChild(suggestionsDiv);
        }

        suggestionsDiv.innerHTML = results.map(team => `
            <div class="suggestion-item" data-team="${team.nombre}">
                <i class="fas fa-futbol"></i>
                <span class="team-name">${team.nombre}</span>
                <span class="team-league">${team.liga || 'Liga Desconocida'}</span>
            </div>
        `).join('');

        suggestionsDiv.style.display = 'block';

        // Event listeners para sugerencias
        suggestionsDiv.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectTeam(item.dataset.team);
                this.hideSearchSuggestions();
            });
        });
    }

    showSearchSuggestions() {
        // Mostrar sugerencias frecuentes
        const suggestions = [
            { nombre: 'Real Madrid', liga: 'La Liga' },
            { nombre: 'Barcelona', liga: 'La Liga' },
            { nombre: 'Manchester United', liga: 'Premier League' },
            { nombre: 'Liverpool', liga: 'Premier League' },
        ];
        this.showSearchResults(suggestions);
    }

    hideSearchSuggestions() {
        const suggestionsDiv = document.querySelector('.search-suggestions');
        if (suggestionsDiv) {
            suggestionsDiv.style.display = 'none';
        }
    }

    selectTeam(teamName) {
        document.querySelector('.search-input').value = teamName;
        this.showNotification(`Equipo seleccionado: ${teamName}`, 'info');
        // Aquí podrías redirigir o cargar datos específicos del equipo
    }

    // Sistema de Notificaciones
    setupNotifications() {
        // Crear contenedor de notificaciones si no existe
        if (!document.querySelector('.notifications-container')) {
            const container = document.createElement('div');
            container.className = 'notifications-container';
            document.body.appendChild(container);
        }
    }

    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        notification.innerHTML = `
            <i class="fas ${icons[type]}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.querySelector('.notifications-container').appendChild(notification);

        // Auto-remove después del tiempo especificado
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }

    // Animaciones
    setupAnimations() {
        // Intersection Observer para animaciones al scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        });

        document.querySelectorAll('.widget-card, .quick-action-card').forEach(el => {
            observer.observe(el);
        });
    }

    // PWA Setup
    setupPWA() {
        // Registrar Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('SW registrado:', registration);
                })
                .catch(error => {
                    console.log('Error al registrar SW:', error);
                });
        }

        // Prompt de instalación
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });
    }

    showInstallPrompt() {
        const installButton = document.createElement('button');
        installButton.className = 'install-prompt btn btn-primary';
        installButton.innerHTML = '<i class="fas fa-download"></i> Instalar App';
        installButton.onclick = () => this.installApp();
        
        document.querySelector('.header-modern .container').appendChild(installButton);
    }

    async installApp() {
        if (!this.deferredPrompt) return;

        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        
        if (outcome === 'accepted') {
            this.showNotification('¡App instalada correctamente!', 'success');
        }
        
        this.deferredPrompt = null;
        document.querySelector('.install-prompt')?.remove();
    }

    // Navegación móvil
    setupMobileNavigation() {
        const menuToggle = document.querySelector('.menu-toggle');
        const mobileMenu = document.querySelector('.mobile-menu');

        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                const isOpen = mobileMenu.classList.toggle('open');
                menuToggle.setAttribute('aria-expanded', isOpen);
            });
        }

        // Cerrar menú al hacer clic en un enlace
        document.querySelectorAll('.mobile-menu a').forEach(link => {
            link.addEventListener('click', () => {
                const mobileMenu = document.querySelector('.mobile-menu');
                mobileMenu.classList.remove('open');
                document.querySelector('.menu-toggle').setAttribute('aria-expanded', 'false');
            });
        });
    }

    // Sistema de Favoritos
    async setupFavorites() {
        this.loadFavoritesFromAPI();
        
        // Event listeners para agregar/quitar favoritos
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-to-favorites') || e.target.closest('.add-to-favorites')) {
                const target = e.target.closest('[data-team]') || e.target;
                const teamName = target.dataset.team;
                const teamId = target.dataset.teamId || Math.floor(Math.random() * 1000); // Simulación
                
                if (teamName) {
                    this.toggleFavorite(teamName, teamId);
                }
            }
            
            if (e.target.classList.contains('favorite-remove')) {
                const teamName = e.target.dataset.team;
                const teamId = e.target.dataset.teamId;
                this.removeFavorite(teamName, teamId);
            }
        });
    }

    async loadFavoritesFromAPI() {
        try {
            const response = await fetch('/api/user/favorites', {
                headers: {
                    'X-No-Loading': 'true' // No mostrar loading
                }
            });
            
            if (response.ok) {
                const favoritesFromAPI = await response.json();
                
                // Actualizar favoritos de localStorage y API
                this.favorites = favoritesFromAPI.map(fav => ({
                    id: fav.id,
                    name: fav.nombre,
                    logo: fav.logo || `/static/img/teams/${fav.nombre.toLowerCase().replace(/\s+/g, '_')}.png`,
                    addedAt: new Date().toISOString()
                }));
                
                this.saveFavorites();
                this.renderFavorites();
            }
        } catch (error) {
            console.error('Error loading favorites:', error);
            // Cargar desde localStorage como fallback
            this.favorites = JSON.parse(localStorage.getItem('favorites')) || [];
            this.renderFavorites();
        }
    }

    async toggleFavorite(teamName, teamId) {
        const index = this.favorites.findIndex(fav => fav.name === teamName);
        
        if (index === -1) {
            await this.addFavorite(teamName, teamId);
        } else {
            await this.removeFavorite(teamName, this.favorites[index].id);
        }
    }

    async addFavorite(teamName, teamId) {
        if (!this.favorites.find(fav => fav.name === teamName)) {
            try {
                const response = await fetch('/api/user/favorites', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        team_id: teamId,
                        team_name: teamName
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    
                    // Añadir a favoritos locales
                    this.favorites.push({
                        id: result.team_id || teamId,
                        name: teamName,
                        addedAt: new Date().toISOString(),
                        logo: `/static/img/teams/${teamName.toLowerCase().replace(/\s+/g, '_')}.png`
                    });
                    
                    this.saveFavorites();
                    this.renderFavorites();
                    this.showNotification(`${teamName} agregado a favoritos`, 'success');
                    
                    // Actualizar botón visual
                    document.querySelectorAll(`[data-team="${teamName}"] .add-to-favorites`).forEach(btn => {
                        btn.classList.add('active');
                        btn.setAttribute('title', 'Quitar de favoritos');
                        btn.innerHTML = '<i class="fas fa-star"></i>';
                    });
                }
            } catch (error) {
                console.error('Error adding favorite:', error);
                this.showNotification('Error al agregar a favoritos', 'error');
            }
        }
    }

    async removeFavorite(teamName, teamId) {
        try {
            const response = await fetch(`/api/user/favorites/${teamId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                // Eliminar de favoritos locales
                this.favorites = this.favorites.filter(fav => fav.name !== teamName);
                
                this.saveFavorites();
                this.renderFavorites();
                this.showNotification(`${teamName} eliminado de favoritos`, 'info');
                
                // Actualizar botón visual
                document.querySelectorAll(`[data-team="${teamName}"] .add-to-favorites`).forEach(btn => {
                    btn.classList.remove('active');
                    btn.setAttribute('title', 'Añadir a favoritos');
                    btn.innerHTML = '<i class="far fa-star"></i>';
                });
            }
        } catch (error) {
            console.error('Error removing favorite:', error);
            this.showNotification('Error al eliminar de favoritos', 'error');
        }
    }

    // Navegación Móvil
    setupMobileNavigation() {
        const hamburgerBtn = document.querySelector('.hamburger-btn');
        const mobileNav = document.querySelector('.mobile-nav');
        const mobileMenuClose = document.querySelector('.mobile-menu-close');
        
        if (hamburgerBtn) {
            hamburgerBtn.addEventListener('click', () => {
                mobileNav?.classList.add('active');
            });
        }

        if (mobileMenuClose) {
            mobileMenuClose.addEventListener('click', () => {
                mobileNav?.classList.remove('active');
            });
        }

        // Cerrar al hacer clic fuera del menú
        if (mobileNav) {
            mobileNav.addEventListener('click', (e) => {
                if (e.target === mobileNav) {
                    mobileNav.classList.remove('active');
                }
            });
        }
    }

    // Comparador de Equipos
    setupTeamComparator() {
        const comparatorContainer = document.querySelector('.team-comparator');
        if (!comparatorContainer) return;

        this.selectedTeams = { team1: null, team2: null };
        
        // Event listeners para selección de equipos
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('team-selector') || e.target.closest('.team-selector')) {
                this.openTeamSelector(e.target.dataset.position || 'team1');
            }
            
            if (e.target.classList.contains('compare-btn')) {
                this.compareTeams();
            }
        });
    }

    async openTeamSelector(position) {
        // Implementar modal de selección de equipos
        const teams = await this.fetchAvailableTeams();
        this.showTeamSelectionModal(teams, position);
    }

    async fetchAvailableTeams() {
        try {
            const response = await fetch('/api/teams');
            return await response.json();
        } catch (error) {
            console.error('Error fetching teams:', error);
            return [];
        }
    }

    showTeamSelectionModal(teams, position) {
        const modal = document.createElement('div');
        modal.className = 'team-selection-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Seleccionar Equipo</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="teams-grid">
                        ${teams.map(team => `
                            <div class="team-option" data-team="${team.nombre}" data-position="${position}">
                                <img src="/static/img/teams/${team.nombre.toLowerCase().replace(/\s+/g, '_')}.png" 
                                     alt="${team.nombre}" onerror="this.src='/static/img/team-default.png'">
                                <span>${team.nombre}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners para el modal
        modal.querySelector('.modal-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
            
            if (e.target.classList.contains('team-option') || e.target.closest('.team-option')) {
                const teamOption = e.target.closest('.team-option');
                const teamName = teamOption.dataset.team;
                const pos = teamOption.dataset.position;
                
                this.selectTeamForComparison(teamName, pos);
                document.body.removeChild(modal);
            }
        });
    }

    selectTeamForComparison(teamName, position) {
        this.selectedTeams[position] = teamName;
        
        const selector = document.querySelector(`[data-position="${position}"]`);
        if (selector) {
            selector.classList.add('selected');
            selector.innerHTML = `
                <img src="/static/img/teams/${teamName.toLowerCase().replace(/\s+/g, '_')}.png" 
                     alt="${teamName}" onerror="this.src='/static/img/team-default.png'">
                <span>${teamName}</span>
            `;
        }

        // Si ambos equipos están seleccionados, habilitar comparación
        if (this.selectedTeams.team1 && this.selectedTeams.team2) {
            const compareBtn = document.querySelector('.compare-btn');
            if (compareBtn) {
                compareBtn.disabled = false;
                compareBtn.textContent = 'Comparar Equipos';
            }
        }
    }

    async compareTeams() {
        if (!this.selectedTeams.team1 || !this.selectedTeams.team2) {
            this.showNotification('Selecciona dos equipos para comparar', 'warning');
            return;
        }

        try {
            this.showLoading('Generando comparación detallada...');
            
            const response = await fetch('/api/analysis/comparative', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    equipo1: this.selectedTeams.team1,
                    equipo2: this.selectedTeams.team2,
                    tipo: 'completo'
                })
            });

            const comparison = await response.json();
            
            // Renderizar comparación
            this.renderTeamComparison(comparison);
            
            // Mostrar opciones para compartir/exportar
            this.showComparisonActions();
            
            // Guardar la comparación en sesión
            this.currentComparison = comparison;
        } catch (error) {
            console.error('Error comparing teams:', error);
            this.showNotification('Error al comparar equipos', 'error');
        }
    }

    showComparisonActions() {
        const actionsContainer = document.querySelector('.comparison-actions');
        if (!actionsContainer) return;
        
        actionsContainer.innerHTML = `
            <div class="action-buttons">
                <button class="btn btn-export" data-format="pdf">
                    <i class="far fa-file-pdf"></i> Exportar PDF
                </button>
                <button class="btn btn-export" data-format="excel">
                    <i class="far fa-file-excel"></i> Exportar Excel
                </button>
                <button class="btn btn-share">
                    <i class="fas fa-share-alt"></i> Compartir
                </button>
            </div>
        `;
        
        // Event listeners
        actionsContainer.querySelector('.btn-share').addEventListener('click', () => {
            this.shareComparison();
        });
        
        actionsContainer.querySelectorAll('.btn-export').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.dataset.format || e.target.closest('[data-format]').dataset.format;
                this.exportComparison(format);
            });
        });
        
        actionsContainer.style.display = 'block';
    }

    async shareComparison() {
        if (!this.currentComparison) return;
        
        try {
            const response = await fetch('/api/compare/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    teams: [this.selectedTeams.team1, this.selectedTeams.team2],
                    analysis_type: 'complete'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Mostrar modal de compartir
                this.showShareModal(result.share_url);
            }
        } catch (error) {
            console.error('Error sharing comparison:', error);
            this.showNotification('Error al compartir la comparación', 'error');
        }
    }

    showShareModal(shareUrl) {
        const modal = document.createElement('div');
        modal.className = 'share-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Compartir Comparación</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Comparte este enlace con quien quieras:</p>
                    <div class="share-link">
                        <input type="text" value="${shareUrl}" readonly>
                        <button class="copy-link" title="Copiar enlace">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                    <div class="share-social">
                        <button class="share-btn twitter" title="Compartir en Twitter">
                            <i class="fab fa-twitter"></i>
                        </button>
                        <button class="share-btn facebook" title="Compartir en Facebook">
                            <i class="fab fa-facebook-f"></i>
                        </button>
                        <button class="share-btn whatsapp" title="Compartir en WhatsApp">
                            <i class="fab fa-whatsapp"></i>
                        </button>
                        <button class="share-btn email" title="Compartir por Email">
                            <i class="fas fa-envelope"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Event listeners
        modal.querySelector('.modal-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.querySelector('.copy-link').addEventListener('click', () => {
            const input = modal.querySelector('input');
            input.select();
            document.execCommand('copy');
            this.showNotification('Enlace copiado al portapapeles', 'success');
        });
        
        // Social sharing
        modal.querySelector('.share-btn.twitter').addEventListener('click', () => {
            window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=Comparación de equipos de fútbol`);
        });
        
        modal.querySelector('.share-btn.facebook').addEventListener('click', () => {
            window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`);
        });
        
        modal.querySelector('.share-btn.whatsapp').addEventListener('click', () => {
            window.open(`https://api.whatsapp.com/send?text=Comparación de equipos: ${encodeURIComponent(shareUrl)}`);
        });
        
        modal.querySelector('.share-btn.email').addEventListener('click', () => {
            window.location.href = `mailto:?subject=Comparación de equipos de fútbol&body=${encodeURIComponent(shareUrl)}`;
        });
    }

    async exportComparison(format) {
        if (!this.currentComparison) return;
        
        try {
            this.showLoading(`Generando archivo ${format.toUpperCase()}...`);
            
            const response = await fetch('/api/data/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    format: format,
                    content_type: 'comparison',
                    data: this.currentComparison
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Simular descarga
                this.showNotification(`Archivo ${format.toUpperCase()} generado correctamente`, 'success');
                
                // Si hay URL de descarga, abrir en nueva ventana/pestaña
                if (result.download_url) {
                    window.open(result.download_url, '_blank');
                }
            }
        } catch (error) {
            console.error(`Error exporting to ${format}:`, error);
            this.showNotification(`Error al exportar a ${format.toUpperCase()}`, 'error');
        }
    }

    // Manejo de widgets
    handleWidgetClick(widget) {
        const widgetType = widget.dataset.widget;
        
        switch (widgetType) {
            case 'predictions':
                window.location.href = '/futuro';
                break;
            case 'historical':
                window.location.href = '/historico';
                break;
            case 'upcoming':
                window.location.href = '/proximo';
                break;
            default:
                this.showNotification('Widget en desarrollo', 'info');
        }
    }

    // Acciones rápidas
    handleQuickAction(action) {
        switch (action) {
            case 'analyze-team':
                this.showTeamAnalysisModal();
                break;
            case 'compare-teams':
                this.showTeamComparisonModal();
                break;
            case 'predict-match':
                this.showMatchPredictionModal();
                break;
            case 'export-data':
                this.exportData();
                break;
            default:
                this.showNotification('Redirigiendo...', 'info');
                window.location.href = '/futuro';
        }
    }

    showTeamAnalysisModal() {
        // Redirigir al análisis histórico
        this.showNotification('Redirigiendo a análisis de equipo...', 'info');
        window.location.href = '/historico';
    }

    showTeamComparisonModal() {
        // Redirigir al comparador de equipos
        this.showNotification('Redirigiendo a comparación de equipos...', 'info');
        window.location.href = '/futuro';
    }

    showMatchPredictionModal() {
        // Redirigir a predicción de partidos
        this.showNotification('Redirigiendo a predicciones...', 'info');
        window.location.href = '/proximo';
    }

    exportData() {
        // Implementar exportación básica de datos simulados
        this.showNotification('Preparando datos para exportar...', 'info');
        
        // Simular datos para exportación
        const data = {
            "predicciones_recientes": [
                {"equipo_local": "Real Madrid", "equipo_visitante": "FC Barcelona", "prediccion": "2-1", "confianza": 67},
                {"equipo_local": "Liverpool", "equipo_visitante": "Manchester City", "prediccion": "1-2", "confianza": 55},
                {"equipo_local": "Bayern Munich", "equipo_visitante": "Borussia Dortmund", "prediccion": "2-2", "confianza": 48}
            ],
            "rendimiento_sistema": {"precision": "84.3%", "partidos_analizados": 1247, "equipos_cubiertos": 156}
        };
        
        // Crear blob para descarga
        const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        
        // Crear link de descarga
        const a = document.createElement('a');
        a.href = url;
        a.download = 'analisis_futbol_export_' + new Date().toISOString().split('T')[0] + '.json';
        document.body.appendChild(a);
        a.click();
        
        // Limpiar
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            this.showNotification('Datos exportados con éxito', 'success');
        }, 100);
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.footballApp = new FootballAnalyzerApp();
});

// Funciones globales para compatibilidad
function toggleTheme() {
    if (window.footballApp) {
        window.footballApp.toggleTheme();
    }
}

function showNotification(message, type = 'info') {
    if (window.footballApp) {
        window.footballApp.showNotification(message, type);
    }
}
