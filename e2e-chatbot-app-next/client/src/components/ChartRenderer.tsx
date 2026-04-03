import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';

const COLORS = [
  '#2dd4bf', '#38bdf8', '#a78bfa', '#fb923c', '#f87171',
  '#4ade80', '#facc15', '#e879f9', '#94a3b8',
];

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
  if (!spec || spec.no_data) {
    if (spec?.reason) {
      return (
        <div className="mt-4 bg-muted/40 border border-border rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            Chart not available: {spec.reason}
          </p>
        </div>
      );
    }
    return null;
  }

  if (!spec.data?.length) {
    return (
      <div className="mt-4 bg-muted/40 border border-border rounded-lg p-4">
        <p className="text-sm text-muted-foreground">No data available for visualization</p>
      </div>
    );
  }

  const { type, title, data, xKey, yKeys = ['value'], text } = spec;

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
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={false} 
              fontSize={11}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
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
                stroke={COLORS[i % COLORS.length]}
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
                stroke={COLORS[i % COLORS.length]}
                fill={COLORS[i % COLORS.length]} 
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
                fill={COLORS[i % COLORS.length]} 
                radius={[4, 4, 0, 0]} 
              />
            ))}
          </BarChart>
        );
    }
  };

  return (
    <div className="mt-4 bg-background/60 border border-border rounded-lg p-4">
      {title && (
        <p className="text-sm font-medium text-foreground mb-3">{title}</p>
      )}
      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>{chartContent()}</ResponsiveContainer>
      </div>
      {text && (
        <p className="text-xs text-muted-foreground mt-2">{text}</p>
      )}
    </div>
  );
}