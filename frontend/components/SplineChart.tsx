"use client";

import { useEffect, useRef, useState, useId } from "react";

interface DataPoint {
  label: string;
  value: number;
}

interface SplineChartProps {
  data: DataPoint[];
  height?: number;
  accentColor?: string;
  showTooltip?: boolean;
}

export default function SplineChart({
  data,
  height = 120,
  accentColor = "#4efa72",
  showTooltip = true,
}: SplineChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hovered, setHovered] = useState<{ x: number; y: number; point: DataPoint } | null>(null);
  const [dims, setDims] = useState({ width: 600, height });

  useEffect(() => {
    if (!svgRef.current) return;
    const ro = new ResizeObserver(([entry]) => {
      setDims({ width: entry.contentRect.width, height });
    });
    ro.observe(svgRef.current.parentElement!);
    return () => ro.disconnect();
  }, [height]);

  const pad = { top: 16, right: 16, bottom: 32, left: 40 };
  const w = dims.width - pad.left - pad.right;
  const h = dims.height - pad.top - pad.bottom;

  const values = data.map((d) => d.value);
  const minV = Math.min(...values) * 0.85;
  const maxV = Math.max(...values) * 1.05;

  const xs = data.map((_, i) => (i / (data.length - 1)) * w + pad.left);
  const ys = data.map((d) => h - ((d.value - minV) / (maxV - minV)) * h + pad.top);

  // Catmull-Rom to cubic bezier
  function toPath(points: [number, number][]): string {
    if (points.length < 2) return "";
    let d = `M ${points[0][0]} ${points[0][1]}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[Math.max(i - 1, 0)];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[Math.min(i + 2, points.length - 1)];
      const cp1x = p1[0] + (p2[0] - p0[0]) / 6;
      const cp1y = p1[1] + (p2[1] - p0[1]) / 6;
      const cp2x = p2[0] - (p3[0] - p1[0]) / 6;
      const cp2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2[0]} ${p2[1]}`;
    }
    return d;
  }

  const pts: [number, number][] = xs.map((x, i) => [x, ys[i]]);
  const linePath = toPath(pts);
  const areaPath = linePath
    ? `${linePath} L ${xs[xs.length - 1]} ${h + pad.top} L ${xs[0]} ${h + pad.top} Z`
    : "";

  const rawId = useId();
  const gradientId = `grad-${rawId.replace(/:/g, "")}`;

  function handleMouseMove(e: React.MouseEvent<SVGSVGElement>) {
    if (!svgRef.current || !showTooltip) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    let closest = 0;
    let minDist = Infinity;
    xs.forEach((x, i) => {
      const dist = Math.abs(x - mx);
      if (dist < minDist) {
        minDist = dist;
        closest = i;
      }
    });
    setHovered({ x: xs[closest], y: ys[closest], point: data[closest] });
  }

  return (
    <svg
      ref={svgRef}
      width="100%"
      height={dims.height}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setHovered(null)}
      className="overflow-visible"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={accentColor} stopOpacity="0.3" />
          <stop offset="100%" stopColor={accentColor} stopOpacity="0.02" />
        </linearGradient>
        <filter id="glow-line">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Y-axis gridlines */}
      {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
        const y = pad.top + (1 - frac) * h;
        const val = minV + frac * (maxV - minV);
        return (
          <g key={frac}>
            <line
              x1={pad.left}
              x2={pad.left + w}
              y1={y}
              y2={y}
              stroke="rgba(93,122,99,0.2)"
              strokeWidth="1"
              strokeDasharray="4 4"
            />
            <text
              x={pad.left - 6}
              y={y + 4}
              textAnchor="end"
              fontSize="10"
              fill="rgba(93,122,99,0.8)"
            >
              {val >= 1000 ? `₹${(val / 1000).toFixed(0)}K` : `₹${val.toFixed(0)}`}
            </text>
          </g>
        );
      })}

      {/* X-axis labels (show 5 evenly) */}
      {data
        .filter((_, i) => i % Math.max(1, Math.floor(data.length / 5)) === 0)
        .map((d, j) => {
          const idx = j * Math.max(1, Math.floor(data.length / 5));
          return (
            <text
              key={j}
              x={xs[Math.min(idx, xs.length - 1)]}
              y={h + pad.top + 20}
              textAnchor="middle"
              fontSize="10"
              fill="rgba(93,122,99,0.8)"
            >
              {d.label}
            </text>
          );
        })}

      {/* Area fill */}
      {areaPath && (
        <path d={areaPath} fill={`url(#${gradientId})`} />
      )}

      {/* Main line */}
      {linePath && (
        <path
          d={linePath}
          fill="none"
          stroke={accentColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#glow-line)"
          className="chart-glow"
        />
      )}

      {/* Hover dot + tooltip */}
      {hovered && (
        <>
          <line
            x1={hovered.x}
            x2={hovered.x}
            y1={pad.top}
            y2={h + pad.top}
            stroke={accentColor}
            strokeWidth="1"
            strokeDasharray="4 3"
            strokeOpacity="0.5"
          />
          <circle
            cx={hovered.x}
            cy={hovered.y}
            r="5"
            fill={accentColor}
            stroke="#0d1410"
            strokeWidth="2"
            style={{ filter: `drop-shadow(0 0 6px ${accentColor})` }}
          />
          <g transform={`translate(${Math.min(hovered.x - 40, dims.width - 100)}, ${Math.max(hovered.y - 52, 4)})`}>
            <rect
              width="90"
              height="38"
              rx="6"
              fill="#161e19"
              stroke="rgba(78,250,114,0.3)"
              strokeWidth="1"
            />
            <text x="8" y="14" fontSize="10" fill="#5d7a63">
              {hovered.point.label}
            </text>
            <text x="8" y="28" fontSize="13" fill="#4efa72" fontWeight="700">
              ₹{hovered.point.value.toLocaleString("en-IN")}
            </text>
          </g>
        </>
      )}
    </svg>
  );
}

