"""
Enhanced Waveform Display Widget
Version 2.0 - Integrated PyQtGraph for high-performance real-time display
"""

import numpy as np
from typing import Dict, Tuple, Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QCheckBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QSlider, QGroupBox, QFileDialog,
    QMessageBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette

import pyqtgraph as pg
from pyqtgraph import PlotWidget, mkPen, mkBrush
import pyqtgraph.exporters


class WaveformWidget(QWidget):
    """Enhanced waveform display widget with PyQtGraph backend"""
    
    # Signals
    measurement_updated = pyqtSignal(dict)
    cursor_moved = pyqtSignal(float, float)
    
    def __init__(self):
        super().__init__()
        
        # Configure PyQtGraph
        pg.setConfigOptions(antialias=True)
        pg.setConfigOption('background', 'k')
        pg.setConfigOption('foreground', 'w')
        
        # Initialize data storage
        self.waveform_data = {}
        self.plot_items = {}
        self.cursors = {'vertical': [], 'horizontal': []}
        self.measurements = {}
        
        # Performance tracking
        self.update_count = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)
        self.last_update_time = 0
        
        # Channel configuration
        self.channel_colors = {
            1: '#FFFF00',  # Yellow
            2: '#00FFFF',  # Cyan
            3: '#FF00FF',  # Magenta
            4: '#00FF00'   # Green
        }
        
        self.channel_enabled = {1: True, 2: False, 3: False, 4: False}
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Plot area
        plot_widget = self.create_plot_widget()
        main_splitter.addWidget(plot_widget)
        
        # Right panel - Controls
        control_panel = self.create_control_panel()
        main_splitter.addWidget(control_panel)
        
        # Set splitter proportions (80% plot, 20% controls)
        main_splitter.setSizes([800, 200])
        
        # Bottom status bar
        status_layout = QHBoxLayout()
        self.fps_label = QLabel("FPS: 0")
        self.samples_label = QLabel("Samples: 0")
        self.cursor_label = QLabel("Cursor: --")
        
        status_layout.addWidget(self.fps_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.samples_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.cursor_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
    def create_plot_widget(self) -> QWidget:
        """Create the main plot widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create plot widget
        self.plot_widget = PlotWidget()
        self.plot_widget.setLabel('left', 'Voltage', 'V')
        self.plot_widget.setLabel('bottom', 'Time', 's')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.enableAutoRange()
        
        # Add crosshair
        self.crosshair_v = pg.InfiniteLine(angle=90, movable=False, pen='w')
        self.crosshair_h = pg.InfiniteLine(angle=0, movable=False, pen='w')
        self.plot_widget.addItem(self.crosshair_v, ignoreBounds=True)
        self.plot_widget.addItem(self.crosshair_h, ignoreBounds=True)
        self.crosshair_v.hide()
        self.crosshair_h.hide()
        
        # Connect mouse events
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.plot_widget.scene().sigMouseClicked.connect(self.on_mouse_clicked)
        
        layout.addWidget(self.plot_widget)
        
        return widget
        
    def create_control_panel(self) -> QWidget:
        """Create control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Channel controls
        channels_group = QGroupBox("Channels")
        channels_layout = QGridLayout(channels_group)
        
        self.channel_controls = {}
        for ch in range(1, 5):
            # Channel enable checkbox
            enable_cb = QCheckBox(f"CH{ch}")
            enable_cb.setChecked(self.channel_enabled[ch])
            enable_cb.toggled.connect(lambda checked, c=ch: self.toggle_channel(c, checked))
            
            # Color indicator
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(f"background-color: {self.channel_colors[ch]}; border: 1px solid white;")
            
            channels_layout.addWidget(enable_cb, ch-1, 0)
            channels_layout.addWidget(color_label, ch-1, 1)
            
            self.channel_controls[ch] = {
                'enable': enable_cb,
                'color': color_label
            }
            
        layout.addWidget(channels_group)
        
        # Display controls
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout(display_group)
        
        # Auto-scale button
        auto_scale_btn = QPushButton("Auto Scale")
        auto_scale_btn.clicked.connect(self.auto_scale)
        display_layout.addWidget(auto_scale_btn)
        
        # Grid toggle
        self.grid_cb = QCheckBox("Grid")
        self.grid_cb.setChecked(True)
        self.grid_cb.toggled.connect(self.toggle_grid)
        display_layout.addWidget(self.grid_cb)
        
        # Crosshair toggle
        self.crosshair_cb = QCheckBox("Crosshair")
        self.crosshair_cb.toggled.connect(self.toggle_crosshair)
        display_layout.addWidget(self.crosshair_cb)
        
        layout.addWidget(display_group)
        
        # Measurement controls
        measurement_group = QGroupBox("Measurements")
        measurement_layout = QVBoxLayout(measurement_group)
        
        # Measurement display
        self.measurement_labels = {}
        for ch in range(1, 5):
            label = QLabel(f"CH{ch}: --")
            label.setFont(QFont("Consolas", 8))
            self.measurement_labels[ch] = label
            measurement_layout.addWidget(label)
            
        layout.addWidget(measurement_group)
        
        # Export controls
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        # Screenshot button
        screenshot_btn = QPushButton("Screenshot")
        screenshot_btn.clicked.connect(self.take_screenshot)
        export_layout.addWidget(screenshot_btn)
        
        # Export data button
        export_data_btn = QPushButton("Export Data")
        export_data_btn.clicked.connect(self.export_data)
        export_layout.addWidget(export_data_btn)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        return panel
        
    def update_waveforms(self, waveform_data: dict):
        """
        Update waveform display
        
        Args:
            waveform_data: Dictionary with channel numbers as keys,
                          (time_data, voltage_data) tuples as values
        """
        self.waveform_data = waveform_data
        self.update_count += 1
        
        # Clear existing plot items for disabled channels
        for ch in list(self.plot_items.keys()):
            if ch not in waveform_data or not self.channel_enabled[ch]:
                self.plot_widget.removeItem(self.plot_items[ch])
                del self.plot_items[ch]
        
        # Update or create plot items for enabled channels
        for channel, (time_data, voltage_data) in waveform_data.items():
            if not self.channel_enabled[channel]:
                continue
                
            color = self.channel_colors[channel]
            pen = mkPen(color=color, width=2)
            
            if channel in self.plot_items:
                # Update existing plot
                self.plot_items[channel].setData(time_data, voltage_data)
            else:
                # Create new plot
                plot_item = self.plot_widget.plot(
                    time_data, voltage_data,
                    pen=pen,
                    name=f'CH{channel}'
                )
                self.plot_items[channel] = plot_item
                
        # Update measurements
        self.update_measurements()
        
        # Update sample count
        total_samples = sum(len(data[1]) for data in waveform_data.values())
        self.samples_label.setText(f"Samples: {total_samples}")
        
    def toggle_channel(self, channel: int, enabled: bool):
        """Toggle channel display"""
        self.channel_enabled[channel] = enabled
        
        if not enabled and channel in self.plot_items:
            self.plot_widget.removeItem(self.plot_items[channel])
            del self.plot_items[channel]
        elif enabled and channel in self.waveform_data:
            # Re-add the channel
            time_data, voltage_data = self.waveform_data[channel]
            color = self.channel_colors[channel]
            pen = mkPen(color=color, width=2)
            
            plot_item = self.plot_widget.plot(
                time_data, voltage_data,
                pen=pen,
                name=f'CH{channel}'
            )
            self.plot_items[channel] = plot_item
            
    def auto_scale(self):
        """Auto-scale the plot"""
        self.plot_widget.autoRange()
        
    def toggle_grid(self, enabled: bool):
        """Toggle grid display"""
        self.plot_widget.showGrid(x=enabled, y=enabled, alpha=0.3)
        
    def toggle_crosshair(self, enabled: bool):
        """Toggle crosshair display"""
        if enabled:
            self.crosshair_v.show()
            self.crosshair_h.show()
        else:
            self.crosshair_v.hide()
            self.crosshair_h.hide()
            
    def on_mouse_moved(self, pos):
        """Handle mouse movement for crosshair"""
        if self.crosshair_cb.isChecked() and self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            self.crosshair_v.setPos(mouse_point.x())
            self.crosshair_h.setPos(mouse_point.y())
            
            # Update cursor label
            self.cursor_label.setText(f"Cursor: {mouse_point.x():.6f}s, {mouse_point.y():.3f}V")
            
            # Emit signal
            self.cursor_moved.emit(mouse_point.x(), mouse_point.y())
            
    def on_mouse_clicked(self, event):
        """Handle mouse clicks"""
        # Future: Add measurement cursors on click
        pass
        
    def update_measurements(self):
        """Update measurement displays"""
        for channel, (time_data, voltage_data) in self.waveform_data.items():
            if not self.channel_enabled[channel]:
                self.measurement_labels[channel].setText(f"CH{channel}: Disabled")
                continue
                
            if len(voltage_data) == 0:
                self.measurement_labels[channel].setText(f"CH{channel}: No Data")
                continue
                
            # Calculate basic measurements
            vpp = np.max(voltage_data) - np.min(voltage_data)
            vrms = np.sqrt(np.mean(voltage_data**2))
            vmean = np.mean(voltage_data)
            
            # Update display
            self.measurement_labels[channel].setText(
                f"CH{channel}: Vpp={vpp:.3f}V RMS={vrms:.3f}V"
            )
            
            # Store measurements
            self.measurements[channel] = {
                'vpp': vpp,
                'vrms': vrms,
                'vmean': vmean
            }
            
        # Emit measurement update signal
        self.measurement_updated.emit(self.measurements)
        
    def update_fps(self):
        """Update FPS display"""
        fps = self.update_count
        self.fps_label.setText(f"FPS: {fps}")
        self.update_count = 0
        
    def take_screenshot(self):
        """Take screenshot of the plot"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"waveform_screenshot_{timestamp}.png"
            
            # Create exporter
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.parameters()['width'] = 1920
            exporter.parameters()['height'] = 1080
            
            # Save screenshot
            exporter.export(filename)
            
            QMessageBox.information(self, "Screenshot", f"Screenshot saved as {filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "Screenshot Error", f"Error saving screenshot: {str(e)}")
            
    def export_data(self):
        """Export waveform data"""
        if not self.waveform_data:
            QMessageBox.warning(self, "No Data", "No waveform data to export")
            return
            
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Waveform Data",
                f"waveform_data_{timestamp}.csv",
                "CSV files (*.csv);;All files (*.*)"
            )
            
            if filename:
                self._export_csv(filename)
                QMessageBox.information(self, "Export", f"Data exported to {filename}")
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Error exporting data: {str(e)}")
            
    def _export_csv(self, filename: str):
        """Export data to CSV format"""
        import csv
        
        # Find maximum length for time alignment
        max_length = max(len(data[0]) for data in self.waveform_data.values())
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            header = ['Time']
            for ch in sorted(self.waveform_data.keys()):
                header.append(f'CH{ch}_Voltage')
            writer.writerow(header)
            
            # Write data
            for i in range(max_length):
                row = []
                
                # Time column (use first channel's time data)
                first_channel = min(self.waveform_data.keys())
                time_data = self.waveform_data[first_channel][0]
                if i < len(time_data):
                    row.append(time_data[i])
                else:
                    row.append('')
                    
                # Voltage columns
                for ch in sorted(self.waveform_data.keys()):
                    voltage_data = self.waveform_data[ch][1]
                    if i < len(voltage_data):
                        row.append(voltage_data[i])
                    else:
                        row.append('')
                        
                writer.writerow(row)
                
    def clear_display(self):
        """Clear waveform display"""
        for plot_item in self.plot_items.values():
            self.plot_widget.removeItem(plot_item)
        self.plot_items.clear()
        self.waveform_data.clear()
        
        # Reset measurements
        for ch in range(1, 5):
            self.measurement_labels[ch].setText(f"CH{ch}: --")
        self.measurements.clear()
        
        # Reset status
        self.samples_label.setText("Samples: 0")
        self.cursor_label.setText("Cursor: --")
        
    def get_measurements(self) -> dict:
        """Get current measurements"""
        return self.measurements.copy()
        
    def set_channel_enabled(self, channel: int, enabled: bool):
        """Set channel enabled state (for external control)"""
        if channel in self.channel_controls:
            self.channel_controls[channel]['enable'].setChecked(enabled)
            
    def is_channel_enabled(self, channel: int) -> bool:
        """Check if channel is enabled"""
        return self.channel_enabled.get(channel, False)
