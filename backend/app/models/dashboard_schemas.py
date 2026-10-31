from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class StatMetric(BaseModel):
    value: float
    formatted: str
    change: float = 0.0
    change_label: str = "vs last month"


class StatCardItem(BaseModel):
    icon: str
    label: str
    value: str
    numeric_value: float
    change: float = 0.0
    change_label: str = "vs last month"
    is_negative: bool = False


class DashboardSummaryResponse(BaseModel):
    revenue: StatMetric
    orders: StatMetric
    active_customers: StatMetric
    pending_dues: StatMetric
    stats: List[StatCardItem]


class SalesDataPoint(BaseModel):
    label: str
    value: float


class DashboardSalesResponse(BaseModel):
    period: Literal["7D", "30D", "3M", "6M"]
    total_sales: float
    change_percentage: float = 0.0
    change_label: str = "vs previous period"
    data: List[SalesDataPoint]


class ActivityItem(BaseModel):
    icon: str
    color: str
    label: str
    count: int
    delta: str


class MemoryHighlight(BaseModel):
    icon: str
    color: str
    text: str
    meta: str


class DashboardActivityResponse(BaseModel):
    activities: List[ActivityItem]
    memories: List[MemoryHighlight]
    new_messages_count: int = 0
    orders_created_count: int = 0
    payments_received_count: int = 0
    dues_reminders_sent_count: int = 0
    memories_updated_count: int = 0


class OrderStatusBreakdown(BaseModel):
    label: str
    value: int
    percentage: float
    color: str


class TopProductItem(BaseModel):
    name: str
    sold: int
    revenue: float
    emoji: str = "📦"


class CustomerDueItem(BaseModel):
    initials: str
    name: str
    orders: int
    amount: float
    phone: str


class DashboardBreakdownResponse(BaseModel):
    order_statuses: List[OrderStatusBreakdown]
    total_orders: int
    top_products: List[TopProductItem]
    pending_dues: List[CustomerDueItem]
    total_pending_dues: float
