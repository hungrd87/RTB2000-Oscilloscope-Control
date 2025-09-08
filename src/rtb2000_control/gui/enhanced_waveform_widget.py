"""
Enhanced Waveform Display Widget using PyQtGraph
Version 2.0 - September 8, 2025

High-performance real-time plotting for RTB2000 oscilloscope
"""

import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGroupBox, QSlider, QSpinBox,
                             QCheckBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import pyqtgraph as pg
from typing import Dict, Tuple, Optional, List


class EnhancedWaveformWidget(QWidget):
    """Enhanced widget for displaying oscilloscope waveforms with PyQtGraph"""
    
    # Signals
    cursor_moved = pyqtSignal(float, float)  # time, voltage
    zoom_changed = pyqtSignal(float, float)  # x_range, y_range
    measurement_requested = pyqtSignal(str, int)  # measurement_type, channel
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.max_points = 10000  # Maximum points to display
        self.update_rate = 30    # FPS for real-time updates
        
        # Data storage
        self.waveform_data = {}  # {channel: (time, voltage)}
        self.plot_items = {}     # {channel: PlotDataItem}
        self.cursors = {}        # {cursor_id: InfiniteLine}
        
        # Channel configuration
        self.channel_colors = {
            1: '#FFFF00',  # Yellow
            2: '#00FFFF',  # Cyan  
            3: '#FF00FF',  # Magenta
            4: '#00FF00'   # Green
        }
        
        self.channel_enabled = {1: True, 2: True, 3: True, 4: True}
        
        # Measurement cursors
        self.cursor_enabled = False
        self.measurement_mode = "None"
        
        self.init_ui()
        self.setup_plot()
        
    def init_ui(self):
        """Initialize enhanced user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Control panel
        controls_group = QGroupBox("Waveform Display Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Channel controls row
        channel_row = QHBoxLayout()
        
        channel_row.addWidget(QLabel("Channels:"))
        
        self.channel_checkboxes = {}
        for ch in range(1, 5):
            cb = QCheckBox(f"CH{ch}")
            cb.setChecked(True)
            cb.setStyleSheet(f"QCheckBox {{ color: {self.channel_colors[ch]}; font-weight: bold; }}")
            cb.toggled.connect(lambda checked, channel=ch: self.toggle_channel(channel, checked))
            self.channel_checkboxes[ch] = cb
            channel_row.addWidget(cb)
            
        channel_row.addStretch()
        controls_layout.addLayout(channel_row)
        
        # Display controls row
        display_row = QHBoxLayout()
        
        # Auto-scale
        self.autoscale_btn = QPushButton("📐 Auto Scale")
        self.autoscale_btn.setToolTip("Auto-scale all axes to fit data")
        self.autoscale_btn.clicked.connect(self.auto_scale)
        display_row.addWidget(self.autoscale_btn)
        
        # Grid toggle
        self.grid_cb = QCheckBox("Grid")
        self.grid_cb.setChecked(True)
        self.grid_cb.toggled.connect(self.toggle_grid)
        display_row.addWidget(self.grid_cb)
        
        # Crosshair toggle
        self.crosshair_cb = QCheckBox("Crosshair")
        self.crosshair_cb.toggled.connect(self.toggle_crosshair)
        display_row.addWidget(self.crosshair_cb)
        
        # Persistence mode
        self.persistence_cb = QCheckBox("Persistence")
        self.persistence_cb.setToolTip("Keep previous waveforms visible")
        self.persistence_cb.toggled.connect(self.toggle_persistence)
        display_row.addWidget(self.persistence_cb)
        
        display_row.addStretch()
        controls_layout.addLayout(display_row)
        
        # Measurement controls row
        measurement_row = QHBoxLayout()
        
        measurement_row.addWidget(QLabel("Measurements:"))
        
        # Cursor controls
        self.cursor_btn = QPushButton("📍 Cursors")
        self.cursor_btn.setCheckable(True)
        self.cursor_btn.toggled.connect(self.toggle_cursors)
        measurement_row.addWidget(self.cursor_btn)
        
        # Measurement type
        self.measurement_combo = QComboBox()
        self.measurement_combo.addItems([
            "None", "Peak-to-Peak", "RMS", "Frequency", 
            "Period", "Rise Time", "Fall Time", "Duty Cycle"
        ])
        self.measurement_combo.currentTextChanged.connect(self.set_measurement_mode)
        measurement_row.addWidget(self.measurement_combo)
        
        # Screenshot button
        self.screenshot_btn = QPushButton("📷 Screenshot")
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        measurement_row.addWidget(self.screenshot_btn)
        
        measurement_row.addStretch()
        controls_layout.addLayout(measurement_row)
        
        # Performance controls
        perf_row = QHBoxLayout()
        
        perf_row.addWidget(QLabel("Max Points:"))
        self.points_spin = QSpinBox()
        self.points_spin.setRange(1000, 100000)
        self.points_spin.setSingleStep(1000)
        self.points_spin.setValue(self.max_points)
        self.points_spin.valueChanged.connect(self.set_max_points)
        perf_row.addWidget(self.points_spin)
        
        perf_row.addWidget(QLabel("Update Rate:"))
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(1, 60)
        self.rate_spin.setSuffix(" FPS")
        self.rate_spin.setValue(self.update_rate)
        self.rate_spin.valueChanged.connect(self.set_update_rate)
        perf_row.addWidget(self.rate_spin)
        
        perf_row.addStretch()
        controls_layout.addLayout(perf_row)
        
        layout.addWidget(controls_group)
        
        # Main plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMinimumHeight(400)
        layout.addWidget(self.plot_widget)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        self.cursor_label = QLabel("Cursor: ---")
        self.cursor_label.setStyleSheet("font-family: monospace;")
        status_layout.addWidget(self.cursor_label)
        
        status_layout.addStretch()
        
        self.performance_label = QLabel("Performance: --- FPS")
        status_layout.addWidget(self.performance_label)
        
        layout.addLayout(status_layout)
        
    def setup_plot(self):
        """Setup the PyQtGraph plot widget"""
        # Configure plot appearance
        self.plot_widget.setBackground('black')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Set labels
        self.plot_widget.setLabel('left', 'Voltage', 'V')
        self.plot_widget.setLabel('bottom', 'Time', 's')
        self.plot_widget.setTitle('RTB2000 Oscilloscope Waveforms')
        
        # Enable mouse interaction
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.enableAutoRange()
        
        # Create legend
        self.legend = self.plot_widget.addLegend()
        
        # Setup crosshair
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', width=1, style=Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', width=1, style=Qt.PenStyle.DashLine))
        
        # Connect mouse move event
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)
        
        # Performance monitoring
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self.update_performance)
        self.perf_timer.start(1000)  # Update every second
        
        self.frame_count = 0
        self.last_perf_time = 0
        
    def toggle_channel(self, channel: int, enabled: bool):
        """Toggle channel visibility"""
        self.channel_enabled[channel] = enabled
        
        if channel in self.plot_items:
            self.plot_items[channel].setVisible(enabled)
            
    def toggle_grid(self, enabled: bool):
        """Toggle grid display"""
        self.plot_widget.showGrid(x=enabled, y=enabled, alpha=0.3)
        
    def toggle_crosshair(self, enabled: bool):
        """Toggle crosshair display"""
        if enabled:
            self.plot_widget.addItem(self.v_line, ignoreBounds=True)
            self.plot_widget.addItem(self.h_line, ignoreBounds=True)
        else:
            self.plot_widget.removeItem(self.v_line)
            self.plot_widget.removeItem(self.h_line)
            
    def toggle_persistence(self, enabled: bool):
        """Toggle persistence mode"""
        if not enabled:
            # Clear all old plot items
            for channel, item in self.plot_items.items():
                if not self.channel_enabled[channel]:
                    self.plot_widget.removeItem(item)
                    
    def toggle_cursors(self, enabled: bool):
        """Toggle measurement cursors"""
        self.cursor_enabled = enabled
        
        if enabled:
            # Create measurement cursors
            if 'cursor1' not in self.cursors:
                self.cursors['cursor1'] = pg.InfiniteLine(
                    angle=90, movable=True, 
                    pen=pg.mkPen('y', width=2),
                    label='C1'
                )
                self.cursors['cursor2'] = pg.InfiniteLine(
                    angle=90, movable=True,
                    pen=pg.mkPen('r', width=2), 
                    label='C2'
                )
                
                # Connect cursor move events
                self.cursors['cursor1'].sigPositionChanged.connect(self.on_cursor_moved)
                self.cursors['cursor2'].sigPositionChanged.connect(self.on_cursor_moved)
                
            self.plot_widget.addItem(self.cursors['cursor1'])
            self.plot_widget.addItem(self.cursors['cursor2'])
        else:
            # Remove cursors
            for cursor in self.cursors.values():
                self.plot_widget.removeItem(cursor)
                
    def set_measurement_mode(self, mode: str):
        """Set measurement mode"""
        self.measurement_mode = mode
        
    def set_max_points(self, points: int):
        """Set maximum points to display"""
        self.max_points = points
        
    def set_update_rate(self, rate: int):
        """Set update rate"""
        self.update_rate = rate
        
    def auto_scale(self):
        """Auto-scale the plot to fit all data"""
        self.plot_widget.autoRange()
        
    def take_screenshot(self):
        """Take screenshot of the plot"""
        try:
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.export('rtb2000_waveform_screenshot.png')
            
            # Show success message in status
            self.cursor_label.setText("Screenshot saved: rtb2000_waveform_screenshot.png")
            
            # Reset status after 3 seconds
            QTimer.singleShot(3000, lambda: self.cursor_label.setText("Cursor: ---"))
            
        except Exception as e:
            self.cursor_label.setText(f"Screenshot error: {e}")
            
    def on_mouse_moved(self, pos):
        """Handle mouse movement for crosshair"""
        if self.crosshair_cb.isChecked():
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            
            self.v_line.setPos(mouse_point.x())
            self.h_line.setPos(mouse_point.y())
            
            # Update cursor display
            self.cursor_label.setText(
                f"Cursor: T={mouse_point.x():.6f}s, V={mouse_point.y():.3f}V"
            )
            
            # Emit signal
            self.cursor_moved.emit(mouse_point.x(), mouse_point.y())
            
    def on_cursor_moved(self):
        """Handle measurement cursor movement"""
        if len(self.cursors) >= 2:
            pos1 = self.cursors['cursor1'].getPos()[0]
            pos2 = self.cursors['cursor2'].getPos()[0]
            
            delta_t = abs(pos2 - pos1)
            freq = 1.0 / delta_t if delta_t > 0 else 0
            
            self.cursor_label.setText(
                f"ΔT={delta_t:.6f}s, F={freq:.2f}Hz"
            )
            
    def update_waveforms(self, waveform_data: Dict[int, Tuple[np.ndarray, np.ndarray]]):
        """
        Update waveform display with new data
        
        Args:
            waveform_data: Dictionary with channel numbers as keys,
                          (time_data, voltage_data) tuples as values
        """
        self.frame_count += 1
        
        for channel, (time_data, voltage_data) in waveform_data.items():
            if not self.channel_enabled[channel]:
                continue
                
            # Limit points for performance
            if len(time_data) > self.max_points:
                step = len(time_data) // self.max_points
                time_data = time_data[::step]
                voltage_data = voltage_data[::step]
                
            # Create or update plot item
            if channel not in self.plot_items:
                self.plot_items[channel] = self.plot_widget.plot(
                    time_data, voltage_data,
                    pen=pg.mkPen(self.channel_colors[channel], width=2),
                    name=f'CH{channel}'
                )
            else:
                self.plot_items[channel].setData(time_data, voltage_data)
                
        # Store data for measurements
        self.waveform_data = waveform_data
        
        # Perform automatic measurements if enabled
        if self.measurement_mode != "None":
            self.perform_measurements()
            
    def perform_measurements(self):
        """Perform automatic measurements on visible channels"""
        # This will be expanded with actual measurement algorithms
        pass
        
    def update_performance(self):
        """Update performance metrics"""
        import time
        current_time = time.time()
        
        if self.last_perf_time > 0:
            elapsed = current_time - self.last_perf_time
            fps = self.frame_count / elapsed if elapsed > 0 else 0
            
            self.performance_label.setText(f"Performance: {fps:.1f} FPS")
            
        self.last_perf_time = current_time
        self.frame_count = 0
        
    def clear_display(self):
        """Clear all waveform data"""
        for item in self.plot_items.values():
            self.plot_widget.removeItem(item)
            
        self.plot_items.clear()
        self.waveform_data.clear()
        
    def get_plot_config(self) -> dict:
        """Get current plot configuration"""
        return {
            'channels_enabled': self.channel_enabled.copy(),
            'grid_enabled': self.grid_cb.isChecked(),
            'crosshair_enabled': self.crosshair_cb.isChecked(),
            'persistence_enabled': self.persistence_cb.isChecked(),
            'cursors_enabled': self.cursor_enabled,
            'measurement_mode': self.measurement_mode,
            'max_points': self.max_points,
            'update_rate': self.update_rate
        }
        
    def set_plot_config(self, config: dict):
        """Apply plot configuration"""
        for channel, enabled in config.get('channels_enabled', {}).items():
            if channel in self.channel_checkboxes:
                self.channel_checkboxes[channel].setChecked(enabled)
                
        self.grid_cb.setChecked(config.get('grid_enabled', True))
        self.crosshair_cb.setChecked(config.get('crosshair_enabled', False))
        self.persistence_cb.setChecked(config.get('persistence_enabled', False))
        
        if config.get('cursors_enabled', False):
            self.cursor_btn.setChecked(True)
            
        measurement_mode = config.get('measurement_mode', 'None')
        index = self.measurement_combo.findText(measurement_mode)
        if index >= 0:
            self.measurement_combo.setCurrentIndex(index)
            
        self.points_spin.setValue(config.get('max_points', 10000))
        self.rate_spin.setValue(config.get('update_rate', 30))


# Maintain backward compatibility
class WaveformWidget(EnhancedWaveformWidget):
    """Backward compatibility wrapper"""
    
    def __init__(self):
        super().__init__()
        # Override some settings for compatibility
        self.measurement_combo.setVisible(False)  # Hide advanced features
        self.cursor_btn.setVisible(False)
        
    def update_waveforms(self, waveform_data: dict):
        """Backward compatible update method"""
        # Convert to expected format if needed
        converted_data = {}
        for channel, data in waveform_data.items():
            if isinstance(data, tuple) and len(data) == 2:
                converted_data[channel] = data
            else:
                # Handle other formats if needed
                continue
                
        super().update_waveforms(converted_data)
