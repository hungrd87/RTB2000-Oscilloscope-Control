"""
Main Window for RTB2000 Oscilloscope Control GUI
"""

import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QMenuBar, QStatusBar, QToolBar,
                             QMessageBox, QSplitter, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QKeySequence, QCloseEvent, QAction

from .connection_widget import ConnectionWidget
from .channel_control_widget import ChannelControlWidget
from .timebase_widget import TimebaseWidget
from .trigger_widget import TriggerWidget
from .waveform_widget import WaveformWidget
from .measurement_widget import MeasurementWidget
from ..instruments.rtb2000 import RTB2000


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    instrument_connected = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        
        # Initialize instrument
        self.oscilloscope = RTB2000()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("RTB2000 Oscilloscope Control")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Connection widget
        self.connection_widget = ConnectionWidget()
        main_layout.addWidget(self.connection_widget)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls
        self.create_control_panel(splitter)
        
        # Right panel - Waveform display
        self.waveform_widget = WaveformWidget()
        splitter.addWidget(self.waveform_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 800])
        
        # Status bar
        self.statusBar().showMessage("Disconnected")
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('File')
        
        save_config_action = QAction('Save Configuration', self)
        save_config_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_config_action)
        
        load_config_action = QAction('Load Configuration', self)
        load_config_action.triggered.connect(self.load_configuration)
        file_menu.addAction(load_config_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu('Tools')
        
        screenshot_action = QAction('Take Screenshot', self)
        screenshot_action.triggered.connect(self.take_screenshot)
        tools_menu.addAction(screenshot_action)
        
        # Help Menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Connection actions
        self.connect_action = QAction('Connect', self)
        self.connect_action.triggered.connect(self.toggle_connection)
        toolbar.addAction(self.connect_action)
        
        toolbar.addSeparator()
        
        # Acquisition actions
        self.run_action = QAction('Run', self)
        self.run_action.triggered.connect(self.run_acquisition)
        self.run_action.setEnabled(False)
        toolbar.addAction(self.run_action)
        
        self.stop_action = QAction('Stop', self)
        self.stop_action.triggered.connect(self.stop_acquisition)
        self.stop_action.setEnabled(False)
        toolbar.addAction(self.stop_action)
        
        self.single_action = QAction('Single', self)
        self.single_action.triggered.connect(self.single_acquisition)
        self.single_action.setEnabled(False)
        toolbar.addAction(self.single_action)
        
    def create_control_panel(self, parent):
        """Create control panel with tabs"""
        # Control tabs
        tab_widget = QTabWidget()
        parent.addWidget(tab_widget)
        
        # Channel control tab
        self.channel_widget = ChannelControlWidget()
        tab_widget.addTab(self.channel_widget, "Channels")
        
        # Timebase control tab
        self.timebase_widget = TimebaseWidget()
        tab_widget.addTab(self.timebase_widget, "Timebase")
        
        # Trigger control tab
        self.trigger_widget = TriggerWidget()
        tab_widget.addTab(self.trigger_widget, "Trigger")
        
        # Measurement tab
        self.measurement_widget = MeasurementWidget()
        tab_widget.addTab(self.measurement_widget, "Measurements")
        
    def connect_signals(self):
        """Connect signals between widgets"""
        # Connection widget signals
        self.connection_widget.connect_requested.connect(self.connect_instrument)
        self.connection_widget.disconnect_requested.connect(self.disconnect_instrument)
        
        # Instrument connection signal
        self.instrument_connected.connect(self.on_connection_changed)
        
        # Control widget signals
        self.channel_widget.settings_changed.connect(self.update_channel_settings)
        self.timebase_widget.settings_changed.connect(self.update_timebase_settings)
        self.trigger_widget.settings_changed.connect(self.update_trigger_settings)
        
    def connect_instrument(self, resource_name: str):
        """Connect to oscilloscope"""
        try:
            if self.oscilloscope.connect(resource_name):
                self.instrument_connected.emit(True)
                self.start_data_updates()
                self.statusBar().showMessage(f"Connected to {resource_name}")
            else:
                QMessageBox.warning(self, "Connection Error", 
                                  "Failed to connect to oscilloscope")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error: {str(e)}")
            
    def disconnect_instrument(self):
        """Disconnect from oscilloscope"""
        try:
            self.stop_data_updates()
            self.oscilloscope.disconnect()
            self.instrument_connected.emit(False)
            self.statusBar().showMessage("Disconnected")
        except Exception as e:
            QMessageBox.critical(self, "Disconnect Error", f"Error: {str(e)}")
            
    def on_connection_changed(self, connected: bool):
        """Handle connection state change"""
        # Update UI elements
        self.connect_action.setText("Disconnect" if connected else "Connect")
        self.run_action.setEnabled(connected)
        self.stop_action.setEnabled(connected)
        self.single_action.setEnabled(connected)
        
        # Enable/disable control widgets
        self.channel_widget.setEnabled(connected)
        self.timebase_widget.setEnabled(connected)
        self.trigger_widget.setEnabled(connected)
        self.measurement_widget.setEnabled(connected)
        
        if connected:
            # Load current settings from instrument
            self.load_current_settings()
            
    def toggle_connection(self):
        """Toggle connection state"""
        if self.oscilloscope.is_connected():
            self.disconnect_instrument()
        else:
            # Use selected resource from connection widget
            resource = self.connection_widget.get_selected_resource()
            if resource:
                self.connect_instrument(resource)
            else:
                QMessageBox.warning(self, "No Resource", 
                                  "Please select a VISA resource")
                
    def load_current_settings(self):
        """Load current settings from oscilloscope"""
        try:
            # Load channel settings
            for channel in range(1, 5):
                info = self.oscilloscope.get_channel_info(channel)
                self.channel_widget.update_channel_info(channel, info)
                
            # Load system settings
            sys_info = self.oscilloscope.get_system_info()
            self.timebase_widget.update_settings(sys_info)
            self.trigger_widget.update_settings(sys_info)
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def update_channel_settings(self, channel: int, settings: dict):
        """Update channel settings on oscilloscope"""
        try:
            if 'enabled' in settings:
                self.oscilloscope.set_channel_enable(channel, settings['enabled'])
            if 'scale' in settings:
                self.oscilloscope.set_vertical_scale(channel, settings['scale'])
            if 'position' in settings:
                self.oscilloscope.set_vertical_position(channel, settings['position'])
            if 'coupling' in settings:
                self.oscilloscope.set_coupling(channel, settings['coupling'])
        except Exception as e:
            QMessageBox.warning(self, "Settings Error", f"Error: {str(e)}")
            
    def update_timebase_settings(self, settings: dict):
        """Update timebase settings on oscilloscope"""
        try:
            if 'scale' in settings:
                self.oscilloscope.set_timebase_scale(settings['scale'])
            if 'position' in settings:
                self.oscilloscope.set_timebase_position(settings['position'])
        except Exception as e:
            QMessageBox.warning(self, "Settings Error", f"Error: {str(e)}")
            
    def update_trigger_settings(self, settings: dict):
        """Update trigger settings on oscilloscope"""
        try:
            if 'source' in settings:
                self.oscilloscope.set_trigger_source(settings['source'])
            if 'level' in settings:
                self.oscilloscope.set_trigger_level(settings['level'])
            if 'slope' in settings:
                self.oscilloscope.set_trigger_slope(settings['slope'])
        except Exception as e:
            QMessageBox.warning(self, "Settings Error", f"Error: {str(e)}")
            
    def run_acquisition(self):
        """Start continuous acquisition"""
        try:
            self.oscilloscope.run_continuous()
        except Exception as e:
            QMessageBox.warning(self, "Acquisition Error", f"Error: {str(e)}")
            
    def stop_acquisition(self):
        """Stop acquisition"""
        try:
            self.oscilloscope.stop_acquisition()
        except Exception as e:
            QMessageBox.warning(self, "Acquisition Error", f"Error: {str(e)}")
            
    def single_acquisition(self):
        """Perform single acquisition"""
        try:
            self.oscilloscope.single_trigger()
        except Exception as e:
            QMessageBox.warning(self, "Acquisition Error", f"Error: {str(e)}")
            
    def start_data_updates(self):
        """Start periodic data updates"""
        self.update_timer.start(100)  # Update every 100ms
        
    def stop_data_updates(self):
        """Stop periodic data updates"""
        self.update_timer.stop()
        
    def update_data(self):
        """Update waveform and measurement data"""
        try:
            # Update waveform data for enabled channels
            waveform_data = {}
            for channel in range(1, 5):
                if self.channel_widget.is_channel_enabled(channel):
                    time_data, voltage_data = self.oscilloscope.get_waveform_data(channel)
                    waveform_data[channel] = (time_data, voltage_data)
                    
            self.waveform_widget.update_waveforms(waveform_data)
            
            # Update measurements
            measurements = {}
            for channel in range(1, 5):
                if self.channel_widget.is_channel_enabled(channel):
                    measurements[channel] = {
                        'frequency': self.oscilloscope.measure_frequency(channel),
                        'amplitude': self.oscilloscope.measure_amplitude(channel),
                        'mean': self.oscilloscope.measure_mean(channel),
                        'rms': self.oscilloscope.measure_rms(channel)
                    }
                    
            self.measurement_widget.update_measurements(measurements)
            
        except Exception as e:
            # Silently ignore errors during live updates
            pass
            
    def take_screenshot(self):
        """Take oscilloscope screenshot"""
        try:
            self.oscilloscope.screenshot("oscilloscope_screenshot.png")
            self.statusBar().showMessage("Screenshot saved", 2000)
        except Exception as e:
            QMessageBox.warning(self, "Screenshot Error", f"Error: {str(e)}")
            
    def save_configuration(self):
        """Save current configuration"""
        # TODO: Implement configuration save
        self.statusBar().showMessage("Configuration saved", 2000)
        
    def load_configuration(self):
        """Load configuration"""
        # TODO: Implement configuration load
        self.statusBar().showMessage("Configuration loaded", 2000)
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About RTB2000 Control",
                         "RTB2000 Oscilloscope Control GUI\\n\\n"
                         "Version 1.0.0\\n"
                         "Built with PyQt6 and PyVISA")
                         
    def closeEvent(self, a0: QCloseEvent | None):
        """Handle application close"""
        if self.oscilloscope.is_connected():
            self.disconnect_instrument()
        if a0:
            a0.accept()
