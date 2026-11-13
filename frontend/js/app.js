// UI wiring: page routing, table rendering, add/edit modal, autocomplete, undo/redo.

const state = {
  categories: [],
  currentPage: "dashboard",
  allRows: [],
};

// ---------- helpers ----------

function rupeesFromPaise(p) {
  return "₹" + (p / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

function paiseFromRupees(r) {
  return Math.round(parseFloat(r) * 100);
}

function fmtDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

function toast(msg, kind = "success") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast ${kind}`;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.add("hidden"), 2500);
}

// ---------- routing ----------

function showPage(name) {
  state.currentPage = name;
  document.querySelectorAll(".page").forEach(p => p.classList.add("hidden"));
  document.getElementById(name).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach(b =>
    b.classList.toggle("active", b.dataset.page === name)
  );
  const titles = {
    dashboard: "Dashboard",
    expenses: "Expenses",
    analytics: "Analytics",
    benchmark: "Benchmark lab",
    registry: "Algorithms",
  };
  document.getElementById("page-title").textContent = titles[name] || name;

  if (name === "dashboard") loadDashboard();
  if (name === "expenses")  loadExpenses();
  if (name === "registry")  loadRegistry();
}

// ---------- dashboard ----------

async function loadDashboard() {
  try {
    const { rows } = await API.listExpenses("date", "desc", "merge_sort");
    state.allRows = rows;

    const now = new Date();
    const thisMonth = now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0");
    const monthRows = rows.filter(r => r.date.startsWith(thisMonth));
    const monthTotal = monthRows.reduce((s, r) => s + r.amount_paise, 0);
    const allTotal = rows.reduce((s, r) => s + r.amount_paise, 0);

    document.getElementById("stat-month").textContent = rupeesFromPaise(monthTotal);
    document.getElementById("stat-month-sub").textContent =
      `${monthRows.length} expense${monthRows.length === 1 ? "" : "s"} this month`;
    document.getElementById("stat-count").textContent = rows.length.toLocaleString("en-IN");
    document.getElementById("stat-avg").textContent =
      rows.length ? rupeesFromPaise(Math.round(allTotal / rows.length)) : "—";

    // Top category
    const byCat = {};
    for (const r of rows) byCat[r.category_name] = (byCat[r.category_name] || 0) + r.amount_paise;
    let topCat = null, topVal = -1;
    for (const [cat, val] of Object.entries(byCat)) {
      if (val > topVal) { topCat = cat; topVal = val; }
    }
    document.getElementById("stat-top-cat").textContent = topCat || "—";
    document.getElementById("stat-top-cat-sub").textContent = topCat
      ? `${rupeesFromPaise(topVal)} total` : "by total amount";

    // Recent 8
    renderTable(
      document.getElementById("recent-table"),
      rows.slice(0, 8),
      { showActions: false }
    );
  } catch (e) {
    toast(`Dashboard failed: ${e.message}`, "error");
  }
}

// ---------- expenses table ----------

async function loadExpenses() {
  const field = document.getElementById("sort-field").value;
  const order = document.getElementById("sort-order").value;
  const algo  = document.getElementById("sort-algo").value;
  try {
    const { rows, stats } = await API.listExpenses(field, order, algo);
    state.allRows = rows;

    document.getElementById("sort-stats").textContent =
      `${stats.algorithm} · ${stats.comparisons} comparisons · ${stats.swaps} swaps · ` +
      `depth ${stats.max_depth} · field=${field} order=${order}`;

    // client-side keyword filter for the search box (full range search is /expenses/search)
    const kw = document.getElementById("search-input").value.trim().toLowerCase();
    const filtered = kw
      ? rows.filter(r =>
          r.description.toLowerCase().includes(kw) ||
          r.category_name.toLowerCase().includes(kw))
      : rows;

    renderTable(
      document.getElementById("expenses-table"),
      filtered,
      { showActions: true }
    );
  } catch (e) {
    toast(`Load failed: ${e.message}`, "error");
  }
}

function renderTable(container, rows, { showActions }) {
  if (!rows.length) {
    container.innerHTML = `<p class="muted" style="padding:12px">No expenses.</p>`;
    return;
  }
  const head = `
    <tr>
      <th>Date</th>
      <th>Description</th>
      <th>Category</th>
      <th>Mode</th>
      <th style="text-align:right">Amount</th>
      ${showActions ? "<th></th>" : ""}
    </tr>`;
  const body = rows.map(r => {
    const isBig = r.amount_paise >= 500000; // ₹5,000+
    return `
      <tr data-id="${r.id}">
        <td>${fmtDate(r.date)}</td>
        <td>${escapeHtml(r.description) || "<span class='muted'>—</span>"}</td>
        <td><span class="badge" style="border-left:3px solid ${r.category_color}">${escapeHtml(r.category_name)}</span></td>
        <td><span class="badge badge-mode">${r.payment_mode}</span></td>
        <td class="amount ${isBig ? "big" : "pos"}">${rupeesFromPaise(r.amount_paise)}</td>
        ${showActions ? `
          <td>
            <div class="row-actions">
              <button class="edit" data-id="${r.id}" title="Edit">✎</button>
              <button class="del" data-id="${r.id}" title="Delete">✕</button>
            </div>
          </td>` : ""}
      </tr>`;
  }).join("");
  container.innerHTML = `<table class="data-table"><thead>${head}</thead><tbody>${body}</tbody></table>`;

  if (showActions) {
    container.querySelectorAll(".edit").forEach(btn =>
      btn.addEventListener("click", () => openEditModal(Number(btn.dataset.id)))
    );
    container.querySelectorAll(".del").forEach(btn =>
      btn.addEventListener("click", () => deleteExpense(Number(btn.dataset.id)))
    );
  }
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// ---------- add / edit modal ----------

function openAddModal() {
  document.getElementById("modal-title").textContent = "Add expense";
  document.getElementById("f-id").value = "";
  document.getElementById("f-amount").value = "";
  document.getElementById("f-date").value = new Date().toISOString().slice(0, 10);
  document.getElementById("f-category").value = state.categories[0]?.id ?? "";
  document.getElementById("f-description").value = "";
  document.getElementById("f-mode").value = "upi";
  document.getElementById("modal-backdrop").classList.remove("hidden");
  document.getElementById("f-amount").focus();
}

function openEditModal(id) {
  const row = state.allRows.find(r => r.id === id);
  if (!row) return;
  document.getElementById("modal-title").textContent = "Edit expense";
  document.getElementById("f-id").value = row.id;
  document.getElementById("f-amount").value = (row.amount_paise / 100).toFixed(2);
  document.getElementById("f-date").value = row.date;
  document.getElementById("f-category").value = row.category_id;
  document.getElementById("f-description").value = row.description;
  document.getElementById("f-mode").value = row.payment_mode;
  document.getElementById("modal-backdrop").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("modal-backdrop").classList.add("hidden");
}

async function submitExpense(ev) {
  ev.preventDefault();
  const id = document.getElementById("f-id").value;
  const payload = {
    amount_paise: paiseFromRupees(document.getElementById("f-amount").value),
    date:         document.getElementById("f-date").value,
    category_id:  Number(document.getElementById("f-category").value),
    description:  document.getElementById("f-description").value.trim(),
    payment_mode: document.getElementById("f-mode").value,
  };
  try {
    if (id) {
      await API.update(Number(id), payload);
      toast("Expense updated", "success");
    } else {
      await API.create(payload);
      toast("Expense added", "success");
    }
    closeModal();
    refreshUndoRedo();
    if (state.currentPage === "expenses")  loadExpenses();
    if (state.currentPage === "dashboard") loadDashboard();
  } catch (e) {
    toast(`Save failed: ${e.message}`, "error");
  }
}

async function deleteExpense(id) {
  if (!confirm("Delete this expense?")) return;
  try {
    await API.del(id);
    toast("Expense deleted", "success");
    refreshUndoRedo();
    if (state.currentPage === "expenses")  loadExpenses();
    if (state.currentPage === "dashboard") loadDashboard();
  } catch (e) {
    toast(`Delete failed: ${e.message}`, "error");
  }
}

// ---------- autocomplete ----------

async function onDescriptionInput(ev) {
  const q = ev.target.value.trim();
  const list = document.getElementById("autocomplete-suggestions");
  if (q.length < 2) { list.innerHTML = ""; return; }
  try {
    const { suggestions } = await API.autocomplete(q);
    list.innerHTML = suggestions.map(s =>
      `<div data-v="${escapeHtml(s)}">${escapeHtml(s)}</div>`
    ).join("");
    list.querySelectorAll("div").forEach(d =>
      d.addEventListener("click", () => {
        document.getElementById("f-description").value = d.dataset.v;
        list.innerHTML = "";
      })
    );
  } catch { list.innerHTML = ""; }
}

// ---------- undo / redo ----------

async function refreshUndoRedo() {
  try {
    const s = await API.undoRedoStatus();
    document.getElementById("undo-btn").disabled = !s.undo_available;
    document.getElementById("redo-btn").disabled = !s.redo_available;
  } catch {}
}

async function doUndo() {
  try { await API.undo(); toast("Undone", "success"); refreshUndoRedo();
        if (state.currentPage === "expenses")  loadExpenses();
        if (state.currentPage === "dashboard") loadDashboard();
  } catch (e) { toast(e.message, "error"); }
}

async function doRedo() {
  try { await API.redo(); toast("Redone", "success"); refreshUndoRedo();
        if (state.currentPage === "expenses")  loadExpenses();
        if (state.currentPage === "dashboard") loadDashboard();
  } catch (e) { toast(e.message, "error"); }
}

// ---------- registry ----------

async function loadRegistry() {
  try {
    const reg = await API.registry();
    const html = Object.entries(reg).map(([name, meta]) => `
      <div class="registry-card">
        <h3>${name}<span class="unit">Unit ${meta.unit}</span></h3>
        <p>${escapeHtml(meta.paradigm)} · ${escapeHtml(meta.how)}</p>
        <div class="complexity">
          <span>avg ${meta.complexity.average}</span>
          <span>worst ${meta.complexity.worst}</span>
          <span>space ${meta.complexity.space}</span>
        </div>
        <p style="margin-top:6px;color:#8a93a6">→ ${escapeHtml(meta.feature)}</p>
      </div>`).join("");
    document.getElementById("registry-body").innerHTML = `<div class="registry-grid">${html}</div>`;
  } catch (e) {
    toast(e.message, "error");
  }
}

// ---------- boot ----------

async function boot() {
  try {
    state.categories = await API.listCategories();
    const sel = document.getElementById("f-category");
    sel.innerHTML = state.categories
      .map(c => `<option value="${c.id}">${c.name}</option>`).join("");
  } catch (e) {
    toast(`Failed to load categories: ${e.message}`, "error");
  }

  // nav
  document.querySelectorAll(".nav-item").forEach(btn =>
    btn.addEventListener("click", () => showPage(btn.dataset.page))
  );

  // undo/redo
  document.getElementById("undo-btn").addEventListener("click", doUndo);
  document.getElementById("redo-btn").addEventListener("click", doRedo);

  // add button
  document.getElementById("add-btn").addEventListener("click", openAddModal);

  // modal
  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal-cancel").addEventListener("click", closeModal);
  document.getElementById("expense-form").addEventListener("submit", submitExpense);
  document.getElementById("modal-backdrop").addEventListener("click", (e) => {
    if (e.target.id === "modal-backdrop") closeModal();
  });

  // autocomplete
  document.getElementById("f-description").addEventListener("input", onDescriptionInput);

  // expense page controls
  ["sort-field", "sort-order", "sort-algo"].forEach(id =>
    document.getElementById(id).addEventListener("change", loadExpenses)
  );
  document.getElementById("search-input").addEventListener("input", () => loadExpenses());

  // keyboard shortcuts
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) { e.preventDefault(); doUndo(); }
    if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.shiftKey && e.key === "Z"))) { e.preventDefault(); doRedo(); }
  });

  refreshUndoRedo();
  showPage("dashboard");
}

document.addEventListener("DOMContentLoaded", boot);
