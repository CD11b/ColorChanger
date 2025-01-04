import os
import re
from PyQt5.QtCore import QThread, pyqtSignal
from utils import hex_to_rgba, rgba_to_rgb  # Import utility functions

class ColorScanWorkerThread(QThread):
    progress_signal = pyqtSignal(int)  # Signal to update progress
    finished_signal = pyqtSignal(dict)  # Signal to send back the extracted color data

    def __init__(self, directory, selected_filetypes):
        super().__init__()
        self.directory = directory
        self.selected_filetypes = selected_filetypes

    def extract_colors_from_file(self, file_path):
        """Extract unique color definitions and usage from a file."""
        color_definitions = {}
        
        # Regex pattern to match hex, rgb(), and rgba() colors in @define-color
        color_pattern = r'@define-color\s+([a-zA-Z0-9_]+)\s+(\#[0-9a-fA-F]{3,6}|rgb\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)|rgba\(\s*(\d+),\s*(\d+),\s*(\d+),\s*([\d\.]+)\s*\));'

        # Regex pattern to match color usage (hex, rgb, rgba, or color variables)
        usage_pattern = r'(\#([0-9a-fA-F]{3,6})|rgb\((\d+),\s*(\d+),\s*(\d+)\)|rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d\.]+)\))'

        # Updated regex pattern to match colors in SVG attributes or inline styles
        svg_color_pattern = r'(#(?:[0-9a-fA-F]{3}){1,2}|rgb\(\d{1,3},\s*\d{1,3},\s*\d{1,3}\)|rgba\(\d{1,3},\s*\d{1,3},\s*\d{1,3},\s*[\d\.]+\))'

        with open(file_path, 'r', encoding='utf-8') as file_obj:
            for line_number, line in enumerate(file_obj, 1):
                # Ignore commented lines
                if line.strip().startswith('/*') or line.strip().startswith('*'):
                    continue

                # Match color definitions in CSS-like syntax
                match = re.search(color_pattern, line.strip())
                if match:
                    color_value = match.group(2)
                    color_name = match.group(1)

                    if color_value not in color_definitions:
                        # Store as a list: [color_name, color_line, usage_count, usage_instances]
                        color_definitions[color_value] = [color_name, line.strip(), 0, []]

                # Track color usage in CSS-like syntax
                for usage_match in re.finditer(usage_pattern, line.strip()):
                    used_color = usage_match.group(1)
                    if used_color in color_definitions:
                        color_definitions[used_color][2] += 1  # Increment the usage count
                        color_definitions[used_color][3].append(f"Line {line_number}: {line.strip()}")

                # If the file is an SVG, extract color values from attributes or inline styles
                if file_path.endswith('.svg'):
                    svg_matches = re.findall(svg_color_pattern, line)
                    for color in svg_matches:
                        # Store each color found in SVG files
                        if color not in color_definitions:
                            color_definitions[color] = [color, line.strip(), 0, []]
                        color_definitions[color][2] += 1  # Increment usage count

        return color_definitions

    def run(self):
        """Scan the directory and extract colors."""
        all_colors = {}
        total_files = 0
        processed_files = 0

        # Walk through the directory to find the selected file types
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if any(file.endswith(ext) for ext in self.selected_filetypes):
                    total_files += 1

        # Now, process each file
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if any(file.endswith(ext) for ext in self.selected_filetypes):
                    file_path = os.path.join(root, file)
                    colors = self.extract_colors_from_file(file_path)
                    for color, data in colors.items():
                        if color not in all_colors:
                            all_colors[color] = data
                    processed_files += 1

                    # Update progress
                    progress_percent = int((processed_files / total_files) * 100)
                    self.progress_signal.emit(progress_percent)

        # Emit the result after scanning all files
        self.finished_signal.emit(all_colors)



class FileTypeWorkerThread(QThread):
    file_types_signal = pyqtSignal(list)  # Signal to send back file types
    
    def __init__(self, directory):
        super().__init__()
        self.directory = directory

    def run(self):
        """Search for file types in the directory."""
        file_types = set()  # To store unique file types

        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_ext = os.path.splitext(file)[1]
                if file_ext:
                    file_types.add(file_ext.lower())  # Convert to lowercase for consistency

        # Emit the signal with the found file types
        self.file_types_signal.emit(list(file_types))


class WorkerThread(QThread):
    progress_signal = pyqtSignal(int)  # Signal to update progress
    finished_signal = pyqtSignal()  # Signal to indicate when the task is finished
    
    def __init__(self, unique_colors, directory, color_entries, selected_filetypes):
        super().__init__()
        self.unique_colors = unique_colors  # Color definitions and usage
        self.directory = directory  # Directory to process
        self.color_entries = color_entries  # Dictionary of color entries from the UI
        self.selected_filetypes = selected_filetypes  # List of selected file types (e.g., .css, .scss)

    def is_valid_color(self, color):
        """Check if the provided color is valid (either hex or rgba)."""
        hex_pattern = r'^#([0-9A-Fa-f]{3}){1,2}$'
        rgba_pattern = r'^rgba\((\d{1,3}), (\d{1,3}), (\d{1,3}), (\d(\.\d+)?)\)$'
        
        return bool(re.match(hex_pattern, color)) or bool(re.match(rgba_pattern, color))
    
    def replace_color_in_files(self, old_color, new_color, updated_files, total_files):
        """Replace occurrences of old_color with new_color in the selected files."""
        changes_made = False
        file_count = 0  # To track the number of files processed

        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if any(file.endswith(ext) for ext in self.selected_filetypes):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if old_color in content:
                        changes_made = True
                        content = content.replace(old_color, new_color)
                        updated_files.append((file_path, content))  # Save updated content
                    
                    # Update the progress bar
                    file_count += 1
                    progress_percent = int((file_count / total_files) * 100)
                    self.progress_signal.emit(progress_percent)

        # Write all updated files
        for file_path, new_content in updated_files:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return changes_made

    def run(self):
        """The main worker thread logic to apply color changes."""
        changes_made = False
        updated_files = []

        total_files = 0
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if any(file.endswith(ext) for ext in self.selected_filetypes):
                    total_files += 1  # Count the files to be processed

        for color_value, (color_name, color_line, usage_count, usage_instances, color_alternative) in self.unique_colors.items():
            new_color = self.color_entries.get(color_value, None).text().strip()
            if new_color:
                if not self.is_valid_color(new_color):
                    continue  # Skip invalid color entries

                changes_made |= self.replace_color_in_files(color_value, new_color, updated_files, total_files)

        self.finished_signal.emit()
