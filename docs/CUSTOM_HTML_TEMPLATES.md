# Custom HTML Templates for LangExtract Visualizations

This guide explains how to customize the HTML visualization that shows extracted data traced back to the source document.

## Overview

LangExtract's default visualization creates an interactive HTML page showing:
- Highlighted extractions in the source text
- Animation controls to step through extractions
- Tooltips with extraction details
- Character position information

With custom templates, you can:
- Change colors, fonts, and layout
- Add custom functionality (export, print, etc.)
- Create domain-specific visualizations
- Build reusable template libraries

## Quick Start

### Using Built-in Templates

```python
from langextract_extensions import visualize_with_template, DarkModeTemplate

# Use dark mode template
html = visualize_with_template(
    "results.jsonl",
    template=DarkModeTemplate()
)

# Save to file
with open("dark_visualization.html", "w") as f:
    f.write(html)
```

### Available Built-in Templates

1. **DarkModeTemplate** - Dark background with light text
2. **MinimalTemplate** - Clean, distraction-free design
3. **CompactTemplate** - Side-by-side layout for better space usage

## Creating Custom Templates

### Method 1: Quick Customization

```python
from langextract_extensions import create_custom_template

template = create_custom_template(
    css_overrides={
        'button_bg': '#e91e63',  # Pink buttons
        'text_font_family': 'Georgia, serif',
        'text_line_height': '2.0'
    },
    custom_css='''
    .lx-highlight { 
        border: 1px solid currentColor;
    }
    ''',
    header_html='<h2>Document Analysis</h2>',
    custom_buttons=[
        '<button onclick="exportData()">Export</button>'
    ]
)

html = visualize_with_template("results.jsonl", template)
```

### Method 2: Template Class

```python
from langextract_extensions import HTMLTemplate

class MyTemplate(HTMLTemplate):
    def get_css_variables(self, **kwargs):
        vars = super().get_css_variables(**kwargs)
        vars.update({
            'button_bg': '#007acc',
            'controls_bg': '#f0f0f0'
        })
        return vars
```

## Customizable Elements

### CSS Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `highlight_border_radius` | `3px` | Rounded corners for highlights |
| `highlight_padding` | `1px 2px` | Space inside highlights |
| `button_bg` | `#4285f4` | Button background color |
| `button_hover_bg` | `#3367d6` | Button hover color |
| `text_font_family` | `monospace` | Font for document text |
| `text_line_height` | `1.6` | Line spacing |
| `text_max_height` | `260px` | Maximum height before scroll |
| `controls_bg` | `#fafafa` | Control panel background |
| `tooltip_bg` | `#333` | Tooltip background |
| `tooltip_color` | `#fff` | Tooltip text color |

### HTML Structure

You can customize these sections:
- `header_html` - Content above the main visualization
- `footer_html` - Content below the controls
- `buttons_html` - Custom control buttons
- `status_html` - Status display format

### JavaScript Functionality

Add custom JavaScript:
- `custom_js_vars` - Additional variables
- `custom_js_functions` - New functions
- `custom_js_init` - Initialization code
- `update_display_custom` - Hook into display updates

## Examples

### Professional Legal Template

```python
class LegalTemplate(HTMLTemplate):
    def get_css_variables(self, **kwargs):
        vars = super().get_css_variables(**kwargs)
        vars.update({
            'button_bg': '#1a237e',  # Deep blue
            'text_font_family': 'Times New Roman, serif',
            'text_bg': '#fffef7',  # Ivory background
            'custom_css': '''
            .lx-animated-wrapper {
                max-width: 800px;
                margin: 0 auto;
            }
            @media print {
                .lx-controls { display: none; }
            }
            '''
        })
        return vars
```

### Export-Enabled Template

```python
template = create_custom_template(
    custom_buttons=[
        '<button onclick="exportJSON()">Export JSON</button>',
        '<button onclick="exportCSV()">Export CSV</button>'
    ],
    custom_js='''
    function exportJSON() {
        const blob = new Blob([JSON.stringify(extractions, null, 2)], 
                            {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'extractions.json';
        a.click();
    }
    '''
)
```

