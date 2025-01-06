import re

def hex_to_rgba(hex_color, alpha=1.0):
    """Convert hex color to rgba."""
    hex_color = hex_color.lstrip('#')
    
    # Handle 6-character hex color (e.g., #0A0A0F)
    if len(hex_color) == 6:
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    # Handle 3-character hex color (e.g., #ABC -> #AABBCC)
    elif len(hex_color) == 3:
        hex_color = ''.join([x*2 for x in hex_color])  # Duplicate each character (e.g., 'A' -> 'AA')
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    else:
        raise ValueError(f"Invalid hex color format: {hex_color}")
    
    return (r, g, b, alpha)  # Returns the rgba tuple

def rgba_to_rgb(rgba_color):
    """Convert rgba color to rgb format."""
    if isinstance(rgba_color, tuple) and len(rgba_color) == 4:
        r, g, b, a = rgba_color
        return f"rgb({r}, {g}, {b})"
    return rgba_color  # Return as is if it's not a tuple

def parse_color_string(color_string):
    """Parse RGB or RGBA color string into a tuple."""
    match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', color_string)
    if not match:
        raise ValueError(f"Invalid color format: {color_string}")
    r, g, b = map(int, match.group(1, 2, 3))
    a = float(match.group(4)) if match.group(4) else 1.0
    return (r, g, b, a)

def rgba_to_hex(rgba_color):
    """Convert RGBA color to HEX format."""
    # Handle string input like 'rgb(234,232,230)' or 'rgba(234,232,230,0.5)'
    if isinstance(rgba_color, str):
        rgba_color = parse_color_string(rgba_color)
    
    if isinstance(rgba_color, tuple) and len(rgba_color) in [3, 4]:
        r, g, b = rgba_color[:3]
        return f"#{r:02X}{g:02X}{b:02X}"
    
    raise ValueError("Invalid RGBA color format.")