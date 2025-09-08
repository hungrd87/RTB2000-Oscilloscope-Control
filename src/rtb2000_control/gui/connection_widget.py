"""
Connection Widget for VISA Resource Selection
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox)
from PyQt6.QtCore import pyqtSignal
from ..communication.visa_instrument import VisaInstrument


class ConnectionWidget(QWidget):
    """Widget for managing VISA connection"""
    
    # Signals
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.refresh_resources()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # Connection group
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout()
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Resource selection
        conn_layout.addWidget(QLabel("VISA Resource:"))
        
        self.resource_combo = QComboBox()
        self.resource_combo.setMinimumWidth(300)
        conn_layout.addWidget(self.resource_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_resources)
        conn_layout.addWidget(self.refresh_btn)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        
        self.connected = False
        
    def refresh_resources(self):
        """Refresh available VISA resources"""
        self.resource_combo.clear()
        resources = VisaInstrument.list_resources()
        
        # Filter for RTB2000 compatible resources
        filtered_resources = []
        for resource in resources:
            if any(keyword in resource.upper() for keyword in ['USB', 'TCPIP', 'RTB']):
                filtered_resources.append(resource)
                
        self.resource_combo.addItems(filtered_resources)
        
    def toggle_connection(self):
        """Toggle connection state"""
        if self.connected:
            self.disconnect_requested.emit()
        else:
            resource = self.resource_combo.currentText()
            if resource:
                self.connect_requested.emit(resource)
                
    def set_connected(self, connected: bool):
        """Update connection state"""
        self.connected = connected
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        self.resource_combo.setEnabled(not connected)
        self.refresh_btn.setEnabled(not connected)
        
    def get_selected_resource(self) -> str:
        """Get currently selected resource"""
        return self.resource_combo.currentText()
