"""
Main Window for RTB2000 Oscilloscope Control GUI
"""

import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QMenuBar, QStatusBar, QToolBar,
                             QMessageBox, QSplitter, QFileDialog, QComboBox,
                             QPushButton, QLabel, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QIcon, QKeySequence, QCloseEvent, QAction

from .connection_widget import ConnectionWidget
from .channel_control_widget import ChannelControlWidget
from .timebase_widget import TimebaseWidget
from .trigger_widget import TriggerWidget
from .waveform_widget import WaveformWidget
from .measurement_widget import MeasurementWidget
from ..instruments.rtb2000 import RTB2000
from ..core.config_manager import ConfigurationManager, RTB2000Configuration
from ..core.performance import PerformanceOptimizer, PerformanceMetrics
from .themes import get_theme_stylesheet, apply_theme_to_application
from .icons import IconManager


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    instrument_connected = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration manager
        self.config_manager = ConfigurationManager()
        
        # Initialize performance optimizer
        self.performance_optimizer = PerformanceOptimizer()
        self.setup_performance_monitoring()
        
        # Initialize instrument
        self.oscilloscope = RTB2000()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        
        # Theme management
        self.current_theme = "dark"
        
        # Animation setup
        self.setup_animations()
        
        self.init_ui()
        self.connect_signals()
        
        # Apply professional styling
        self.apply_professional_styling()
        
        # Load last configuration
        self.load_current_configuration()
        
        # Setup auto-save
        self.setup_auto_save()
        
        # Start performance optimization
        self.performance_optimizer.start_optimization()
        
    def setup_animations(self):
        """Setup UI animations"""
        self.status_animation = QPropertyAnimation(self, b"geometry")
        self.status_animation.setDuration(300)
        self.status_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def setup_performance_monitoring(self):
        """Setup performance monitoring and optimization"""
        # Connect performance signals
        self.performance_optimizer.optimization_performed.connect(self.on_optimization_performed)
        self.performance_optimizer.fps_limit_changed.connect(self.on_fps_limit_changed)
        self.performance_optimizer.monitor.performance_warning.connect(self.on_performance_warning)
        self.performance_optimizer.monitor.metrics_updated.connect(self.on_performance_metrics_updated)
        
        # Performance status tracking
        self.last_performance_metrics = None
        self.performance_warnings_count = 0
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("RTB2000 Oscilloscope Control - Professional Edition")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Set application icon
        self.setWindowIcon(IconManager.get_icon("settings", 32))
        
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
        save_config_action.setShortcut(QKeySequence.StandardKey.Save)
        save_config_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_config_action)
        
        load_config_action = QAction('Load Configuration', self)
        load_config_action.setShortcut(QKeySequence.StandardKey.Open)
        load_config_action.triggered.connect(self.load_configuration)
        file_menu.addAction(load_config_action)
        
        file_menu.addSeparator()
        
        # Preset management submenu
        preset_menu = file_menu.addMenu('Presets')
        
        save_preset_menu_action = QAction('Save Current as Preset...', self)
        save_preset_menu_action.setShortcut(QKeySequence('Ctrl+Shift+P'))
        save_preset_menu_action.triggered.connect(self.save_current_as_preset)
        preset_menu.addAction(save_preset_menu_action)
        
        load_preset_menu_action = QAction('Load Preset...', self)
        load_preset_menu_action.triggered.connect(self.show_preset_dialog)
        preset_menu.addAction(load_preset_menu_action)
        
        preset_menu.addSeparator()
        
        export_presets_action = QAction('Export All Presets...', self)
        export_presets_action.triggered.connect(self.export_all_presets)
        preset_menu.addAction(export_presets_action)
        
        import_presets_action = QAction('Import Presets...', self)
        import_presets_action.triggered.connect(self.import_presets)
        preset_menu.addAction(import_presets_action)
        
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu('Export')
        
        export_data_action = QAction('Export Waveform Data...', self)
        export_data_action.setShortcut(QKeySequence('Ctrl+E'))
        export_data_action.triggered.connect(self.export_waveform_data)
        export_menu.addAction(export_data_action)
        
        screenshot_action = QAction('Take Screenshot...', self)
        screenshot_action.setShortcut(QKeySequence('Ctrl+Shift+S'))
        screenshot_action.triggered.connect(self.take_screenshot)
        export_menu.addAction(screenshot_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu('View')
        
        auto_scale_action = QAction('Auto Scale', self)
        auto_scale_action.setShortcut(QKeySequence('Ctrl+A'))
        auto_scale_action.triggered.connect(self.auto_scale_waveform)
        view_menu.addAction(auto_scale_action)
        
        toggle_grid_action = QAction('Toggle Grid', self)
        toggle_grid_action.setShortcut(QKeySequence('Ctrl+G'))
        toggle_grid_action.setCheckable(True)
        toggle_grid_action.setChecked(True)
        toggle_grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(toggle_grid_action)
        self.toggle_grid_action = toggle_grid_action
        
        toggle_crosshair_action = QAction('Toggle Crosshair', self)
        toggle_crosshair_action.setShortcut(QKeySequence('Ctrl+H'))
        toggle_crosshair_action.setCheckable(True)
        toggle_crosshair_action.triggered.connect(self.toggle_crosshair)
        view_menu.addAction(toggle_crosshair_action)
        self.toggle_crosshair_action = toggle_crosshair_action
        
        # Tools Menu
        tools_menu = menubar.addMenu('Tools')
        
        clear_display_action = QAction('Clear Display', self)
        clear_display_action.setShortcut(QKeySequence('Ctrl+L'))
        clear_display_action.triggered.connect(self.clear_waveform_display)
        tools_menu.addAction(clear_display_action)
        
        # Performance Menu
        performance_menu = menubar.addMenu('Performance')
        
        monitor_action = QAction('Performance Monitor...', self)
        monitor_action.setShortcut(QKeySequence('Ctrl+Shift+P'))
        monitor_action.triggered.connect(self.show_performance_dialog)
        performance_menu.addAction(monitor_action)
        
        performance_menu.addSeparator()
        
        optimize_action = QAction('Optimize Now', self)
        optimize_action.triggered.connect(lambda: self.performance_optimizer.optimize_performance())
        performance_menu.addAction(optimize_action)
        
        cleanup_action = QAction('Memory Cleanup', self)
        cleanup_action.triggered.connect(lambda: self.performance_optimizer.memory_optimizer.force_cleanup())
        performance_menu.addAction(cleanup_action)
        
        performance_menu.addSeparator()
        
        auto_optimize_action = QAction('Auto-Optimization', self)
        auto_optimize_action.setCheckable(True)
        auto_optimize_action.setChecked(True)
        auto_optimize_action.triggered.connect(self.toggle_auto_optimization)
        performance_menu.addAction(auto_optimize_action)
        self.auto_optimize_action = auto_optimize_action
        
        # Help Menu
        help_menu = menubar.addMenu('Help')
        
        keyboard_shortcuts_action = QAction('Keyboard Shortcuts', self)
        keyboard_shortcuts_action.triggered.connect(self.show_keyboard_shortcuts)
        help_menu.addAction(keyboard_shortcuts_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar()
        toolbar.setObjectName("MainToolBar")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        # Connection actions with professional icons
        self.connect_action = QAction(IconManager.get_icon("connect"), 'Connect', self)
        self.connect_action.triggered.connect(self.toggle_connection)
        self.connect_action.setToolTip("Connect to RTB2000 instrument")
        toolbar.addAction(self.connect_action)
        
        toolbar.addSeparator()
        
        # Acquisition actions with professional icons
        self.run_action = QAction(IconManager.get_icon("run"), 'Run', self)
        self.run_action.setShortcut(QKeySequence('F5'))
        self.run_action.triggered.connect(self.run_acquisition)
        self.run_action.setEnabled(False)
        self.run_action.setToolTip("Start continuous acquisition (F5)")
        toolbar.addAction(self.run_action)
        
        self.stop_action = QAction(IconManager.get_icon("stop"), 'Stop', self)
        self.stop_action.setShortcut(QKeySequence('F5'))  # Same key toggles
        self.stop_action.triggered.connect(self.stop_acquisition)
        self.stop_action.setEnabled(False)
        self.stop_action.setToolTip("Stop acquisition (F5)")
        toolbar.addAction(self.stop_action)
        
        self.single_action = QAction(IconManager.get_icon("single"), 'Single', self)
        self.single_action.setShortcut(QKeySequence('F6'))
        self.single_action.triggered.connect(self.single_acquisition)
        self.single_action.setEnabled(False)
        self.single_action.setToolTip("Single shot acquisition (F6)")
        toolbar.addAction(self.single_action)
        
        toolbar.addSeparator()
        
        # View actions with professional icons
        auto_scale_toolbar_action = QAction(IconManager.get_icon("auto_scale"), 'Auto Scale', self)
        auto_scale_toolbar_action.triggered.connect(self.auto_scale_waveform)
        auto_scale_toolbar_action.setShortcut(QKeySequence('Ctrl+A'))
        auto_scale_toolbar_action.setToolTip("Auto scale all channels (Ctrl+A)")
        toolbar.addAction(auto_scale_toolbar_action)
        
        clear_display_toolbar_action = QAction(IconManager.get_icon("clear"), 'Clear', self)
        clear_display_toolbar_action.triggered.connect(self.clear_waveform_display)
        clear_display_toolbar_action.setShortcut(QKeySequence('Ctrl+L'))
        clear_display_toolbar_action.setToolTip("Clear waveform display (Ctrl+L)")
        toolbar.addAction(clear_display_toolbar_action)
        
        toolbar.addSeparator()
        
        # Configuration management controls
        self.add_preset_controls(toolbar)
        
    def add_preset_controls(self, toolbar):
        """Add preset management controls to toolbar"""
        # Preset label with enhanced styling
        preset_label = QLabel("Preset:")
        preset_label.setProperty("class", "preset-label")
        preset_label.setToolTip("Configuration presets")
        toolbar.addWidget(preset_label)
        
        # Preset selection combo box with enhanced styling
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(180)
        self.preset_combo.setMaximumWidth(250)
        self.preset_combo.setToolTip("Select preset configuration")
        self.preset_combo.currentTextChanged.connect(self.load_selected_preset)
        toolbar.addWidget(self.preset_combo)
        
        # Save preset button with icon
        self.save_preset_action = QAction(IconManager.get_icon("save"), 'Save Preset', self)
        self.save_preset_action.setShortcut(QKeySequence('Ctrl+Shift+P'))
        self.save_preset_action.triggered.connect(self.save_current_as_preset)
        self.save_preset_action.setToolTip("Save current configuration as preset (Ctrl+Shift+P)")
        toolbar.addAction(self.save_preset_action)
        
        # Delete preset button with icon
        self.delete_preset_action = QAction(IconManager.get_icon("delete"), 'Delete', self)
        self.delete_preset_action.triggered.connect(self.delete_current_preset)
        self.delete_preset_action.setToolTip("Delete selected preset")
        toolbar.addAction(self.delete_preset_action)
        
        # Refresh presets button with icon
        self.refresh_presets_action = QAction(IconManager.get_icon("refresh"), 'Refresh', self)
        self.refresh_presets_action.triggered.connect(self.refresh_preset_list)
        self.refresh_presets_action.setToolTip("Refresh preset list")
        toolbar.addAction(self.refresh_presets_action)
        
        toolbar.addSeparator()
        
        # Theme selector
        theme_label = QLabel("Theme:")
        theme_label.setProperty("class", "preset-label")
        toolbar.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "High Contrast"])
        self.theme_combo.setCurrentText("Dark")
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        self.theme_combo.setToolTip("Change application theme")
        toolbar.addWidget(self.theme_combo)
        
        # Initialize preset list
        self.refresh_preset_list()
        
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
        
        # Analysis tab
        self.analysis_widget = self.create_analysis_widget()
        tab_widget.addTab(self.analysis_widget, "Analysis")
        
    def create_analysis_widget(self):
        """Create comprehensive analysis widget"""
        from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout
        
        analysis_tab_widget = QTabWidget()
        
        try:
            # FFT Analysis tab
            from ..analysis.fft_analysis import FFTAnalyzer, FFTWidget
            self.fft_analyzer = FFTAnalyzer()
            fft_widget = FFTWidget(self.fft_analyzer)
            analysis_tab_widget.addTab(fft_widget, "FFT")
            
            # Statistics tab
            from ..analysis.statistics import StatisticalAnalyzer, StatisticsWidget
            self.statistical_analyzer = StatisticalAnalyzer()
            statistics_widget = StatisticsWidget(self.statistical_analyzer)
            analysis_tab_widget.addTab(statistics_widget, "Statistics")
            
            # Measurements tab
            from ..analysis.measurements import MeasurementEngine, MeasurementWidget
            self.measurement_engine = MeasurementEngine()
            measurement_analysis_widget = MeasurementWidget(self.measurement_engine)
            analysis_tab_widget.addTab(measurement_analysis_widget, "Auto Measurements")
            
            # Data Export tab
            from ..analysis.data_export import DataExporter, ExportWidget
            self.data_exporter = DataExporter()
            export_widget = ExportWidget(self.data_exporter)
            analysis_tab_widget.addTab(export_widget, "Export")
            
            # Connect analysis systems to data updates
            self.setup_analysis_connections()
            
        except ImportError as e:
            # Fallback if analysis modules not available
            fallback_widget = QWidget()
            layout = QVBoxLayout(fallback_widget)
            from PyQt6.QtWidgets import QLabel
            layout.addWidget(QLabel(f"Analysis features not available: {e}"))
            analysis_tab_widget.addTab(fallback_widget, "Analysis Unavailable")
        
        return analysis_tab_widget
    
    def setup_analysis_connections(self):
        """Setup connections for analysis systems"""
        try:
            # Connect waveform data updates to analysis systems
            if hasattr(self, 'waveform_widget'):
                # This would connect when waveform data is updated
                # self.waveform_widget.data_updated.connect(self.update_analysis_data)
                pass
            
            # Setup auto-measurements on data updates
            if hasattr(self, 'measurement_engine'):
                # Enable some default auto-measurements
                default_measurements = ['DC Average', 'RMS', 'Peak-Peak', 'Frequency']
                self.measurement_engine.set_auto_measurements(default_measurements)
                
        except Exception as e:
            print(f"Error setting up analysis connections: {e}")
    
    def update_analysis_data(self, channel_data: dict):
        """Update analysis systems with new data"""
        try:
            for channel, data in channel_data.items():
                if 'time' in data and 'voltage' in data:
                    time_data = data['time']
                    voltage_data = data['voltage']
                    sample_rate = data.get('sample_rate', 1e6)
                    
                    # Update FFT analyzer
                    if hasattr(self, 'fft_analyzer'):
                        self.fft_analyzer.compute_fft(voltage_data, sample_rate)
                    
                    # Update statistical analyzer
                    if hasattr(self, 'statistical_analyzer'):
                        self.statistical_analyzer.compute_basic_statistics(voltage_data)
                        self.statistical_analyzer.compute_histogram(voltage_data)
                    
                    # Update measurement engine
                    if hasattr(self, 'measurement_engine'):
                        self.measurement_engine.update_data(channel, voltage_data)
                    
                    # Update data exporter
                    if hasattr(self, 'data_exporter'):
                        self.data_exporter.set_waveform_data(
                            channel, time_data, voltage_data, sample_rate
                        )
                        
        except Exception as e:
            print(f"Error updating analysis data: {e}")
        
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
        
        # Enhanced waveform widget signals
        self.waveform_widget.measurement_updated.connect(self.on_waveform_measurements)
        self.waveform_widget.cursor_moved.connect(self.on_cursor_moved)
        
    def on_waveform_measurements(self, measurements: dict):
        """Handle measurement updates from waveform widget"""
        # Update measurement widget with new measurements
        self.measurement_widget.update_measurements(measurements)
        
        # Update status bar with key measurements
        if measurements:
            status_text = "Measurements: "
            for ch, data in measurements.items():
                if 'vpp' in data:
                    status_text += f"CH{ch}:{data['vpp']:.2f}Vpp "
            self.statusBar().showMessage(status_text)
            
    def on_cursor_moved(self, x: float, y: float):
        """Handle cursor movement from waveform widget"""
        # Update status bar with cursor position
        cursor_text = f"Cursor: {x*1000:.3f}ms, {y:.3f}V"
        # Could also update a dedicated cursor display widget
        
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
            # Use enhanced waveform widget's screenshot capability
            self.waveform_widget.take_screenshot()
        except Exception as e:
            QMessageBox.warning(self, "Screenshot Error", f"Error: {str(e)}")
            
    def export_waveform_data(self):
        """Export waveform data using enhanced widget"""
        try:
            self.waveform_widget.export_data()
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Error: {str(e)}")
            
    def auto_scale_waveform(self):
        """Auto-scale waveform display"""
        self.waveform_widget.auto_scale()
        
    def toggle_grid(self, checked: bool):
        """Toggle grid display"""
        self.waveform_widget.toggle_grid(checked)
        
    def toggle_crosshair(self, checked: bool):
        """Toggle crosshair display"""
        self.waveform_widget.toggle_crosshair(checked)
        
    def clear_waveform_display(self):
        """Clear waveform display"""
        self.waveform_widget.clear_display()
        
    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts_text = """
Keyboard Shortcuts:

File Operations:
Ctrl+S - Save Configuration
Ctrl+O - Load Configuration
Ctrl+E - Export Waveform Data
Ctrl+Shift+S - Take Screenshot
Ctrl+Shift+P - Save Current as Preset
Ctrl+Q - Exit

View Operations:
Ctrl+A - Auto Scale
Ctrl+G - Toggle Grid
Ctrl+H - Toggle Crosshair
Ctrl+L - Clear Display

Acquisition:
F5 - Run/Stop
F6 - Single Trigger

Configuration:
• Auto-save every 30 seconds
• Session restore on startup
• Preset management via toolbar
"""
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)
            
    def save_configuration(self):
        """Save current configuration"""
        try:
            # Update configuration from current UI state
            self.update_configuration_from_ui()
            
            # Save current configuration
            if self.config_manager.save_current():
                self.statusBar().showMessage("Configuration saved successfully", 2000)
            else:
                QMessageBox.warning(self, "Error", "Failed to save configuration")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
        
    def load_configuration(self):
        """Load configuration"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", 
            "", "JSON files (*.json);;All files (*.*)"
        )
        
        if filename:
            try:
                if self.config_manager.import_configuration(filename):
                    self.apply_configuration_to_ui()
                    self.statusBar().showMessage(f"Configuration loaded from {filename}", 2000)
                else:
                    QMessageBox.warning(self, "Error", "Failed to load configuration")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration: {str(e)}")
    
    def load_current_configuration(self):
        """Load current configuration on startup"""
        try:
            self.config_manager.load_current()
            self.apply_configuration_to_ui()
        except Exception as e:
            print(f"Failed to load current configuration: {e}")
            
    def update_configuration_from_ui(self):
        """Update configuration manager from current UI state"""
        try:
            # Update display configuration from waveform widget
            self.config_manager.update_display_config(
                grid_enabled=self.waveform_widget.grid_enabled,
                crosshair_enabled=self.waveform_widget.crosshair_enabled,
                theme="dark"  # Default theme
            )
            
            # TODO: Update other configurations from UI widgets
            # self.config_manager.update_channel_config(...)
            # self.config_manager.update_timebase_config(...)
            
        except Exception as e:
            print(f"Error updating configuration from UI: {e}")
            
    def apply_configuration_to_ui(self):
        """Apply configuration to UI widgets"""
        try:
            config = self.config_manager.get_current_config()
            
            # Apply display configuration to waveform widget
            if hasattr(self.waveform_widget, 'set_grid_enabled'):
                self.waveform_widget.set_grid_enabled(config.display.grid_enabled)
            if hasattr(self.waveform_widget, 'set_crosshair_enabled'):
                self.waveform_widget.set_crosshair_enabled(config.display.crosshair_enabled)
                
            # TODO: Apply other configurations to UI widgets
            # Apply channel configs to channel_widget
            # Apply timebase configs to timebase_widget
            
        except Exception as e:
            print(f"Error applying configuration to UI: {e}")
    
    # Preset Management Methods
    def refresh_preset_list(self):
        """Refresh the preset combo box"""
        try:
            current_text = self.preset_combo.currentText()
            self.preset_combo.clear()
            
            # Add default option
            self.preset_combo.addItem("-- Select Preset --")
            
            # Add saved presets
            presets = self.config_manager.list_presets()
            for preset in presets:
                self.preset_combo.addItem(preset['name'])
                
            # Restore selection if possible
            if current_text:
                index = self.preset_combo.findText(current_text)
                if index >= 0:
                    self.preset_combo.setCurrentIndex(index)
                    
        except Exception as e:
            print(f"Error refreshing preset list: {e}")
            
    def load_selected_preset(self, preset_name):
        """Load selected preset"""
        if not preset_name or preset_name == "-- Select Preset --":
            return
            
        try:
            if self.config_manager.load_preset(preset_name):
                self.apply_configuration_to_ui()
                self.statusBar().showMessage(f"Loaded preset: {preset_name}", 2000)
            else:
                QMessageBox.warning(self, "Error", f"Failed to load preset: {preset_name}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preset: {str(e)}")
            
    def save_current_as_preset(self):
        """Save current configuration as new preset"""
        try:
            # Get preset name from user
            preset_name, ok = QInputDialog.getText(
                self, "Save Preset", 
                "Enter preset name:",
                text="New Preset"
            )
            
            if ok and preset_name.strip():
                preset_name = preset_name.strip()
                
                # Get optional description
                description, ok2 = QInputDialog.getText(
                    self, "Save Preset", 
                    "Enter description (optional):",
                    text=""
                )
                
                if ok2:
                    # Update configuration from UI
                    self.update_configuration_from_ui()
                    
                    # Save preset
                    if self.config_manager.save_preset(preset_name, description.strip()):
                        self.refresh_preset_list()
                        
                        # Select the new preset
                        index = self.preset_combo.findText(preset_name)
                        if index >= 0:
                            self.preset_combo.setCurrentIndex(index)
                            
                        self.statusBar().showMessage(f"Saved preset: {preset_name}", 2000)
                    else:
                        QMessageBox.warning(self, "Error", f"Failed to save preset: {preset_name}")
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preset: {str(e)}")
            
    def delete_current_preset(self):
        """Delete currently selected preset"""
        current_preset = self.preset_combo.currentText()
        
        if not current_preset or current_preset == "-- Select Preset --":
            QMessageBox.information(self, "Information", "Please select a preset to delete")
            return
            
        try:
            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete preset '{current_preset}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.config_manager.delete_preset(current_preset):
                    self.refresh_preset_list()
                    self.statusBar().showMessage(f"Deleted preset: {current_preset}", 2000)
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete preset: {current_preset}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete preset: {str(e)}")
            
    def show_preset_dialog(self):
        """Show preset selection dialog"""
        try:
            presets = self.config_manager.list_presets()
            
            if not presets:
                QMessageBox.information(self, "Information", "No presets available")
                return
                
            preset_names = [preset['name'] for preset in presets]
            
            preset_name, ok = QInputDialog.getItem(
                self, "Load Preset", 
                "Select preset to load:",
                preset_names, 0, False
            )
            
            if ok and preset_name:
                self.load_selected_preset(preset_name)
                
                # Update combo box selection
                index = self.preset_combo.findText(preset_name)
                if index >= 0:
                    self.preset_combo.setCurrentIndex(index)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show preset dialog: {str(e)}")
            
    def export_all_presets(self):
        """Export all presets to file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export All Presets",
                f"rtb2000_presets_{self.config_manager.current_config.created[:10]}.json",
                "JSON files (*.json);;All files (*.*)"
            )
            
            if filename:
                if self.config_manager.export_configuration(filename, include_presets=True):
                    self.statusBar().showMessage(f"Exported all presets to {filename}", 3000)
                    QMessageBox.information(self, "Success", f"All presets exported to:\n{filename}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to export presets")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export presets: {str(e)}")
            
    def import_presets(self):
        """Import presets from file"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Import Presets",
                "", "JSON files (*.json);;All files (*.*)"
            )
            
            if filename:
                if self.config_manager.import_configuration(filename, import_presets=True):
                    self.refresh_preset_list()
                    self.statusBar().showMessage(f"Imported presets from {filename}", 3000)
                    QMessageBox.information(self, "Success", f"Presets imported from:\n{filename}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to import presets")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import presets: {str(e)}")
            
    def apply_professional_styling(self):
        """Apply professional styling to the application"""
        # Apply theme stylesheet
        stylesheet = get_theme_stylesheet(self.current_theme)
        self.setStyleSheet(stylesheet)
        
        # Set professional window properties
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | 
                           Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)
        
        # Configure status bar
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #2d2d30;
                color: #cccccc;
                border-top: 1px solid #3e3e42;
                padding: 4px;
            }
        """)
        
        # Add professional status indicators
        self.add_status_indicators()
        
    def add_status_indicators(self):
        """Add professional status indicators to status bar"""
        # Connection status indicator
        self.connection_status_label = QLabel()
        self.connection_status_label.setProperty("class", "status-label")
        self.update_connection_status(False)
        self.statusBar().addPermanentWidget(self.connection_status_label)
        
        # Performance status indicator
        self.performance_status_label = QLabel("Performance: Good")
        self.performance_status_label.setProperty("class", "status-label")
        self.performance_status_label.setToolTip("Real-time performance monitoring")
        self.statusBar().addPermanentWidget(self.performance_status_label)
        
        # Memory usage indicator
        self.memory_status_label = QLabel("Memory: 0 MB")
        self.memory_status_label.setProperty("class", "status-label")
        self.memory_status_label.setToolTip("Current memory usage")
        self.statusBar().addPermanentWidget(self.memory_status_label)
        
        # FPS indicator
        self.fps_status_label = QLabel("FPS: 0")
        self.fps_status_label.setProperty("class", "status-label")
        self.fps_status_label.setToolTip("Current frames per second")
        self.statusBar().addPermanentWidget(self.fps_status_label)
        
        # Theme indicator
        theme_status = QLabel(f"Theme: {self.current_theme.title()}")
        theme_status.setProperty("class", "status-label")
        self.statusBar().addPermanentWidget(theme_status)
        
        # Version indicator
        version_label = QLabel("v2.0 Professional")
        version_label.setProperty("class", "status-label")
        self.statusBar().addPermanentWidget(version_label)
        
    def update_connection_status(self, connected):
        """Update connection status indicator with animation"""
        if connected:
            self.connection_status_label.setText("🟢 Connected")
            self.connection_status_label.setToolTip("RTB2000 instrument connected")
            self.connect_action.setIcon(IconManager.get_icon("disconnect"))
            self.connect_action.setText("Disconnect")
        else:
            self.connection_status_label.setText("🔴 Disconnected")
            self.connection_status_label.setToolTip("RTB2000 instrument disconnected")
            self.connect_action.setIcon(IconManager.get_icon("connect"))
            self.connect_action.setText("Connect")
            
        # Animate status change
        self.animate_status_change()
        
    def animate_status_change(self):
        """Animate status bar changes"""
        # Simple fade effect for status updates
        current_geometry = self.statusBar().geometry()
        self.status_animation.setStartValue(current_geometry)
        self.status_animation.setEndValue(current_geometry)
        self.status_animation.start()
    
    def update_performance_status(self, metrics):
        """Update performance status indicators"""
        # Update performance status
        cpu_percent = metrics.get('cpu_percent', 0)
        memory_percent = metrics.get('memory_percent', 0)
        
        if cpu_percent > 80 or memory_percent > 80:
            status = "Poor"
            color = "#ff4444"
        elif cpu_percent > 60 or memory_percent > 60:
            status = "Fair"
            color = "#ffaa00"
        else:
            status = "Good"
            color = "#44ff44"
        
        self.performance_status_label.setText(f"Performance: {status}")
        self.performance_status_label.setStyleSheet(f"color: {color};")
        
        # Update memory indicator
        memory_mb = metrics.get('memory_mb', 0)
        self.memory_status_label.setText(f"Memory: {memory_mb:.1f} MB")
        
        # Update FPS indicator
        fps = metrics.get('fps', 0)
        self.fps_status_label.setText(f"FPS: {fps:.0f}")
        
        # Update tooltip with detailed info
        tooltip = f"""Performance Metrics:
CPU: {cpu_percent:.1f}%
Memory: {memory_percent:.1f}% ({memory_mb:.1f} MB)
FPS: {fps:.1f}
GPU Memory: {metrics.get('gpu_memory_mb', 0):.1f} MB"""
        self.performance_status_label.setToolTip(tooltip)
    
    def on_performance_warning(self, message):
        """Handle performance warnings"""
        self.logger.warning(f"Performance warning: {message}")
        self.statusBar().showMessage(f"Performance Warning: {message}", 5000)
    
    def show_performance_dialog(self):
        """Show detailed performance monitoring dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Performance Monitor")
        dialog.setModal(False)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Current metrics display
        metrics_label = QLabel("Current Performance Metrics:")
        metrics_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(metrics_label)
        
        # Real-time metrics text area
        metrics_text = QTextEdit()
        metrics_text.setReadOnly(True)
        metrics_text.setMaximumHeight(200)
        layout.addWidget(metrics_text)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        optimize_btn = QPushButton("Optimize Now")
        optimize_btn.clicked.connect(lambda: self.performance_optimizer.optimize_performance())
        button_layout.addWidget(optimize_btn)
        
        gc_btn = QPushButton("Force Cleanup")
        gc_btn.clicked.connect(lambda: self.performance_optimizer.memory_optimizer.force_cleanup())
        button_layout.addWidget(gc_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Update metrics periodically
        def update_metrics_display():
            if hasattr(self, 'performance_optimizer'):
                metrics = self.performance_optimizer.get_current_metrics()
                text = f"""CPU Usage: {metrics.get('cpu_percent', 0):.1f}%
