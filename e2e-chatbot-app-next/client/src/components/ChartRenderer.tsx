import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';
import { useState, useRef, useMemo } from 'react';

const COLOR_PALETTES = {
  default: ['#2dd4bf', '#38bdf8', '#a78bfa', '#fb923c', '#f87171', '#4ade80', '#facc15', '#e879f9', '#94a3b8'],
  ocean: ['#0ea5e9', '#06b6d4', '#0891b2', '#0e7490', '#155e75', '#164e63', '#083344', '#0c4a6e', '#075985'],
  forest: ['#22c55e', '#16a34a', '#15803d', '#166534', '#14532d', '#365314', '#4d7c0f', '#65a30d', '#84cc16'],
  sunset: ['#f59e0b', '#f97316', '#ea580c', '#dc2626', '#b91c1c', '#991b1b', '#7f1d1d', '#ef4444', '#f87171'],
  purple: ['#a855f7', '#9333ea', '#7c3aed', '#6d28d9', '#5b21b6', '#4c1d95', '#581c87', '#6b21a8', '#7c2d12'],
  monochrome: ['#374151', '#4b5563', '#6b7280', '#9ca3af', '#d1d5db', '#e5e7eb', '#f3f4f6', '#f9fafb', '#111827'],
};

const CHART_SIZES = {
  small: 200,
  medium: 280,
  large: 400,
  xlarge: 500,
};

const darkTooltipStyle = {
  backgroundColor: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '8px',
  color: '#e2e8f0',
  fontSize: '12px',
};

interface ChartSpec {
  type: 'bar' | 'line' | 'pie' | 'area';
  title?: string;
  data: Array<Record<string, any>>;
  xKey: string;
  yKeys: string[];
  text?: string;
  no_data?: boolean;
  reason?: string;
}

interface ChartRendererProps {
  spec: ChartSpec | null | undefined;
}