### Financial Document Template

```python
class FinancialTemplate(HTMLTemplate):
    def get_css_variables(self, **kwargs):
        vars = super().get_css_variables(**kwargs)
        vars['custom_css'] = '''
        .lx-highlight[data-class="amount"] {
            background: #c8e6c9 !important;
            border: 1px solid #4caf50;
        }
        '''
        return vars
    
    def get_js_variables(self, **kwargs):
        vars = super().get_js_variables(**kwargs)
        vars['custom_js_init'] = '''
        // Calculate total of all amounts
        const amounts = extractions.filter(e => e.class === 'amount');
        let total = 0;
        amounts.forEach(amt => {
            const value = parseFloat(amt.text.replace(/[^0-9.-]+/g, ''));
            if (!isNaN(value)) total += value;
        });
        console.log('Total:', total);
        '''
        return vars
```

## Reusable Templates

Save templates as Python files:

```python
# my_template.py
from langextract_extensions.custom_visualization import HTMLTemplate

class BrandedTemplate(HTMLTemplate):
    def get_css_variables(self, **kwargs):
        # Your customizations
        pass
```

Load and use:

```python
from langextract_extensions import load_template_from_file

template = load_template_from_file('my_template.py')
html = visualize_with_template('results.jsonl', template)
```

## Advanced Features

### Dynamic Content

Access extraction data in templates:

```python
def get_html_variables(self, **kwargs):
    extractions = kwargs.get('extractions', [])
    
    # Count by class
    class_counts = {}
    for ext in extractions:
        class_counts[ext.extraction_class] = class_counts.get(ext.extraction_class, 0) + 1
    
    # Build summary
    summary = '<div class="summary">'
    for cls, count in class_counts.items():
        summary += f'<p>{cls}: {count} found</p>'
    summary += '</div>'
    
    vars = super().get_html_variables(**kwargs)
    vars['header_html'] = summary
    return vars
```

### Conditional Styling

Style based on extraction attributes:

```python
vars['custom_css'] = '''
/* Highlight high-value amounts */
.lx-highlight[data-class="amount"]:has(.lx-attr-value:contains("principal")) {
    background: #ffeb3b !important;
    font-weight: bold;
}
'''
```

### Integration with External Libraries

Add Chart.js for visualizations:

```python
vars['header_html'] = '''
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<canvas id="extractionChart" width="400" height="200"></canvas>
'''

vars['custom_js_init'] = '''
// Create chart of extraction classes
const ctx = document.getElementById('extractionChart').getContext('2d');
const classCounts = {};
extractions.forEach(e => {
    classCounts[e.class] = (classCounts[e.class] || 0) + 1;
});

new Chart(ctx, {
    type: 'bar',
    data: {
        labels: Object.keys(classCounts),
        datasets: [{
            label: 'Extractions',
            data: Object.values(classCounts),
            backgroundColor: '#4285f4'
        }]
    }
});
'''
```

## Best Practices

1. **Preserve Core Functionality**: Don't remove essential elements like extraction highlighting
2. **Test Responsiveness**: Ensure templates work on different screen sizes
3. **Consider Printing**: Add print-friendly styles if needed
4. **Document Templates**: Add comments explaining customizations
5. **Version Control**: Save templates in your repository

## Troubleshooting

### Extractions Not Highlighting

Make sure your template preserves:
- The `data-idx` attributes on spans
- The `.lx-current-highlight` class functionality
- The JavaScript that adds/removes highlight classes

### Buttons Not Working

Ensure JavaScript functions are in the global scope:
```javascript
window.myFunction = myFunction;
```

### Styles Not Applying

Check CSS specificity. Use `!important` if needed:
```css
.lx-highlight {
    background: #yellow !important;
}
```

## Full Example

See [examples/custom_html_templates.py](../examples/custom_html_templates.py) for complete working examples of all template types.