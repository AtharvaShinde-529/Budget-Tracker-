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
  if (name === "analytics") loadAnalytics();
  if (name === "optimiser") loadOptimiser();
  if (name === "lab") loadLab();
  if (name === "coverage") loadCoverage();
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

  // sort-field: hide non-comparison sorts (counting/radix) for non-amount fields
  document.getElementById("sort-field").addEventListener("change", () => {
    const field = document.getElementById("sort-field").value;
    const algoSel = document.getElementById("sort-algo");
    Array.from(algoSel.options).forEach(opt => {
      if (opt.value === "counting_sort" || opt.value === "radix_sort") {
        opt.disabled = (field !== "amount_paise");
        opt.style.display = (field !== "amount_paise") ? "none" : "";
      }
    });
    if ((algoSel.value === "counting_sort" || algoSel.value === "radix_sort")
        && field !== "amount_paise") {
      algoSel.value = "merge_sort";
    }
    loadExpenses();
  });
  // generic change handlers for order + algo
  ["sort-order", "sort-algo"].forEach(id =>
    document.getElementById(id).addEventListener("change", loadExpenses)
  );
  document.getElementById("search-input").addEventListener("input", () => loadExpenses());

  // optimiser controls
  document.getElementById("run-goals").addEventListener("click", loadOptimiser);
  document.getElementById("adv-run").addEventListener("click", runAdversary);
  document.getElementById("mt-run").addEventListener("click", runMasterTheorem);
  document.getElementById("run-change").addEventListener("click", loadOptimiser);

  // keyboard shortcuts
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) { e.preventDefault(); doUndo(); }
    if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.shiftKey && e.key === "Z"))) { e.preventDefault(); doRedo(); }
  });

  refreshUndoRedo();
  showPage("dashboard");
}

document.addEventListener("DOMContentLoaded", boot);

// ---------- analytics page ----------

let categoryChart = null;

async function loadAnalytics() {
  try {
    const [med, p90, streak, dom, outlierRes, dupRes, invRes, cats] = await Promise.all([
      fetch("/analytics/median").then(r => r.json()),
      fetch("/analytics/percentile?p=90").then(r => r.json()),
      fetch("/analytics/streak").then(r => r.json()),
      fetch("/analytics/dominant-category").then(r => r.json()),
      fetch("/analytics/outliers").then(r => r.json()),
      fetch("/analytics/duplicates").then(r => r.json()),
      fetch("/analytics/inversions").then(r => r.json()),
      fetch("/analytics/category-totals").then(r => r.json()),
    ]);

    document.getElementById("an-median").textContent = rupeesFromPaise(med.median_paise || 0);
    document.getElementById("an-median-sub").textContent =
      `${med.stats?.comparisons ?? 0} comparisons · ${med.stats?.calls ?? 0} partition passes`;
    document.getElementById("an-p90").textContent = rupeesFromPaise(p90.value_paise || 0);

    if (streak.start && streak.end) {
      document.getElementById("an-streak").textContent = rupeesFromPaise(streak.sum_paise);
      document.getElementById("an-streak-sub").textContent =
        `${streak.start} → ${streak.end} (${streak.window_days} days)`;
    } else {
      document.getElementById("an-streak").textContent = "—";
      document.getElementById("an-streak-sub").textContent = "no data";
    }

    if (dom.category) {
      document.getElementById("an-dominant").textContent = dom.category;
      const pct = ((dom.count / dom.total) * 100).toFixed(0);
      document.getElementById("an-dominant").nextElementSibling.textContent =
        `${dom.count}/${dom.total} transactions (${pct}%)` + (dom.strict_majority ? " · strict majority" : "");
    }

    // Outliers
    const ol = outlierRes.outliers || [];
    if (ol.length) {
      document.getElementById("outliers-table").innerHTML = renderSimpleTable(
        ["Date", "Description", "Category", "Amount"],
        ol.map(r => [
          fmtDate(r.date),
          escapeHtml(r.description),
          escapeHtml(r.category_name),
          `<span class="amount big">${rupeesFromPaise(r.amount_paise)}</span>`,
        ])
      );
    } else {
      document.getElementById("outliers-table").innerHTML =
        `<p class="muted">None outside the fences.</p>`;
    }

    // Duplicates
    const dups = dupRes.duplicates || [];
    if (dups.length === 2) {
      document.getElementById("duplicates-table").innerHTML = renderSimpleTable(
        ["Date", "Description", "Category", "Amount"],
        dups.map(r => [
          fmtDate(r.date),
          escapeHtml(r.description),
          escapeHtml(r.category_name),
          rupeesFromPaise(r.amount_paise),
        ])
      );
    } else {
      document.getElementById("duplicates-table").innerHTML =
        `<p class="muted">No suspiciously close pairs.</p>`;
    }

    // Inversions
    document.getElementById("inversions-text").textContent =
      invRes.inversions === 0 || !invRes.prev_month
        ? "Not enough history (need 2 months of data)."
        : `${invRes.inversions} inversions between ${invRes.prev_month} and ${invRes.this_month} rankings. ` +
          `0 = no change in ordering; larger numbers mean category spend rankings shuffled.`;

    // Chart
    const labels = cats.map(c => c.category);
    const totals = cats.map(c => c.total_paise / 100);
    const colors = cats.map(c => c.color || "#6366f1");
    const ctx = document.getElementById("category-chart");
    if (categoryChart) categoryChart.destroy();
    categoryChart = new Chart(ctx, {
      type: "bar",
      data: { labels, datasets: [{ label: "Total (₹)", data: totals, backgroundColor: colors }] },
      options: {
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#8a93a6" }, grid: { color: "#2a3040" } },
          y: { ticks: { color: "#e6e9f0" }, grid: { display: false } },
        },
      },
    });
  } catch (e) {
    toast(`Analytics failed: ${e.message}`, "error");
  }
}

