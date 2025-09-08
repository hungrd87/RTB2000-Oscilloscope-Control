"""
Measurement Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt


class MeasurementWidget(QWidget):
    """Widget for displaying measurements"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Measurements group
        group = QGroupBox("Automatic Measurements")
        group_layout = QVBoxLayout()
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        # Create measurement table
        self.measurement_table = QTableWidget()
        self.measurement_table.setColumnCount(5)
        self.measurement_table.setHorizontalHeaderLabels([
            "Channel", "Frequency (Hz)", "Amplitude (V)", "Mean (V)", "RMS (V)"
        ])
        self.measurement_table.setRowCount(4)  # 4 channels
        
        # Set channel labels
        for i in range(4):
            item = QTableWidgetItem(f"CH{i+1}")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.measurement_table.setItem(i, 0, item)
            
        group_layout.addWidget(self.measurement_table)
        
    def update_measurements(self, measurements: dict):
        """
        Update measurement display
        
        Args:
            measurements: Dictionary with channel numbers as keys,
                         measurement dictionaries as values
        """
        for channel, data in measurements.items():
            row = channel - 1  # Convert to 0-based index
            
            # Update frequency
            if 'frequency' in data:
                item = QTableWidgetItem(f"{data['frequency']:.2f}")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.measurement_table.setItem(row, 1, item)
                
            # Update amplitude
            if 'amplitude' in data:
                item = QTableWidgetItem(f"{data['amplitude']:.3f}")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.measurement_table.setItem(row, 2, item)
                
            # Update mean
            if 'mean' in data:
                item = QTableWidgetItem(f"{data['mean']:.3f}")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.measurement_table.setItem(row, 3, item)
                
            # Update RMS
            if 'rms' in data:
                item = QTableWidgetItem(f"{data['rms']:.3f}")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.measurement_table.setItem(row, 4, item)
                
    def clear_measurements(self):
        """Clear all measurements"""
        for row in range(4):
            for col in range(1, 5):
                item = QTableWidgetItem("---")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.measurement_table.setItem(row, col, item)
