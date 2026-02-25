"""Text formatting utilities for wargame CLI.

Provides functions for wrapping, indenting, and structuring text output
with keyword detection and visual hierarchy.
"""

import textwrap
import re
from typing import List, Tuple
from cli.theme import theme_manager, SYMBOLS


def wrap_text(text: str, width: int = 75, indent: int = 2, 
              subsequent_indent: int = None) -> str:
    """Wrap text with indentation.
    
    Args:
        text: Text to wrap
        width: Maximum line width
        indent: Initial indent (spaces)
        subsequent_indent: Indent for continuation lines (defaults to indent)
        
    Returns:
        Wrapped and indented text
    """
    if subsequent_indent is None:
        subsequent_indent = indent
    
    initial = " " * indent
    subsequent = " " * subsequent_indent
    
    return textwrap.fill(
        text,
        width=width,
        initial_indent=initial,
        subsequent_indent=subsequent,
        break_long_words=False,
        break_on_hyphens=False
    )


def indent_block(text: str, spaces: int = 2) -> str:
    """Indent all lines in a text block.
    
    Args:
        text: Multi-line text
        spaces: Number of spaces to indent
        
    Returns:
        Indented text
    """
    indent = " " * spaces
    lines = text.split('\n')
    return '\n'.join(indent + line if line.strip() else "" for line in lines)


def parse_response(text: str) -> List[Tuple[str, str]]:
    """Parse advisor response for special keywords and structure.
    
    Detects:
    - CRITICAL, URGENT, WARNING (warnings)
    - RECOMMEND, RECOMMENDATION (actions)
    - NOTE, IMPORTANT (notes)
    
    Args:
        text: Response text
        
    Returns:
        List of (type, content) tuples where type is 'warning', 'action', 'note', or 'normal'
    """
    # Split into paragraphs
    paragraphs = text.split('\n\n')
    
    results = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Detect paragraph type by keywords
        upper_para = para.upper()
        
        if any(word in upper_para for word in ['CRITICAL', 'URGENT', 'WARNING']):
            results.append(('warning', para))
        elif any(word in upper_para for word in ['RECOMMEND', 'RECOMMENDATION']):
            results.append(('action', para))
        elif any(word in upper_para for word in ['NOTE', 'IMPORTANT']):
            results.append(('note', para))
        else:
            results.append(('normal', para))
    
    return results


def highlight_keywords(text: str) -> str:
    """Bold important keywords in text and process basic Markdown.
    
    Args:
        text: Text to process
        
    Returns:
        Text with Rich markup for keywords and markdown
    """
    COLORS = theme_manager.get_colors()
    
    # 1. Process Markdown-style formatting first
    # Bold: **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', text)
    # Italic: *text* (be careful not to match inside tags)
    text = re.sub(r'(?<!\[)\*(.+?)\*(?!\])', r'[italic]\1[/italic]', text)
    # Bullet points: "- " at start of line
    text = re.sub(r'^-\s', r'• ', text, flags=re.MULTILINE)
    
    # 2. Highlight keywords
    keywords = [
        'CRITICAL', 'URGENT', 'WARNING',
        'RECOMMEND', 'RECOMMENDATION',
        'IMMEDIATE', 'PRIORITY',
        'CAUTION', 'ALERT'
    ]
    
    result = text
    for keyword in keywords:
        # Case-insensitive replacement with bold, but only if not already in a tag
        # Simplified: just replace whole words
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        result = pattern.sub(f"[{COLORS['emphasis']}]{keyword.upper()}[/{COLORS['emphasis']}]", result)
    
    return result


def format_advisor_response(advisor_name: str, response: str) -> str:
    """Format advisor response with visual structure.
    
    Adds:
    - Indentation (2 spaces)
    - Keyword highlighting
    - Special markers for warnings/actions
    - Proper wrapping
    
    Args:
        advisor_name: Name of advisor (can be empty if already printed)
        response: Response text
        
    Returns:
        Formatted response with Rich markup
    """
    COLORS = theme_manager.get_colors()
    lines = []
    
    # Parse response for special content
    parsed = parse_response(response)
    
    for para_type, para_text in parsed:
        # DO NOT apply keyword highlighting inside coloured blocks - causes nested tag issues
        # Instead, highlight first, then wrap in colour
        highlighted = highlight_keywords(para_text)
        
        if para_type == 'warning':
            # Warning paragraph with ! marker
            wrapped = wrap_text(highlighted, width=75, indent=2, subsequent_indent=4)
            # Add warning marker to first line
            first_line = wrapped.split('\n')[0]
            rest_lines = '\n'.join(wrapped.split('\n')[1:])
            
            marker = f"[{COLORS['warning']}]{SYMBOLS['warning']}[/{COLORS['warning']}]"
            # Don't wrap whole line in colour - just the marker
            lines.append(f"  {marker} {first_line.strip()}")
            if rest_lines:
                lines.append(rest_lines)
                
        elif para_type == 'action':
            # Action/recommendation with → marker
            # Add blank line before recommendations for better visibility
            if lines and lines[-1] != "":
                lines.append("")
            
            wrapped = wrap_text(highlighted, width=75, indent=2, subsequent_indent=4)
            first_line = wrapped.split('\n')[0]
            rest_lines = '\n'.join(wrapped.split('\n')[1:])
            
            marker = f"[{COLORS['primary']}]{SYMBOLS['action']}[/{COLORS['primary']}]"
            # Don't wrap whole line in colour - just the marker
            lines.append(f"  {marker} {first_line.strip()}")
            if rest_lines:
                lines.append(rest_lines)
                
        elif para_type == 'note':
            # Note with * marker
            wrapped = wrap_text(highlighted, width=75, indent=2, subsequent_indent=4)
            first_line = wrapped.split('\n')[0]
            rest_lines = '\n'.join(wrapped.split('\n')[1:])
            
            marker = f"[{COLORS['accent']}]{SYMBOLS['note']}[/{COLORS['accent']}]"
            lines.append(f"  {marker} {first_line.strip()}")
            if rest_lines:
                lines.append(rest_lines)
                
        else:
            # Normal paragraph, just wrap and indent
            wrapped = wrap_text(highlighted, width=75, indent=2)
            lines.append(wrapped)
        
        # Blank line after paragraph
        lines.append("")
    
    return '\n'.join(lines)


def format_metric_status(value: int, metric_type: str) -> str:
    """Generate status label for a metric value.
    
    Args:
        value: Metric value (0-100)
        metric_type: Type of metric ('risk', 'stability', 'cohesion', 'influence')
        
    Returns:
        Status label (e.g., "CRITICAL", "ELEVATED", "STABLE")
    """
    if metric_type == 'risk':
        # High risk is bad
        if value >= 80:
            return "CRITICAL"
        elif value >= 70:
            return "SEVERE"
        elif value >= 60:
            return "ELEVATED"
        elif value >= 50:
            return "MODERATE"
        else:
            return "LOW"
            
    elif metric_type in ['stability', 'cohesion']:
        # Low stability/cohesion is bad
        if value >= 70:
            return "STRONG"
        elif value >= 50:
            return "STABLE"
        elif value >= 30:
            return "WEAK"
        elif value >= 20:
            return "UNSTABLE"
        else:
            return "CRITICAL"
            
    elif metric_type == 'influence':
        # Influence is -10 to +10
        if value >= 7:
            return "VERY HIGH"
        elif value >= 4:
            return "HIGH"
        elif value >= 1:
            return "POSITIVE"
        elif value >= -3:
            return "NEUTRAL"
        elif value >= -6:
            return "LOW"
        else:
            return "VERY LOW"
    
    return "UNKNOWN"