function renderSimpleTable(headers, rows) {
  const h = `<tr>${headers.map(x => `<th>${x}</th>`).join("")}</tr>`;
  const b = rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join("")}</tr>`).join("");
  return `<table class="data-table"><thead>${h}</thead><tbody>${b}</tbody></table>`;
}



// ---------- optimiser page ----------

function _rupees(paise) {
  return "₹" + (paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

async function loadOptimiser() {
  // Goal funding — run with current savings input
  try {
    const amount = parseInt(document.getElementById("savings-input").value || "8000", 10) * 100;
    const res = await fetch("/optimize/goals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ monthly_savings_paise: amount }),
    }).then(r => r.json());

    const rows = res.picked.map(p => `
      <tr>
        <td>${escapeHtml(p.name)}</td>
        <td class="amount">${_rupees(p.weight_taken_paise)}</td>
        <td>${p.fraction === 1 ? "fully funded" : `${Math.round(p.fraction * 100)}% funded`}</td>
        <td class="amount">${p.value_taken.toFixed(2)}</td>
      </tr>`).join("");
    document.getElementById("goals-result").innerHTML = `
      <p class="muted">Total value: <strong>${res.total_value}</strong> · Spent: <strong>${_rupees(res.total_spent_paise)}</strong> of ${_rupees(res.monthly_savings_paise)}
        · ${res.stats.comparisons} comparisons</p>
      <table class="data-table">
        <thead><tr><th>Goal</th><th class="amount">Cost</th><th>Status</th><th class="amount">Value</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  } catch (e) { toast(`Goals: ${e.message}`, "error"); }

  // Bills
  try {
    const res = await fetch("/optimize/bills").then(r => r.json());
    const rows = res.scheduled.map(s => `
      <tr>
        <td>Day ${s.slot}</td>
        <td>${escapeHtml(s.name)}</td>
        <td class="amount">${_rupees(s.penalty_paise)}</td>
      </tr>`).join("");
    const skipped = res.skipped.map(s =>
      `<span class="badge" style="border-color:var(--danger);color:#fca5a5">${escapeHtml(s.name)}</span>`
    ).join(" ");
    document.getElementById("bills-result").innerHTML = `
      <p class="muted">Penalty avoided: <strong>${_rupees(res.penalty_saved_paise)}</strong> of ${_rupees(res.penalty_possible_paise)}
        · ${res.stats.comparisons} comparisons</p>
      <table class="data-table">
        <thead><tr><th>Slot</th><th>Bill</th><th class="amount">Penalty</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      ${skipped ? `<p class="muted" style="margin-top:8px">Skipped (no free slot): ${skipped}</p>` : ""}`;
  } catch (e) { toast(`Bills: ${e.message}`, "error"); }

  // Cash breakdown
  try {
    const amountRupees = parseFloat(document.getElementById("change-input").value || "1237");
    const amountPaise = Math.round(amountRupees * 100);
    const res = await fetch("/optimize/change", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount_paise: amountPaise }),
    }).then(r => r.json());

    const chips = res.breakdown.map(b => {
      const label = b.denomination_rupees >= 1
        ? `₹${b.denomination_rupees}`
        : `${b.denomination_paise}p`;
      return `<div class="denom-chip"><span class="denom-label">${label}</span> × <strong>${b.count}</strong></div>`;
    }).join("");
    document.getElementById("change-result").innerHTML = `
      <p class="muted">${res.breakdown.length} denominations · ${res.matches_input ? "✓ reconstructs exactly" : "✗ mismatch"}</p>
      <div class="denom-row">${chips}</div>`;
  } catch (e) { toast(`Change: ${e.message}`, "error"); }

  // Shifts
  try {
    const res = await fetch("/optimize/shifts").then(r => r.json());
    const rows = res.selected.map(s => `
      <tr><td>${escapeHtml(s.name)}</td><td>${s.start}:00</td><td>${s.end}:00</td>
      <td class="amount">${s.end - s.start}h</td></tr>`).join("");
    document.getElementById("shifts-result").innerHTML = `
      <p class="muted">${res.selected.length} of ${res.all_shifts.length} shifts · total ${res.total_hours} hours</p>
      <table class="data-table">
        <thead><tr><th>Shift</th><th>Start</th><th>End</th><th class="amount">Hours</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  } catch (e) { toast(`Shifts: ${e.message}`, "error"); }

  // Settlement
  try {
    const res = await fetch("/settle").then(r => r.json());
    const rows = res.transactions.map(t =>
      `<tr><td>${escapeHtml(t.from)}</td><td>→</td><td>${escapeHtml(t.to)}</td>
      <td class="amount pos">${_rupees(t.amount_paise)}</td></tr>`).join("");
    document.getElementById("settle-result").innerHTML = `
      <p class="muted">${res.transaction_count} transactions to settle ${_rupees(res.total_money_moved_paise)}</p>
      <table class="data-table">
        <thead><tr><th>From</th><th></th><th>To</th><th class="amount">Amount</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  } catch (e) { toast(`Settle: ${e.message}`, "error"); }

  // Huffman
  try {
    const res = await fetch("/compress/huffman").then(r => r.json());
    if (res.error) {
      document.getElementById("huffman-result").innerHTML = `<p class="muted">${escapeHtml(res.error)}</p>`;
    } else {
      const pct = (res.compression_ratio * 100).toFixed(1);
      const top = res.top_codes.map(c =>
        `<tr><td><code>${c.char}</code></td><td><code>${c.code}</code></td>
        <td class="amount">${c.freq}</td><td class="amount">${c.bits}</td></tr>`).join("");
      document.getElementById("huffman-result").innerHTML = `
        <p class="muted">${res.original_chars} chars → ${res.compressed_bits} bits (${pct}% of 8-bit baseline) · ${res.unique_chars} unique chars · prefix-free: ${res.prefix_free}</p>
        <table class="data-table">
          <thead><tr><th>Char</th><th>Code</th><th class="amount">Freq</th><th class="amount">Bits</th></tr></thead>
          <tbody>${top}</tbody>
        </table>`;
    }
  } catch (e) { toast(`Huffman: ${e.message}`, "error"); }
}




