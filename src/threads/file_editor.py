import os
import re
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from utilities import COLOR_CODE_PATTERN, COLOR_DEFINITION_PATTERN


class FileEditor(QThread):
	progressSignal = pyqtSignal(int)  # Signal to update progress
	finishedSignal = pyqtSignal()  # Signal to indicate when the task is finished
	
	def __init__(self, uniqueColors, directory, colorEntries, selectedFileTypes):
		super().__init__()
		self._uniqueColors = uniqueColors  # Color definitions and usage
		self._directory = directory  # Directory to process
		self._colorEntries = colorEntries  # Dictionary of color entries from the UI
		self._selectedFileTypes = selectedFileTypes  # List of selected file types (e.g., .css, .scss)

	def is_valid_color(self, color):
		"""Check if the provided color is valid (either hex or rgba)."""
		
		return bool(re.match(COLOR_CODE_PATTERN, color))

	def replace_color_in_files(self, oldColor, newColor, updatedFiles, totalFiles):
		"""Replace occurrences of oldColor with newColor in the selected files."""
		changesMade = False
		fileCount = 0  # To track the number of files processed

		for root, dirs, files in os.walk(self._directory):
			for file in files:
				if any(file.endswith(ext) for ext in self._selectedFileTypes):
					filePath = os.path.join(root, file)
					with open(filePath, 'r', encoding='utf-8') as f:
						content = f.read()

					if oldColor in content:
						changesMade = True
						content = content.replace(oldColor, newColor)
						updatedFiles.append((filePath, content))  # Save updated content
					
					# Update the progress bar
					fileCount += 1
					progressPercent = int((fileCount / totalFiles) * 100)
					self.progressSignal.emit(progressPercent)

		# Write all updated files
		for filePath, newContent in updatedFiles:
			with open(filePath, 'w', encoding='utf-8') as f:
				f.write(newContent)

		return changesMade

	def run(self):
		"""The main worker thread logic to apply color changes."""
		changesMade = False
		updatedFiles = []

		totalFiles = 0
		for root, dirs, files in os.walk(self._directory):
			for file in files:
				if any(file.endswith(ext) for ext in self._selectedFileTypes):
					totalFiles += 1  # Count the files to be processed

		for color_value, (colorName, colorLine, usageCount, usageInstances, colorAlternative) in self._uniqueColors.items():
			newColor = self._colorEntries.get(color_value, None).text().strip()
			if newColor:
				if not self.is_valid_color(newColor):
					continue  # Skip invalid color entries

				changesMade |= self.replace_color_in_files(color_value, newColor, updatedFiles, totalFiles)

		self.finishedSignal.emit()
