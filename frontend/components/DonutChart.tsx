"use client";

interface DonutChartProps {
  data: { label: string; value: number; color: string }[];
  total: number;
  size?: number;
}

export default function DonutChart({ data, total, size = 140 }: DonutChartProps) {
  const radius = (size / 2) * 0.75;
  const circumference = 2 * Math.PI * radius;
  const cx = size / 2;
  const cy = size / 2;
  const strokeWidth = (size / 2) * 0.22;

  let cumulative = 0;
  const segments = data.map((d) => {
    const fraction = d.value / total;
    const offset = circumference * (1 - cumulative);
    cumulative += fraction;
    return {
      ...d,
      fraction,
      dashArray: `${circumference * fraction - 2} ${circumference}`,
      dashOffset: offset,
    };
  });

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        {/* Background ring */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke="rgba(78,250,114,0.06)"
          strokeWidth={strokeWidth}
        />
        {segments.map((seg, i) => (
          <circle
            key={i}
            cx={cx}
            cy={cy}
            r={radius}
            fill="none"
            stroke={seg.color}
            strokeWidth={strokeWidth}
            strokeDasharray={seg.dashArray}
            strokeDashoffset={seg.dashOffset}
            strokeLinecap="round"
            style={{
              filter:
                i === 0
                  ? `drop-shadow(0 0 6px ${seg.color}80)`
                  : undefined,
              transition: "stroke-dasharray 0.5s ease",
            }}
          />
        ))}
      </svg>
      {/* Center label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-[#f0fdf4]">{total}</span>
        <span className="text-[10px] text-[#5d7a63] font-medium">Orders</span>
      </div>
    </div>
  );
}

