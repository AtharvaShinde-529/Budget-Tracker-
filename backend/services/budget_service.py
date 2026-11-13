"""Budget optimiser service: demo goals/bills/shifts + wrappers over greedy algorithms."""

from backend.algorithms import greedy, huffman


# ---------- demo data (in-memory, deterministic) ----------

DEMO_GOALS = [
    {"name": "Noise-cancelling headphones", "weight_paise": 350000, "value": 9},
    {"name": "Study desk lamp",             "weight_paise": 120000, "value": 7},
    {"name": "Waterproof backpack",         "weight_paise": 250000, "value": 8},
    {"name": "Mechanical keyboard",         "weight_paise": 450000, "value": 6},
    {"name": "Running shoes",               "weight_paise": 300000, "value": 8},
    {"name": "Desk organiser",              "weight_paise":  80000, "value": 4},
    {"name": "Power bank 20000mAh",         "weight_paise": 180000, "value": 7},
]

DEMO_BILLS = [
    {"name": "Hostel rent",         "amount_paise": 450000, "deadline_day":  5, "penalty_paise": 50000},
    {"name": "Phone recharge",      "amount_paise":  29900, "deadline_day":  3, "penalty_paise":  5000},
    {"name": "Spotify premium",     "amount_paise":  11900, "deadline_day":  7, "penalty_paise":  2000},
    {"name": "Netflix share",       "amount_paise":  16600, "deadline_day": 10, "penalty_paise":  3000},
    {"name": "Electricity share",   "amount_paise":  85000, "deadline_day": 12, "penalty_paise": 10000},
    {"name": "College exam fee",    "amount_paise": 120000, "deadline_day": 15, "penalty_paise": 30000},
    {"name": "Gym membership",      "amount_paise": 100000, "deadline_day": 20, "penalty_paise": 15000},
    {"name": "Book rental",         "amount_paise":  40000, "deadline_day":  8, "penalty_paise":  4000},
]

DEMO_SHIFTS = [
    {"id": 1, "name": "Library assistant",  "start":  9, "end": 11},
    {"id": 2, "name": "Cafe counter",       "start": 10, "end": 13},
    {"id": 3, "name": "Teaching assistant", "start": 14, "end": 16},
    {"id": 4, "name": "Lab monitor",        "start": 15, "end": 17},
    {"id": 5, "name": "Evening tutor",      "start": 18, "end": 20},
    {"id": 6, "name": "Weekend library",    "start": 11, "end": 14},
    {"id": 7, "name": "Cafe evening",       "start": 17, "end": 21},
    {"id": 8, "name": "Lab night shift",    "start": 19, "end": 22},
]


# ---------- wrappers ----------

def optimize_goals(monthly_savings_paise):
    picked, stats = greedy.fractional_knapsack(DEMO_GOALS, monthly_savings_paise)
    total_value = sum(p["value_taken"] for p in picked)
    total_spent = sum(p["weight_taken_paise"] for p in picked)
    return {
        "picked": picked,
        "total_value": round(total_value, 2),
        "total_spent_paise": total_spent,
        "monthly_savings_paise": monthly_savings_paise,
        "stats": stats.as_dict(),
    }


def schedule_bills():
    scheduled, stats = greedy.job_sequencing_with_deadlines(DEMO_BILLS)
    scheduled_names = {s["name"] for s in scheduled}
    total_penalty_saved = sum(s["penalty_paise"] for s in scheduled)
    total_penalty_possible = sum(b["penalty_paise"] for b in DEMO_BILLS)
    skipped = [b for b in DEMO_BILLS if b["name"] not in scheduled_names]
    return {
        "scheduled": scheduled,
        "skipped": skipped,
        "penalty_saved_paise": total_penalty_saved,
        "penalty_possible_paise": total_penalty_possible,
        "stats": stats.as_dict(),
    }


def breakdown_cash(amount_paise):
    breakdown, stats = greedy.coin_change_greedy(amount_paise)
    as_list = []
    for d, count in breakdown.items():
        as_list.append({"denomination_paise": d,
                        "denomination_rupees": d / 100.0,
                        "count": count})
    # Sort by denomination descending
    as_list.sort(key=lambda x: -x["denomination_paise"])
    total_check = sum(x["denomination_paise"] * x["count"] for x in as_list)
    return {
        "amount_paise": amount_paise,
        "breakdown": as_list,
        "total_reconstructed_paise": total_check,
        "matches_input": total_check == amount_paise,
        "stats": stats.as_dict(),
    }


def schedule_shifts():
    ids, stats = greedy.interval_scheduling(DEMO_SHIFTS)
    chosen = [s for s in DEMO_SHIFTS if s["id"] in ids]
    total_hours = sum(s["end"] - s["start"] for s in chosen)
    return {
        "selected": chosen,
        "total_hours": total_hours,
        "all_shifts": DEMO_SHIFTS,
        "stats": stats.as_dict(),
    }


def compress_expense_log(conn):
    """Read all expense descriptions, Huffman-compress them, report ratio."""
    rows = conn.execute("SELECT description FROM expenses").fetchall()
    text = "\n".join(r["description"] for r in rows if r["description"])
    if not text:
        return {"error": "no expense descriptions to compress"}

    codes, root, build_stats = huffman.build_huffman(text)
    bits, enc_stats = huffman.huffman_encode(text, codes)

    # Baseline: 8 bits per char (uncompressed UTF-8 ASCII assumption)
    original_bits = len(text) * 8
    compressed_bits = len(bits)

    # Show top 10 codes by (length * freq) savings potential
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    top = []
    for ch, code in codes.items():
        top.append({"char": ch if ch != "\n" else "\\n",
                    "code": code,
                    "freq": freq[ch],
                    "bits": len(code)})
    top.sort(key=lambda x: -(x["freq"] * x["bits"]))
    top = top[:10]

    return {
        "original_chars": len(text),
        "original_bits": original_bits,
        "compressed_bits": compressed_bits,
        "compression_ratio": round(compressed_bits / original_bits, 4),
        "unique_chars": len(codes),
        "prefix_free": huffman.is_prefix_free(codes),
        "top_codes": top,
        "build_stats": build_stats.as_dict(),
        "encode_stats": enc_stats.as_dict(),
    }