// ---------- theory lab ----------

async function runAdversary() {
  const n = parseInt(document.getElementById("adv-n").value, 10) || 4;
  try {
    const res = await fetch(`/lab/adversary?n=${n}`).then(r => r.json());
    document.getElementById("adversary-result").innerHTML = `
      <table class="data-table">
        <tbody>
          <tr><td>Permutations enumerated</td><td class="amount">${res.permutation_count}</td></tr>
          <tr><td>n!</td><td class="amount">${res.n_factorial.toLocaleString()}</td></tr>
          <tr><td>log₂(n!)</td><td class="amount">${res.log2_n_factorial}</td></tr>
          <tr><td><strong>Lower bound ⌈log₂(n!)⌉</strong></td><td class="amount"><strong>${res.lower_bound_ceil}</strong></td></tr>
          <tr><td>merge_sort min comparisons</td><td class="amount">${res.min_comparisons}</td></tr>
          <tr><td>merge_sort mean comparisons</td><td class="amount">${res.mean_comparisons}</td></tr>
          <tr><td>merge_sort max comparisons</td><td class="amount">${res.max_comparisons}</td></tr>
          <tr><td>Ratio (mean / bound)</td><td class="amount">${res.ratio_mean_over_bound}</td></tr>
        </tbody>
      </table>
      <p class="muted" style="margin-top:10px">Interpretation: any comparison sort must make at least ${res.lower_bound_ceil} comparisons in the worst case (because it needs to distinguish all ${res.n_factorial.toLocaleString()} permutations). merge_sort's worst case is ${res.max_comparisons} — close to optimal.</p>`;
  } catch (e) {
    toast(`Adversary: ${e.message}`, "error");
  }
}

