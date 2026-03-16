import { type ComponentProps, memo } from 'react';
import { DatabricksMessageCitationStreamdownIntegration } from '../databricks-message-citation';
import { Streamdown } from 'streamdown';

type ResponseProps = ComponentProps<typeof Streamdown>;

// Function to detect and extract visualization content with base64 data
function parseVisualizationContent(content: string): {
  isVisualization: boolean;
  displayContent: string;
  imageData?: string;
} {
  // Check if this is a visualization response
  if (content.includes('✅ **Visualization Created Successfully')) {
    // Look for base64 image data
    const base64Pattern = /!\[Chart\]\(data:image\/png;base64,([A-Za-z0-9+/=]+)\)/;
    const base64Match = content.match(base64Pattern);
    
    if (base64Match && base64Match[1]) {
      const imageData = base64Match[1];
      const displayContent = content.replace(base64Pattern, '').trim();
      
      return {
        isVisualization: true,
        displayContent,
        imageData
      };
    }
    
    // Check for URL-based images  
    const urlPattern = /!\[Chart\]\(([^)]+)\)/;
    const urlMatch = content.match(urlPattern);
    
    if (urlMatch) {
      return {
        isVisualization: true,
        displayContent: content.replace(urlPattern, '').trim() + `\n\n**Chart URL:** ${urlMatch[1]}`
      };
    }
  }
  
  return {
    isVisualization: false,
    displayContent: content
  };
}

export const Response = memo(
  (props: ResponseProps) => {
    const content = props.children?.toString() || '';
    const { isVisualization, displayContent, imageData } = parseVisualizationContent(content);
    
    return (
      <div className="response-container">
        {/* Regular markdown content */}
        <Streamdown
          components={{
            a: DatabricksMessageCitationStreamdownIntegration,
          }}
          className="flex flex-col gap-4"
          {...props}
        >
          {displayContent}
        </Streamdown>
        
        {/* Visualization image display */}
        {isVisualization && imageData && (
          <div className="visualization-display mt-4 p-4 border rounded-lg bg-gray-50">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">📊</span>
              <h4 className="font-medium text-sm">Generated Visualization</h4>
            </div>
            <div className="visualization-image bg-white p-2 rounded border">
              <img
                src={`data:image/png;base64,${imageData}`}
                alt="Generated Chart"
                className="max-w-full h-auto mx-auto block"
                style={{ maxHeight: '500px' }}
              />
            </div>
            <p className="text-xs text-gray-600 mt-2 text-center">
              Interactive chart generated from your data
            </p>
          </div>
        )}
      </div>
    );
  },
  (prevProps, nextProps) => prevProps.children === nextProps.children,
);

Response.displayName = 'Response';
