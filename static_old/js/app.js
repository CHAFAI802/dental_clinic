const AUTH_TOKEN_KEY = 'dental_auth_token';
const AUTH_USER_KEY = 'dental_auth_user';
const AUTH_MODULES_KEY = 'dental_auth_modules';

const DentalApp = {
  token: localStorage.getItem(AUTH_TOKEN_KEY),
  user: null,
  modules: [],
  activeModule: null,

  init() {
    this.loadStoredSession();
    this.bindEvents();
    this.render();
    if (this.token) {
      this.refreshSession();
    }
  },

  loadStoredSession() {
    try {
      this.user = JSON.parse(localStorage.getItem(AUTH_USER_KEY) || 'null');
      this.modules = JSON.parse(localStorage.getItem(AUTH_MODULES_KEY) || '[]');
    } catch {
      this.clearSession(false);
    }
  },

  bindEvents() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        this.login();
      });
    }

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => this.logout());
    }

    const modulesGrid = document.getElementById('modules-grid');
    if (modulesGrid) {
      modulesGrid.addEventListener('click', (event) => {
        const card = event.target.closest('[data-module-path]');
        if (card) {
          event.preventDefault();
          this.openModule(card.dataset.modulePath, card.dataset.moduleName);
        }
      });
    }

    const closeViewerBtn = document.getElementById('close-viewer-btn');
    if (closeViewerBtn) {
      closeViewerBtn.addEventListener('click', () => this.closeModuleViewer());
    }
  },

  async apiRequest(path, options = {}) {
    const headers = {
      Accept: 'application/json',
      ...(options.headers || {}),
    };

    if (this.token) {
      headers.Authorization = `Token ${this.token}`;
    }

    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    const response = await fetch(path, { ...options, headers });
    let data = null;

    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      const message = data?.detail || data?.non_field_errors?.[0] || 'Une erreur est survenue.';
      throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
    }

    return data;
  },

  async login() {
    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');
    const submitBtn = document.getElementById('login-submit');
    const errorBox = document.getElementById('login-error');

    errorBox?.classList.add('hidden');

    submitBtn.disabled = true;
    submitBtn.textContent = 'Connexion...';

    try {
      const data = await this.apiRequest('/api/auth/login/', {
        method: 'POST',
        body: {
          email: emailInput.value.trim(),
          password: passwordInput.value,
        },
      });

      this.setSession(data.token, data.user, data.accessible_modules, data.role_label);
      passwordInput.value = '';
      this.render();
    } catch (error) {
      if (errorBox) {
        errorBox.textContent = error.message;
        errorBox.classList.remove('hidden');
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Se connecter';
    }
  },

  async logout() {
    try {
      if (this.token) {
        await this.apiRequest('/api/auth/logout/', { method: 'POST' });
      }
    } catch {
      // Token may already be invalid; clear local session anyway.
    }
    this.clearSession();
    this.render();
  },

  async refreshSession() {
    try {
      const data = await this.apiRequest('/api/auth/me/');
      this.setSession(this.token, data.user, data.accessible_modules, data.role_label);
      this.render();
    } catch {
      this.clearSession();
      this.render();
    }
  },

  setSession(token, user, modules, roleLabel) {
    this.token = token;
    this.user = { ...user, role_label: roleLabel || user.role };
    this.modules = modules || [];

    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(this.user));
    localStorage.setItem(AUTH_MODULES_KEY, JSON.stringify(this.modules));
  },

  clearSession(clearStorage = true) {
    this.token = null;
    this.user = null;
    this.modules = [];
    this.activeModule = null;

    if (clearStorage) {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_USER_KEY);
      localStorage.removeItem(AUTH_MODULES_KEY);
    }
  },

  render() {
    const isAuthenticated = Boolean(this.token && this.user);

    document.getElementById('login-panel')?.classList.toggle('hidden', isAuthenticated);
    document.getElementById('user-panel')?.classList.toggle('hidden', !isAuthenticated);
    document.getElementById('dashboard-section')?.classList.toggle('locked', !isAuthenticated);

    const topbarUser = document.getElementById('topbar-user');
    if (topbarUser) {
      topbarUser.classList.toggle('visible', isAuthenticated);
      if (isAuthenticated) {
        document.getElementById('topbar-user-name').textContent =
          `${this.user.first_name} ${this.user.last_name}`;
        document.getElementById('topbar-user-role').textContent = this.user.role_label || this.user.role;
      }
    }

    if (isAuthenticated) {
      document.getElementById('user-full-name').textContent =
        `${this.user.first_name} ${this.user.last_name}`;
      document.getElementById('user-email').textContent = this.user.email;
      document.getElementById('user-role-badge').textContent = this.user.role_label || this.user.role;
    }

    this.renderModules();
  },

  renderModules() {
    const grid = document.getElementById('modules-grid');
    const lockedMessage = document.getElementById('modules-locked-message');
    if (!grid) return;

    grid.innerHTML = '';

    if (!this.token || !this.user) {
      lockedMessage?.classList.remove('hidden');
      return;
    }

    lockedMessage?.classList.add('hidden');

    if (!this.modules.length) {
      grid.innerHTML = '<p class="empty-state">Aucun module accessible pour votre rôle.</p>';
      return;
    }

    this.modules.forEach((module) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'link-card';
      button.dataset.modulePath = module.path;
      button.dataset.moduleName = module.name;
      button.innerHTML = `
        <strong>${module.name}</strong>
        <span>${module.description}</span>
        <span class="app-tag">${module.app}</span>
      `;
      grid.appendChild(button);
    });
  },

  async openModule(path, name) {
    this.activeModule = { path, name };
    const viewer = document.getElementById('module-viewer');
    const title = document.getElementById('module-viewer-title');
    const body = document.getElementById('module-viewer-body');

    viewer?.classList.add('visible');
    if (title) title.textContent = name;
    if (body) body.innerHTML = '<p class="loading-state">Chargement des données...</p>';

    document.querySelectorAll('[data-module-path]').forEach((el) => {
      el.classList.toggle('active', el.dataset.modulePath === path);
    });

    try {
      const data = await this.apiRequest(path);
      const rows = Array.isArray(data) ? data : data.results || [];
      body.innerHTML = this.renderTable(rows);
    } catch (error) {
      body.innerHTML = `<p class="form-error">${error.message}</p>`;
    }
  },

  closeModuleViewer() {
    this.activeModule = null;
    document.getElementById('module-viewer')?.classList.remove('visible');
    document.querySelectorAll('[data-module-path]').forEach((el) => el.classList.remove('active'));
  },

  renderTable(rows) {
    if (!rows.length) {
      return '<p class="empty-state">Aucun enregistrement trouvé.</p>';
    }

    const columns = Object.keys(rows[0]).slice(0, 6);
    const header = columns.map((col) => `<th>${col}</th>`).join('');
    const body = rows
      .map((row) => {
        const cells = columns
          .map((col) => `<td>${this.formatCell(row[col])}</td>`)
          .join('');
        return `<tr>${cells}</tr>`;
      })
      .join('');

    return `
      <div class="data-table-wrap">
        <table class="data-table">
          <thead><tr>${header}</tr></thead>
          <tbody>${body}</tbody>
        </table>
      </div>
    `;
  },

  formatCell(value) {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  },
};

document.addEventListener('DOMContentLoaded', () => DentalApp.init());
