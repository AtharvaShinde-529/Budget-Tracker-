"""Pydantic request/response schemas for the API layer."""

from typing import Literal

from pydantic import BaseModel, Field


PaymentMode = Literal["cash", "upi", "card", "netbanking", "wallet"]

SortField = Literal["date", "amount_paise", "category_name", "description"]
SortAlgorithm = Literal[
    "merge_sort", "quick_sort", "heap_sort",
    "insertion_sort", "selection_sort", "bubble_sort",
    "counting_sort", "radix_sort",
]
SortOrder = Literal["asc", "desc"]


class CategoryOut(BaseModel):
    id: int
    name: str
    color: str
    monthly_limit_paise: int


class ExpenseCreate(BaseModel):
    amount_paise: int = Field(..., ge=0, description="Amount in paise (?1 = 100 paise)")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="ISO date YYYY-MM-DD")
    category_id: int = Field(..., ge=1)
    description: str = Field("", max_length=200)
    payment_mode: PaymentMode = "cash"


class ExpenseUpdate(BaseModel):
    amount_paise: int | None = Field(None, ge=0)
    date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    category_id: int | None = Field(None, ge=1)
    description: str | None = Field(None, max_length=200)
    payment_mode: PaymentMode | None = None


class ExpenseOut(BaseModel):
    id: int
    amount_paise: int
    date: str
    category_id: int
    category_name: str
    category_color: str
    description: str
    payment_mode: str
    created_at: str


class SortStats(BaseModel):
    algorithm: str
    comparisons: int
    swaps: int
    calls: int
    max_depth: int


class SortResult(BaseModel):
    rows: list[ExpenseOut]
    stats: SortStats
    field: str
    order: str


class SearchResult(BaseModel):
    rows: list[ExpenseOut]
    binary_search_comparisons: int
    total_count: int


class UndoRedoStatus(BaseModel):
    undo_depth: int
    redo_depth: int
    undo_available: bool
    redo_available: bool


class MutationResult(BaseModel):
    id: int
    status: str
    undo_redo: UndoRedoStatus
