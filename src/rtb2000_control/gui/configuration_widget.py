"""
Configuration Management Widget for RTB2000
Version 2.0 - September 8, 2025

Modern GUI for managing instrument configurations and presets
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
    QListWidget, QListWidgetItem, QTabWidget, QGroupBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QSlider,
    QMessageBox, QFileDialog, QProgressBar, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette

from ..core.config_manager import ConfigurationManager, RTB2000Configuration
from ..core.simple_data_exporter import DataExporter, ExportFormat


class ConfigurationWidget(QWidget):
    """Advanced configuration management widget"""
    
    # Signals
    configuration_loaded = pyqtSignal(object)  # RTB2000Configuration
    configuration_saved = pyqtSignal(str)  # config name
    
    def __init__(self, config_manager: ConfigurationManager = None):
        super().__init__()
        
        self.config_manager = config_manager or ConfigurationManager()
        self.current_config = self.config_manager.get_current_config()
        
        self.setup_ui()
        self.setup_connections()
        self.refresh_presets()
        self.load_current_config()
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Configuration Management")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Presets
        left_panel = self.create_presets_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Configuration tabs
        right_panel = self.create_config_tabs()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 500])
        
        # Bottom panel - Actions
        bottom_panel = self.create_actions_panel()
        layout.addWidget(bottom_panel)
        
    def create_presets_panel(self) -> QWidget:
        """Create presets management panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Presets group
        presets_group = QGroupBox("Saved Presets")
        presets_layout = QVBoxLayout(presets_group)
        
        # Presets list
        self.presets_list = QListWidget()
        self.presets_list.itemDoubleClicked.connect(self.load_selected_preset)
        presets_layout.addWidget(self.presets_list)
        
        # Preset actions
        preset_actions = QHBoxLayout()
        
        self.load_preset_btn = QPushButton("Load")
        self.load_preset_btn.clicked.connect(self.load_selected_preset)
        preset_actions.addWidget(self.load_preset_btn)
        
        self.save_preset_btn = QPushButton("Save As...")
        self.save_preset_btn.clicked.connect(self.save_as_preset)
        preset_actions.addWidget(self.save_preset_btn)
        
        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.clicked.connect(self.delete_selected_preset)
        preset_actions.addWidget(self.delete_preset_btn)
        
        presets_layout.addLayout(preset_actions)
        layout.addWidget(presets_group)
        
        # Import/Export group
        io_group = QGroupBox("Import/Export")
        io_layout = QVBoxLayout(io_group)
        
        self.export_config_btn = QPushButton("Export Configuration...")
        self.export_config_btn.clicked.connect(self.export_configuration)
        io_layout.addWidget(self.export_config_btn)
        
        self.import_config_btn = QPushButton("Import Configuration...")
        self.import_config_btn.clicked.connect(self.import_configuration)
        io_layout.addWidget(self.import_config_btn)
        
        self.export_all_btn = QPushButton("Export All Presets...")
        self.export_all_btn.clicked.connect(self.export_all_presets)
        io_layout.addWidget(self.export_all_btn)
        
        layout.addWidget(io_group)
        
        # Session info
        session_group = QGroupBox("Session Info")
        session_layout = QVBoxLayout(session_group)
        
        self.session_info = QLabel()
        self.update_session_info()
        session_layout.addWidget(self.session_info)
        
        layout.addWidget(session_group)
        
        layout.addStretch()
        return panel
        
    def create_config_tabs(self) -> QWidget:
        """Create configuration tabs"""
        self.config_tabs = QTabWidget()
        
        # Channel Configuration
        self.channels_tab = self.create_channels_tab()
        self.config_tabs.addTab(self.channels_tab, "Channels")
        
        # Timebase Configuration
        self.timebase_tab = self.create_timebase_tab()
        self.config_tabs.addTab(self.timebase_tab, "Timebase")
        
        # Trigger Configuration
        self.trigger_tab = self.create_trigger_tab()
        self.config_tabs.addTab(self.trigger_tab, "Trigger")
        
        # Display Configuration
        self.display_tab = self.create_display_tab()
        self.config_tabs.addTab(self.display_tab, "Display")
        
        # Acquisition Configuration
        self.acquisition_tab = self.create_acquisition_tab()
        self.config_tabs.addTab(self.acquisition_tab, "Acquisition")
        
        return self.config_tabs
        
    def create_channels_tab(self) -> QWidget:
        """Create channels configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Channel controls
        self.channel_controls = {}
        
        for ch in range(1, 5):
            group = QGroupBox(f"Channel {ch}")
            group_layout = QGridLayout(group)
            
            controls = {}
            
            # Enable checkbox
            controls['enabled'] = QCheckBox("Enable")
            group_layout.addWidget(controls['enabled'], 0, 0, 1, 2)
            
            # Scale
            group_layout.addWidget(QLabel("Scale (V/div):"), 1, 0)
            controls['scale'] = QDoubleSpinBox()
            controls['scale'].setRange(0.001, 10.0)
            controls['scale'].setDecimals(3)
            controls['scale'].setSingleStep(0.001)
            group_layout.addWidget(controls['scale'], 1, 1)
            
            # Position
            group_layout.addWidget(QLabel("Position (div):"), 2, 0)
            controls['position'] = QDoubleSpinBox()
            controls['position'].setRange(-5.0, 5.0)
            controls['position'].setDecimals(2)
            controls['position'].setSingleStep(0.1)
            group_layout.addWidget(controls['position'], 2, 1)
            
            # Coupling
            group_layout.addWidget(QLabel("Coupling:"), 3, 0)
            controls['coupling'] = QComboBox()
            controls['coupling'].addItems(["DC", "AC", "GND"])
            group_layout.addWidget(controls['coupling'], 3, 1)
            
            # Label
            group_layout.addWidget(QLabel("Label:"), 4, 0)
            controls['label'] = QLineEdit()
            group_layout.addWidget(controls['label'], 4, 1)
            
            # Color (display only)
            group_layout.addWidget(QLabel("Color:"), 5, 0)
            controls['color_label'] = QLabel()
            controls['color_label'].setMinimumHeight(20)
            controls['color_label'].setStyleSheet("border: 1px solid gray; border-radius: 2px;")
            group_layout.addWidget(controls['color_label'], 5, 1)
            
            self.channel_controls[ch] = controls
            layout.addWidget(group)
            
            # Connect signals
            for control in controls.values():
                if hasattr(control, 'valueChanged'):
                    control.valueChanged.connect(self.on_config_changed)
                elif hasattr(control, 'textChanged'):
                    control.textChanged.connect(self.on_config_changed)
                elif hasattr(control, 'currentTextChanged'):
                    control.currentTextChanged.connect(self.on_config_changed)
                elif hasattr(control, 'toggled'):
                    control.toggled.connect(self.on_config_changed)
                    
        layout.addStretch()
        return widget
        
    def create_timebase_tab(self) -> QWidget:
        """Create timebase configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Timebase Settings")
        group_layout = QGridLayout(group)
        
        # Scale
        group_layout.addWidget(QLabel("Scale (s/div):"), 0, 0)
        self.timebase_scale = QDoubleSpinBox()
        self.timebase_scale.setRange(1e-9, 10.0)
        self.timebase_scale.setDecimals(9)
        self.timebase_scale.setValue(1e-3)
        self.timebase_scale.valueChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.timebase_scale, 0, 1)
        
        # Position
        group_layout.addWidget(QLabel("Position (s):"), 1, 0)
        self.timebase_position = QDoubleSpinBox()
        self.timebase_position.setRange(-1.0, 1.0)
        self.timebase_position.setDecimals(6)
        self.timebase_position.valueChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.timebase_position, 1, 1)
        
        # Mode
        group_layout.addWidget(QLabel("Mode:"), 2, 0)
        self.timebase_mode = QComboBox()
        self.timebase_mode.addItems(["MAIN", "ZOOM", "ROLL"])
        self.timebase_mode.currentTextChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.timebase_mode, 2, 1)
        
        # Reference
        group_layout.addWidget(QLabel("Reference:"), 3, 0)
        self.timebase_reference = QComboBox()
        self.timebase_reference.addItems(["LEFT", "CENTER", "RIGHT"])
        self.timebase_reference.setCurrentText("CENTER")
        self.timebase_reference.currentTextChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.timebase_reference, 3, 1)
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
        
    def create_trigger_tab(self) -> QWidget:
        """Create trigger configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Trigger Settings")
        group_layout = QGridLayout(group)
        
        # Source
        group_layout.addWidget(QLabel("Source:"), 0, 0)
        self.trigger_source = QComboBox()
        self.trigger_source.addItems(["CH1", "CH2", "CH3", "CH4", "EXT", "LINE"])
        self.trigger_source.currentTextChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.trigger_source, 0, 1)
        
        # Level
        group_layout.addWidget(QLabel("Level (V):"), 1, 0)
        self.trigger_level = QDoubleSpinBox()
        self.trigger_level.setRange(-10.0, 10.0)
        self.trigger_level.setDecimals(3)
        self.trigger_level.valueChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.trigger_level, 1, 1)
        
        # Slope
        group_layout.addWidget(QLabel("Slope:"), 2, 0)
        self.trigger_slope = QComboBox()
        self.trigger_slope.addItems(["POS", "NEG"])
        self.trigger_slope.currentTextChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.trigger_slope, 2, 1)
        
        # Mode
        group_layout.addWidget(QLabel("Mode:"), 3, 0)
        self.trigger_mode = QComboBox()
        self.trigger_mode.addItems(["EDGE", "PULSE", "VIDEO"])
        self.trigger_mode.currentTextChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.trigger_mode, 3, 1)
        
        # Coupling
        group_layout.addWidget(QLabel("Coupling:"), 4, 0)
        self.trigger_coupling = QComboBox()
        self.trigger_coupling.addItems(["DC", "AC", "HF", "LF"])
        self.trigger_coupling.currentTextChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.trigger_coupling, 4, 1)
        
        # Holdoff
        group_layout.addWidget(QLabel("Holdoff (s):"), 5, 0)
        self.trigger_holdoff = QDoubleSpinBox()
        self.trigger_holdoff.setRange(0.0, 1.0)
        self.trigger_holdoff.setDecimals(6)
        self.trigger_holdoff.valueChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.trigger_holdoff, 5, 1)
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
        
    def create_display_tab(self) -> QWidget:
        """Create display configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Display options
        group1 = QGroupBox("Display Options")
        group1_layout = QGridLayout(group1)
        
        self.grid_enabled = QCheckBox("Grid")
        self.grid_enabled.setChecked(True)
        self.grid_enabled.toggled.connect(self.on_config_changed)
        group1_layout.addWidget(self.grid_enabled, 0, 0)
        
        self.crosshair_enabled = QCheckBox("Crosshair")
        self.crosshair_enabled.toggled.connect(self.on_config_changed)
        group1_layout.addWidget(self.crosshair_enabled, 0, 1)
        
        self.persistence_enabled = QCheckBox("Persistence")
        self.persistence_enabled.toggled.connect(self.on_config_changed)
        group1_layout.addWidget(self.persistence_enabled, 1, 0)
        
        self.cursors_enabled = QCheckBox("Cursors")
        self.cursors_enabled.toggled.connect(self.on_config_changed)
        group1_layout.addWidget(self.cursors_enabled, 1, 1)
        
        layout.addWidget(group1)
        
        # Performance settings
        group2 = QGroupBox("Performance Settings")
        group2_layout = QGridLayout(group2)
        
        group2_layout.addWidget(QLabel("Max Points:"), 0, 0)
        self.max_points = QSpinBox()
        self.max_points.setRange(1000, 100000)
        self.max_points.setValue(10000)
        self.max_points.valueChanged.connect(self.on_config_changed)
        group2_layout.addWidget(self.max_points, 0, 1)
        
        group2_layout.addWidget(QLabel("Update Rate (Hz):"), 1, 0)
        self.update_rate = QSpinBox()
        self.update_rate.setRange(1, 60)
        self.update_rate.setValue(30)
        self.update_rate.valueChanged.connect(self.on_config_changed)
        group2_layout.addWidget(self.update_rate, 1, 1)
        
        group2_layout.addWidget(QLabel("Theme:"), 2, 0)
        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])
        self.theme.currentTextChanged.connect(self.on_config_changed)
        group2_layout.addWidget(self.theme, 2, 1)
        
        layout.addWidget(group2)
        layout.addStretch()
        return widget
        
    def create_acquisition_tab(self) -> QWidget:
        """Create acquisition configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Acquisition Settings")
        group_layout = QGridLayout(group)
        
        # Mode
        group_layout.addWidget(QLabel("Mode:"), 0, 0)
        self.acquisition_mode = QComboBox()
        self.acquisition_mode.addItems(["NORMAL", "AVERAGE", "PEAK_DETECT"])
        self.acquisition_mode.currentTextChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.acquisition_mode, 0, 1)
        
        # Sample rate
        group_layout.addWidget(QLabel("Sample Rate (Sa/s):"), 1, 0)
        self.sample_rate = QDoubleSpinBox()
        self.sample_rate.setRange(1e3, 1e10)
        self.sample_rate.setValue(1e9)
        self.sample_rate.setDecimals(0)
        self.sample_rate.valueChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.sample_rate, 1, 1)
        
        # Memory depth
        group_layout.addWidget(QLabel("Memory Depth:"), 2, 0)
        self.memory_depth = QSpinBox()
        self.memory_depth.setRange(1000, 10000000)
        self.memory_depth.setValue(1000000)
        self.memory_depth.valueChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.memory_depth, 2, 1)
        
        # Averages
        group_layout.addWidget(QLabel("Averages:"), 3, 0)
        self.averages = QSpinBox()
        self.averages.setRange(2, 1024)
        self.averages.setValue(16)
        self.averages.valueChanged.connect(self.on_config_changed)
        group_layout.addWidget(self.averages, 3, 1)
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
        
    def create_actions_panel(self) -> QWidget:
        """Create actions panel"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Apply button
        self.apply_btn = QPushButton("Apply Configuration")
        self.apply_btn.clicked.connect(self.apply_configuration)
        layout.addWidget(self.apply_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        layout.addWidget(self.reset_btn)
        
        # Auto-save checkbox
        self.auto_save_cb = QCheckBox("Auto-save")
        self.auto_save_cb.setChecked(True)
        layout.addWidget(self.auto_save_cb)
        
        layout.addStretch()
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        return panel
        
    def setup_connections(self):
        """Setup signal connections"""
        pass
        
    def on_config_changed(self):
        """Handle configuration change"""
        self.update_current_config()
        self.status_label.setText("Configuration modified")
        
    def update_current_config(self):
        """Update current configuration from UI"""
        # Update channels
        for ch, controls in self.channel_controls.items():
            config = self.current_config.channels[ch]
            config.enabled = controls['enabled'].isChecked()
            config.scale = controls['scale'].value()
            config.position = controls['position'].value()
            config.coupling = controls['coupling'].currentText()
            config.label = controls['label'].text()
            
        # Update timebase
        self.current_config.timebase.scale = self.timebase_scale.value()
        self.current_config.timebase.position = self.timebase_position.value()
        self.current_config.timebase.mode = self.timebase_mode.currentText()
        self.current_config.timebase.reference = self.timebase_reference.currentText()
        
        # Update trigger
        self.current_config.trigger.source = self.trigger_source.currentText()
        self.current_config.trigger.level = self.trigger_level.value()
        self.current_config.trigger.slope = self.trigger_slope.currentText()
        self.current_config.trigger.mode = self.trigger_mode.currentText()
        self.current_config.trigger.coupling = self.trigger_coupling.currentText()
        self.current_config.trigger.holdoff = self.trigger_holdoff.value()
        
        # Update display
        self.current_config.display.grid_enabled = self.grid_enabled.isChecked()
        self.current_config.display.crosshair_enabled = self.crosshair_enabled.isChecked()
        self.current_config.display.persistence_enabled = self.persistence_enabled.isChecked()
        self.current_config.display.cursors_enabled = self.cursors_enabled.isChecked()
        self.current_config.display.max_points = self.max_points.value()
        self.current_config.display.update_rate = self.update_rate.value()
        self.current_config.display.theme = self.theme.currentText()
        
        # Update acquisition
        self.current_config.acquisition.mode = self.acquisition_mode.currentText()
        self.current_config.acquisition.sample_rate = self.sample_rate.value()
        self.current_config.acquisition.memory_depth = self.memory_depth.value()
        self.current_config.acquisition.averages = self.averages.value()
        
    def load_current_config(self):
        """Load current configuration to UI"""
        # Load channels
        for ch, config in self.current_config.channels.items():
            if ch in self.channel_controls:
                controls = self.channel_controls[ch]
                controls['enabled'].setChecked(config.enabled)
                controls['scale'].setValue(config.scale)
                controls['position'].setValue(config.position)
                controls['coupling'].setCurrentText(config.coupling)
                controls['label'].setText(config.label)
                controls['color_label'].setStyleSheet(f"background-color: {config.color}; border: 1px solid gray; border-radius: 2px;")
                
        # Load timebase
        self.timebase_scale.setValue(self.current_config.timebase.scale)
        self.timebase_position.setValue(self.current_config.timebase.position)
        self.timebase_mode.setCurrentText(self.current_config.timebase.mode)
        self.timebase_reference.setCurrentText(self.current_config.timebase.reference)
        
        # Load trigger
        self.trigger_source.setCurrentText(self.current_config.trigger.source)
        self.trigger_level.setValue(self.current_config.trigger.level)
        self.trigger_slope.setCurrentText(self.current_config.trigger.slope)
        self.trigger_mode.setCurrentText(self.current_config.trigger.mode)
        self.trigger_coupling.setCurrentText(self.current_config.trigger.coupling)
        self.trigger_holdoff.setValue(self.current_config.trigger.holdoff)
        
        # Load display
        self.grid_enabled.setChecked(self.current_config.display.grid_enabled)
        self.crosshair_enabled.setChecked(self.current_config.display.crosshair_enabled)
        self.persistence_enabled.setChecked(self.current_config.display.persistence_enabled)
        self.cursors_enabled.setChecked(self.current_config.display.cursors_enabled)
        self.max_points.setValue(self.current_config.display.max_points)
        self.update_rate.setValue(self.current_config.display.update_rate)
        self.theme.setCurrentText(self.current_config.display.theme)
        
        # Load acquisition
        self.acquisition_mode.setCurrentText(self.current_config.acquisition.mode)
        self.sample_rate.setValue(self.current_config.acquisition.sample_rate)
        self.memory_depth.setValue(self.current_config.acquisition.memory_depth)
        self.averages.setValue(self.current_config.acquisition.averages)
        
    def refresh_presets(self):
        """Refresh presets list"""
        self.presets_list.clear()
        
        presets = self.config_manager.list_presets()
        for preset in presets:
            item = QListWidgetItem(preset['name'])
            item.setToolTip(f"Description: {preset['description']}\nCreated: {preset['created']}")
            self.presets_list.addItem(item)
            
    def load_selected_preset(self):
        """Load selected preset"""
        current_item = self.presets_list.currentItem()
        if current_item:
            preset_name = current_item.text()
            if self.config_manager.load_preset(preset_name):
                self.current_config = self.config_manager.get_current_config()
                self.load_current_config()
                self.status_label.setText(f"Loaded preset: {preset_name}")
                self.configuration_loaded.emit(self.current_config)
            else:
                QMessageBox.warning(self, "Error", f"Failed to load preset: {preset_name}")
                
    def save_as_preset(self):
        """Save current configuration as preset"""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if ok and name:
            description, ok2 = QInputDialog.getText(self, "Save Preset", "Description (optional):")
            if ok2:
                self.update_current_config()
                if self.config_manager.save_preset(name, description):
                    self.refresh_presets()
                    self.status_label.setText(f"Saved preset: {name}")
                    self.configuration_saved.emit(name)
                else:
                    QMessageBox.warning(self, "Error", f"Failed to save preset: {name}")
                    
    def delete_selected_preset(self):
        """Delete selected preset"""
        current_item = self.presets_list.currentItem()
        if current_item:
            preset_name = current_item.text()
            reply = QMessageBox.question(
                self, "Confirm Delete", 
                f"Are you sure you want to delete preset '{preset_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.config_manager.delete_preset(preset_name):
                    self.refresh_presets()
                    self.status_label.setText(f"Deleted preset: {preset_name}")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete preset: {preset_name}")
                    
    def export_configuration(self):
        """Export current configuration"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", 
            f"rtb2000_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON files (*.json)"
        )
        
        if filepath:
            if self.config_manager.export_configuration(filepath, include_presets=False):
                self.status_label.setText(f"Exported configuration to {filepath}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export configuration")
                
    def import_configuration(self):
        """Import configuration"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "",
            "JSON files (*.json)"
        )
        
        if filepath:
            if self.config_manager.import_configuration(filepath, import_presets=False):
                self.current_config = self.config_manager.get_current_config()
                self.load_current_config()
                self.status_label.setText(f"Imported configuration from {filepath}")
                self.configuration_loaded.emit(self.current_config)
            else:
                QMessageBox.warning(self, "Error", "Failed to import configuration")
                
    def export_all_presets(self):
        """Export all presets"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export All Presets", 
            f"rtb2000_presets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON files (*.json)"
        )
        
        if filepath:
            if self.config_manager.export_configuration(filepath, include_presets=True):
                self.status_label.setText(f"Exported all presets to {filepath}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export presets")
                
    def apply_configuration(self):
        """Apply current configuration"""
        self.update_current_config()
        if self.config_manager.save_current():
            self.status_label.setText("Configuration applied and saved")
            self.configuration_loaded.emit(self.current_config)
        else:
            QMessageBox.warning(self, "Error", "Failed to save configuration")
            
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        reply = QMessageBox.question(
            self, "Confirm Reset", 
            "Are you sure you want to reset to default configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_config = RTB2000Configuration()
            self.load_current_config()
            self.status_label.setText("Reset to default configuration")
            
    def auto_save(self):
        """Auto-save current configuration"""
        if self.auto_save_cb.isChecked():
            self.update_current_config()
            self.config_manager.save_current()
            
    def update_session_info(self):
        """Update session information"""
        presets_count = len(self.config_manager.list_presets())
        info_text = f"Presets: {presets_count}\n"
        info_text += f"Last modified: {self.current_config.modified[:16] if self.current_config.modified else 'Never'}"
        self.session_info.setText(info_text)
        
    def get_current_configuration(self) -> RTB2000Configuration:
        """Get current configuration"""
        self.update_current_config()
        return self.current_config
