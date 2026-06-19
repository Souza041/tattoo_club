const Auth = {
  renderLogin() {
    document.getElementById("bottom-nav").classList.add("hidden");
    document.getElementById("user-area").innerHTML = "";
    return `
      <div class="card">
        <h2>Entrar</h2>
        <form id="login-form">
          <label>E-mail</label>
          <input type="email" name="email" required value="admin@tattooclub.com"/>
          <label>Senha</label>
          <input type="password" name="password" required value="admin123"/>
          <button class="primary" type="submit">Entrar</button>
        </form>
        <p class="muted" id="login-msg"></p>
        <hr style="border-color:#2a2a32"/>
        <button class="secondary" onclick="Router.go('register')">Criar conta de cliente</button>
      </div>
      <p class="muted">
        Contas de teste:<br/>
        admin@tattooclub.com / admin123<br/>
        cliente1@tattooclub.com / cliente123<br/>
        marina@tattooclub.com / artist123
      </p>
    `;
  },

  bindLogin() {
    const form = document.getElementById("login-form");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const body = new URLSearchParams();
      body.append("username", fd.get("email"));
      body.append("password", fd.get("password"));
      try {
        const t = await API.form("/api/auth/login", body);
        API.saveSession(t);
        Router.go("home");
      } catch (err) {
        document.getElementById("login-msg").textContent = err.message;
      }
    });
  },

  renderRegister() {
    return `
      <div class="card">
        <h2>Cadastrar cliente</h2>
        <form id="reg-form">
          <label>Nome</label><input name="name" required />
          <label>E-mail</label><input type="email" name="email" required />
          <label>Senha</label><input type="password" name="password" required minlength="6"/>
          <button class="primary" type="submit">Criar conta</button>
        </form>
        <p class="muted" id="reg-msg"></p>
        <button class="secondary" onclick="Router.go('login')">Voltar</button>
      </div>
    `;
  },

  bindRegister() {
    const form = document.getElementById("reg-form");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        const t = await API.post("/api/auth/register", {
          name: fd.get("name"),
          email: fd.get("email"),
          password: fd.get("password"),
          role: "client",
        });
        API.saveSession(t);
        Router.go("home");
      } catch (err) {
        document.getElementById("reg-msg").textContent = err.message;
      }
    });
  },

  renderUserArea() {
    const area = document.getElementById("user-area");
    if (!API.token()) { area.innerHTML = ""; return; }
    area.innerHTML = `${API.name()} (${API.role()}) <button onclick="Auth.logout()">Sair</button>`;
  },

  logout() {
    API.clearSession();
    Router.go("login");
  }
};