Memory Usage: {metrics.get('memory_percent', 0):.1f}% ({metrics.get('memory_mb', 0):.1f} MB)
FPS: {metrics.get('fps', 0):.1f}
GPU Memory: {metrics.get('gpu_memory_mb', 0):.1f} MB
Optimization Level: {metrics.get('optimization_level', 'Standard')}
Auto-Optimization: {'Enabled' if metrics.get('auto_optimization', False) else 'Disabled'}"""
                metrics_text.setPlainText(text)
        
        # Setup timer for updates
        from PyQt6.QtCore import QTimer
        update_timer = QTimer()
        update_timer.timeout.connect(update_metrics_display)
        update_timer.start(1000)  # Update every second
        
        # Cleanup timer when dialog closes
        dialog.finished.connect(update_timer.stop)
        
        update_metrics_display()  # Initial update
        dialog.show()
        
        return dialog
    
    def toggle_auto_optimization(self, enabled):
        """Toggle automatic performance optimization"""
        if hasattr(self, 'performance_optimizer'):
            self.performance_optimizer.set_auto_optimization(enabled)
            status = "enabled" if enabled else "disabled"
            self.statusBar().showMessage(f"Auto-optimization {status}", 3000)
            self.logger.info(f"Auto-optimization {status}")
    
    def on_optimization_performed(self, results):
        """Handle optimization performed signal"""
        memory_result = results.get('memory', 0)
        if memory_result > 0:
            self.statusBar().showMessage(f"Optimization completed: {memory_result:.1f} MB freed", 3000)
            self.logger.info(f"Performance optimization freed {memory_result:.1f} MB")
    
    def on_fps_limit_changed(self, new_limit):
        """Handle FPS limit change"""
        self.logger.info(f"FPS limit adjusted to: {new_limit} ms interval")
    
    def on_performance_metrics_updated(self, metrics):
        """Handle updated performance metrics"""
        try:
            # Convert metrics to dict if needed
            if hasattr(metrics, '__dict__'):
                metrics_dict = {
                    'cpu_percent': metrics.cpu_percent,
                    'memory_percent': metrics.memory_percent,
                    'memory_mb': metrics.memory_mb,
                    'fps': metrics.fps,
                    'gpu_memory_mb': getattr(metrics, 'gpu_memory_mb', 0)
                }
            else:
                metrics_dict = metrics
            
            # Update performance status indicators
            self.update_performance_status(metrics_dict)
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
        
        
    def change_theme(self, theme_name):
        """Change application theme"""
        theme_map = {
            "Dark": "dark",
            "Light": "light", 
            "High Contrast": "high_contrast"
        }
        
        if theme_name in theme_map:
            self.current_theme = theme_map[theme_name]
            self.apply_professional_styling()
            
            # Update theme status
            theme_status = self.statusBar().findChild(QLabel)
            if theme_status:
                theme_status.setText(f"Theme: {theme_name}")
                
            self.statusBar().showMessage(f"Theme changed to {theme_name}", 2000)
            
            # Save theme preference to configuration
            try:
                self.config_manager.update_display_config(theme=self.current_theme)
                self.config_manager.save_current()
            except Exception as e:
                print(f"Failed to save theme preference: {e}")
                
    def show_settings_dialog(self):
        """Show application settings dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QCheckBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("RTB2000 Settings")
        dialog.setWindowIcon(IconManager.get_icon("settings"))
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Theme settings group
        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout(theme_group)
        
        # Theme selection
        theme_layout.addWidget(QLabel("Theme:"))
        theme_combo = QComboBox()
        theme_combo.addItems(["Dark", "Light", "High Contrast"])
        theme_combo.setCurrentText(self.current_theme.title())
        theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_combo)
        
        layout.addWidget(theme_group)
        
        # Performance settings group
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout(perf_group)
        
        auto_save_check = QCheckBox("Enable auto-save (every 30 seconds)")
        auto_save_check.setChecked(True)
        perf_layout.addWidget(auto_save_check)
        
        high_dpi_check = QCheckBox("High DPI scaling")
        high_dpi_check.setChecked(True)
        perf_layout.addWidget(high_dpi_check)
        
        layout.addWidget(perf_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
        """Show enhanced about dialog"""
        about_text = """
        <h3>RTB2000 Oscilloscope Control</h3>
        <p><b>Professional Edition v2.0</b></p>
        
        <p>A professional-grade control interface for Rohde & Schwarz RTB2000 series oscilloscopes.</p>
        
        <h4>Features:</h4>
        <ul>
        <li>🎯 High-performance real-time waveform display (60 FPS)</li>
        <li>⚙️ Advanced configuration management with presets</li>
        <li>🎨 Professional UI with multiple themes</li>
        <li>📊 Interactive cursors and real-time measurements</li>
        <li>💾 Comprehensive data export capabilities</li>
        <li>⌨️ Productivity-focused keyboard shortcuts</li>
        <li>🔄 Auto-save and session restoration</li>
        </ul>
        
        <h4>Technology Stack:</h4>
        <p>Built with PyQt6, PyVISA, PyQtGraph, and professional UI design principles</p>
        
        <p><small>© 2025 RTB2000 Project - Professional Edition</small></p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About RTB2000 Professional")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowIcon(IconManager.get_icon("help"))
        msg.exec()
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About RTB2000 Control",
                         "RTB2000 Oscilloscope Control GUI\n\n"
                         "Version 2.0 Enhanced Edition\n"
                         "Built with PyQt6, PyVISA, and PyQtGraph\n\n"
                         "Features:\n"
                         "• High-performance real-time waveform display\n"
                         "• Interactive cursors and measurements\n"
                         "• Professional data export capabilities\n"
                         "• Advanced configuration management\n"
                         "• Keyboard shortcuts for productivity\n\n"
                         "© 2025 RTB2000 Project")
                         
    def closeEvent(self, a0: QCloseEvent | None):
        """Handle application close"""
        try:
            # Auto-save current configuration before closing
            self.update_configuration_from_ui()
            self.config_manager.save_current()
            
            # Disconnect instrument
            if self.oscilloscope.is_connected():
                self.disconnect_instrument()
                
        except Exception as e:
            print(f"Error during application close: {e}")
            
        if a0:
            a0.accept()
            
    def auto_save_configuration(self):
        """Auto-save configuration periodically"""
        try:
            self.update_configuration_from_ui()
            self.config_manager.save_current()
        except Exception as e:
            print(f"Auto-save failed: {e}")
            
    def setup_auto_save(self):
        """Setup auto-save timer"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_configuration)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
