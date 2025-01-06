import os
import re
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from utilities import hex_to_rgba, rgba_to_rgb, rgba_to_hex
from utilities import COLOR_CODE_PATTERN, COLOR_DEFINITION_PATTERN


class ColorScanner(QThread):
	progressSignal = pyqtSignal(int)  # Signal to update progress
	finishedSignal = pyqtSignal(dict)  # Signal to send back the extracted color data

	def __init__(self, directory, selectedFileTypes):
		super().__init__()
		self._directory = directory
		self._selectedFileTypes = selectedFileTypes
		self._fileColors = {}
		self._allColors = {}
		self._mutex = QMutex() # For thread safety

	def get_colors_from_file(self, filePath):
		"""Extract unique color definitions and usage from a file."""
  
		self._fileColors = {}

		with open(filePath, 'r', encoding='utf-8') as fileObj:
			buffer = '' # For lazy reading in chunks 
      
			while chunk := fileObj.read(1024):  # Read 1KB chunks
				buffer += chunk  # Add new chunk to buffer

				# Process each line in the buffer
				for lineNumber, line in enumerate(buffer.splitlines(), 1):
                    
					# Ignore commented lines
					if line.strip().startswith('/*') or line.strip().startswith('*'):
						continue
				
					# Track color usage in CSS and SVG-compatible syntax
					if re.findall(COLOR_CODE_PATTERN, line):
						for identifiedColor in re.findall(COLOR_CODE_PATTERN, line):
			
							colorCode = identifiedColor[0]
							colorAlternative = self.color_conversion(colorCode)
							
							with QMutexLocker(self._mutex):
								if colorCode in self._fileColors:
									self._fileColors[colorCode][2] += 1  # Increment the usage count
									self._fileColors[colorCode][3].append(f"Line {lineNumber}: {line.strip()} in {filePath}")
			
								elif re.search(COLOR_DEFINITION_PATTERN, line):
									# Match to @define-color <group 1> <group 2> e.g. @define-color primary #000000;
									# Store as a list: [color_name, color_line, usage_count, usage_instances, alternativeColor]
									self._fileColors[re.search(COLOR_DEFINITION_PATTERN, line).group(2)] = [re.search(COLOR_DEFINITION_PATTERN, line).group(1), line.strip(), 0, [], colorAlternative]
									
								else:
									# Store as a list: [color_name, color_line, usage_count, usage_instances, alternativeColor]
									self._fileColors[colorCode] = ['', line.strip(), 0, [], colorAlternative]
				
				if len(buffer) > 2048:  # Keep only the last 2KB of data
					buffer = buffer[-1024:]  # Retain the last chunk's worth of data for the next iteration

		return self._fileColors


	def color_conversion(self, colorCode):

		# Convert the hex color to RGBA (with full opacity by default)
		if colorCode.startswith("#"):
			colorAlternative = hex_to_rgba(colorCode)  # Convert hex to rgba
		elif colorCode.lower().startswith("rgb"):
			colorAlternative = rgba_to_hex(colorCode)
		else:
			colorAlternative = ''

		return colorAlternative

	def run(self):
		"""Scan the directory and extract colors."""
		self._allColors = {}
		totalFiles = 0
		processedFiles = 0

		# Process each file
		for root, dirs, files in os.walk(self._directory):
			for file in files:
				if any(file.endswith(ext) for ext in self._selectedFileTypes):
					totalFiles += 1
					file_path = os.path.join(root, file)
					colors = self.get_colors_from_file(file_path)
					for color, data in colors.items():
						if color not in self._allColors:
							self._allColors[color] = data
					processedFiles += 1

					# Update progress
					progressPercent = int((processedFiles / totalFiles) * 100)
					self.progressSignal.emit(progressPercent)

		# Emit the result after scanning all files
		self.finishedSignal.emit(self._allColors)

# dirname = os.path.dirname(__file__)
# colorInstance = ColorScanner(dirname, [".css", ".svg"])
# colorInstance.run()
# print(colorInstance._allColors)
