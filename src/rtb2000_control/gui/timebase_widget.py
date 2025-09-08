"""
Timebase Control Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QGroupBox, QGridLayout)
from PyQt6.QtCore import pyqtSignal


class TimebaseWidget(QWidget):
    """Widget for controlling timebase settings"""
    
    # Signals
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Timebase group
        group = QGroupBox("Horizontal Timebase")
        grid_layout = QGridLayout()
        group.setLayout(grid_layout)
        layout.addWidget(group)
        
        # Time scale
        grid_layout.addWidget(QLabel("Time Scale (s/div):"), 0, 0)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(1e-9, 10.0)
        self.scale_spin.setValue(1e-3)
        self.scale_spin.setDecimals(9)
        self.scale_spin.valueChanged.connect(self.on_scale_changed)
        grid_layout.addWidget(self.scale_spin, 0, 1)
        
        # Time position
        grid_layout.addWidget(QLabel("Position (s):"), 1, 0)
        self.position_spin = QDoubleSpinBox()
        self.position_spin.setRange(-10.0, 10.0)
        self.position_spin.setValue(0.0)
        self.position_spin.setDecimals(6)
        self.position_spin.valueChanged.connect(self.on_position_changed)
        grid_layout.addWidget(self.position_spin, 1, 1)
        
    def on_scale_changed(self, value: float):
        """Handle scale change"""
        self.settings_changed.emit({'scale': value})
        
    def on_position_changed(self, value: float):
        """Handle position change"""
        self.settings_changed.emit({'position': value})
        
    def update_settings(self, settings: dict):
        """Update widget with current settings"""
        if 'timebase_scale' in settings:
            self.scale_spin.setValue(settings['timebase_scale'])
        if 'timebase_position' in settings:
            self.position_spin.setValue(settings['timebase_position'])
