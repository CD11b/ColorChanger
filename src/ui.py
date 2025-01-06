import os
import re
import shutil
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import  QWidget, QPushButton, QVBoxLayout, QLabel, QCheckBox, QScrollArea, QProgressBar, QLineEdit, QGroupBox, QHBoxLayout, QGridLayout, QFileDialog, QFrame, QColorDialog, QDialog, QDialogButtonBox, QMessageBox
from worker_threads import WorkerThread, FileTypeWorkerThread
from utils import rgba_to_rgb, hex_to_rgba, rgba_to_hex
from styles import light_mode_style, dark_mode_style  # Import styles

class ColorChangerApp(QWidget):
	def __init__(self):
		super().__init__()

		self.setWindowTitle('GTK Color Changer')

		self.directory = ""
		self.unique_colors = {}
		self.color_entries = {}
		self.selected_filetypes = ['.css', '.scss', '.less', '.svg']  # Default filetype

		self.initUI()

	def initUI(self):
		layout = QVBoxLayout()

		# Select Directory Button
		self.select_dir_btn = QPushButton('Select Directory', self)
		self.select_dir_btn.clicked.connect(self.select_directory)

		# Directory label
		self.dir_label = QLabel('No directory selected', self)

		self.default_filetype_groupbox = QGroupBox('Default File Types', self)
		default_filetype_layout = QGridLayout()

		self.css_checkbox = QCheckBox('.css', self)
		self.css_checkbox.setChecked(True)
		self.css_checkbox.stateChanged.connect(self.update_file_types)
		default_filetype_layout.addWidget(self.css_checkbox, 0, 0)

		self.scss_checkbox = QCheckBox('.scss', self)
		self.scss_checkbox.setChecked(True)
		self.scss_checkbox.stateChanged.connect(self.update_file_types)
		default_filetype_layout.addWidget(self.scss_checkbox, 0, 1)

		self.less_checkbox = QCheckBox('.less', self)
		self.less_checkbox.setChecked(True)
		self.less_checkbox.stateChanged.connect(self.update_file_types)
		default_filetype_layout.addWidget(self.less_checkbox, 1, 0)

		self.svg_checkbox = QCheckBox('.svg', self)
		self.svg_checkbox.setChecked(True)
		self.svg_checkbox.stateChanged.connect(self.update_file_types)
		default_filetype_layout.addWidget(self.svg_checkbox, 1, 1)

		self.default_filetype_groupbox.setLayout(default_filetype_layout)

		# Experimental Section with Multi-column Layout
		self.experimental_groupbox = QGroupBox('Experimental File Types', self)
		self.experimental_layout = QGridLayout()
		self.experimental_groupbox.setLayout(self.experimental_layout)

		# Scroll Area for colors
		self.scroll_area = QScrollArea(self)
		self.scroll_area.setWidgetResizable(True)
		self.scroll_content_frame = QFrame(self.scroll_area)
		self.scroll_area.setWidget(self.scroll_content_frame)

		# Apply Changes Button
		self.apply_changes_btn = QPushButton('Apply Changes', self)
		self.apply_changes_btn.clicked.connect(self.apply_changes)

		# Preview Changes Button
		self.preview_changes_btn = QPushButton('Preview Changes', self)
		self.preview_changes_btn.clicked.connect(self.preview_changes)

		# Progress Bar
		self.progress_bar = QProgressBar(self)
		self.progress_bar.setRange(0, 100)
		self.progress_bar.setValue(0)
		self.progress_bar.setVisible(False)  # Hide progress bar initially

		# Layout for content area
		content_layout = QVBoxLayout()
		content_layout.addWidget(self.select_dir_btn)
		content_layout.addWidget(self.dir_label)
		content_layout.addWidget(self.default_filetype_groupbox)
		content_layout.addWidget(self.experimental_groupbox)
		content_layout.addWidget(self.scroll_area)
		content_layout.addWidget(self.apply_changes_btn)
		content_layout.addWidget(self.preview_changes_btn)
		content_layout.addWidget(self.progress_bar)

		layout.addLayout(content_layout)

		# Bottom layout with the dark mode toggle button and backup checkbox
		bottom_layout = QHBoxLayout()  # Use QHBoxLayout to keep things in a row
		bottom_layout.addStretch(1)  # Push the toggle button to the far right

		# Dark mode toggle button
		self.dark_mode_toggle_btn = QPushButton('🌙', self)  # Using a moon icon
		self.dark_mode_toggle_btn.clicked.connect(self.toggle_dark_mode)
		self.dark_mode_toggle_btn.setFixedSize(30, 30)  # Small button size
		self.dark_mode_toggle_btn.setStyleSheet("background-color: transparent; border: none;")
		bottom_layout.addWidget(self.dark_mode_toggle_btn)  # Add toggle button to the right side

		# Backup checkbox
		self.backup_checkbox = QCheckBox('Backup Files', self)
		self.backup_checkbox.setChecked(True)  # Default is to backup files
		bottom_layout.addWidget(self.backup_checkbox)  # Add backup checkbox

		layout.addLayout(bottom_layout)  # Add the bottom layout with the toggle button

		self.setLayout(layout)

		# Start with Dark Mode
		self.setStyleSheet(dark_mode_style)  # Set initial theme to dark mode

	def toggle_dark_mode(self):
		"""Toggle between light and dark modes."""
		if self.dark_mode_toggle_btn.text() == '🌙':  # If it's in dark mode, show moon icon
			self.setStyleSheet(light_mode_style)
			self.dark_mode_toggle_btn.setText('☀️')  # Switch to sun icon
		else:
			self.setStyleSheet(dark_mode_style)
			self.dark_mode_toggle_btn.setText('🌙')  # Switch to moon icon
			
	def select_directory(self):
		"""Open a file dialog to select a directory."""
		folder = QFileDialog.getExistingDirectory(self, 'Select Directory')
		if folder:
			self.directory = folder
			self.dir_label.setText(f'Directory: {self.directory}')
			self.scan_for_colors()

			# Start the thread to find file types in the selected directory
			self.file_type_worker_thread = FileTypeWorkerThread(self.directory)
			self.file_type_worker_thread.file_types_signal.connect(self.update_file_type_checkboxes)
			self.file_type_worker_thread.start()

	def update_file_type_checkboxes(self, file_types):
		"""Dynamically add checkboxes for the found file types."""
		# Clear existing experimental checkboxes
		for checkbox in self.experimental_groupbox.findChildren(QCheckBox):
			checkbox.deleteLater()

		# Add new checkboxes for experimental file types
		row, col = 0, 0
		for file_type in sorted(file_types):
			if file_type not in ['.css', '.scss', '.less', '.svg']:  # Only experimental file types
				file_type_checkbox = QCheckBox(file_type, self)
				file_type_checkbox.setChecked(False)  # Toggle off by default
				file_type_checkbox.stateChanged.connect(self.update_file_types)
				self.experimental_layout.addWidget(file_type_checkbox, row, col)

				# Move to the next column
				col += 1
				if col > 2:  # Limit to 3 columns, then move to the next row
					col = 0
					row += 1

	def update_file_types(self):
		"""Update the list of selected file types based on checkbox states."""
		self.selected_filetypes.clear()
		for checkbox in self.default_filetype_groupbox.findChildren(QCheckBox):
			if checkbox.isChecked():
				self.selected_filetypes.append(checkbox.text())

		# Include experimental types
		for checkbox in self.experimental_groupbox.findChildren(QCheckBox):
			if checkbox.isChecked():
				self.selected_filetypes.append(checkbox.text())
				
	def clear_widgets_in_layout(self, layout):
		"""Clears the widgets in a layout without resetting the layout itself."""
		if layout:
			print(f"Clearing widgets in layout: {layout}")
			for i in range(layout.count()):
				item = layout.itemAt(i)
				widget = item.widget()
				if widget:
					print(f"Deleting widget: {widget}")
					widget.deleteLater()
		else:
			print("No layout to clear.")



	def show_usage(self, color_value):
		"""Show usage information in a dialog for the selected color."""
		color_name, color_line, usage_count, usage_instances, color_alternative = self.unique_colors.get(color_value, (None, None, 0, [], None))

		if usage_count == 0:
			msg = f"The color {color_name} ({color_value}) has not been used in any files."
		else:
			msg = f"Color {color_name} ({color_value}) is used {usage_count} time(s):\n\n"
			msg += "\n".join(usage_instances)

		usage_dialog = QDialog(self)
		usage_dialog.setWindowTitle(f"Usage of {color_name}")
		usage_layout = QVBoxLayout()

		# Scroll Area for usage details
		scroll_area = QScrollArea(usage_dialog)
		scroll_area.setWidgetResizable(True)

		# Create a widget to hold the usage details text
		usage_widget = QWidget(scroll_area)
		usage_layout_widget = QVBoxLayout(usage_widget)

		# Add the message and usage instances
		usage_label = QLabel(msg, usage_widget)
		usage_layout_widget.addWidget(usage_label)

		usage_widget.setLayout(usage_layout_widget)

		# Set the scrollable area for the dialog
		scroll_area.setWidget(usage_widget)
		usage_layout.addWidget(scroll_area)

		# Ok button to close the dialog
		button_box = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, usage_dialog)
		button_box.accepted.connect(usage_dialog.accept)
		usage_layout.addWidget(button_box)

		usage_dialog.setLayout(usage_layout)
		usage_dialog.exec_()

	def apply_changes(self):
		"""Apply the color changes based on the mappings provided in the UI."""
		if not self.directory:
			QMessageBox.warning(self, 'No Directory', 'Please select a directory first.')
			return

		# Check if backup is selected
		if self.backup_checkbox.isChecked():
			# Generate a timestamped backup directory name
			timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
			backup_dir = f"{self.directory}_backup_{timestamp}"

			# Ensure the backup directory doesn't already exist
			if os.path.exists(backup_dir):
				shutil.rmtree(backup_dir)  # Remove existing backup if any
			shutil.copytree(self.directory, backup_dir)  # Create backup

		# Create a new worker thread and pass selected_filetypes
		self.worker_thread = WorkerThread(self.unique_colors, self.directory, self.color_entries, self.selected_filetypes)
		self.worker_thread.progress_signal.connect(self.update_progress_bar)
		self.worker_thread.finished_signal.connect(self.on_apply_changes_finished)

		self.progress_bar.setVisible(True)
		self.progress_bar.setValue(0)

		# Start the worker thread
		self.worker_thread.start()


	def update_progress_bar(self, value):
		"""Update progress bar from worker thread."""
		self.progress_bar.setValue(value)

	def on_apply_changes_finished(self):
		"""When the apply changes operation finishes, show a message box."""
		QMessageBox.information(self, 'Changes Applied', 'The color changes have been applied successfully.')
		self.progress_bar.setVisible(False)  # Hide progress bar after applying

	def preview_changes(self):
		"""Preview the changes by simulating the replacement in the UI."""
		for color_value, (color_name, color_line, usage_count, usage_instances, color_alternative) in self.unique_colors.items():
			# Get the new color from the user input (from the UI)
			new_color = self.color_entries.get(color_value, None).text().strip()
			if new_color:
				# Validate the new color format (either hex or rgba)
				if not self.is_valid_color(new_color):
					continue

				# Preview the color by temporarily applying the new color in the UI
				for widget in self.scroll_content_frame.findChildren(QLabel):
					if widget.text() == f"Hex: {color_value}" or widget.text() == f"rgba: {color_value}":
						widget.setStyleSheet(f"background-color: {new_color}; border: 1px solid black;")

	def pick_color(self, color_value):
		"""Pick a color using QColorDialog and update the corresponding entry."""
		# Open the QColorDialog with the correct style
		color_dialog = QColorDialog(self)
		color_dialog.setOption(QColorDialog.DontUseNativeDialog, True)  # Use Qt's native dialog
		color_dialog.setStyleSheet(self.styleSheet())  # Apply the current stylesheet (dark or light)

		if color_dialog.exec_():
			selected_color = color_dialog.selectedColor().name()
			self.color_entries[color_value].setText(selected_color)  # Update the text entry with the picked color
