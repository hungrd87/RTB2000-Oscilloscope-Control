"""
Waveform Display Widget
"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class WaveformWidget(QWidget):
    """Widget for displaying oscilloscope waveforms"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Create subplot
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Voltage (V)')
        self.ax.set_title('Oscilloscope Waveforms')
        self.ax.grid(True, alpha=0.3)
        
        # Channel colors
        self.channel_colors = {
            1: 'yellow',
            2: 'cyan', 
            3: 'magenta',
            4: 'green'
        }
        
        self.waveform_lines = {}
        
    def update_waveforms(self, waveform_data: dict):
        """
        Update waveform display
        
        Args:
            waveform_data: Dictionary with channel numbers as keys,
                          (time_data, voltage_data) tuples as values
        """
        # Clear existing lines
        for line in self.waveform_lines.values():
            line.remove()
        self.waveform_lines.clear()
        
        # Plot new data
        for channel, (time_data, voltage_data) in waveform_data.items():
            color = self.channel_colors.get(channel, 'white')
            line, = self.ax.plot(time_data, voltage_data, 
                               color=color, 
                               label=f'CH{channel}',
                               linewidth=1.5)
            self.waveform_lines[channel] = line
            
        # Update axes
        if waveform_data:
            self.ax.relim()
            self.ax.autoscale()
            self.ax.legend()
            
        self.canvas.draw()
        
    def clear_display(self):
        """Clear waveform display"""
        self.ax.clear()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Voltage (V)')
        self.ax.set_title('Oscilloscope Waveforms')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
