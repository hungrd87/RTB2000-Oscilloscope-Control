"""
Trigger Control Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QComboBox, QGroupBox, QGridLayout)
from PyQt6.QtCore import pyqtSignal


class TriggerWidget(QWidget):
    """Widget for controlling trigger settings"""
    
    # Signals
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Trigger group
        group = QGroupBox("Trigger Settings")
        grid_layout = QGridLayout()
        group.setLayout(grid_layout)
        layout.addWidget(group)
        
        # Trigger source
        grid_layout.addWidget(QLabel("Source:"), 0, 0)
        self.source_combo = QComboBox()
        self.source_combo.addItems(["CH1", "CH2", "CH3", "CH4", "EXT"])
        self.source_combo.currentTextChanged.connect(self.on_source_changed)
        grid_layout.addWidget(self.source_combo, 0, 1)
        
        # Trigger level
        grid_layout.addWidget(QLabel("Level (V):"), 1, 0)
        self.level_spin = QDoubleSpinBox()
        self.level_spin.setRange(-10.0, 10.0)
        self.level_spin.setValue(0.0)
        self.level_spin.setDecimals(3)
        self.level_spin.valueChanged.connect(self.on_level_changed)
        grid_layout.addWidget(self.level_spin, 1, 1)
        
        # Trigger slope
        grid_layout.addWidget(QLabel("Slope:"), 2, 0)
        self.slope_combo = QComboBox()
        self.slope_combo.addItems(["POS", "NEG"])
        self.slope_combo.currentTextChanged.connect(self.on_slope_changed)
        grid_layout.addWidget(self.slope_combo, 2, 1)
        
    def on_source_changed(self, source: str):
        """Handle source change"""
        self.settings_changed.emit({'source': source})
        
    def on_level_changed(self, level: float):
        """Handle level change"""
        self.settings_changed.emit({'level': level})
        
    def on_slope_changed(self, slope: str):
        """Handle slope change"""
        self.settings_changed.emit({'slope': slope})
        
    def update_settings(self, settings: dict):
        """Update widget with current settings"""
        if 'trigger_source' in settings:
            index = self.source_combo.findText(settings['trigger_source'])
            if index >= 0:
                self.source_combo.setCurrentIndex(index)
                
        if 'trigger_level' in settings:
            self.level_spin.setValue(settings['trigger_level'])
            
        if 'trigger_slope' in settings:
            index = self.slope_combo.findText(settings['trigger_slope'])
            if index >= 0:
                self.slope_combo.setCurrentIndex(index)