async function runMasterTheorem() {
  const a = parseFloat(document.getElementById("mt-a").value) || 2;
  const b = parseFloat(document.getElementById("mt-b").value) || 2;
  const d = parseFloat(document.getElementById("mt-d").value) || 1;
  try {
    const res = await fetch(`/lab/master-theorem?a=${a}&b=${b}&d=${d}`).then(r => r.json());
    document.getElementById("mt-result").innerHTML = `
      <div class="card" style="margin-top:14px">
        <div class="card-label">T(n) = ${a}·T(n/${b}) + Θ(n^${d})</div>
        <div class="card-value" style="color:var(--accent-hover);font-size:22px">${res.teta}</div>
        <div class="card-sub">Case ${res.case} · log_b(a) = ${res.log_b_a}</div>
      </div>
      <p class="muted" style="margin-top:10px">${res.explanation}</p>`;
  } catch (e) {
    toast(`Master theorem: ${e.message}`, "error");
  }
}

async function loadPresets() {
  try {
    const presets = await fetch("/lab/presets").then(r => r.json());
    document.getElementById("mt-presets").innerHTML = `
      <div class="denom-row" style="margin-top:8px;margin-bottom:10px">
        ${presets.map(p => `<button class="denom-chip" data-a="${p.a}" data-b="${p.b}" data-d="${p.d}">
          <span class="denom-label">${p.name}</span> ${p.formula}
        </button>`).join("")}
      </div>`;
    document.querySelectorAll("#mt-presets .denom-chip").forEach(btn => {
      btn.addEventListener("click", () => {
        document.getElementById("mt-a").value = btn.dataset.a;
        document.getElementById("mt-b").value = btn.dataset.b;
        document.getElementById("mt-d").value = btn.dataset.d;
        runMasterTheorem();
      });
    });
  } catch {}
}

function loadLab() {
  loadPresets().then(() => {
    runAdversary();
    runMasterTheorem();
  });
}

// ---------- coverage page ----------

async function loadCoverage() {
  try {
    const res = await fetch("/coverage").then(r => r.json());
    const s = res.summary;
    document.getElementById("coverage-summary").textContent =
      `${s.implemented}/${s.total} implemented · ${s.partial} partial · ${s.stub} stub · ${s.completion_pct}% complete`;

    const byUnit = {};
    for (const r of res.rows) byUnit[r.unit] = (byUnit[r.unit] || []).concat(r);

    const unitTitles = {
      "I":   "Unit I — Basics, complexity, lower bounds",
      "II":  "Unit II — Recursion and Divide & Conquer",
      "III": "Unit III — Dynamic Programming",
      "IV":  "Unit IV — Greedy and Backtracking",
      "V":   "Unit V — Network Flows",
      "VI":  "Unit VI — NP-completeness",
    };

    let html = "";
    for (const unit of ["I", "II", "III", "IV", "V", "VI"]) {
      if (!byUnit[unit]) continue;
      html += `<div class="panel" style="margin-top:14px">
        <h2>${unitTitles[unit]}</h2>
        <table class="data-table">
          <thead><tr><th>Topic</th><th>Feature</th><th style="width:130px">Status</th></tr></thead>
          <tbody>
            ${byUnit[unit].map(r => {
              const badge = r.status === "implemented"
                ? "background:var(--success);color:#064e3b"
                : r.status === "partial"
                  ? "background:var(--warning);color:#451a03"
                  : "background:var(--surface-2);color:var(--text-dim)";
              return `<tr>
                <td>${escapeHtml(r.topic)}</td>
                <td>${escapeHtml(r.feature)}</td>
                <td><span class="badge" style="${badge}">${r.status}</span></td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>
      </div>`;
    }
    document.getElementById("coverage-body").innerHTML = html;
  } catch (e) {
    toast(`Coverage: ${e.message}`, "error");
  }
}


