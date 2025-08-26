"""
Custom HTML visualization templates for LangExtract.

This module provides customizable HTML templates for visualizing extractions,
allowing users to modify the appearance, layout, and behavior of the visualization.
"""

import html
import json
import pathlib
import textwrap
from typing import Optional, Dict, List, Union
from string import Template

from langextract import data as _data
from langextract import io as _io
from langextract import visualization as _viz


class HTMLTemplate:
    """Base class for custom HTML templates."""
    
    def __init__(self, 
                 css_template: Optional[str] = None,
                 html_template: Optional[str] = None,
                 js_template: Optional[str] = None):
        """Initialize custom template with optional overrides.
        
        Args:
            css_template: Custom CSS template (uses Template strings)
            html_template: Custom HTML structure template 
            js_template: Custom JavaScript template
        """
        self.css_template = css_template or self.DEFAULT_CSS_TEMPLATE
        self.html_template = html_template or self.DEFAULT_HTML_TEMPLATE
        self.js_template = js_template or self.DEFAULT_JS_TEMPLATE
    
    # Default templates based on LangExtract's visualization
    DEFAULT_CSS_TEMPLATE = """
    <style>
    /* Base styles */
    .lx-highlight { 
        position: relative; 
        border-radius: ${highlight_border_radius}; 
        padding: ${highlight_padding};
    }
    
    /* Tooltip styles */
    .lx-highlight .lx-tooltip {
        visibility: hidden;
        opacity: 0;
        transition: opacity ${tooltip_transition};
        background: ${tooltip_bg};
        color: ${tooltip_color};
        text-align: left;
        border-radius: ${tooltip_radius};
        padding: ${tooltip_padding};
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        font-size: ${tooltip_font_size};
        max-width: ${tooltip_max_width};
        white-space: normal;
        box-shadow: ${tooltip_shadow};
    }
    
    .lx-highlight:hover .lx-tooltip { 
        visibility: visible; 
        opacity: 1; 
    }
    
    /* Main wrapper */
    .lx-animated-wrapper { 
        max-width: 100%; 
        font-family: ${main_font_family}; 
    }
    
    /* Controls panel */
    .lx-controls {
        background: ${controls_bg}; 
        border: ${controls_border}; 
        border-radius: ${controls_radius};
        padding: ${controls_padding}; 
        margin-bottom: ${controls_margin};
    }
    
    /* Buttons */
    .lx-control-btn {
        background: ${button_bg}; 
        color: ${button_color}; 
        border: ${button_border}; 
        border-radius: ${button_radius};
        padding: ${button_padding}; 
        cursor: pointer; 
        font-size: ${button_font_size}; 
        font-weight: ${button_font_weight};
        transition: background-color ${button_transition};
    }
    
    .lx-control-btn:hover { 
        background: ${button_hover_bg}; 
    }
    
    /* Text window */
    .lx-text-window {
        font-family: ${text_font_family}; 
        white-space: pre-wrap; 
        border: ${text_border};
        padding: ${text_padding}; 
        max-height: ${text_max_height}; 
        overflow-y: auto; 
        margin-bottom: ${text_margin};
        line-height: ${text_line_height};
        background: ${text_bg};
    }
    
    /* Current highlight */
    .lx-current-highlight {
        border-bottom: ${current_highlight_border};
        font-weight: ${current_highlight_weight};
        animation: lx-pulse ${pulse_duration} ease-in-out;
    }
    
    @keyframes lx-pulse {
        0% { border-bottom-color: ${pulse_color_start}; }
        50% { border-bottom-color: ${pulse_color_mid}; }
        100% { border-bottom-color: ${pulse_color_end}; }
    }
    
    /* Custom styles */
    ${custom_css}
    </style>
    """
    
    DEFAULT_HTML_TEMPLATE = """
    <div class="lx-animated-wrapper">
        ${header_html}
        
        <div class="lx-attributes-panel">
            ${legend_html}
            <div id="attributesContainer"></div>
        </div>
        
        <div class="lx-text-window" id="textWindow">
            ${highlighted_text}
        </div>
        
        <div class="lx-controls">
            <div class="lx-button-row">
                ${buttons_html}
            </div>
            <div class="lx-progress-container">
                <input type="range" id="progressSlider" class="lx-progress-slider"
                       min="0" max="${max_index}" value="0"
                       onchange="jumpToExtraction(this.value)">
            </div>
            <div class="lx-status-text">
                ${status_html}
            </div>
        </div>
        
        ${footer_html}
    </div>
    """
    
    DEFAULT_JS_TEMPLATE = """
    <script>
    (function() {
        const extractions = ${extractions_json};
        let currentIndex = 0;
        let isPlaying = false;
        let animationInterval = null;
        let animationSpeed = ${animation_speed};
        
        ${custom_js_vars}
        
        function updateDisplay() {
            const extraction = extractions[currentIndex];
            if (!extraction) return;
            
            ${update_display_custom}
            
            // Default update logic
            document.getElementById('attributesContainer').innerHTML = extraction.attributesHtml;
            document.getElementById('entityInfo').textContent = (currentIndex + 1) + '/' + extractions.length;
            document.getElementById('posInfo').textContent = '[' + extraction.startPos + '-' + extraction.endPos + ']';
            document.getElementById('progressSlider').value = currentIndex;
            
            const playBtn = document.querySelector('.lx-control-btn');
            if (playBtn) playBtn.textContent = isPlaying ? '⏸ Pause' : '▶️ Play';
            
            // Highlight current extraction
            const prevHighlight = document.querySelector('.lx-text-window .lx-current-highlight');
            if (prevHighlight) prevHighlight.classList.remove('lx-current-highlight');
            const currentSpan = document.querySelector('.lx-text-window span[data-idx="' + currentIndex + '"]');
            if (currentSpan) {
                currentSpan.classList.add('lx-current-highlight');
                currentSpan.scrollIntoView({block: 'center', behavior: 'smooth'});
            }
        }
        
        function nextExtraction() {
            currentIndex = (currentIndex + 1) % extractions.length;
            updateDisplay();
        }
        
        function prevExtraction() {
            currentIndex = (currentIndex - 1 + extractions.length) % extractions.length;
            updateDisplay();
        }
        
        function jumpToExtraction(index) {
            currentIndex = parseInt(index);
            updateDisplay();
        }
        
        function playPause() {
            if (isPlaying) {
                clearInterval(animationInterval);
                isPlaying = false;
            } else {
                animationInterval = setInterval(nextExtraction, animationSpeed * 1000);
                isPlaying = true;
            }
            updateDisplay();
        }
        
        ${custom_js_functions}
        
        // Make functions available globally
        window.playPause = playPause;
        window.nextExtraction = nextExtraction;
        window.prevExtraction = prevExtraction;
        window.jumpToExtraction = jumpToExtraction;
        
        // Initialize
        updateDisplay();
        ${custom_js_init}
    })();
    </script>
    """
    
    def render(self, 
               text: str,
               extractions: List[_data.Extraction],
               color_map: Dict[str, str],
               **kwargs) -> str:
        """Render the complete HTML visualization with custom template."""
        # Build the highlighted text using core function
        highlighted_text = _viz._build_highlighted_text(text, extractions, color_map)
        
        # Build extraction data
        extraction_data = _viz._prepare_extraction_data(text, extractions, color_map)
        
        # Build legend
        legend_html = _viz._build_legend_html(color_map) if kwargs.get('show_legend', True) else ''
        
        # Prepare template variables
        css_vars = self.get_css_variables(**kwargs)
        html_vars = self.get_html_variables(
            highlighted_text=highlighted_text,
            legend_html=legend_html,
            extractions=extractions,
            **kwargs
        )
        js_vars = self.get_js_variables(
            extraction_data=extraction_data,
            **kwargs
        )
        
        # Render templates
        css = Template(self.css_template).safe_substitute(**css_vars)
        html_content = Template(self.html_template).safe_substitute(**html_vars)
        js = Template(self.js_template).safe_substitute(**js_vars)
        
        return css + html_content + js
    
    def get_css_variables(self, **kwargs) -> Dict[str, str]:
        """Get CSS template variables. Override to customize."""
        return {
            # Highlights
            'highlight_border_radius': kwargs.get('highlight_border_radius', '3px'),
            'highlight_padding': kwargs.get('highlight_padding', '1px 2px'),
            
            # Tooltips
            'tooltip_transition': kwargs.get('tooltip_transition', '0.2s ease-in-out'),
            'tooltip_bg': kwargs.get('tooltip_bg', '#333'),
            'tooltip_color': kwargs.get('tooltip_color', '#fff'),
            'tooltip_radius': kwargs.get('tooltip_radius', '4px'),
            'tooltip_padding': kwargs.get('tooltip_padding', '6px 8px'),
            'tooltip_font_size': kwargs.get('tooltip_font_size', '12px'),
            'tooltip_max_width': kwargs.get('tooltip_max_width', '240px'),
            'tooltip_shadow': kwargs.get('tooltip_shadow', '0 2px 6px rgba(0,0,0,0.3)'),
            
            # Main
            'main_font_family': kwargs.get('main_font_family', 'Arial, sans-serif'),
            
            # Controls
            'controls_bg': kwargs.get('controls_bg', '#fafafa'),
            'controls_border': kwargs.get('controls_border', '1px solid #90caf9'),
            'controls_radius': kwargs.get('controls_radius', '8px'),
            'controls_padding': kwargs.get('controls_padding', '12px'),
            'controls_margin': kwargs.get('controls_margin', '16px'),
            
            # Buttons
            'button_bg': kwargs.get('button_bg', '#4285f4'),
            'button_color': kwargs.get('button_color', 'white'),
            'button_border': kwargs.get('button_border', 'none'),
            'button_radius': kwargs.get('button_radius', '4px'),
            'button_padding': kwargs.get('button_padding', '8px 16px'),
            'button_font_size': kwargs.get('button_font_size', '13px'),
            'button_font_weight': kwargs.get('button_font_weight', '500'),
            'button_transition': kwargs.get('button_transition', '0.2s'),
            'button_hover_bg': kwargs.get('button_hover_bg', '#3367d6'),
            
            # Text window
            'text_font_family': kwargs.get('text_font_family', 'monospace'),
            'text_border': kwargs.get('text_border', '1px solid #90caf9'),
            'text_padding': kwargs.get('text_padding', '12px'),
            'text_max_height': kwargs.get('text_max_height', '260px'),
            'text_margin': kwargs.get('text_margin', '12px'),
            'text_line_height': kwargs.get('text_line_height', '1.6'),
            'text_bg': kwargs.get('text_bg', 'white'),
            
            # Current highlight
            'current_highlight_border': kwargs.get('current_highlight_border', '4px solid #ff4444'),
            'current_highlight_weight': kwargs.get('current_highlight_weight', 'bold'),
            
            # Pulse animation
            'pulse_duration': kwargs.get('pulse_duration', '1s'),
            'pulse_color_start': kwargs.get('pulse_color_start', '#ff4444'),
            'pulse_color_mid': kwargs.get('pulse_color_mid', '#ff0000'),
            'pulse_color_end': kwargs.get('pulse_color_end', '#ff4444'),
            
            # Custom CSS
            'custom_css': kwargs.get('custom_css', ''),
        }
    
    def get_html_variables(self, **kwargs) -> Dict[str, str]:
        """Get HTML template variables. Override to customize."""
        extractions = kwargs.get('extractions', [])
        
        # Default buttons
        buttons = kwargs.get('buttons', [
            '<button class="lx-control-btn" onclick="playPause()">▶️ Play</button>',
            '<button class="lx-control-btn" onclick="prevExtraction()">⏮ Previous</button>',
            '<button class="lx-control-btn" onclick="nextExtraction()">⏭ Next</button>',
        ])
        
        # Status template
        status_template = kwargs.get('status_template', 
            'Entity <span id="entityInfo">1/${total}</span> | '
            'Pos <span id="posInfo">${first_pos}</span>'
        )
        
        first_pos = '[0-0]'
        if extractions and extractions[0].char_interval:
            first_pos = f'[{extractions[0].char_interval.start_pos}-{extractions[0].char_interval.end_pos}]'
        
        status_html = Template(status_template).safe_substitute(
            total=len(extractions),
            first_pos=first_pos
        )
        
        return {
            'header_html': kwargs.get('header_html', ''),
            'footer_html': kwargs.get('footer_html', ''),
            'highlighted_text': kwargs.get('highlighted_text', ''),
            'legend_html': kwargs.get('legend_html', ''),
            'buttons_html': '\n'.join(buttons),
            'status_html': status_html,
            'max_index': len(extractions) - 1 if extractions else 0,
        }
    
    def get_js_variables(self, **kwargs) -> Dict[str, str]:
        """Get JavaScript template variables. Override to customize."""
        extraction_data = kwargs.get('extraction_data', [])
        
        return {
            'extractions_json': json.dumps(extraction_data),
            'animation_speed': kwargs.get('animation_speed', 1.0),
            'custom_js_vars': kwargs.get('custom_js_vars', ''),
            'custom_js_functions': kwargs.get('custom_js_functions', ''),
            'custom_js_init': kwargs.get('custom_js_init', ''),
            'update_display_custom': kwargs.get('update_display_custom', ''),
        }


