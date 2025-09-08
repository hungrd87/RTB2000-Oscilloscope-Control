"""
RTB2000 Phase 2 Test Application
Version 2.0 - September 8, 2025

Test application for Phase 2 advanced features:
- PyQtGraph waveform display
- Configuration management
- Data export system
"""

import sys
import os
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QComboBox, QSpinBox,
    QMessageBox, QFileDialog, QProgressBar, QStatusBar
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

# Import our enhanced components
from rtb2000_control.gui.enhanced_waveform_widget import EnhancedWaveformWidget
from rtb2000_control.gui.configuration_widget import ConfigurationWidget
from rtb2000_control.core.config_manager import ConfigurationManager
from rtb2000_control.core.simple_data_exporter import (
    DataExporter, WaveformData, MeasurementData, ExportFormat
)


class Phase2TestWindow(QMainWindow):
    """Test window for Phase 2 features"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.config_manager = ConfigurationManager()
        self.data_exporter = DataExporter()
        
        # Test data
        self.test_channels = [1, 2, 3, 4]
        self.sample_rate = 1e6  # 1 MSa/s
        self.test_frequency = 1000  # 1 kHz
        
        self.setup_ui()
        self.setup_test_data()
        self.setup_timers()
        
        # Apply initial configuration
        self.apply_test_configuration()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("RTB2000 Phase 2 Test Application")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("RTB2000 Phase 2 Advanced Features Test")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Enhanced Waveform Display
        self.waveform_widget = EnhancedWaveformWidget()
        self.tabs.addTab(self.waveform_widget, "Enhanced Waveform Display")
        
        # Configuration Management
        self.config_widget = ConfigurationWidget(self.config_manager)
        self.config_widget.configuration_loaded.connect(self.on_configuration_loaded)
        self.tabs.addTab(self.config_widget, "Configuration Management")
        
        # Data Export Test
        export_test_widget = self.create_export_test_widget()
        self.tabs.addTab(export_test_widget, "Data Export Test")
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Phase 2 Test Application Ready")
        
    def create_control_panel(self) -> QWidget:
        """Create control panel"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Test data controls
        layout.addWidget(QLabel("Test Signal:"))
        
        self.signal_type = QComboBox()
        self.signal_type.addItems([
            "Sine Wave", "Square Wave", "Triangle Wave", 
            "Sawtooth", "Noise", "Chirp", "Multi-tone"
        ])
        self.signal_type.currentTextChanged.connect(self.update_test_signal)
        layout.addWidget(self.signal_type)
        
        layout.addWidget(QLabel("Frequency (Hz):"))
        self.frequency_spin = QSpinBox()
        self.frequency_spin.setRange(10, 100000)
        self.frequency_spin.setValue(1000)
        self.frequency_spin.valueChanged.connect(self.update_test_signal)
        layout.addWidget(self.frequency_spin)
        
        layout.addWidget(QLabel("Channels:"))
        self.active_channels = QComboBox()
        self.active_channels.addItems(["1", "1,2", "1,2,3", "1,2,3,4"])
        self.active_channels.setCurrentText("1,2")
        self.active_channels.currentTextChanged.connect(self.update_active_channels)
        layout.addWidget(self.active_channels)
        
        # Action buttons
        layout.addStretch()
        
        self.start_btn = QPushButton("Start Test")
        self.start_btn.clicked.connect(self.start_test)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Test")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        self.export_btn = QPushButton("Quick Export")
        self.export_btn.clicked.connect(self.quick_export)
        layout.addWidget(self.export_btn)
        
        return panel
        
    def create_export_test_widget(self) -> QWidget:
        """Create data export test widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Data Export System Test")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Export controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Export Format:"))
        self.export_format = QComboBox()
        for fmt in ExportFormat:
            self.export_format.addItem(fmt.value.upper(), fmt)
        controls_layout.addWidget(self.export_format)
        
        self.export_waveforms_btn = QPushButton("Export Waveforms")
        self.export_waveforms_btn.clicked.connect(self.export_waveforms)
        controls_layout.addWidget(self.export_waveforms_btn)
        
        self.export_measurements_btn = QPushButton("Export Measurements")
        self.export_measurements_btn.clicked.connect(self.export_measurements)
        controls_layout.addWidget(self.export_measurements_btn)
        
        self.create_report_btn = QPushButton("Create Session Report")
        self.create_report_btn.clicked.connect(self.create_session_report)
        controls_layout.addWidget(self.create_report_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Export status
        self.export_status = QLabel("Ready for export")
        layout.addWidget(self.export_status)
        
        # Progress bar
        self.export_progress = QProgressBar()
        self.export_progress.setVisible(False)
        layout.addWidget(self.export_progress)
        
        # Test results
        results_label = QLabel("Export Test Results:")
        results_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(results_label)
        
        self.export_results = QLabel("No exports performed yet")
        self.export_results.setStyleSheet("padding: 10px; border: 1px solid gray; background-color: #f0f0f0;")
        self.export_results.setWordWrap(True)
        layout.addWidget(self.export_results)
        
        layout.addStretch()
        return widget
        
    def setup_test_data(self):
        """Setup test data generation"""
        self.time_duration = 0.01  # 10ms
        self.samples_per_channel = int(self.sample_rate * self.time_duration)
        self.time_base = np.linspace(0, self.time_duration, self.samples_per_channel)
        
        # Initialize waveform data storage
        self.current_waveforms = {}
        self.test_measurements = []
        
        self.update_test_signal()
        
    def setup_timers(self):
        """Setup update timers"""
        # Data update timer
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_data)
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 1 second
        
    def update_test_signal(self):
        """Update test signal based on current settings"""
        signal_type = self.signal_type.currentText()
        frequency = self.frequency_spin.value()
        
        # Generate base signal
        t = self.time_base
        omega = 2 * np.pi * frequency
        
        if signal_type == "Sine Wave":
            base_signal = np.sin(omega * t)
        elif signal_type == "Square Wave":
            base_signal = np.sign(np.sin(omega * t))
        elif signal_type == "Triangle Wave":
            base_signal = 2 * np.arcsin(np.sin(omega * t)) / np.pi
        elif signal_type == "Sawtooth":
            base_signal = 2 * (frequency * t - np.floor(frequency * t + 0.5))
        elif signal_type == "Noise":
            base_signal = np.random.normal(0, 0.3, len(t))
        elif signal_type == "Chirp":
            # Frequency sweep from frequency to 2*frequency
            base_signal = np.sin(omega * t + frequency * np.pi * t**2 / self.time_duration)
        elif signal_type == "Multi-tone":
            # Multiple frequencies
            base_signal = (np.sin(omega * t) + 
                          0.5 * np.sin(2 * omega * t) + 
                          0.3 * np.sin(3 * omega * t))
        else:
            base_signal = np.sin(omega * t)
            
        # Generate channel-specific signals
        active_ch_list = [int(ch) for ch in self.active_channels.currentText().split(',')]
        
        for ch in range(1, 5):
            if ch in active_ch_list:
                # Add channel-specific variations
                phase_shift = (ch - 1) * np.pi / 4  # 45° phase shift per channel
                amplitude = 1.0 - 0.1 * (ch - 1)  # Slight amplitude variation
                noise = np.random.normal(0, 0.02, len(t))  # Small noise
                
                signal = amplitude * np.roll(base_signal, int(phase_shift * len(t) / (2 * np.pi))) + noise
                
                # Create waveform data
                self.current_waveforms[ch] = WaveformData(
                    channel=ch,
                    time=t.copy(),
                    voltage=signal,
                    sample_rate=self.sample_rate,
                    scale=amplitude,
                    offset=0.0,
                    label=f"CH{ch} Test Signal",
                    color=["#FFFF00", "#00FFFF", "#FF00FF", "#00FF00"][ch-1]
                )
                
                # Calculate measurements
                rms = np.sqrt(np.mean(signal**2))
                peak_to_peak = np.max(signal) - np.min(signal)
                mean_val = np.mean(signal)
                
                self.test_measurements.extend([
                    MeasurementData(f"RMS_CH{ch}", rms, "V", ch),
                    MeasurementData(f"Vpp_CH{ch}", peak_to_peak, "V", ch),
                    MeasurementData(f"Mean_CH{ch}", mean_val, "V", ch)
                ])
            else:
                # Channel disabled
                if ch in self.current_waveforms:
                    del self.current_waveforms[ch]
                    
    def update_active_channels(self):
        """Update active channels"""
        self.update_test_signal()
        if hasattr(self, 'waveform_widget'):
            # Update waveform display
            waveform_data = {}
            for ch in range(1, 5):
                if ch in self.current_waveforms:
                    waveform_data[ch] = (
                        self.current_waveforms[ch].time,
                        self.current_waveforms[ch].voltage
                    )
            
            self.waveform_widget.update_waveforms(waveform_data)
                    
    def apply_test_configuration(self):
        """Apply test configuration"""
        config = self.config_manager.get_current_config()
        
        # Configure active channels
        active_ch_list = [int(ch) for ch in self.active_channels.currentText().split(',')]
        
        for ch in range(1, 5):
            config.channels[ch].enabled = ch in active_ch_list
            if ch in active_ch_list:
                config.channels[ch].scale = 1.0
                config.channels[ch].position = 0.0
                config.channels[ch].coupling = "DC"
                config.channels[ch].label = f"Test CH{ch}"
                
        # Configure timebase
        config.timebase.scale = self.time_duration / 10  # 10 divisions
        config.timebase.position = 0.0
        
        # Configure display
        config.display.grid_enabled = True
        config.display.max_points = self.samples_per_channel
        config.display.update_rate = 30
        
        self.config_manager.save_current()
        
    def start_test(self):
        """Start test data generation"""
        self.data_timer.start(100)  # 10 Hz update rate
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_bar.showMessage("Test running - generating live data")
        
    def stop_test(self):
        """Stop test data generation"""
        self.data_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("Test stopped")
        
    def update_data(self):
        """Update test data (simulate live acquisition)"""
        # Add some time-varying effects
        time_factor = datetime.now().timestamp() % 10  # 10-second cycle
        
        for ch, waveform in self.current_waveforms.items():
            # Add slow amplitude modulation
            amplitude_mod = 1.0 + 0.1 * np.sin(2 * np.pi * time_factor / 10)
            
            # Add slow frequency drift
            freq_mod = self.frequency_spin.value() * (1 + 0.05 * np.sin(2 * np.pi * time_factor / 8))
            
            # Regenerate signal with modulation
            omega = 2 * np.pi * freq_mod
            t = waveform.time
            
            if self.signal_type.currentText() == "Sine Wave":
                base_signal = amplitude_mod * np.sin(omega * t)
            else:
                # Keep original signal type but apply modulation
                base_signal = amplitude_mod * waveform.voltage / waveform.scale
                
            # Add phase shift and noise
            phase_shift = (ch - 1) * np.pi / 4
            noise = np.random.normal(0, 0.01, len(t))
            
            new_signal = np.roll(base_signal, int(phase_shift * len(t) / (2 * np.pi))) + noise
            
            # Update waveform
            waveform.voltage = new_signal
            waveform.scale = amplitude_mod
            
            # Update display
            waveform_data = {}
            for ch, waveform in self.current_waveforms.items():
                waveform_data[ch] = (waveform.time, waveform.voltage)
                
            self.waveform_widget.update_waveforms(waveform_data)
            
    def update_status(self):
        """Update status information"""
        if hasattr(self, 'config_widget'):
            self.config_widget.update_session_info()
            
    def on_configuration_loaded(self, config):
        """Handle configuration loaded"""
        self.status_bar.showMessage("Configuration applied")
        
    def quick_export(self):
        """Quick export current data"""
        if not self.current_waveforms:
            QMessageBox.warning(self, "Warning", "No waveform data to export")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rtb2000_quick_export_{timestamp}.csv"
        
        waveforms = list(self.current_waveforms.values())
        
        if self.data_exporter.export_waveforms(
            waveforms, filename, ExportFormat.CSV,
            metadata={"source": "Phase 2 Test", "signal_type": self.signal_type.currentText()}
        ):
            self.status_bar.showMessage(f"Quick export saved: {filename}")
        else:
            QMessageBox.warning(self, "Error", "Export failed")
            
    def export_waveforms(self):
        """Export waveforms with user-selected format"""
        if not self.current_waveforms:
            QMessageBox.warning(self, "Warning", "No waveform data to export")
            return
            
        format_obj = self.export_format.currentData()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Waveforms",
            f"rtb2000_waveforms_{timestamp}.{format_obj.value}",
            f"{format_obj.value.upper()} files (*.{format_obj.value})"
        )
        
        if filename:
            self.export_progress.setVisible(True)
            self.export_progress.setValue(25)
            
            waveforms = list(self.current_waveforms.values())
            metadata = {
                "source": "RTB2000 Phase 2 Test",
                "signal_type": self.signal_type.currentText(),
                "frequency": self.frequency_spin.value(),
                "sample_rate": self.sample_rate,
                "export_timestamp": datetime.now().isoformat()
            }
            
            self.export_progress.setValue(50)
            
            success = self.data_exporter.export_waveforms(
                waveforms, filename, format_obj, metadata
            )
            
            self.export_progress.setValue(100)
            
            if success:
                self.export_status.setText(f"Exported waveforms to {filename}")
                self.export_results.setText(
                    f"Last Export: {datetime.now().strftime('%H:%M:%S')}\n"
                    f"Format: {format_obj.value.upper()}\n"
                    f"Channels: {len(waveforms)}\n"
                    f"Samples per channel: {len(waveforms[0].voltage) if waveforms else 0}\n"
                    f"File: {filename}"
                )
            else:
                self.export_status.setText("Export failed")
                QMessageBox.warning(self, "Error", "Waveform export failed")
                
            self.export_progress.setVisible(False)
            
    def export_measurements(self):
        """Export measurement data"""
        if not self.test_measurements:
            QMessageBox.warning(self, "Warning", "No measurement data to export")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Measurements",
            f"rtb2000_measurements_{timestamp}.csv",
            "CSV files (*.csv)"
        )
        
        if filename:
            if self.data_exporter.export_measurements(
                self.test_measurements, filename, ExportFormat.CSV
            ):
                self.export_status.setText(f"Exported measurements to {filename}")
            else:
                QMessageBox.warning(self, "Error", "Measurement export failed")
                
    def create_session_report(self):
        """Create comprehensive session report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, _ = QFileDialog.getSaveFileName(
            self, "Create Session Report",
            f"rtb2000_session_report_{timestamp}.json",
            "JSON files (*.json)"
        )
        
        if filename:
            if self.data_exporter.create_session_report(filename):
                self.export_status.setText(f"Session report created: {filename}")
                
                # Show report summary
                QMessageBox.information(
                    self, "Session Report",
                    f"Session report created successfully!\n\n"
                    f"Waveforms: {len(self.data_exporter.session_data['waveforms'])}\n"
                    f"Measurements: {len(self.data_exporter.session_data['measurements'])}\n"
                    f"Exports: {self.data_exporter.session_data['export_count']}\n"
                    f"File: {filename}"
                )
            else:
                QMessageBox.warning(self, "Error", "Session report creation failed")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("RTB2000 Phase 2 Test")
    app.setApplicationVersion("2.0")
    
    # Create and show main window
    window = Phase2TestWindow()
    window.show()
    
    # Start with some test data
    window.update_test_signal()
    window.update_active_channels()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
