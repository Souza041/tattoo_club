const ArtistUI = {
  async dashboard() {
    const appts = await API.get("/api/artist/appointments");
    const pend = appts.filter(a => a.status !== "payment_released").length;
    Router.app().innerHTML = `
      <h2>Bem-vindo(a), ${API.name()}</h2>
      <div class="row">
        <div class="card"><h3>Solicitações ativas</h3><div style="font-size:28px;font-weight:700">${pend}</div></div>
        <div class="card"><h3>Total no histórico</h3><div style="font-size:28px;font-weight:700">${appts.length}</div></div>
      </div>
      <div class="card">
        <button class="primary" onclick="Router.go('requests')">Ver solicitações</button>
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
};

