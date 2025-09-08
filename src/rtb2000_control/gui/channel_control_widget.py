"""
Channel Control Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QDoubleSpinBox, QComboBox, QGroupBox,
                             QGridLayout)
from PyQt6.QtCore import pyqtSignal


class ChannelControlWidget(QWidget):
    """Widget for controlling oscilloscope channels"""
    
    # Signals
    settings_changed = pyqtSignal(int, dict)  # channel, settings
    
    def __init__(self):
        super().__init__()
        self.channels = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create controls for each channel
        for channel in range(1, 5):
            group = self.create_channel_group(channel)
            layout.addWidget(group)
            
    def create_channel_group(self, channel: int) -> QGroupBox:
        """Create control group for a channel"""
        group = QGroupBox(f"Channel {channel}")
        layout = QGridLayout()
        group.setLayout(layout)
        
        # Channel enable
        enable_cb = QCheckBox("Enable")
        enable_cb.stateChanged.connect(
            lambda state, ch=channel: self.on_setting_changed(ch, 'enabled', enable_cb.isChecked())
        )
        layout.addWidget(enable_cb, 0, 0)
        
        # Vertical scale
        layout.addWidget(QLabel("Scale (V/div):"), 1, 0)
        scale_spin = QDoubleSpinBox()
        scale_spin.setRange(0.001, 10.0)
        scale_spin.setValue(1.0)
        scale_spin.setDecimals(3)
        scale_spin.valueChanged.connect(
            lambda value, ch=channel: self.on_setting_changed(ch, 'scale', value)
        )
        layout.addWidget(scale_spin, 1, 1)
        
        # Vertical position
        layout.addWidget(QLabel("Position (div):"), 2, 0)
        pos_spin = QDoubleSpinBox()
        pos_spin.setRange(-5.0, 5.0)
        pos_spin.setValue(0.0)
        pos_spin.valueChanged.connect(
            lambda value, ch=channel: self.on_setting_changed(ch, 'position', value)
        )
        layout.addWidget(pos_spin, 2, 1)
        
        # Coupling
        layout.addWidget(QLabel("Coupling:"), 3, 0)
        coupling_combo = QComboBox()
        coupling_combo.addItems(["DC", "AC", "GND"])
        coupling_combo.currentTextChanged.connect(
            lambda text, ch=channel: self.on_setting_changed(ch, 'coupling', text)
        )
        layout.addWidget(coupling_combo, 3, 1)
        
        # Store references
        self.channels[channel] = {
            'enable': enable_cb,
            'scale': scale_spin,
            'position': pos_spin,
            'coupling': coupling_combo
        }
        
        return group
        
    def on_setting_changed(self, channel: int, setting: str, value):
        """Handle setting change"""
        self.settings_changed.emit(channel, {setting: value})
        
    def update_channel_info(self, channel: int, info: dict):
        """Update channel display with current info"""
        if channel in self.channels:
            controls = self.channels[channel]
            
            if 'enabled' in info:
                controls['enable'].setChecked(info['enabled'])
            if 'scale' in info:
                controls['scale'].setValue(info['scale'])
            if 'position' in info:
                controls['position'].setValue(info['position'])
            if 'coupling' in info:
                index = controls['coupling'].findText(info['coupling'])
                if index >= 0:
                    controls['coupling'].setCurrentIndex(index)
                    
    def is_channel_enabled(self, channel: int) -> bool:
        """Check if channel is enabled"""
        if channel in self.channels:
            return self.channels[channel]['enable'].isChecked()
        return False
