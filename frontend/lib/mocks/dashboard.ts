export const MOCK_CONFIG = {
  SHOW_TRUST_BADGE: false,
  TRUST_BADGE_TEXT: "Bharat ke 10,000+ vyapariyon ka bharosa",
};

export const MOCK_SELLER = {
  name: "Neha",
  businessName: "Neha's Closet",
  initials: "NC",
  phone: "+91 98765 43210",
  whatsappNumber: "14155238886",
  status: "Active",
};

export const MOCK_KPI_STATS = [
  {
    id: "revenue",
    icon: "ShoppingBag",
    label: "Revenue (this month)",
    value: "₹86,420",
    numericValue: 86420,
    change: 18,
    changeLabel: "+18%",
    isNegative: false,
  },
  {
    id: "orders",
    icon: "Package",
    label: "Orders",
    value: "124",
    numericValue: 124,
    change: 12,
    changeLabel: "+12%",
    isNegative: false,
  },
  {
    id: "customers",
    icon: "Users",
    label: "Active customers",
    value: "67",
    numericValue: 67,
    change: 24,
    changeLabel: "+24%",
    isNegative: false,
  },
  {
    id: "dues",
    icon: "Wallet",
    label: "Pending dues",
    value: "₹12,480",
    numericValue: 12480,
    change: 6,
    changeLabel: "+6%",
    isNegative: true,
  },
];

export const MOCK_SALES_SERIES = {
  "7D": [
    { label: "Mon", value: 9200 },
    { label: "Tue", value: 11400 },
    { label: "Wed", value: 8900 },
    { label: "Thu", value: 14200 },
    { label: "Fri", value: 16800 },
    { label: "Sat", value: 21500 },
    { label: "Sun", value: 19800 },
  ],
  "30D": [
    { label: "Oct 1", value: 32000 },
    { label: "Oct 5", value: 45000 },
    { label: "Oct 10", value: 38000 },
    { label: "Oct 15", value: 58000 },
    { label: "Oct 20", value: 52000 },
    { label: "Oct 25", value: 74000 },
    { label: "Oct 30", value: 86420 },
  ],
  "3M": [
    { label: "Aug", value: 68000 },
    { label: "Sep", value: 74500 },
    { label: "Oct", value: 86420 },
  ],
  "6M": [
    { label: "May", value: 51000 },
    { label: "Jun", value: 58000 },
    { label: "Jul", value: 62000 },
    { label: "Aug", value: 68000 },
    { label: "Sep", value: 74500 },
    { label: "Oct", value: 86420 },
  ],
};

export const MOCK_ORDER_STATUSES = [
  { label: "Completed", value: 82, percentage: 66, color: "#B6F23C" },
  { label: "Processing", value: 18, percentage: 15, color: "#60A5FA" },
  { label: "Pending Payment", value: 12, percentage: 10, color: "#FDBA74" },
  { label: "Cancelled", value: 10, percentage: 8, color: "#C084FC" },
];

export const MOCK_TOP_PRODUCTS = [
  { name: "Blue Kurti", sold: 48, revenue: 38352, emoji: "👗" },
  { name: "Anarkali Kurti", sold: 27, revenue: 32130, emoji: "👘" },
  { name: "Black Kurti", sold: 21, revenue: 16758, emoji: "👚" },
];

export const MOCK_PENDING_DUES = [
  {
    name: "Riya Sharma",
    initials: "RS",
    orders: 2,
    amount: 4200,
    phone: "919876543210",
  },
  {
    name: "Aditi Khanna",
    initials: "AK",
    orders: 1,
    amount: 3800,
    phone: "919876543211",
  },
  {
    name: "Sneha Mehta",
    initials: "SM",
    orders: 1,
    amount: 2480,
    phone: "919876543212",
  },
];

export const MOCK_ACTIVITIES = [
  { label: "New messages", count: 42, delta: "+11" },
  { label: "Orders created", count: 9, delta: "+3" },
  { label: "Payments received", count: 8, delta: "+2" },
  { label: "Dues reminders sent", count: 3, delta: "+3" },
  { label: "Memories updated", count: 6, delta: "+6" },
];

export const MOCK_MEMORIES = [
  {
    text: "Priya prefers blue kurtis, size M",
    meta: "Updated today",
    type: "user",
  },
  {
    text: "Exchange policy (7 days) added",
    meta: "Promoted to business knowledge",
    type: "policy",
  },
  {
    text: "High interest in Anarkali collection",
    meta: "Seen in 12 conversations",
    type: "trend",
  },
];

export const MOCK_BUSINESS_TYPES = [
  { id: "clothing", label: "Kapde ki dukaan", icon: "Shirt" },
  { id: "kirana", label: "General Store", icon: "ShoppingBasket" },
  { id: "cosmetics", label: "Cosmetics & Gifts", icon: "Sparkles" },
  { id: "wholesale", label: "Wholesale", icon: "Package" },
];

