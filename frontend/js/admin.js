const AdminUI = {
  async dashboard() {
    const d = await API.get("/api/admin/dashboard");
    Router.app().innerHTML = `
      <h2>Painel admin</h2>
      <div class="row">
        <div class="card kpi">
          <div class="kpi-label">Clientes</div>
          <div class="kpi-value blue">${d.total_clients}</div>
        </div>

        <div class="card kpi">
          <div class="kpi-label">Tatuadores</div>
          <div class="kpi-value blue">${d.total_artists}</div>
        </div>

        <div class="card kpi">
          <div class="kpi-label">Adimplentes no mês</div>
          <div class="kpi-value green">${d.paying_clients}</div>
        </div>

        <div class="card kpi">
          <div class="kpi-label">Inadimplentes</div>
          <div class="kpi-value orange">${d.non_paying_clients}</div>
        </div>
        
        <div class="card kpi">
          <div class="kpi-label">Assembleias realizadas</div>
          <div class="kpi-value orange">${d.assemblies_done}</div>
        </div>
      </div>
      
      <div class="card">
        <h3>Ações rápidas</h3>
        <div class="action-grid">
          <button class="primary" onclick="Router.go('payments')">Registrar pagamento</button>
          <button class="secondary" onclick="Router.go('assemblies')">Executar assembleia</button>
          <button class="secondary" onclick="Router.go('artists')">Gerenciar tatuadores</button>
        </div>
      </div>`;
  },

  async clients() {
    const rows = await API.get("/api/admin/clients");
    Router.app().innerHTML = `<h2>Clientes</h2>
      <div class="card">
        <table><tr><th>#</th><th>Nome</th><th>Plano</th><th>Sorte</th><th>Saldo</th></tr>
          ${rows.map(c => `<tr>
            <td>${c.id}</td><td>${c.name}<br/><span class="muted">${c.email}</span></td>
            <td>${c.plan?.name || '-'}</td>
            <td>${c.lucky_number ? '#'+String(c.lucky_number).padStart(4,'0') : '-'}</td>
            <td>R$ ${c.virtual_balance.toFixed(2)}</td>
          </tr>`).join("") || `<tr><td colspan="5" class="muted">Sem clientes</td></tr>`}
        </table>
      </div>`;
  },

  async artists() {
    const rows = await API.get("/api/admin/artists");
    Router.app().innerHTML = `
      <h2>Tatuadores</h2>
      <div class="card">
        <h3>Novo tatuador</h3>
        <form id="art-form">
          <label>Nome artístico</label><input name="artistic_name" required/>
          <label>Especialidades</label><input name="specialties"/>
          <label>Cidade</label><input name="city"/>
          <label>Instagram</label><input name="instagram"/>
          <label>Bio</label><textarea name="bio"></textarea>
          <hr style="border-color:#2a2a32"/>
          <p class="muted">Criar login (opcional):</p>
          <label>Nome de login</label><input name="name"/>
          <label>E-mail</label><input type="email" name="email"/>
          <label>Senha</label><input type="password" name="password"/>
          <button class="primary" type="submit">Criar</button>
        </form>
      </div>
      <div class="card">
        <table><tr><th>#</th><th>Nome</th><th>Cidade</th><th>Ativo</th><th></th></tr>
        ${rows.map(a => `<tr>
          <td>${a.id}</td><td>${a.artistic_name}</td><td>${a.city}</td>
          <td>${a.active ? 'sim' : 'não'}</td>
          <td><button class="secondary" onclick="AdminUI.deactivateArtist(${a.id})">Desativar</button></td>
        </tr>`).join("")}
        </table>
      </div>`;
    document.getElementById("art-form").addEventListener("submit", async e => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = Object.fromEntries(fd.entries());
      for (const k of ["name","email","password"]) if (!body[k]) delete body[k];
      try { await API.post("/api/admin/artists", body); AdminUI.artists(); }
      catch (err) { alert(err.message); }
    });
  },
  async deactivateArtist(id) {
    if (!confirm("Desativar este tatuador?")) return;
    await API.del(`/api/admin/artists/${id}`); AdminUI.artists();
  },

  async plans() {
    const rows = await API.get("/api/admin/plans");
    Router.app().innerHTML = `
      <h2>Planos</h2>
      <div class="card">
        <h3>Novo plano</h3>
        <form id="plan-form">
          <label>Nome</label><input name="name" required/>
          <label>Valor mensal</label><input name="monthly_value" type="number" step="0.01" required/>
          <label>Descrição</label><textarea name="description"></textarea>
          <button class="primary" type="submit">Criar</button>
        </form>
      </div>
      <div class="card">
        <table><tr><th>#</th><th>Nome</th><th>Valor</th><th>Ativo</th><th></th></tr>
        ${rows.map(p => `<tr>
          <td>${p.id}</td><td>${p.name}</td><td>R$ ${p.monthly_value.toFixed(2)}</td>
          <td>${p.active ? 'sim' : 'não'}</td>
          <td><button class="secondary" onclick="AdminUI.deactivatePlan(${p.id})">Desativar</button></td>
        </tr>`).join("")}
        </table>
      </div>`;
    document.getElementById("plan-form").addEventListener("submit", async e => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await API.post("/api/admin/plans", {
          name: fd.get("name"),
          monthly_value: parseFloat(fd.get("monthly_value")),
          description: fd.get("description") || "",
          active: true,
        });
        AdminUI.plans();
      } catch (err) { alert(err.message); }
    });
  },
  async deactivatePlan(id) {
    if (!confirm("Desativar este plano?")) return;
    await API.del(`/api/admin/plans/${id}`); AdminUI.plans();
  },

  async payments() {
    const clients = await API.get("/api/admin/clients");
    const pays = await API.get("/api/admin/payments");
    const now = new Date();
    Router.app().innerHTML = `
      <h2>Pagamentos</h2>
      <div class="card">
        <h3>Registrar pagamento</h3>
        <form id="pay-form">
          <label>Cliente</label>
          <select name="client_id" required>
            ${clients.map(c => `<option value="${c.id}">${c.name} (${c.plan?.name || 'sem plano'})</option>`).join("")}
          </select>
          <label>Mês</label><input type="number" name="reference_month" min="1" max="12" value="${now.getMonth()+1}" required/>
          <label>Ano</label><input type="number" name="reference_year" value="${now.getFullYear()}" required/>
          <button class="primary" type="submit">Registrar como pago</button>
        </form>
        <p class="muted">Simula confirmação manual. Aumenta o saldo virtual do cliente conforme o plano.</p>
      </div>
      <div class="card">
        <h3>Últimos pagamentos</h3>
        <table><tr><th>#</th><th>Cliente</th><th>Mês/Ano</th><th>Valor</th><th>Status</th></tr>
        ${pays.map(p => {
          const c = clients.find(x => x.id === p.client_id);
          return `<tr>
            <td>${p.id}</td><td>${c?.name || p.client_id}</td>
            <td>${String(p.reference_month).padStart(2,'0')}/${p.reference_year}</td>
            <td>R$ ${p.amount.toFixed(2)}</td><td>${p.status}</td>
          </tr>`;
        }).join("") || `<tr><td colspan="5" class="muted">Sem pagamentos</td></tr>`}
        </table>
      </div>`;
    document.getElementById("pay-form").addEventListener("submit", async e => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await API.post("/api/admin/payments", {
          client_id: parseInt(fd.get("client_id")),
          reference_month: parseInt(fd.get("reference_month")),
          reference_year: parseInt(fd.get("reference_year")),
        });
        AdminUI.payments();
      } catch (err) { alert(err.message); }
    });
  },

  async assemblies() {
    const rows = await API.get("/api/admin/assemblies");
    const now = new Date();
    Router.app().innerHTML = `
      <h2>Assembleias</h2>
      <div class="card">
        <h3>Executar nova assembleia</h3>
        <form id="asm-form">
          <label>Mês</label><input type="number" name="reference_month" min="1" max="12" value="${now.getMonth()+1}" required/>
          <label>Ano</label><input type="number" name="reference_year" value="${now.getFullYear()}" required/>
          <label><input type="checkbox" name="exclude_winners" checked/> Excluir clientes já contemplados</label>
          <button class="primary" type="submit">Sortear agora</button>
        </form>
      </div>
      ${rows.map(a => `
        <div class="card">
          <h3>${String(a.reference_month).padStart(2,'0')}/${a.reference_year}</h3>
          <p>Sorteado: <b>${a.winner_name || '-'}</b> — #${String(a.winner_lucky_number || 0).padStart(4,'0')}</p>
          <p class="muted">${a.participants.length} participantes — ${new Date(a.executed_at).toLocaleString('pt-BR')}</p>
        </div>`).join("")}`;
    document.getElementById("asm-form").addEventListener("submit", async e => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        const r = await API.post("/api/admin/assemblies/execute", {
          reference_month: parseInt(fd.get("reference_month")),
          reference_year: parseInt(fd.get("reference_year")),
          exclude_winners: fd.get("exclude_winners") === "on",
        });
        alert(`Contemplado: ${r.winner_name} (#${String(r.winner_lucky_number).padStart(4,'0')})`);
        AdminUI.assemblies();
      } catch (err) { alert(err.message); }
    });
  },

  async appointments() {
    const rows = await API.get("/api/admin/appointments");
    Router.app().innerHTML = `<h2>Agendamentos</h2>
      <div class="card">
        <table><tr><th>#</th><th>Cliente</th><th>Tatuador</th><th>Status</th><th>Criado em</th></tr>
        ${rows.map(a => `<tr>
          <td>${a.id}</td><td>${a.client_name}</td><td>${a.artist_name}</td>
          <td>${a.status}</td><td>${new Date(a.created_at).toLocaleString('pt-BR')}</td>
        </tr>`).join("") || `<tr><td colspan="5" class="muted">Sem agendamentos</td></tr>`}
        </table>
      </div>`;
  },
};