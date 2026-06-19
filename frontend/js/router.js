const Router = {
  current: "home",
  app: () => document.getElementById("app"),
  nav: () => document.getElementById("bottom-nav"),

  start() { this.go(API.token() ? "home" : "login"); },

  go(view, params={}) {
    this.current = view;
    Auth.renderUserArea();
    if (!API.token() && view !== "login" && view !== "register") {
      this.current = "login";
      this.app().innerHTML = Auth.renderLogin();
      Auth.bindLogin();
      return;
    }
    if (view === "login") {
      this.app().innerHTML = Auth.renderLogin(); Auth.bindLogin(); return;
    }
    if (view === "register") {
      this.app().innerHTML = Auth.renderRegister(); Auth.bindRegister(); return;
    }

    if (view === "home") {
      this.renderNav();
      return this.homeForRole();
    }

    const handler = (this._views[API.role()] || {})[view];

    if (handler) handler(params);
    else this.app().innerHTML = `<div class="card">Tela não encontrada: ${view}</div>`;
    this.renderNav();
  },

  homeForRole() {
    const r = API.role();
    if (r === "client") return ClientUI.dashboard();
    if (r === "tattoo_artist") return ArtistUI.dashboard();
    if (r === "admin") return AdminUI.dashboard();
    this.go("login");
  },

  renderNav() {
    const r = API.role();
    const items = {
      client: [
        ["home", "Início"], ["plans", "Planos"], ["artists", "Tatuadores"],
        ["payments", "Pagamentos"], ["assemblies", "Assembleias"], ["appointment", "Tattoo"],
        ["transactions", "Extrato"],
      ],
      tattoo_artist: [
        ["home", "Início"], ["requests", "Solicitações"],
      ],
      admin: [
        ["home", "Início"], ["clients", "Clientes"], ["artists", "Tatuadores"],
        ["plans", "Planos"], ["payments", "Pagamentos"],
        ["assemblies", "Assembleias"], ["appointments", "Agendamentos"],
      ],
    }[r] || [];
    const nav = this.nav();
    if (!items.length) { nav.classList.add("hidden"); return; }
    nav.classList.remove("hidden");
    nav.innerHTML = items.map(([v, label]) =>
      `<button class="${v===this.current?'active':''}" onclick="Router.go('${v}')">${label}</button>`
    ).join("");
  },

  _views: {
    client: {
      plans:        () => ClientUI.plans(),
      artists:      () => ClientUI.artists(),
      payments:     () => ClientUI.payments(),
      assemblies:   () => ClientUI.assemblies(),
      appointment:  () => ClientUI.appointment(),
      transactions: () => ClientUI.transactions(),
    },
    tattoo_artist: {
      requests:     () => ArtistUI.requests(),
    },
    admin: {
      clients:      () => AdminUI.clients(),
      artists:      () => AdminUI.artists(),
      plans:        () => AdminUI.plans(),
      payments:     () => AdminUI.payments(),
      assemblies:   () => AdminUI.assemblies(),
      appointments: () => AdminUI.appointments(),
    },
  },
};