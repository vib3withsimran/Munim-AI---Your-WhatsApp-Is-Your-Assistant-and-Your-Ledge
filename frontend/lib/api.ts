import { createClient } from "@/lib/supabase/client";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// --- Types matching FastAPI / Supabase Schemas ---

export interface StatMetric {
  value: number;
  formatted: string;
  change: number;
  change_label: string;
}

export interface StatCardItem {
  icon: string;
  label: string;
  value: string;
  numeric_value: number;
  change: number;
  change_label: string;
  is_negative: boolean;
}

export interface DashboardSummaryResponse {
  revenue: StatMetric;
  orders: StatMetric;
  active_customers: StatMetric;
  pending_dues: StatMetric;
  stats: StatCardItem[];
}

export interface SalesDataPoint {
  label: string;
  value: number;
}

export interface DashboardSalesResponse {
  period: "7D" | "30D" | "3M" | "6M";
  total_sales: number;
  change_percentage: number;
  change_label: string;
  data: SalesDataPoint[];
}

export interface ActivityItem {
  icon: string;
  color: string;
  label: string;
  count: number;
  delta: string;
}

export interface MemoryHighlight {
  icon: string;
  color: string;
  text: string;
  meta: string;
}

export interface DashboardActivityResponse {
  activities: ActivityItem[];
  memories: MemoryHighlight[];
  new_messages_count: number;
  orders_created_count: number;
  payments_received_count: number;
  dues_reminders_sent_count: number;
  memories_updated_count: number;
}

export interface OrderStatusBreakdown {
  label: string;
  value: number;
  percentage: number;
  color: string;
}

export interface TopProductItem {
  name: string;
  sold: number;
  revenue: number;
  emoji: string;
}

export interface CustomerDueItem {
  initials: string;
  name: string;
  orders: number;
  amount: number;
  phone: string;
}

export interface DashboardBreakdownResponse {
  order_statuses: OrderStatusBreakdown[];
  total_orders: number;
  top_products: TopProductItem[];
  pending_dues: CustomerDueItem[];
  total_pending_dues: number;
}

export interface SellerProfile {
  id: string;
  email?: string | null;
  business_name?: string | null;
  phone?: string | null;
  business_type?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

// --- Fetch Helper with Supabase Auth Header ---

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const token = session?.access_token;
  if (!token) {
    throw new ApiError("No active authentication session. Please log in.", 401);
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...(options.headers as Record<string, string>),
  };

  const url = `${API_BASE_URL}${endpoint}`;
  let response: Response;

  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Network error";
    throw new ApiError(
      `Unable to connect to Munim AI server (${errorMsg}). Please ensure backend is running.`,
      0
    );
  }

  if (response.status === 401) {
    // Session expired or invalid
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("munim:unauthorized"));
    }
    throw new ApiError("Session expired or unauthorized. Please re-login.", 401);
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      // response wasn't JSON
    }
    throw new ApiError(errorDetail, response.status);
  }

  return response.json();
}

// --- Dashboard API Client ---

export const api = {
  getSummary: () => fetchWithAuth<DashboardSummaryResponse>("/dashboard/summary"),
  getSales: (period: "7D" | "30D" | "3M" | "6M" = "30D") =>
    fetchWithAuth<DashboardSalesResponse>(`/dashboard/sales?period=${period}`),
  getActivity: () => fetchWithAuth<DashboardActivityResponse>("/dashboard/activity"),
  getBreakdown: () => fetchWithAuth<DashboardBreakdownResponse>("/dashboard/breakdown"),
  getProfile: () => fetchWithAuth<SellerProfile>("/auth/me"),
  updateProfile: (data: Partial<SellerProfile>) =>
    fetchWithAuth<SellerProfile>("/auth/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
