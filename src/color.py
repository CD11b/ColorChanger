import os
import re
import shutil
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import  QWidget, QPushButton, QVBoxLayout, QLabel, QCheckBox, QScrollArea, QProgressBar, QLineEdit, QGroupBox, QHBoxLayout, QGridLayout, QFileDialog, QFrame, QColorDialog, QDialog, QDialogButtonBox, QMessageBox
# from worker_threads import WorkerThread, FileTypeWorkerThread
# from .utils import rgba_to_rgb, hex_to_rgba, rgba_to_hex
# from styles import light_mode_style, dark_mode_style  # Import styles
from threads import ColorScanner, FileEditor

class ColorChangerApp(QWidget):
	def __init__(self):
		super().__init__()

		self.setWindowTitle('Color Code Changer')

		self.directory = ""
		self.unique_colors = {}
		self.color_entries = {}
		self.selected_filetypes = ['.css', '.scss', '.less', '.svg']  # Default filetype

	def scan_for_colors(self):
		"""Scan the selected file types for color definitions."""
		self.unique_colors.clear()
		self.color_entries.clear()

		# Get the current layout of the scroll_content_frame if it exists
		current_layout = self.scroll_content_frame.layout()

		# If there's an existing layout, clear its widgets first
		if current_layout:
			self.clear_widgets_in_layout(current_layout)
			current_layout.deleteLater()  # Delete the old layout to avoid reuse
		else:
			print("No layout to clear.")

		# Now we can safely create and set the new layout
		colors_layout = QVBoxLayout()

		# Scan all selected file types in the directory for color definitions
		self.unique_colors = extract_colors_from_directory(self.directory)

		# Iterate over unique colors and add widgets to the new layout
		for color_value, (color_name, color_line, usage_count, usage_instances, alternative_value) in sorted(self.unique_colors.items()):
			display_color = rgba_to_rgb(alternative_value)  # Convert rgba to rgb for display

			# Color box to show color with black border
			color_box = QWidget(self.scroll_content_frame)
			color_box.setFixedSize(30, 30)
			color_box.setStyleSheet(f'background-color: {display_color}; border: 1px solid black;')

			# Label to show the color value (hex or rgba)
			color_label = QLabel(f"Hex: {color_value}", self.scroll_content_frame)
			rgba_label = QLabel(f"Alternative: {alternative_value}", self.scroll_content_frame)  # Show RGBA too

			# Label to show the color name (e.g., GRAPE_900)
			if color_name.lower().startswith('rgb') or color_name.startswith('#'):
				color_name = "" # Ignore names with # or rgb
			color_name_label = QLabel(color_name, self.scroll_content_frame)


			# Label to show the number of instances
			instance_label = QLabel(f'Used {usage_count} time(s)', self.scroll_content_frame)

			# Input box for new color (increased width)
			color_entry = QLineEdit(self.scroll_content_frame)
			color_entry.setPlaceholderText('Enter new color (Hex or rgba)')
			self.color_entries[color_value] = color_entry
			color_entry.setFixedWidth(250)  # Increased width of the textboxes

			# Button to show the usage of the color
			show_usage_btn = QPushButton('Show Usage', self.scroll_content_frame)
			show_usage_btn.clicked.connect(lambda _, color_value=color_value: self.show_usage(color_value))

			# Add a "Pick Color" button to select a color visually
			pick_color_btn = QPushButton('Pick Color', self.scroll_content_frame)
			pick_color_btn.clicked.connect(lambda _, color_value=color_value: self.pick_color(color_value))

			# Horizontal layout for color box, color code, name, instances, and input box
			row_layout = QHBoxLayout()
			row_layout.addWidget(color_box)
			row_layout.addWidget(color_label)
			row_layout.addWidget(rgba_label)  # Add RGBA label
			row_layout.addWidget(color_name_label)
			row_layout.addWidget(instance_label)
			row_layout.addWidget(color_entry)
			row_layout.addWidget(pick_color_btn)  # Add the Pick Color button
			row_layout.addWidget(show_usage_btn)

			colors_layout.addLayout(row_layout)

		# Now that the layout is empty of old widgets, set the new layout
		self.scroll_content_frame.setLayout(colors_layout)




