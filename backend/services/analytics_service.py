"""Analytics service: ties the D&C and order-statistics algorithms to real data."""

from collections import defaultdict
from datetime import date

from backend.algorithms import divide_conquer, order_stats


class AnalyticsService:
    def __init__(self, conn):
        self.conn = conn

    def _fetch_all(self):
        sql = """
        SELECT e.id, e.amount_paise, e.date, e.category_id,
               c.name AS category_name, c.color AS category_color,
               e.description, e.payment_mode
        FROM expenses e JOIN categories c ON c.id = e.category_id
        ORDER BY e.date
        """
        return [dict(r) for r in self.conn.execute(sql).fetchall()]

    # ---------- order statistics ----------

    def median_expense(self):
        amounts = [r["amount_paise"] for r in self._fetch_all()]
        if not amounts:
            return {"median": 0, "count": 0}
        med, stats = order_stats.median(amounts, method="randomized")
        return {
            "median_paise": round(med),
            "count": len(amounts),
            "stats": stats.as_dict(),
        }

    def percentile(self, p):
        amounts = [r["amount_paise"] for r in self._fetch_all()]
        if not amounts:
            return {"percentile": p, "value_paise": 0}
        val, stats = order_stats.percentile(amounts, p)
        return {
            "percentile": p,
            "value_paise": round(val),
            "count": len(amounts),
            "stats": stats.as_dict(),
        }

    def top_k(self, k):
        rows = self._fetch_all()
        if not rows:
            return {"items": [], "k": k}
        amounts = [r["amount_paise"] for r in rows]
        top_amounts, stats = order_stats.top_k(amounts, k)
        # Find a matching row for each amount (first match wins; ties are fine)
        by_amount = defaultdict(list)
        for r in rows:
            by_amount[r["amount_paise"]].append(r)
        items = []
        for amt in top_amounts:
            if by_amount[amt]:
                items.append(by_amount[amt].pop())
        return {"items": items, "k": k, "stats": stats.as_dict()}

    def outliers(self):
        rows = self._fetch_all()
        amounts = [r["amount_paise"] for r in rows]
        if len(amounts) < 4:
            return {"outliers": [], "thresholds": {}}
        idxs, stats = order_stats.iqr_outliers(amounts)
        outliers = [rows[i] for i, _ in idxs]
        return {
            "outliers": outliers,
            "thresholds": stats.extra,
            "count": len(outliers),
        }

    # ---------- divide & conquer ----------

    def worst_streak(self):
        """Max-sum subarray on (daily_spend - mean_daily_spend).

        The winning window is the costliest run of days above the average."""
        rows = self._fetch_all()
        if not rows:
            return {"start": None, "end": None, "sum_paise": 0}
        daily = defaultdict(int)
        for r in rows:
            daily[r["date"]] += r["amount_paise"]
        days = sorted(daily)
        if len(days) < 2:
            return {"start": days[0] if days else None,
                    "end": days[0] if days else None,
                    "sum_paise": 0}

        mean = sum(daily[d] for d in days) / len(days)
        values = [daily[d] - mean for d in days]
        best, lo, hi, stats = divide_conquer.max_sum_subarray_dc(values)
        return {
            "start": days[lo] if lo < len(days) else None,
            "end": days[hi - 1] if 0 < hi <= len(days) else None,
            "sum_paise": round(best),
            "window_days": hi - lo,
            "stats": stats.as_dict(),
        }

    def inversions(self, granularity="category"):
        """Kendall-tau-style inversion count between two ranking lists.

        Default: categories ranked by spend this month vs last month."""
        rows = self._fetch_all()
        if not rows:
            return {"inversions": 0}
        dates = [r["date"] for r in rows]
        months = sorted({d[:7] for d in dates})
        if len(months) < 2:
            return {"inversions": 0, "this_month": months[0] if months else None,
                    "prev_month": None}
        this_m, prev_m = months[-1], months[-2]

        def spend_by_cat(m):
            d = defaultdict(int)
            for r in rows:
                if r["date"].startswith(m):
                    d[r["category_name"]] += r["amount_paise"]
            return d

        this_s = spend_by_cat(this_m)
        prev_s = spend_by_cat(prev_m)
        # rank = position when sorted desc by spend
        cats = sorted(set(this_s) | set(prev_s),
                      key=lambda c: -(this_s.get(c, 0) + prev_s.get(c, 0)))
        if not cats:
            return {"inversions": 0}
        this_rank = [cats.index(c) if c in this_s else len(cats) for c in cats]
        prev_rank = [cats.index(c) if c in prev_s else len(cats) for c in cats]
        # order categories by prev_rank, then count inversions in this_rank
        order = sorted(range(len(cats)), key=lambda i: prev_rank[i])
        this_ranked = [this_rank[i] for i in order]
        inv, stats = divide_conquer.inversion_count(this_ranked)
        return {
            "inversions": inv,
            "this_month": this_m,
            "prev_month": prev_m,
            "categories": len(cats),
            "stats": stats.as_dict(),
        }

    def dominant_category(self):
        rows = self._fetch_all()
        if not rows:
            return {"category": None, "count": 0}
        # Boyer-Moore on transaction count per category
        names = [r["category_name"] for r in rows]
        cand, cnt, stats = divide_conquer.majority_element(names)
        # Fall back to simple mode if no strict majority
        if cand is None:
            counts = defaultdict(int)
            for n in names:
                counts[n] += 1
            cand, cnt = max(counts.items(), key=lambda kv: kv[1])
        return {
            "category": cand,
            "count": cnt,
            "total": len(names),
            "strict_majority": cnt > len(names) // 2,
            "stats": stats.as_dict(),
        }

    def duplicates(self, tolerance_paise=500):
        """Closest-pair detection on (day_of_year, amount_paise/100).

        Two expenses within tolerance on both axes are flagged as possible
        duplicates. Uses D&C closest pair ? O(n log n)."""
        rows = self._fetch_all()
        if len(rows) < 2:
            return {"duplicates": [], "min_distance_sq": None}
        base = date(2026, 1, 1).toordinal()

        def to_point(r):
            try:
                d = date.fromisoformat(r["date"]).toordinal() - base
            except ValueError:
                d = 0
            return (d, r["amount_paise"] / 100.0)

        pts = [to_point(r) for r in rows]
        dist_sq, i, j, stats = divide_conquer.closest_pair(pts)
        # Only flag when the pair is genuinely close (within tolerance on both axes)
        flag = False
        if dist_sq is not None and i >= 0 and j >= 0:
            dy = abs(pts[i][0] - pts[j][0])
            damt = abs(pts[i][1] - pts[j][1]) * 100
            flag = dy <= 2 and damt <= tolerance_paise
        return {
            "duplicates": [rows[i], rows[j]] if flag else [],
            "min_distance_sq": dist_sq,
            "stats": stats.as_dict(),
        }

    # ---------- aggregation (for chart) ----------

    def category_totals(self):
        rows = self._fetch_all()
        agg = defaultdict(lambda: {"total_paise": 0, "count": 0, "color": "#6366f1"})
        for r in rows:
            agg[r["category_name"]]["total_paise"] += r["amount_paise"]
            agg[r["category_name"]]["count"] += 1
            agg[r["category_name"]]["color"] = r["category_color"]
        out = [{"category": k, **v} for k, v in agg.items()]
        out.sort(key=lambda x: -x["total_paise"])
        return out

    def daily_spend(self, days=30):
        rows = self._fetch_all()
        daily = defaultdict(int)
        for r in rows:
            daily[r["date"]] += r["amount_paise"]
        days_sorted = sorted(daily)[-days:]
        return [{"date": d, "total_paise": daily[d]} for d in days_sorted]

    def summary(self):
        rows = self._fetch_all()
        if not rows:
            return {"count": 0, "total_paise": 0, "min_paise": 0,
                    "max_paise": 0, "avg_paise": 0}
        amounts = [r["amount_paise"] for r in rows]
        return {
            "count": len(amounts),
            "total_paise": sum(amounts),
            "min_paise": min(amounts),
            "max_paise": max(amounts),
            "avg_paise": round(sum(amounts) / len(amounts)),
        }
