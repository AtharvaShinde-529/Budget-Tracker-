// Thin fetch wrapper. All UI calls go through here.

const API = {
  async _req(method, path, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    if (!res.ok) {
      let msg = res.statusText;
      try { const j = await res.json(); msg = j.detail || j.message || msg; } catch {}
      throw new Error(msg);
    }
    return res.json();
  },

  listCategories:       () => API._req("GET", "/categories"),
  listExpenses:  (field, order, algo) =>
    API._req("GET", `/expenses?field=${field}&order=${order}&algo=${algo}`),
  search:        (from, to, q) => {
    const params = new URLSearchParams();
    if (from) params.set("from_date", from);
    if (to)   params.set("to_date", to);
    if (q)    params.set("q", q);
    return API._req("GET", `/expenses/search?${params.toString()}`);
  },
  create:        (payload) => API._req("POST", "/expenses", payload),
  update:        (id, p)   => API._req("PATCH", `/expenses/${id}`, p),
  del:           (id)      => API._req("DELETE", `/expenses/${id}`),
  undo:          ()        => API._req("POST", "/undo"),
  redo:          ()        => API._req("POST", "/redo"),
  undoRedoStatus:()        => API._req("GET",  "/undo-redo-status"),
  autocomplete:  (q)       => API._req("GET",  `/autocomplete?q=${encodeURIComponent(q)}`),
  registry:      ()        => API._req("GET",  "/registry"),
};
