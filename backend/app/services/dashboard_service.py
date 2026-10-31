import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from supabase import Client
from backend.app.models.dashboard_schemas import (
    DashboardSummaryResponse,
    StatMetric,
    StatCardItem,
    DashboardSalesResponse,
    SalesDataPoint,
    DashboardActivityResponse,
    ActivityItem,
    MemoryHighlight,
    DashboardBreakdownResponse,
    OrderStatusBreakdown,
    TopProductItem,
    CustomerDueItem,
)

logger = logging.getLogger(__name__)

# Status color mappings matching frontend DonutChart & theme
STATUS_COLOR_MAP = {
    "completed": "#4efa72",
    "delivered": "#4efa72",
    "processing": "#60a5fa",
    "shipped": "#60a5fa",
    "pending": "#fbbf24",
    "pending_payment": "#fbbf24",
    "unpaid": "#fbbf24",
    "cancelled": "#f87171",
    "canceled": "#f87171",
}


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        # Normalize trailing Z to +00:00
        clean_str = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _calculate_pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100.0, 1)


def _get_initials(name: Optional[str]) -> str:
    if not name or not name.strip():
        return "C"
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    return parts[0][:2].upper()


def _format_currency(val: float) -> str:
    return f"₹{int(val):,}"


def get_dashboard_summary(seller_id: str, db: Client) -> DashboardSummaryResponse:
    """
    Computes dashboard summary metrics strictly adhering to:
    - Monthly revenue: sum of verified payments in current month (excluding cancelled orders).
    - Unverified or rejected payments DO NOT reduce outstanding dues.
    - Cancelled orders DO NOT count towards revenue.
    - Outstanding dues = order total_amount minus verified payments for non-cancelled orders.
    """
    now = datetime.now(timezone.utc)
    current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    # Previous month start and end
    if now.month == 1:
        prev_month_start = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
    else:
        prev_month_start = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
    prev_month_end = current_month_start - timedelta(microseconds=1)

    # 1. Fetch Orders for this seller
    orders_res = (
        db.table("orders")
        .select("id, status, total_amount, customer_id, created_at")
        .eq("seller_id", seller_id)
        .execute()
    )
    orders: List[Dict[str, Any]] = orders_res.data or []

    # Map cancelled orders
    cancelled_order_ids = {
        str(o["id"]) for o in orders if str(o.get("status", "")).lower() in ("cancelled", "canceled")
    }
    non_cancelled_orders = [o for o in orders if str(o["id"]) not in cancelled_order_ids]

    # 2. Fetch Payments for this seller
    payments_res = (
        db.table("payments")
        .select("id, order_id, amount, status, paid_at, created_at")
        .eq("seller_id", seller_id)
        .execute()
    )
    payments: List[Dict[str, Any]] = payments_res.data or []

    # Filter verified payments
    verified_statuses = {"verified", "completed", "success"}
    verified_payments = [
        p for p in payments
        if str(p.get("status", "")).lower() in verified_statuses
        and str(p.get("order_id")) not in cancelled_order_ids
    ]

    # Calculate Revenue (Current Month vs Previous Month)
    current_month_revenue = 0.0
    prev_month_revenue = 0.0

    for p in verified_payments:
        pay_date = _parse_iso(p.get("paid_at") or p.get("created_at"))
        if not pay_date:
            continue
        amt = float(p.get("amount") or 0.0)
        if pay_date >= current_month_start:
            current_month_revenue += amt
        elif prev_month_start <= pay_date <= prev_month_end:
            prev_month_revenue += amt

    revenue_change = _calculate_pct_change(current_month_revenue, prev_month_revenue)

    # Calculate Orders (Total non-cancelled & monthly change)
    total_orders_count = len(non_cancelled_orders)
    curr_month_orders = 0
    prev_month_orders = 0

    for o in non_cancelled_orders:
        o_date = _parse_iso(o.get("created_at"))
        if not o_date:
            continue
        if o_date >= current_month_start:
            curr_month_orders += 1
        elif prev_month_start <= o_date <= prev_month_end:
            prev_month_orders += 1

    orders_change = _calculate_pct_change(curr_month_orders, prev_month_orders)

    # Calculate Active Customers
    active_customer_ids = {str(o.get("customer_id")) for o in non_cancelled_orders if o.get("customer_id")}
    active_customers_count = len(active_customer_ids)

    # Calculate Pending Dues:
    # Rule: Unverified or rejected payments must NOT reduce outstanding dues.
    # Group verified payments by order_id
    order_verified_payments: Dict[str, float] = defaultdict(float)
    for p in verified_payments:
        oid = str(p.get("order_id"))
        order_verified_payments[oid] += float(p.get("amount") or 0.0)

    total_pending_dues = 0.0
    for o in non_cancelled_orders:
        oid = str(o["id"])
        tot = float(o.get("total_amount") or 0.0)
        paid = order_verified_payments.get(oid, 0.0)
        due = max(0.0, tot - paid)
        total_pending_dues += due

    # Dues change: positive is worse (more debt), or we format as signed percentage
    dues_change = 0.0

    return DashboardSummaryResponse(
        revenue=StatMetric(
            value=current_month_revenue,
            formatted=_format_currency(current_month_revenue),
            change=revenue_change,
            change_label="vs last month",
        ),
        orders=StatMetric(
            value=float(total_orders_count),
            formatted=str(total_orders_count),
            change=orders_change,
            change_label="vs last month",
        ),
        active_customers=StatMetric(
            value=float(active_customers_count),
            formatted=str(active_customers_count),
            change=0.0,
            change_label="active buyers",
        ),
        pending_dues=StatMetric(
            value=total_pending_dues,
            formatted=_format_currency(total_pending_dues),
            change=dues_change,
            change_label="outstanding",
        ),
        stats=[
            StatCardItem(
                icon="🛍️",
                label="Revenue (this month)",
                value=_format_currency(current_month_revenue),
                numeric_value=current_month_revenue,
                change=revenue_change,
                change_label="vs last month",
            ),
            StatCardItem(
                icon="📦",
                label="Orders",
                value=str(total_orders_count),
                numeric_value=float(total_orders_count),
                change=orders_change,
                change_label="vs last month",
            ),
            StatCardItem(
                icon="👥",
                label="Active customers",
                value=str(active_customers_count),
                numeric_value=float(active_customers_count),
                change=0.0,
                change_label="vs last month",
            ),
            StatCardItem(
                icon="🔔",
                label="Pending dues",
                value=_format_currency(total_pending_dues),
                numeric_value=total_pending_dues,
                change=dues_change,
                change_label="outstanding",
                is_negative=True,
            ),
        ],
    )


