import type { FC } from 'react';
import { cn } from '@/lib/utils';

interface VisualizationDisplayProps {
  imageData: string;
  title?: string;
  size?: number;
  className?: string;
}

export const VisualizationDisplay: FC<VisualizationDisplayProps> = ({
  imageData,
  title = "Generated Visualization",
  size,
  className
}) => {
  return (
    <div className={cn(
      "visualization-container rounded-lg border bg-muted/20 p-4 my-4",
      className
    )}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-foreground">
          📊 {title}
        </h4>
        {size && (
          <span className="text-xs text-muted-foreground">
            {Math.round(size / 1024)}KB
          </span>
        )}
      </div>
      
      <div className="visualization-image-wrapper rounded-md overflow-hidden bg-white">
        <img
          src={`data:image/png;base64,${imageData}`}
          alt={title}
          className="w-full h-auto max-w-full"
          style={{ display: 'block', margin: '0 auto' }}
          loading="lazy"
        />
      </div>
      
      <p className="text-xs text-muted-foreground mt-2 text-center">
        Interactive visualization generated from your data
      </p>
    </div>
  );
};