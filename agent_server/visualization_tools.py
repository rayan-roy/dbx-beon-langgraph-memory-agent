"""LangGraph tools for creating secure data visualizations.

This module provides visualization tools that are restricted to matplotlib and seaborn
for security. Plots are returned as base64-encoded images for direct display in chat UI.
"""

import base64
import io
import logging
import sys
from typing import Optional, Dict, Any

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Set default style
plt.style.use('default')
sns.set_palette("husl")


def visualization_tools():
    """Factory function returning secure visualization tools for the agent.

    Returns a list of tools:
    - create_visualization: Create plots using matplotlib/seaborn with data from CSV tools
    
    Security features:
    - Only allows matplotlib, seaborn, pandas, numpy imports
    - Executes in restricted environment
    - Returns base64 image for direct UI display
    """

    @tool
    async def create_visualization(
        plot_code: str, 
        data_input: str = "",
        config: RunnableConfig = None
    ) -> str:
        """Create a data visualization using matplotlib and seaborn.

        This tool safely executes visualization code using only matplotlib and seaborn.
        The plot is returned as a base64 image for display in the chat UI.

        Args:
            plot_code: Python code for creating the visualization. Should use 'data' variable 
                      if data_input is provided. Only matplotlib, seaborn, pandas, numpy allowed.
            data_input: Optional CSV data as string (from get_all_csv_data tool). 
                       Will be available as 'data' DataFrame in the plot code.

        Example:
            plot_code = '''
            plt.figure(figsize=(10, 6))
            sns.histplot(data['column_name'])
            plt.title('Distribution of Column Name')
            plt.xlabel('Values')
            plt.ylabel('Frequency')
            '''
        """
        try:
            # Create a restricted environment for code execution
            restricted_globals = {
                '__builtins__': {
                    'len': len, 'range': range, 'enumerate': enumerate,
                    'zip': zip, 'map': map, 'filter': filter,
                    'sum': sum, 'max': max, 'min': min, 'abs': abs,
                    'round': round, 'sorted': sorted, 'list': list,
                    'dict': dict, 'set': set, 'tuple': tuple,
                    'str': str, 'int': int, 'float': float,
                    'print': print  # For debugging
                },
                'plt': plt,
                'sns': sns,
                'pd': pd,
                'np': np,
                'matplotlib': matplotlib
            }

            # Prepare data if provided
            if data_input.strip():
                try:
                    # Convert CSV string to DataFrame
                    from io import StringIO
                    data = pd.read_csv(StringIO(data_input))
                    restricted_globals['data'] = data
                except Exception as e:
                    return f"Error parsing data input: {str(e)}\nPlease ensure data is in valid CSV format."

            # Security check: scan for potentially dangerous operations
            dangerous_patterns = [
                'import ', 'from ', '__import__', 'exec(', 'eval(',
                'open(', 'file(', 'input(', 'raw_input(',
                'os.', 'sys.', 'subprocess', 'pickle',
                'globals(', 'locals(', 'vars(', 'dir(',
                'setattr(', 'getattr(', 'delattr(', 'hasattr('
            ]
            
            plot_code_lower = plot_code.lower()
            for pattern in dangerous_patterns:
                if pattern in plot_code_lower:
                    return f"Security error: '{pattern}' is not allowed in visualization code."

            # Clear any existing plots
            plt.clf()
            plt.close('all')
            
            # Execute the plot code
            exec(plot_code, restricted_globals)
            
            # Save plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            
            # Get the image as base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            buffer.close()
            
            # Clear the plot
            plt.clf()
            plt.close('all')
            
            # Return the image in a format that can be displayed in chat UI
            return f"![Visualization](data:image/png;base64,{image_base64})"
            
        except Exception as e:
            # Clear any plots on error
            plt.clf() 
            plt.close('all')
            return f"Error creating visualization: {str(e)}\n\nPlease check your plot code syntax and ensure you're only using matplotlib, seaborn, pandas, and numpy functions."

    @tool 
    async def list_visualization_examples(config: RunnableConfig = None) -> str:
        """Get examples of visualization code patterns that work with create_visualization tool."""
        
        examples = """
**Visualization Examples:**

**1. Histogram:**
```python
plt.figure(figsize=(10, 6))
sns.histplot(data['column_name'])
plt.title('Distribution of Column Name')
plt.xlabel('Values')
plt.ylabel('Frequency')
```

**2. Scatter Plot:**
```python
plt.figure(figsize=(10, 6))
sns.scatterplot(data=data, x='column1', y='column2')
plt.title('Relationship between Column1 and Column2')
```

**3. Box Plot:**
```python
plt.figure(figsize=(10, 6))
sns.boxplot(data=data, x='category_column', y='numeric_column')
plt.title('Distribution by Category')
plt.xticks(rotation=45)
```

**4. Line Plot:**
```python
plt.figure(figsize=(12, 6))
plt.plot(data['x_column'], data['y_column'], marker='o')
plt.title('Trend Over Time')
plt.xlabel('X Axis')
plt.ylabel('Y Axis')
plt.grid(True)
```

**5. Correlation Heatmap:**
```python
plt.figure(figsize=(10, 8))
correlation_matrix = data.select_dtypes(include=[np.number]).corr()
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Correlation Matrix')
```

**Tips:**
- Always start with `plt.figure(figsize=(width, height))`
- Use `data` variable to access CSV data when provided
- Only matplotlib, seaborn, pandas, and numpy are available
- Plots are automatically displayed in chat - no need to call plt.show()
"""
        return examples

    return [create_visualization, list_visualization_examples]