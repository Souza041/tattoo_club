const ArtistUI = {
  async dashboard() {
    const appts = await API.get("/api/artist/appointments");
    const pend = appts.filter(a => a.status !== "payment_released").length;
    Router.app().innerHTML = `
      <h2>Bem-vindo(a), ${API.name()}</h2>
      <div class="row">
        <div class="card kpi">
          <div class="kpi-label">Solicitações ativas</div>
          <div class="kpi-value blue">${pend}</div>
        </div>

        <div class="card kpi">
          <div class="kpi-label">Total no histórico</div>
          <div class="kpi-value green>${appts.length}</div>
        </div>
      </div>

      <div class="card">
        <h3>Agenda do tatuador</h3>
        <p class="muted">Gerencie horários, sessões e solicitações dos clientes.</p>
        <div class="action-grid">
          <button class="primary" onclick="Router.go('requests')">Ver solicitações</button>
          <button class="secondary" onclick="Router.go('schedule')">Configurar agenda</button>
          <button class="secondary" onclick="Router.go('availability')">Ver horários gerados</button><button class="secondary" onclick="Router.go('availability')">Minha agenda</button>
        </div>
      </div>`;
  },

  async requests() {
    const appts = await API.get("/api/artist/appointments");
    Router.app().innerHTML = `<h2>Solicitações</h2>` + (appts.length ? appts.map(a => `
      <div class="card">
        <h3>${a.client_name}</h3>
        <p>${a.description}</p>
        <p>Status: <b>${a.status}</b></p>
        ${a.scheduled_date ? `<p>Data: ${new Date(a.scheduled_date).toLocaleString('pt-BR')}</p>` : ""}
        <div class="row">
          ${a.status === "requested" ? `<button class="secondary" onclick="ArtistUI.setStatus(${a.id},'scheduled')">Marcar como agendada</button>` : ""}
          ${a.status === "scheduled" ? `<button class="secondary" onclick="ArtistUI.setStatus(${a.id},'in_progress')">Iniciar execução</button>` : ""}
          ${a.status === "in_progress" ? `<button class="primary" onclick="ArtistUI.setStatus(${a.id},'completed')">Concluir</button>` : ""}
          ${a.status === "completed" ? `<p class="muted">Aguardando cliente liberar pagamento.</p>` : ""}
          ${a.status === "payment_released" ? `<span class="badge ok">PAGO</span>` : ""}
        </div>
      </div>`).join("") : `<div class="card muted">Sem solicitações.</div>`);
  },

  async setStatus(id, status) {
    try { await API.patch(`/api/artist/appointments/${id}/status`, { status }); ArtistUI.requests(); }
    catch (e) { alert(e.message); }
  },

  async availability() {
    const rows = await API.get("/api/artist/availability");

    Router.app().innerHTML = `
      <h2>Horários gerados</h2>

      <div class="card">
        <h3>Disponibilidade automática</h3>
        <p class="muted">
          Estes horários são gerados automaticamente a partir da sua agenda semanal.
          Para alterar, vá em <b>Agenda</b> e salve novamente.
        </p>

        <button class="secondary" onclick="Router.go('schedule')">
          Configurar agenda
        </button>
      </div>

      ${rows.length ? rows.map(r => `
        <div class="card session-card">
          <b>${new Date(r.available_at).toLocaleString('pt-BR')}</b>
          <p>
            ${r.is_booked
              ? '<span class="badge warn">Reservado</span>'
              : '<span class="badge ok">Disponível</span>'}
          </p>
        </div>
      `).join("") : `
        <div class="card muted">
          Nenhum horário gerado ainda. Configure sua agenda semanal primeiro.
        </div>
      `}
    `;
  },

  async schedule() {
    const saved = await API.get("/api/artist/schedule");

    const dayNames = [
      "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"
    ];

    const byDay = {};

    saved.forEach(s => {
      byDay[s.weekday] = s;
    });

    Router.app().innerHTML = `
      <h2>Minha agenda</h2>

      <div class="card">
        <h3>Configurar disponibilidade semanal</h3>
        <p class="muted">
          Defina seus dias e horários de trabalho. O sistema vai gerar automaticamente horários disponíveis para os próximos 60 dias.
        </p>

        <form id="schedule-form">

          <div>
            <label>Duração padrão da sessão</label>
            <select name="default_session_hours">
              <option value="2">2 horas</option>
              <option value="3">3 horas</option>               <option value="4">4 horas</option>
              <option value="5">5 horas</option>
              <option value="6">6 horas</option>
              <option value="8">8 horas</option>
            </select>
          </div>

          ${dayNames.map((name, idx) => {
            const row = byDay[idx] || {
              weekday: idx,
              start_hour: idx === 5 ? "09:00" : "09:00",
              end_hour: idx === 5 ? "15:00" : "19:00",
              active: idx < 6
            };

            return `
              <div class="card session-card">
                <label style="display:flex;align-items:center;gap:10px;">
                  <input
                    type="checkbox"
                    name="active_${idx}"
                    ${row.active ? "checked" : ""}
                    style="width:auto;margin:0;"
                  />
                  <b>${name}</b>
                </label>

                <div class="row">
                  <div>
                    <label>Início</label>
                    <select name="start_${idx}">
                      ${ArtistUI.hourOptions(row.start_hour)}
                    </select>
                  </div>

                  <div>
                    <label>Fim</label>
                    <select name="end_${idx}">
                      ${ArtistUI.hourOptions(row.end_hour)}
                    </select>
                  </div>
                </div>
              </div>
            `;
          }).join("")}

          <button class="primary" type="submit">Salvar e gerar horários</button>
        </form>

        <p class="muted" id="schedule-msg"></p>
      </div>
    `;

    document.getElementById("schedule-form").addEventListener("submit", async e => {
      e.preventDefault();

      const fd = new FormData(e.target);
      const defaultSessionHours = parseFloat(fd.get("default_session_hours"));
      const rows = [];

      for (let i = 0; i <= 6; i++) {
        rows.push({
          weekday: i,
          start_hour: fd.get(`start_${i}`),
          end_hour: fd.get(`end_${i}`),
          active: fd.get(`active_${i}`) === "on",
        });
      }

      try {
        await API.post("/api/artist/schedule", {
          default_session_hours: defaultSessionHours,
          schedule: rows,
        });
        document.getElementById("schedule-msg").textContent =
          "Agenda salva e horários gerados com sucesso.";
      } catch (err) {
        document.getElementById("schedule-msg").textContent = err.message;
      }
    });
  },

  hourOptions(selected) {
    const hours = [];

    for (let h = 6; h <= 22; h++) {
      hours.push(`${String(h).padStart(2, "0")}:00`);
    }

    return hours.map(h => `
      <option value="${h}" ${h === selected ? "selected" : ""}>
        ${h}
      </option>
    `).join("");
  },
};

