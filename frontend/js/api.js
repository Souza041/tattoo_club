const API = {
  token: () => localStorage.getItem("tc_token"),
  role:  () => localStorage.getItem("tc_role"),
  name:  () => localStorage.getItem("tc_name"),

  async request(method, path, body, opts = {}) {
    const headers = { "Accept": "application/json" };
    if (!opts.form) headers["Content-Type"] = "application/json";
    const t = API.token();
    if (t) headers["Authorization"] = "Bearer " + t;
    const r = await fetch(path, {
      method,
      headers,
      body: opts.form ? body : (body ? JSON.stringify(body) : undefined),
    });
    const text = await r.text();

    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { detail: text || r.statusText };
    }

    if (!r.ok) throw new Error(data?.detail || r.statusText);
    return data;
  },
  get:    (p)        => API.request("GET", p),
  post:   (p, b)     => API.request("POST", p, b),
  put:    (p, b)     => API.request("PUT", p, b),
  patch:  (p, b)     => API.request("PATCH", p, b),
  del:    (p)        => API.request("DELETE", p),
  form:   (p, form)  => API.request("POST", p, form, { form: true }),

saveSession(t) {
    localStorage.setItem("tc_token", t.access_token);
    localStorage.setItem("tc_role", t.role);
    localStorage.setItem("tc_name", t.name);
    localStorage.setItem("tc_user_id", t.user_id);
  },
  clearSession() {
    localStorage.clear();
  }
};