def get_dashboard_sales(seller_id: str, period: str, db: Client) -> DashboardSalesResponse:
    """
    Generates date-wise sales totals suitable for SalesChart and SplineChart.
    Periods supported: 7D, 30D, 3M, 6M.
    Uses verified payments (cash sales) or completed order line totals.
    """
    now = datetime.now(timezone.utc)
    verified_statuses = {"verified", "completed", "success"}

    # Determine date range & buckets
    buckets: List[Tuple[str, datetime, datetime]] = []

    if period == "7D":
        start_time = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(7):
            d = start_time + timedelta(days=i)
            d_end = d + timedelta(days=1) - timedelta(microseconds=1)
            label = d.strftime("%b %d")
            buckets.append((label, d, d_end))

    elif period == "30D":
        start_time = (now - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
        # Create 6-7 intervals across 30 days matching frontend SalesChart
        step = 5
        curr = start_time
        while curr <= now:
            c_end = min(curr + timedelta(days=step) - timedelta(microseconds=1), now)
            label = curr.strftime("%b %d")
            buckets.append((label, curr, c_end))
            curr += timedelta(days=step)

    elif period == "3M":
        # 3 calendar months
        start_time = (now.replace(day=1) - timedelta(days=60)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        curr = start_time
        for _ in range(3):
            # next month
            next_m = (curr.month % 12) + 1
            next_y = curr.year + (1 if curr.month == 12 else 0)
            end_m = datetime(next_y, next_m, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
            buckets.append((curr.strftime("%b"), curr, end_m))
            curr = datetime(next_y, next_m, 1, tzinfo=timezone.utc)

    elif period == "6M":
        # 6 calendar months
        start_time = (now.replace(day=1) - timedelta(days=150)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        curr = start_time
        for _ in range(6):
            next_m = (curr.month % 12) + 1
            next_y = curr.year + (1 if curr.month == 12 else 0)
            end_m = datetime(next_y, next_m, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
            buckets.append((curr.strftime("%b"), curr, end_m))
            curr = datetime(next_y, next_m, 1, tzinfo=timezone.utc)

    # Fetch verified payments within the overall window
    min_date = buckets[0][1].isoformat()
    payments_res = (
        db.table("payments")
        .select("amount, status, paid_at, created_at")
        .eq("seller_id", seller_id)
        .gte("created_at", min_date)
        .execute()
    )
    payments: List[Dict[str, Any]] = payments_res.data or []

    # Aggregate by bucket
    data_points: List[SalesDataPoint] = []
    total_sales = 0.0

    for label, b_start, b_end in buckets:
        bucket_sum = 0.0
        for p in payments:
            if str(p.get("status", "")).lower() not in verified_statuses:
                continue
            p_date = _parse_iso(p.get("paid_at") or p.get("created_at"))
            if p_date and b_start <= p_date <= b_end:
                bucket_sum += float(p.get("amount") or 0.0)

        data_points.append(SalesDataPoint(label=label, value=bucket_sum))
        total_sales += bucket_sum

    return DashboardSalesResponse(
        period=period,  # type: ignore
        total_sales=total_sales,
        change_percentage=0.0,
        change_label=f"vs previous {period}",
        data=data_points,
    )


def get_dashboard_activity(seller_id: str, db: Client) -> DashboardActivityResponse:
    """
    Returns actual counts of today's activities and Meko memory highlights from agent_logs.
    Does not fabricate counts. Returns empty list if memories are not yet integrated.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start - timedelta(microseconds=1)

    today_iso = today_start.isoformat()
    yesterday_iso = yesterday_start.isoformat()

    # 1. Orders today & yesterday
    orders_res = (
        db.table("orders")
        .select("id, created_at")
        .eq("seller_id", seller_id)
        .gte("created_at", yesterday_iso)
        .execute()
    )
    orders: List[Dict[str, Any]] = orders_res.data or []
    orders_today = sum(1 for o in orders if (_parse_iso(o.get("created_at")) or now) >= today_start)
    orders_yesterday = sum(1 for o in orders if yesterday_start <= (_parse_iso(o.get("created_at")) or now) <= yesterday_end)
    orders_delta = f"{'+' if orders_today >= orders_yesterday else ''}{orders_today - orders_yesterday}"

    # 2. Payments today & yesterday
    payments_res = (
        db.table("payments")
        .select("id, created_at")
        .eq("seller_id", seller_id)
        .gte("created_at", yesterday_iso)
        .execute()
    )
    payments: List[Dict[str, Any]] = payments_res.data or []
    payments_today = sum(1 for p in payments if (_parse_iso(p.get("created_at")) or now) >= today_start)
    payments_yesterday = sum(1 for p in payments if yesterday_start <= (_parse_iso(p.get("created_at")) or now) <= yesterday_end)
    payments_delta = f"{'+' if payments_today >= payments_yesterday else ''}{payments_today - payments_yesterday}"

    # 3. Agent logs for messages, dues reminders, and memories
    logs_res = (
        db.table("agent_logs")
        .select("*")
        .eq("seller_id", seller_id)
        .gte("created_at", yesterday_iso)
        .execute()
    )
    logs: List[Dict[str, Any]] = logs_res.data or []

    messages_today = 0
    messages_yesterday = 0
    reminders_today = 0
    reminders_yesterday = 0
    memories_today = 0
    memories_yesterday = 0

    for l in logs:
        l_date = _parse_iso(l.get("created_at")) or now
        act = str(l.get("action", "")).lower()
        etype = str(l.get("entity_type", "")).lower()
        has_meko = bool(l.get("meko_operation"))

        is_msg = "message" in act or etype == "message"
        is_rem = "reminder" in act or etype == "reminder"
        is_mem = has_meko or "memory" in act or etype == "memory"

        if l_date >= today_start:
            if is_msg:
                messages_today += 1
            if is_rem:
                reminders_today += 1
            if is_mem:
                memories_today += 1
        elif yesterday_start <= l_date <= yesterday_end:
            if is_msg:
                messages_yesterday += 1
            if is_rem:
                reminders_yesterday += 1
            if is_mem:
                memories_yesterday += 1

    messages_delta = f"{'+' if messages_today >= messages_yesterday else ''}{messages_today - messages_yesterday}"
    reminders_delta = f"{'+' if reminders_today >= reminders_yesterday else ''}{reminders_today - reminders_yesterday}"
    memories_delta = f"{'+' if memories_today >= memories_yesterday else ''}{memories_today - memories_yesterday}"

    activities = [
        ActivityItem(icon="💬", color="#4efa72", label="New messages", count=messages_today, delta=messages_delta),
        ActivityItem(icon="📦", color="#60a5fa", label="Orders created", count=orders_today, delta=orders_delta),
        ActivityItem(icon="₹", color="#fbbf24", label="Payments received", count=payments_today, delta=payments_delta),
        ActivityItem(icon="🔔", color="#f87171", label="Dues reminders sent", count=reminders_today, delta=reminders_delta),
        ActivityItem(icon="✨", color="#c084fc", label="Memories updated", count=memories_today, delta=memories_delta),
    ]

    # Fetch recent memory records from agent_logs (if genuine records exist)
    memory_logs_res = (
        db.table("agent_logs")
        .select("*")
        .eq("seller_id", seller_id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    all_logs: List[Dict[str, Any]] = memory_logs_res.data or []

    memory_highlights: List[MemoryHighlight] = []
    for l in all_logs:
        if l.get("meko_operation") or "memory" in str(l.get("action", "")).lower() or l.get("entity_type") == "memory":
            meta_dict = l.get("metadata") or {}
            text = meta_dict.get("summary") or meta_dict.get("text") or f"{l.get('agent_name', 'Munim')}: {l.get('action')}"
            memory_highlights.append(
                MemoryHighlight(
                    icon="✨",
                    color="#4efa72",
                    text=text,
                    meta=meta_dict.get("source", "Updated recently"),
                )
            )

    return DashboardActivityResponse(
        activities=activities,
        memories=memory_highlights,
        new_messages_count=messages_today,
        orders_created_count=orders_today,
        payments_received_count=payments_today,
        dues_reminders_sent_count=reminders_today,
        memories_updated_count=memories_today,
    )


def get_dashboard_breakdown(seller_id: str, db: Client) -> DashboardBreakdownResponse:
    """
    Returns:
    - Order counts by status (mapped to display colors and labels).
    - Top selling products from order_items.
    - Customers with pending dues and verified order balances.
    """
    # 1. Orders by Status
    orders_res = (
        db.table("orders")
        .select("id, status, total_amount, customer_id")
        .eq("seller_id", seller_id)
        .execute()
    )
    orders: List[Dict[str, Any]] = orders_res.data or []
    total_orders = len(orders)

    status_counts: Dict[str, int] = defaultdict(int)
    for o in orders:
        st = str(o.get("status") or "pending").lower().strip()
        status_counts[st] += 1

    order_statuses: List[OrderStatusBreakdown] = []
    for raw_st, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        label = raw_st.replace("_", " ").title()
        pct = round((count / total_orders * 100.0), 1) if total_orders > 0 else 0.0
        color = STATUS_COLOR_MAP.get(raw_st, "#9db8a0")
        order_statuses.append(
            OrderStatusBreakdown(label=label, value=count, percentage=pct, color=color)
        )

    # 2. Top-selling products from order_items
    items_res = (
        db.table("order_items")
        .select("product_name_snapshot, quantity, unit_price, line_total")
        .eq("seller_id", seller_id)
        .execute()
    )
    items: List[Dict[str, Any]] = items_res.data or []

    product_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {"sold": 0.0, "revenue": 0.0})
    for it in items:
        pname = it.get("product_name_snapshot") or "Standard Item"
        qty = float(it.get("quantity") or 0.0)
        lt = float(it.get("line_total") or (float(it.get("unit_price") or 0.0) * qty))
        product_stats[pname]["sold"] += qty
        product_stats[pname]["revenue"] += lt

    top_products: List[TopProductItem] = []
    for pname, stats in sorted(product_stats.items(), key=lambda x: x[1]["sold"], reverse=True)[:5]:
        top_products.append(
            TopProductItem(
                name=pname,
                sold=int(stats["sold"]),
                revenue=stats["revenue"],
                emoji="👘" if "kurti" in pname.lower() else "📦",
            )
        )

    # 3. Pending Dues by Customer
    # Exclude cancelled orders
    cancelled_ids = {str(o["id"]) for o in orders if str(o.get("status", "")).lower() in ("cancelled", "canceled")}
    active_orders = [o for o in orders if str(o["id"]) not in cancelled_ids]

    payments_res = (
        db.table("payments")
        .select("order_id, amount, status")
        .eq("seller_id", seller_id)
        .execute()
    )
    payments: List[Dict[str, Any]] = payments_res.data or []

    verified_statuses = {"verified", "completed", "success"}
    order_paid: Dict[str, float] = defaultdict(float)
    for p in payments:
        if str(p.get("status", "")).lower() in verified_statuses:
            order_paid[str(p.get("order_id"))] += float(p.get("amount") or 0.0)

    customer_dues_agg: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"amount": 0.0, "orders": 0})
    for o in active_orders:
        oid = str(o["id"])
        cid = str(o.get("customer_id") or "")
        tot = float(o.get("total_amount") or 0.0)
        paid = order_paid.get(oid, 0.0)
        due = max(0.0, tot - paid)
        if due > 0 and cid:
            customer_dues_agg[cid]["amount"] += due
            customer_dues_agg[cid]["orders"] += 1

    # Fetch customer details for debtors
    debtor_ids = list(customer_dues_agg.keys())
    customer_info_map: Dict[str, Dict[str, Any]] = {}
    if debtor_ids:
        cust_res = (
            db.table("customers")
            .select("id, name, phone")
            .eq("seller_id", seller_id)
            .in_("id", debtor_ids)
            .execute()
        )
        for c in cust_res.data or []:
            customer_info_map[str(c["id"])] = c

    pending_dues: List[CustomerDueItem] = []
    total_pending_amount = 0.0

    for cid, dues_data in sorted(customer_dues_agg.items(), key=lambda x: x[1]["amount"], reverse=True)[:5]:
        cinfo = customer_info_map.get(cid, {})
        cname = cinfo.get("name") or "Customer"
        cphone = cinfo.get("phone") or ""
        amt = dues_data["amount"]
        total_pending_amount += amt

        pending_dues.append(
            CustomerDueItem(
                initials=_get_initials(cname),
                name=cname,
                orders=dues_data["orders"],
                amount=amt,
                phone=cphone,
            )
        )

    return DashboardBreakdownResponse(
        order_statuses=order_statuses,
        total_orders=total_orders,
        top_products=top_products,
        pending_dues=pending_dues,
        total_pending_dues=total_pending_amount,
    )
