const ClientUI = {
  async dashboard() {
    try {
      const d = await API.get("/api/client/dashboard");
      const nextAssembly = await API.get("/api/client/next-assembly");
      const luckyBlock = d.lucky_number
        ? `<div class="lucky">#${String(d.lucky_number).padStart(4,'0')}</div>`
        : `<p class="muted">Escolha um plano para receber seu número da sorte.</p>`;
      const eligibility = d.eligible_for_assembly
        ? `<span class="badge ok">APTO para assembleia</span>`
        : `<span class="badge warn">INAPTO — pague a mensalidade do mês</span>`;
      Router.app().innerHTML = `
        <div class="card">
          <h2>Olá, ${d.name}!</h2>
          ${eligibility}
        </div>
        <div class="row">
          <div class="card">
            <h3>Seu número da sorte</h3>
            ${luckyBlock}
          </div>
          <div class="card">
            <h3>Saldo virtual</h3>
            <div style="font-size:24px;font-weight:700">R$ ${d.virtual_balance.toFixed(2)}</div>
            <p class="muted">Reservado para sua tatuagem.</p>
          </div>
        </div>
        <div class="row">
          <div class="card">
            <h3>Plano</h3>
            ${d.plan ? `<p><b>${d.plan.name}</b><br/>R$ ${d.plan.monthly_value.toFixed(2)}/mês</p>` : `<p class="muted">Sem plano</p>`}
            <button class="secondary" onclick="Router.go('plans')">Escolher plano</button>
          </div>
          <div class="card">
            <h3>Tatuador</h3>
            ${d.preferred_artist ? `<p><b>${d.preferred_artist.artistic_name}</b><br/>${d.preferred_artist.city}</p>` : `<p class="muted">Sem tatuador</p>`}
            <button class="secondary" onclick="Router.go('artists')">Escolher tatuador</button>
          </div>
        </div>
        <div class="card">
          <h3>Mensalidade do mês</h3>
          <p>${d.current_month_paid ? '<span class="badge ok">PAGA</span>' : '<span class="badge warn">PENDENTE</span>'}</p>
          <p class="muted">No MVP a confirmação é feita pelo admin manualmente.</p>
        </div>

        <div class="card">

          <h3>Próxima assembleia</h3>

          <div style="
            font-size:24px;
            font-weight:bold">

            15/07/2026

          </div>

        </div>

        <div class="card">

          <button
            class="primary"
            onclick="Router.go('transactions')">

            Ver Extrato

          </button>

        </div>
      `;
    } catch (e) { Router.app().innerHTML = `<p class="error">${e.message}</p>`; }
  },

  async plans() {
    const plans = await API.get("/api/plans");
    Router.app().innerHTML = `<h2>Planos disponíveis</h2>` + plans.map(p => `
      <div class="card">
        <h3>${p.name}</h3>
        <p>${p.description}</p>
        <p><b>R$ ${p.monthly_value.toFixed(2)}/mês</b></p>
        <button class="primary" onclick="ClientUI.choosePlan(${p.id})">Escolher</button>
      </div>`).join("");
  },
  async choosePlan(id) {
    try {
      const r = await API.post("/api/client/plan", { plan_id: id });
      alert(`Plano escolhido. Seu número da sorte é #${String(r.lucky_number).padStart(4,'0')}`);
      Router.go("home");
    } catch (e) { alert(e.message); }
  },

  async artists() {
    const artists = await API.get("/api/artists");
    Router.app().innerHTML = `<h2>Tatuadores</h2>` + artists.map(a => `
      <div class="card">
        <img src="${a.avatar_url || '/img/default-avatar.png'}"
            class="artist-avatar">

        <h3>${a.artistic_name}</h3>

        <p class="muted">
          ${a.city}
          ${a.verified ? '✔️ Verificado' : ''}
        </p>

        <p>⭐ ${a.rating.toFixed(1)}</p>

        <p>${a.specialties}</p>

        <button class="primary"
                onclick="ClientUI.chooseArtist(${a.id})">
          Escolher
        </button>
      </div>`).join("");
  },
  async chooseArtist(id) {
    try { await API.post("/api/client/artist", { artist_id: id }); alert("Tatuador escolhido"); Router.go("home"); }
    catch (e) { alert(e.message); }
  },

  async payments() {
    const rows = await API.get("/api/client/payments");
    Router.app().innerHTML = `
      <h2>Histórico de pagamentos</h2>
      <div class="card">
        <table><tr><th>Mês/Ano</th><th>Valor</th><th>Status</th></tr>
          ${rows.map(p => `<tr>
            <td>${String(p.reference_month).padStart(2,'0')}/${p.reference_year}</td>
            <td>R$ ${p.amount.toFixed(2)}</td>
            <td>${p.status}</td>
          </tr>`).join("") || `<tr><td colspan="3" class="muted">Sem pagamentos</td></tr>`}
        </table>
      </div>`;
  },

  async assemblies() {
    const rows = await API.get("/api/client/assemblies");
    Router.app().innerHTML = `<h2>Assembleias</h2>` + (rows.length ? rows.map(a => `
      <div class="card">
        <h3>${String(a.reference_month).padStart(2,'0')}/${a.reference_year}</h3>
        <p>Sorteado: <b>${a.winner_name || '-'}</b> — número #${String(a.winner_lucky_number||0).padStart(4,'0')}</p>
        <p class="muted">${new Date(a.executed_at).toLocaleString('pt-BR')}</p>
      </div>`).join("") : `<div class="card muted">Nenhuma assembleia realizada ainda.</div>`);
  },

  async appointment() {
    const appts = await API.get("/api/client/appointments");
    if (appts.length === 0) {
      Router.app().innerHTML = `
        <h2>Tatuagem</h2>
        <div class="card">
          <p>Se você foi contemplado em uma assembleia, solicite o agendamento abaixo.</p>
          <form id="appt-form">
            <label>Descrição da tatuagem desejada</label>
            <textarea name="description" rows="4" required></textarea>
            <label>Data desejada (opcional)</label>
            <input type="datetime-local" name="scheduled_date"/>
            <button class="primary" type="submit">Solicitar agendamento</button>
          </form>
          <p class="muted" id="appt-msg"></p>
        </div>`;
      document.getElementById("appt-form").addEventListener("submit", async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          await API.post("/api/client/appointments", {
            description: fd.get("description"),
            scheduled_date: fd.get("scheduled_date") || null,
          });
          ClientUI.appointment();
        } catch (err) { document.getElementById("appt-msg").textContent = err.message; }
      });
      return;
    }
    Router.app().innerHTML = `<h2>Tatuagem</h2>` + appts.map(a => `
      <div class="card">
        <h3>${a.artist_name}</h3>
        <p>${a.description}</p>
        <p>Status: <b>${a.status}</b></p>
        ${a.scheduled_date ? `<p>Agendada: ${new Date(a.scheduled_date).toLocaleString('pt-BR')}</p>` : ""}
        ${a.status === "completed"
          ? `<button class="primary" onclick="ClientUI.release(${a.id})">Liberar pagamento ao tatuador</button>`
          : `<p class="muted">A liberação só é permitida após a conclusão.</p>`}
      </div>`).join("");
  },
  async release(id) {
    if (!confirm("Liberar pagamento ao tatuador? Esta ação não pode ser desfeita.")) return;
    try { const r = await API.post(`/api/client/appointments/${id}/release`); alert(`Liberado R$ ${r.released.toFixed(2)}`); ClientUI.appointment(); }
    catch (e) { alert(e.message); }
  },

  async transactions() {

    const rows =
      await API.get("/api/client/transactions");

    Router.app().innerHTML = `
      <h2>Extrato</h2>

      ${rows.map(t => `
        <div class="card">

          <b>${t.description}</b>

          <p>

          ${t.type === "deposit"
            ? "➕"
            : "➖"}

          R$ ${t.amount.toFixed(2)}

          </p>

        </div>
      `).join("")}
    `;
  },
};