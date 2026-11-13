# BudgetTracker - DAA Project
A personalised budget and expense tracker for students, built to demonstrate algorithm paradigms from the DAA syllabus (Units I-VI).

## Tech Stack
- **Backend**: Python 3.10, FastAPI, SQLite
- **Frontend**: HTML, CSS, Vanilla JS, Chart.js
- **Algorithms**: 100% hand-written (no built-in `sorted()`, `heapq`, etc.)

## How to Run
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