export default function ChartRenderer({ spec }: ChartRendererProps) {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [chartType, setChartType] = useState<'bar' | 'line' | 'pie' | 'area'>('bar');
  const [colorPalette, setColorPalette] = useState<keyof typeof COLOR_PALETTES>('default');
  const [chartSize, setChartSize] = useState<keyof typeof CHART_SIZES>('medium');
  const [dataFilter, setDataFilter] = useState('');
  const [showTopN, setShowTopN] = useState<number | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  // Initialize chart type from spec
  useState(() => {
    if (spec?.type) {
      setChartType(spec.type);
    }
  });

  // Filter and process data
  const processedData = useMemo(() => {
    if (!spec?.data) return [];
    
    let filtered = spec.data;
    
    // Apply text filter
    if (dataFilter) {
      filtered = filtered.filter(item => 
        Object.values(item).some(val => 
          String(val).toLowerCase().includes(dataFilter.toLowerCase())
        )
      );
    }
    
    // Apply top N filter
    if (showTopN && spec.yKeys?.[0]) {
      filtered = [...filtered]
        .sort((a, b) => (b[spec.yKeys[0]] || 0) - (a[spec.yKeys[0]] || 0))
        .slice(0, showTopN);
    }
    
    return filtered;
  }, [spec?.data, spec?.yKeys, dataFilter, showTopN]);

  const colors = COLOR_PALETTES[colorPalette];
  const currentSpec = spec ? { 
    ...spec, 
    type: chartType, 
    data: processedData 
  } : null;

  const downloadChart = async () => {
    if (!chartRef.current) return;
    
    try {
      const svgElement = chartRef.current.querySelector('svg');
      if (!svgElement) return;

      // Create canvas
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Set canvas dimensions
      const svgRect = svgElement.getBoundingClientRect();
      canvas.width = svgRect.width * 2; // Higher resolution
      canvas.height = svgRect.height * 2;
      
      // Create image from SVG
      const svgData = new XMLSerializer().serializeToString(svgElement);
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);
      
      const img = new Image();
      img.onload = () => {
        ctx.scale(2, 2); // Scale for higher resolution
        ctx.fillStyle = '#0f172a'; // Dark background
        ctx.fillRect(0, 0, canvas.width / 2, canvas.height / 2);
        ctx.drawImage(img, 0, 0);
        
        // Download
        canvas.toBlob((blob) => {
          if (blob) {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `chart-${Date.now()}.png`;
            link.click();
          }
        });
        
        URL.revokeObjectURL(url);
      };
      img.src = url;
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  const handleZoom = (direction: 'in' | 'out' | 'reset') => {
    setZoomLevel(prev => {
      switch (direction) {
        case 'in': return Math.min(prev * 1.2, 3);
        case 'out': return Math.max(prev / 1.2, 0.5);
        case 'reset': return 1;
        default: return prev;
      }
    });
  };
  if (!currentSpec || currentSpec.no_data) {
    if (currentSpec?.reason) {
      return (
        <div className="mt-4 bg-muted/40 border border-border rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            Chart not available: {currentSpec.reason}
          </p>
        </div>
      );
    }
    return null;
  }

  if (!currentSpec.data?.length) {
    return (
      <div className="mt-4 bg-muted/40 border border-border rounded-lg p-4">
        <p className="text-sm text-muted-foreground">No data available for visualization</p>
      </div>
    );
  }

  const { type, title, data, xKey, yKeys = ['value'], text } = currentSpec;

  const chartContent = () => {
    switch (type) {
      case 'pie':
        return (
          <PieChart>
            <Pie 
              data={data} 
              dataKey={yKeys[0]} 
              nameKey={xKey} 
              cx="50%" 
              cy="50%"
              outerRadius={80} 
              label={(entry: any) => `${entry.name} ${(entry.percent * 100).toFixed(0)}%`}
              labelLine={false} 
              fontSize={11}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={colors[i % colors.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={darkTooltipStyle} />
          </PieChart>
        );
      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey={xKey} tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip contentStyle={darkTooltipStyle} />
            {yKeys.length > 1 && <Legend />}
            {yKeys.map((k, i) => (
              <Line 
                key={k} 
                type="monotone" 
                dataKey={k} 
                stroke={colors[i % colors.length]}
                strokeWidth={2} 
                dot={{ r: 3 }} 
              />
            ))}
          </LineChart>
        );
      case 'area':
        return (
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey={xKey} tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip contentStyle={darkTooltipStyle} />
            {yKeys.length > 1 && <Legend />}
            {yKeys.map((k, i) => (
              <Area 
                key={k} 
                type="monotone" 
                dataKey={k} 
                stroke={colors[i % colors.length]}
                fill={colors[i % colors.length]} 
                fillOpacity={0.2} 
              />
            ))}
          </AreaChart>
        );
      default: // bar
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey={xKey} tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip contentStyle={darkTooltipStyle} />
            {yKeys.length > 1 && <Legend />}
            {yKeys.map((k, i) => (
              <Bar 
                key={k} 
                dataKey={k} 
                fill={colors[i % colors.length]} 
                radius={[4, 4, 0, 0]} 
              />
            ))}
          </BarChart>
        );
    }
  };

  return (
    <div className="mt-4 bg-background/60 border border-border rounded-lg p-4">
      <div className="flex justify-between items-center mb-3">
        {title && (
          <p className="text-sm font-medium text-foreground">{title}</p>
        )}
        <div className="flex gap-2">
          {/* Settings Toggle */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 rounded border border-border"
            title="Chart Settings"
          >
            ⚙️
          </button>
          
          {/* Zoom Controls */}
          <div className="flex gap-1">
            <button
              onClick={() => handleZoom('out')}
              disabled={zoomLevel <= 0.5}
              className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed rounded border border-border"
              title="Zoom Out"
            >
              🔍-
            </button>
            <button
              onClick={() => handleZoom('reset')}
              className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 rounded border border-border"
              title="Reset Zoom"
            >
              ↻
            </button>
            <button
              onClick={() => handleZoom('in')}
              disabled={zoomLevel >= 3}
              className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed rounded border border-border"
              title="Zoom In"
            >
              🔍+
            </button>
          </div>
          
          {/* Download Button */}
          <button
            onClick={downloadChart}
            className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded border border-blue-600"
            title="Download Chart"
          >
            ⬇️ PNG
          </button>
        </div>
      </div>
      
      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-4 p-3 bg-muted/50 rounded border border-border space-y-3">
          {/* Data Filtering */}
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-foreground">Data Filtering</h4>
            <div className="flex gap-2 flex-wrap">
              <input
                type="text"
                placeholder="Filter data..."
                value={dataFilter}
                onChange={(e) => setDataFilter(e.target.value)}
                className="px-2 py-1 text-xs bg-background border border-border rounded flex-1 min-w-[120px]"
              />
              <select
                value={showTopN || ''}
                onChange={(e) => setShowTopN(e.target.value ? parseInt(e.target.value) : null)}
                className="px-2 py-1 text-xs bg-background border border-border rounded"
              >
                <option value="">Show All</option>
                <option value="5">Top 5</option>
                <option value="10">Top 10</option>
                <option value="20">Top 20</option>
              </select>
            </div>
          </div>
          
          {/* Chart Type */}
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-foreground">Chart Type</h4>
            <div className="flex gap-1">
              {(['bar', 'line', 'pie', 'area'] as const).map(type => (
                <button
                  key={type}
                  onClick={() => setChartType(type)}
                  className={`px-2 py-1 text-xs rounded border capitalize ${
                    chartType === type 
                      ? 'bg-blue-600 text-white border-blue-600' 
                      : 'bg-muted hover:bg-muted/80 border-border'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          
          {/* Color Palette */}
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-foreground">Color Theme</h4>
            <div className="flex gap-1 flex-wrap">
              {Object.keys(COLOR_PALETTES).map(palette => (
                <button
                  key={palette}
                  onClick={() => setColorPalette(palette as keyof typeof COLOR_PALETTES)}
                  className={`px-2 py-1 text-xs rounded border capitalize ${
                    colorPalette === palette 
                      ? 'bg-blue-600 text-white border-blue-600' 
                      : 'bg-muted hover:bg-muted/80 border-border'
                  }`}
                  title={palette}
                >
                  <div className="flex gap-1">
                    {COLOR_PALETTES[palette as keyof typeof COLOR_PALETTES].slice(0, 3).map((color, i) => (
                      <div key={i} className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Chart Size */}
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-foreground">Chart Size</h4>
            <div className="flex gap-1">
              {Object.keys(CHART_SIZES).map(size => (
                <button
                  key={size}
                  onClick={() => setChartSize(size as keyof typeof CHART_SIZES)}
                  className={`px-2 py-1 text-xs rounded border capitalize ${
                    chartSize === size 
                      ? 'bg-blue-600 text-white border-blue-600' 
                      : 'bg-muted hover:bg-muted/80 border-border'
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      
      <div 
        ref={chartRef}
        style={{ 
          width: '100%', 
          height: Math.round(CHART_SIZES[chartSize] * zoomLevel),
          transition: 'height 0.2s ease',
          overflow: 'hidden'
        }}
      >
        <ResponsiveContainer width="100%" height="100%">
          {chartContent()}
        </ResponsiveContainer>
      </div>
      
      {text && (
        <p className="text-xs text-muted-foreground mt-2">{text}</p>
      )}
      
      <div className="flex justify-between items-center mt-2">
        <div className="text-xs text-muted-foreground">
          Showing {processedData.length} of {spec?.data?.length || 0} records
        </div>
        {zoomLevel !== 1 && (
          <p className="text-xs text-muted-foreground">
            Zoom: {Math.round(zoomLevel * 100)}%
          </p>
        )}
      </div>
    </div>
  );
}