class MinimalTemplate(HTMLTemplate):
    """A minimal, clean template focusing on the text."""
    
    def get_css_variables(self, **kwargs):
        vars = super().get_css_variables(**kwargs)
        vars.update({
            'controls_bg': '#f5f5f5',
            'controls_border': 'none',
            'controls_radius': '0',
            'button_bg': '#666',
            'button_hover_bg': '#333',
            'text_border': 'none',
            'text_bg': '#fafafa',
            'text_padding': '20px',
            'text_max_height': '500px',
        })
        return vars


class DarkModeTemplate(HTMLTemplate):
    """A dark mode template."""
    
    def get_css_variables(self, **kwargs):
        vars = super().get_css_variables(**kwargs)
        vars.update({
            'controls_bg': '#1e1e1e',
            'controls_border': '1px solid #444',
            'text_bg': '#121212',
            'text_border': '1px solid #444',
            'tooltip_bg': '#fff',
            'tooltip_color': '#000',
            'button_bg': '#007acc',
            'button_hover_bg': '#005a9e',
            'custom_css': '''
            .lx-animated-wrapper { background: #121212; color: #e0e0e0; }
            .lx-text-window { color: #e0e0e0; }
            .lx-status-text { color: #888; }
            .lx-attributes-panel { background: #1e1e1e; color: #e0e0e0; border: 1px solid #444; }
            '''
        })
        return vars


