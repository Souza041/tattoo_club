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
          <div class="card kpi">
            <div class="kpi-label">Número da sorte</div>
            <div class="kpi-value blue">
              ${d.lucky_number ? '#' + String(d.lucky_number).padStart(4,'0') : '--'}
            </div>
            <p class="muted">Usado nas assembleias mensais</p>
          </div>

          <div class="card kpi">
            <div class="kpi-label">Saldo virtual</div>
            <div class="kpi-value green">R$ ${d.virtual_balance.toFixed(2)}</div>
            <p class="muted">Reservado para sua tatuagem</p>
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
          <div style="font-size:24px;font-weight:700">${nextAssembly.label}</div>
          <p>
            ${nextAssembly.eligible
              ? '<span class="badge ok">Você está apto</span>'
              : '<span class="badge warn">Regularize sua mensalidade</span>'}
          </p>
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
        ${a.avatar_url
          ? `<img src="${a.avatar_url}" class="artist-avatar">`
          : `<div class="artist-avatar artist-placeholder">Sem foto</div>`
        }

        <h3>${a.artistic_name}</h3>

        <p class="muted">
          ${a.city}
          ${a.verified ? '✔️ Verificado' : ''}
        </p>

        <p>⭐ ${a.rating.toFixed(1)}</p>

        <p>${a.specialties}</p>

        <div class="portfolio-grid">
          <div class="portfolio-item">Portfólio</div>
          <div class="portfolio-item">Arte</div>
          <div class="portfolio-item">Referência</div>
        </div>

        <button class="primary"
                onclick="ClientUI.chooseArtist(${a.id})">
          Escolher
        </button>
      </div>
    `).join("");
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
    const dash = await API.get("/api/client/dashboard");

    let slots = [];

    if (dash.preferred_artist) {
      slots = await API.get(`/api/artists/${dash.preferred_artist.id}/availability`);
    }
    
    if (appts.length === 0) {
      Router.app().innerHTML = `
        <h2>Tatuagem</h2>
        <div class="card">
          <p>Se você foi contemplado em uma assembleia, solicite o agendamento abaixo.</p>
          <form id="appt-form">
            <label>Descrição da tatuagem desejada</label>
            <textarea name="description" rows="4" required></textarea>

            <label>Quantidade de sessões</label>
            <input type="number" name="total_sessions" min="1" max="10" value="1" required />

            <div id="session-fields"></div>

            <button class="primary" type="submit">Solicitar agendamento</button>
          </form>
          <p class="muted" id="appt-msg"></p>
        </div>`;

      const totalInput = document.querySelector('[name="total_sessions"]');
      const sessionFields = document.getElementById("session-fields");

      async function loadSlots() {
        if (!dash.preferred_artist) return [];

        return await API.get(`/api/artists/${dash.preferred_artist.id}/availability`);
      }

      const dash = await API.get("/api/client/dashboard");
      const slots = await loadSlots();

      function renderSessionFields() {
        const total = parseInt(totalInput.value || "1");

        sessionFields.innerHTML = "";

        for (let i = 1; i <= total; i++) {
          sessionFields.innerHTML += `
            <div class="card session-card">
              <div class="session-number">Sessão ${i}</div>

              <label>Horário disponível</label>
              <select name="session_${i}" required>
                <option value="">Selecione um horário</option>
                ${slots.map(s => `
                  <option value="${s.available_at}">
                    ${new Date(s.available_at).toLocaleString('pt-BR')}
                  </option>
                `).join("")}
              </select>
            </div>
          `;
        }
      }

      totalInput.addEventListener("input", renderSessionFields);
      renderSessionFields();

      document.getElementById("appt-form").addEventListener("submit", async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          const total = parseInt(fd.get("total_sessions"));
          const sessions = [];

          for (let i = 1; i <= total; i++) {
            sessions.push({
              scheduled_start: fd.get(`session_${i}`)
            });
          }

          await API.post("/api/client/appointments", {
            description: fd.get("description"),
            total_sessions: total,
            session_duration_hours: dash.preferred_artist.default_session_hours || 2,
            sessions: sessions,
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
    const rows = await API.get("/api/client/transactions");

    Router.app().innerHTML = `
      <h2>Extrato</h2>

      ${rows.length ? rows.map(t => `
        <div class="card">
          <b>${t.description}</b>
          <p>
            ${t.type === "deposit" ? "➕" : "➖"}
            R$ ${t.amount.toFixed(2)}
          </p>
          <p class="muted">${new Date(t.created_at).toLocaleString('pt-BR')}</p>
        </div>
      `).join("") : `
        <div class="card muted">
          Nenhuma movimentação encontrada ainda.
        </div>
      `}
    `;
  }
};