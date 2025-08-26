"""
GIF export functionality for LangExtract visualizations
"""

import os
import tempfile
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont
try:
    import imgkit
    IMGKIT_AVAILABLE = True
except ImportError:
    IMGKIT_AVAILABLE = False
from langextract import io as lx_io
from langextract import data
import base64


def export_to_gif(
    jsonl_path: str,
    output_path: str = "extraction.gif",
    frame_duration: int = 1500,
    width: int = 1200,
    height: int = 800,
    font_size: int = 16,
    highlight_color: str = "#ffeb3b",
    loop: int = 0
) -> str:
    """
    Export LangExtract visualization as animated GIF.
    
    Args:
        jsonl_path: Path to the JSONL file with annotated documents
        output_path: Output path for the GIF file
        frame_duration: Duration of each frame in milliseconds
        width: Width of the GIF in pixels
        height: Height of the GIF in pixels
        font_size: Font size for text
        highlight_color: Color for highlighting current extraction
        loop: Number of loops (0 = infinite)
        
    Returns:
        Path to the created GIF file
    """
    # Load annotated documents
    documents = list(lx_io.load_annotated_documents_jsonl(jsonl_path))
    
    if not documents:
        raise ValueError("No documents found in JSONL file")
    
    # For now, handle the first document
    doc = documents[0]
    
    # Create frames for each extraction
    frames = []
    
    # Create initial frame (no highlights)
    frames.append(_create_text_frame(
        doc.text, 
        [], 
        width, 
        height, 
        font_size
    ))
    
    # Create a frame for each extraction
    for i, extraction in enumerate(doc.extractions):
        frame = _create_text_frame(
            doc.text,
            doc.extractions[:i+1],  # Show all extractions up to current
            width,
            height,
            font_size,
            current_extraction=extraction
        )
        frames.append(frame)
    
    # Add final frame with all highlights
    frames.append(_create_text_frame(
        doc.text,
        doc.extractions,
        width,
        height,
        font_size
    ))
    
    # Save as GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration,
        loop=loop,
        optimize=True
    )
    
    print(f"✓ Created animated GIF: {output_path}")
    print(f"  Frames: {len(frames)}")
    print(f"  Duration: {frame_duration}ms per frame")
    
    return output_path


def _create_text_frame(
    text: str,
    extractions: List[data.Extraction],
    width: int,
    height: int,
    font_size: int,
    current_extraction: Optional[data.Extraction] = None
) -> Image.Image:
    """Create a single frame showing text with highlights."""
    
    # Create image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load a font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Colors for different extraction classes
    colors = {
        'case_number': '#4285f4',
        'court': '#ea4335',
        'plaintiff': '#34a853',
        'defendant': '#fbbc04',
        'amount': '#9c27b0',
        'rate': '#00acc1',
        'date': '#ff5722',
        'default': '#607d8b'
    }
    
    # Prepare text with highlighting info
    highlight_ranges = []
    for ext in extractions:
        if ext.char_interval and ext.char_interval.start_pos is not None:
            color = colors.get(ext.extraction_class, colors['default'])
            if ext == current_extraction:
                # Make current extraction stand out
                color = '#ff0000'
            highlight_ranges.append({
                'start': ext.char_interval.start_pos,
                'end': ext.char_interval.end_pos,
                'color': color,
                'text': ext.extraction_text,
                'class': ext.extraction_class
            })
    
    # Sort by start position
    highlight_ranges.sort(key=lambda x: x['start'])
    
    # Draw text with highlights
    x, y = 20, 20
    char_width = font_size * 0.6  # Approximate
    line_height = font_size * 1.5
    
    current_pos = 0
    lines = text.split('\n')
    
    for line in lines:
        x = 20
        line_start = current_pos
        
        # Check for highlights in this line
        line_highlights = []
        for hr in highlight_ranges:
            if hr['start'] >= line_start and hr['start'] < line_start + len(line):
                # Adjust positions relative to line
                line_highlights.append({
                    'start': hr['start'] - line_start,
                    'end': min(hr['end'] - line_start, len(line)),
                    'color': hr['color'],
                    'text': hr['text'],
                    'class': hr['class']
                })
        
        # Draw line with highlights
        if line_highlights:
            pos = 0
            for lh in line_highlights:
                # Draw text before highlight
                if lh['start'] > pos:
                    pre_text = line[pos:lh['start']]
                    draw.text((x, y), pre_text, fill='black', font=font)
                    x += len(pre_text) * char_width
                
                # Draw highlighted text
                highlight_text = line[lh['start']:lh['end']]
                # Draw background
                text_width = len(highlight_text) * char_width
                draw.rectangle(
                    [(x-2, y-2), (x + text_width + 2, y + line_height - 2)],
                    fill=lh['color']
                )
                # Draw text
                draw.text((x, y), highlight_text, fill='white', font=font)
                x += text_width
                pos = lh['end']
            
            # Draw remaining text
            if pos < len(line):
                draw.text((x, y), line[pos:], fill='black', font=font)
        else:
            # No highlights in this line
            draw.text((x, y), line, fill='black', font=font)
        
        y += line_height
        current_pos += len(line) + 1  # +1 for newline
        
        if y > height - 50:
            break
    
    # Add legend
    legend_y = height - 40
    legend_x = 20
    draw.text((legend_x, legend_y), "Extractions: ", fill='black', font=font)
    legend_x += 100
    
    shown_classes = set()
    for ext in extractions:
        if ext.extraction_class not in shown_classes:
            color = colors.get(ext.extraction_class, colors['default'])
            draw.rectangle(
                [(legend_x, legend_y), (legend_x + 15, legend_y + 15)],
                fill=color
            )
            draw.text((legend_x + 20, legend_y), ext.extraction_class, fill='black', font=font)
            legend_x += 150
            shown_classes.add(ext.extraction_class)
    
    return img