class CompactTemplate(HTMLTemplate):
    """A compact template with side-by-side layout."""
    
    DEFAULT_HTML_TEMPLATE = """
    <div class="lx-animated-wrapper lx-compact">
        <div class="lx-compact-container">
            <div class="lx-compact-left">
                <div class="lx-text-window" id="textWindow">
                    ${highlighted_text}
                </div>
            </div>
            <div class="lx-compact-right">
                <div class="lx-attributes-panel">
                    ${legend_html}
                    <div id="attributesContainer"></div>
                </div>
                <div class="lx-controls">
                    ${buttons_html}
                    <div class="lx-progress-container">
                        <input type="range" id="progressSlider" class="lx-progress-slider"
                               min="0" max="${max_index}" value="0"
                               onchange="jumpToExtraction(this.value)">
                    </div>
                    <div class="lx-status-text">
                        ${status_html}
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    
    def get_css_variables(self, **kwargs):
        vars = super().get_css_variables(**kwargs)
        vars['custom_css'] = '''
        .lx-compact-container {
            display: flex;
            gap: 20px;
        }
        .lx-compact-left {
            flex: 2;
        }
        .lx-compact-right {
            flex: 1;
            position: sticky;
            top: 0;
            height: fit-content;
        }
        .lx-compact .lx-text-window {
            max-height: 600px;
            margin-bottom: 0;
        }
        .lx-compact .lx-button-row {
            flex-direction: column;
            gap: 4px;
        }
        .lx-compact .lx-control-btn {
            width: 100%;
        }
        '''
        return vars


def visualize_with_template(
    data_source: Union[_data.AnnotatedDocument, str, pathlib.Path],
    template: Optional[HTMLTemplate] = None,
    **kwargs
) -> str:
    """
    Visualize extractions with a custom HTML template.
    
    Args:
        data_source: Either an AnnotatedDocument or path to a JSONL file
        template: Custom HTMLTemplate instance (defaults to base template)
        **kwargs: Additional parameters passed to template rendering
        
    Returns:
        Complete HTML string for visualization
        
    Example:
        # Use built-in dark mode template
        html = visualize_with_template(
            "results.jsonl",
            template=DarkModeTemplate()
        )
        
        # Or customize specific aspects
        html = visualize_with_template(
            "results.jsonl",
            button_bg='#ff5722',
            text_max_height='400px'
        )
    """
    # Load document if needed
    if isinstance(data_source, (str, pathlib.Path)):
        file_path = pathlib.Path(data_source)
        if not file_path.exists():
            raise FileNotFoundError(f'JSONL file not found: {file_path}')
        
        documents = list(_io.load_annotated_documents_jsonl(file_path))
        if not documents:
            raise ValueError(f'No documents found in JSONL file: {file_path}')
        
        annotated_doc = documents[0]
    else:
        annotated_doc = data_source
    
    if not annotated_doc or annotated_doc.text is None:
        raise ValueError('Document must contain text to visualize.')
    
    if annotated_doc.extractions is None:
        raise ValueError('Document must contain extractions to visualize.')
    
    # Filter valid extractions
    valid_extractions = _viz._filter_valid_extractions(annotated_doc.extractions)
    
    if not valid_extractions:
        return '<div class="lx-animated-wrapper"><p>No valid extractions to animate.</p></div>'
    
    # Sort extractions properly
    def _extraction_sort_key(extraction):
        start = extraction.char_interval.start_pos
        end = extraction.char_interval.end_pos
        span_length = end - start
        return (start, -span_length)
    
    sorted_extractions = sorted(valid_extractions, key=_extraction_sort_key)
    
    # Get color map
    color_map = _viz._assign_colors(sorted_extractions)
    
    # Use template to render
    if template is None:
        template = HTMLTemplate()
    
    return template.render(
        text=annotated_doc.text,
        extractions=sorted_extractions,
        color_map=color_map,
        **kwargs
    )


def create_custom_template(
    css_overrides: Optional[Dict[str, str]] = None,
    custom_css: Optional[str] = None,
    custom_buttons: Optional[List[str]] = None,
    header_html: Optional[str] = None,
    footer_html: Optional[str] = None,
    custom_js: Optional[str] = None
) -> HTMLTemplate:
    """
    Create a custom template with specific overrides.
    
    Args:
        css_overrides: Dictionary of CSS variable overrides
        custom_css: Additional CSS rules
        custom_buttons: List of custom button HTML strings
        header_html: HTML to insert at the top
        footer_html: HTML to insert at the bottom
        custom_js: Additional JavaScript code
        
    Returns:
        Configured HTMLTemplate instance
        
    Example:
        template = create_custom_template(
            css_overrides={
                'button_bg': '#e91e63',
                'text_font_family': 'Georgia, serif',
                'text_line_height': '2.0'
            },
            custom_css='''
            .lx-highlight { 
                text-decoration: underline; 
                background: none !important;
            }
            ''',
            header_html='<h2>Document Analysis Results</h2>',
            custom_buttons=[
                '<button onclick="exportData()">Export</button>'
            ],
            custom_js='function exportData() { console.log(extractions); }'
        )
    """
    class CustomTemplate(HTMLTemplate):
        def get_css_variables(self, **kwargs):
            vars = super().get_css_variables(**kwargs)
            if css_overrides:
                vars.update(css_overrides)
            if custom_css:
                vars['custom_css'] = custom_css
            return vars
        
        def get_html_variables(self, **kwargs):
            vars = super().get_html_variables(**kwargs)
            if header_html:
                vars['header_html'] = header_html
            if footer_html:
                vars['footer_html'] = footer_html
            if custom_buttons:
                vars['buttons'] = custom_buttons
            return vars
        
        def get_js_variables(self, **kwargs):
            vars = super().get_js_variables(**kwargs)
            if custom_js:
                vars['custom_js_functions'] = custom_js
            return vars
    
    return CustomTemplate()


# Convenience function for loading template from file
def load_template_from_file(template_path: Union[str, pathlib.Path]) -> HTMLTemplate:
    """
    Load a custom template from a Python file.
    
    The file should define a class that inherits from HTMLTemplate.
    
    Args:
        template_path: Path to Python file containing template class
        
    Returns:
        Instance of the custom template
        
    Example:
        # In my_template.py:
        from langextract_extensions.custom_visualization import HTMLTemplate
        
        class MyTemplate(HTMLTemplate):
            def get_css_variables(self, **kwargs):
                vars = super().get_css_variables(**kwargs)
                vars['button_bg'] = '#ff5722'
                return vars
        
        # Load and use:
        template = load_template_from_file('my_template.py')
        html = visualize_with_template('results.jsonl', template)
    """
    import importlib.util
    
    template_path = pathlib.Path(template_path)
    spec = importlib.util.spec_from_file_location("custom_template", template_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find HTMLTemplate subclass
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and 
            issubclass(obj, HTMLTemplate) and 
            obj is not HTMLTemplate):
            return obj()
    
    raise ValueError(f"No HTMLTemplate subclass found in {template_path}")