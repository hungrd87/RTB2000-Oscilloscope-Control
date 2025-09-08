"""
Enhanced Connection Widget for VISA Resource Selection
Version 2.0 - September 8, 2025
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QProgressBar,
                             QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
                             QMessageBox)
from PyQt6.QtCore import pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont
from ..communication.enhanced_visa import EnhancedVisaInstrument
import time


class ResourceDiscoveryThread(QThread):
    """Background thread for resource discovery"""
    resources_found = pyqtSignal(list, list)  # resources, errors
    
    def run(self):
        """Run resource discovery in background"""
        resources, errors = EnhancedVisaInstrument.list_resources()
        self.resources_found.emit(resources, errors)


class EnhancedConnectionWidget(QWidget):
    """Enhanced widget for managing VISA connection with better error handling"""
    
    # Signals
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    connection_status_changed = pyqtSignal(bool, str)  # connected, message
    
    def __init__(self):
        super().__init__()
        self.connected = False
        self.current_resource = None
        self.discovery_thread = None
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_resources)
        
        self.init_ui()
        self.refresh_resources()
        
    def init_ui(self):
        """Initialize enhanced user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Main connection group
        conn_group = QGroupBox("Instrument Connection")
        conn_layout = QVBoxLayout()
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Connection controls row
        controls_layout = QHBoxLayout()
        conn_layout.addLayout(controls_layout)
        
        # Resource selection
        controls_layout.addWidget(QLabel("VISA Resource:"))
        
        self.resource_combo = QComboBox()
        self.resource_combo.setMinimumWidth(350)
        self.resource_combo.setToolTip("Select a VISA resource to connect to")
        controls_layout.addWidget(self.resource_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Refresh available VISA resources")
        self.refresh_btn.clicked.connect(self.refresh_resources)
        controls_layout.addWidget(self.refresh_btn)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setToolTip("Connect to selected instrument")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """)
        controls_layout.addWidget(self.connect_btn)
        
        # Auto-refresh checkbox
        self.auto_refresh_cb = QPushButton("Auto-refresh: OFF")
        self.auto_refresh_cb.setCheckable(True)
        self.auto_refresh_cb.toggled.connect(self.toggle_auto_refresh)
        self.auto_refresh_cb.setToolTip("Automatically refresh resources every 5 seconds")
        controls_layout.addWidget(self.auto_refresh_cb)
        
        # Progress bar for discovery
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        conn_layout.addWidget(self.progress_bar)
        
        # Status and details tabs
        details_tabs = QTabWidget()
        conn_layout.addWidget(details_tabs)
        
        # Status tab
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        
        # Connection status
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_layout.addLayout(status_row)
        
        # Connection info
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setPlainText("No connection information available")
        self.info_text.setReadOnly(True)
        status_layout.addWidget(QLabel("Connection Details:"))
        status_layout.addWidget(self.info_text)
        
        details_tabs.addTab(status_widget, "Status")
        
        # Resources tab
        resources_widget = QWidget()
        resources_layout = QVBoxLayout(resources_widget)
        
        # Resources table
        self.resources_table = QTableWidget()
        self.resources_table.setColumnCount(2)
        self.resources_table.setHorizontalHeaderLabels(["Resource", "Type"])
        self.resources_table.setAlternatingRowColors(True)
        self.resources_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.resources_table.itemDoubleClicked.connect(self.on_resource_double_click)
        resources_layout.addWidget(self.resources_table)
        
        # Error messages
        self.error_text = QTextEdit()
        self.error_text.setMaximumHeight(60)
        self.error_text.setReadOnly(True)
        self.error_text.setVisible(False)
        resources_layout.addWidget(QLabel("Discovery Messages:"))
        resources_layout.addWidget(self.error_text)
        
        details_tabs.addTab(resources_widget, "Available Resources")
        
    def refresh_resources(self):
        """Refresh available VISA resources in background"""
        if self.discovery_thread and self.discovery_thread.isRunning():
            return  # Already discovering
            
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start discovery in background thread
        self.discovery_thread = ResourceDiscoveryThread()
        self.discovery_thread.resources_found.connect(self.on_resources_discovered)
        self.discovery_thread.finished.connect(self.on_discovery_finished)
        self.discovery_thread.start()
        
    @pyqtSlot(list, list)
    def on_resources_discovered(self, resources, errors):
        """Handle discovered resources"""
        # Update combo box
        current_selection = self.resource_combo.currentText()
        self.resource_combo.clear()
        
        # Filter for RTB2000 compatible resources
        filtered_resources = []
        for resource in resources:
            if any(keyword in resource.upper() for keyword in ['USB', 'TCPIP', 'RTB', 'ASRL']):
                filtered_resources.append(resource)
                
        self.resource_combo.addItems(filtered_resources)
        
        # Restore selection if possible
        index = self.resource_combo.findText(current_selection)
        if index >= 0:
            self.resource_combo.setCurrentIndex(index)
            
        # Update resources table
        self.update_resources_table(filtered_resources)
        
        # Update error messages
        if errors:
            self.error_text.setPlainText('\\n'.join(errors))
            self.error_text.setVisible(True)
        else:
            self.error_text.setVisible(False)
            
    def on_discovery_finished(self):
        """Handle discovery completion"""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        
    def update_resources_table(self, resources):
        """Update the resources table"""
        self.resources_table.setRowCount(len(resources))
        
        for row, resource in enumerate(resources):
            # Resource name
            self.resources_table.setItem(row, 0, QTableWidgetItem(resource))
            
            # Resource type detection
            resource_type = "Unknown"
            if "USB" in resource:
                resource_type = "USB"
            elif "TCPIP" in resource:
                resource_type = "Ethernet"
            elif "ASRL" in resource:
                resource_type = "Serial"
            elif "GPIB" in resource:
                resource_type = "GPIB"
                
            self.resources_table.setItem(row, 1, QTableWidgetItem(resource_type))
            
        self.resources_table.resizeColumnsToContents()
        
    def on_resource_double_click(self, item):
        """Handle double-click on resource table"""
        if item.column() == 0:  # Resource name column
            resource_name = item.text()
            index = self.resource_combo.findText(resource_name)
            if index >= 0:
                self.resource_combo.setCurrentIndex(index)
                
    def toggle_auto_refresh(self, enabled):
        """Toggle auto-refresh functionality"""
        if enabled:
            self.auto_refresh_timer.start(5000)  # 5 seconds
            self.auto_refresh_cb.setText("Auto-refresh: ON")
            self.auto_refresh_cb.setStyleSheet("background-color: #4CAF50; color: white;")
        else:
            self.auto_refresh_timer.stop()
            self.auto_refresh_cb.setText("Auto-refresh: OFF")
            self.auto_refresh_cb.setStyleSheet("")
            
    def toggle_connection(self):
        """Toggle connection state with enhanced error handling"""
        if self.connected:
            self.disconnect_requested.emit()
        else:
            resource = self.resource_combo.currentText()
            if resource:
                self.connect_requested.emit(resource)
            else:
                QMessageBox.warning(self, "No Resource Selected", 
                                  "Please select a VISA resource from the dropdown menu")
                
    def set_connected(self, connected: bool, message: str = ""):
        """Update connection state with enhanced feedback"""
        self.connected = connected
        
        if connected:
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet(\"\"\"
                QPushButton { 
                    background-color: #f44336; 
                    color: white; 
                    font-weight: bold;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover { background-color: #d32f2f; }
                QPushButton:pressed { background-color: #b71c1c; }
            \"\"\")
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.current_resource = self.resource_combo.currentText()
            
            # Update connection info
            info_text = f"Connected to: {self.current_resource}\\n"
            if message:
                info_text += f"Details: {message}\\n"
            info_text += f"Connection time: {time.strftime('%H:%M:%S')}"
            self.info_text.setPlainText(info_text)
            
        else:
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet(\"\"\"
                QPushButton { 
                    background-color: #4CAF50; 
                    color: white; 
                    font-weight: bold;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover { background-color: #45a049; }
                QPushButton:pressed { background-color: #3d8b40; }
            \"\"\")
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.current_resource = None
            
            # Update connection info
            info_text = "No active connection\\n"
            if message:
                info_text += f"Last message: {message}\\n"
            info_text += f"Disconnected at: {time.strftime('%H:%M:%S')}"
            self.info_text.setPlainText(info_text)
            
        # Enable/disable controls
        self.resource_combo.setEnabled(not connected)
        self.refresh_btn.setEnabled(not connected)
        
        # Emit status change signal
        self.connection_status_changed.emit(connected, message)
        
    def get_selected_resource(self) -> str:
        """Get currently selected resource"""
        return self.resource_combo.currentText()
        
    def get_connection_status(self) -> dict:
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'resource': self.current_resource,
            'available_resources': [self.resource_combo.itemText(i) 
                                  for i in range(self.resource_combo.count())],
            'auto_refresh': self.auto_refresh_timer.isActive()
        }


# Maintain backward compatibility
class ConnectionWidget(EnhancedConnectionWidget):
    """Backward compatibility wrapper"""
    pass