def export_to_html_frames(
    jsonl_path: str,
    output_dir: str = "frames",
    highlight_one_by_one: bool = True
) -> List[str]:
    """
    Export visualization as individual HTML frames.
    
    This is an alternative approach that creates HTML files for each frame,
    which can then be converted to images using external tools.
    
    Args:
        jsonl_path: Path to the JSONL file
        output_dir: Directory to save HTML frames
        highlight_one_by_one: If True, highlight one extraction at a time
        
    Returns:
        List of paths to created HTML files
    """
    import langextract as lx
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load documents
    documents = list(lx_io.load_annotated_documents_jsonl(jsonl_path))
    if not documents:
        raise ValueError("No documents found")
    
    doc = documents[0]
    frame_paths = []
    
    # Create frames
    if highlight_one_by_one:
        # Frame for each extraction
        for i in range(len(doc.extractions) + 1):
            # Create document with only extractions up to i
            frame_doc = data.AnnotatedDocument(
                text=doc.text,
                extractions=doc.extractions[:i],
                document_id=f"{doc.document_id}_frame_{i}"
            )
            
            # Save and visualize
            frame_jsonl = os.path.join(output_dir, f"frame_{i}.jsonl")
            lx.io.save_annotated_documents([frame_doc], output_name=frame_jsonl)
            
            # Generate HTML
            html = lx.visualize(frame_jsonl)
            html_path = os.path.join(output_dir, f"frame_{i}.html")
            
            # Modify HTML to highlight current extraction
            if i > 0:
                html = html.replace(
                    f'data-idx="{i-1}"',
                    f'data-idx="{i-1}" class="current-extraction"'
                )
                # Add CSS for current extraction
                html = html.replace(
                    '</style>',
                    '.current-extraction { outline: 3px solid red !important; }</style>'
                )
            
            with open(html_path, 'w') as f:
                f.write(html)
            
            frame_paths.append(html_path)
    
    print(f"✓ Created {len(frame_paths)} HTML frames in {output_dir}")
    return frame_paths


# Simplified GIF creation using matplotlib (no external dependencies)
def create_simple_gif(
    jsonl_path: str,
    output_path: str = "extraction_simple.gif",
    fps: int = 1
) -> str:
    """
    Create a simple GIF visualization using matplotlib.
    
    This doesn't require external tools like wkhtmltoimage.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation, PillowWriter
    
    # Load documents
    documents = list(lx_io.load_annotated_documents_jsonl(jsonl_path))
    if not documents:
        raise ValueError("No documents found")
    
    doc = documents[0]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Display text
    text_lines = doc.text.split('\n')[:20]  # First 20 lines
    text_str = '\n'.join(text_lines)
    
    text_obj = ax.text(5, 95, text_str, fontsize=10, 
                       verticalalignment='top', 
                       fontfamily='monospace')
    
    # Animation function
    def animate(frame):
        ax.clear()
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis('off')
        
        # Show text
        ax.text(5, 95, text_str, fontsize=10, 
                verticalalignment='top', 
                fontfamily='monospace')
        
        # Add title
        if frame == 0:
            ax.text(50, 98, "LangExtract Visualization", 
                    fontsize=14, ha='center', weight='bold')
        else:
            extraction = doc.extractions[min(frame-1, len(doc.extractions)-1)]
            ax.text(50, 98, f"Extracted: {extraction.extraction_text}", 
                    fontsize=12, ha='center', 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow"))
        
        # Show extraction count
        ax.text(5, 2, f"Extractions: {min(frame, len(doc.extractions))}/{len(doc.extractions)}", 
                fontsize=10)
    
    # Create animation
    anim = FuncAnimation(fig, animate, frames=len(doc.extractions)+2, 
                         interval=1000/fps, repeat=True)
    
    # Save as GIF
    writer = PillowWriter(fps=fps)
    anim.save(output_path, writer=writer)
    plt.close()
    
    print(f"✓ Created simple GIF: {output_path}")
    return output_path