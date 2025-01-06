# Common pattern for hexadecimal color codes
HEX_PATTERN = r'\#[0-9a-fA-F]{3,6}'

# Common pattern for RGB color codes
RGB_PATTERN = r'rgb\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)'

# Common pattern for RGBA color codes
RGBA_PATTERN = r'rgba\(\s*(\d+),\s*(\d+),\s*(\d+),\s*([\d\.]+)\s*\)'

# Abstracted color code pattern (combining hex, RGB, and RGBA)
COLOR_CODE_PATTERN = rf'({HEX_PATTERN}|{RGB_PATTERN}|{RGBA_PATTERN})'

# Abstracted color definition pattern
COLOR_DEFINITION_PATTERN = rf'@define-color\s+([a-zA-Z0-9_]+)\s+{COLOR_CODE_PATTERN}'