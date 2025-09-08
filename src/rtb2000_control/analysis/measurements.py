#!/usr/bin/env python3
"""
RTB2000 Measurement Engine Module
=================================

Advanced measurement engine for oscilloscope data:
- Automated measurement routines
- Custom measurement definitions
- Measurement cursors and annotations
- Measurement history and tracking
"""

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QPushButton, QTableWidget, QTableWidgetItem,
                            QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox)
import pyqtgraph as pg
from typing import Dict, List, Tuple, Optional, Any, Callable
import logging
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MeasurementResult:
    """Data class for measurement results"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    channel: str
    valid: bool = True
    error_message: str = ""


class MeasurementEngine(QObject):
    """Advanced measurement engine for oscilloscope data"""
    
    # Signals
    measurement_completed = pyqtSignal(object)  # MeasurementResult
    measurement_failed = pyqtSignal(str, str)  # measurement_name, error_message
    measurements_updated = pyqtSignal(list)  # List of MeasurementResult
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Measurement functions registry
        self.measurement_functions = {}
        self.register_standard_measurements()
        
        # Measurement history
        self.measurement_history = []
        self.max_history_size = 1000
        
        # Automatic measurement settings
        self.auto_measurements = []
        self.auto_measurement_enabled = False
        self.auto_measurement_timer = QTimer()
        self.auto_measurement_timer.timeout.connect(self.perform_auto_measurements)
        self.auto_measurement_interval = 1000  # 1 second
        
        # Current data
        self.current_data = {}
        self.sample_rate = 1e6  # Default 1 MHz
        
        self.logger.info("Measurement Engine initialized")
    
    def register_measurement(self, name: str, function: Callable, unit: str = "", 
                           description: str = ""):
        """
        Register a measurement function
        
        Args:
            name: Measurement name
            function: Measurement function that takes (data, sample_rate) and returns float
            unit: Unit of measurement
            description: Description of the measurement
        """
        self.measurement_functions[name] = {
            'function': function,
            'unit': unit,
            'description': description
        }
        self.logger.debug(f"Registered measurement: {name}")
    
    def register_standard_measurements(self):
        """Register standard oscilloscope measurements"""
        
        # Voltage measurements
        self.register_measurement("DC Average", self.measure_dc_average, "V", 
                                "DC average (mean) value")
        self.register_measurement("RMS", self.measure_rms, "V", 
                                "Root mean square value")
        self.register_measurement("Peak-Peak", self.measure_peak_to_peak, "V", 
                                "Peak-to-peak amplitude")
        self.register_measurement("Maximum", self.measure_maximum, "V", 
                                "Maximum value")
        self.register_measurement("Minimum", self.measure_minimum, "V", 
                                "Minimum value")
        self.register_measurement("Amplitude", self.measure_amplitude, "V", 
                                "Signal amplitude (max - min)")
        
        # Timing measurements
        self.register_measurement("Period", self.measure_period, "s", 
                                "Signal period")
        self.register_measurement("Frequency", self.measure_frequency, "Hz", 
                                "Signal frequency")
        self.register_measurement("Rise Time", self.measure_rise_time, "s", 
                                "10% to 90% rise time")
        self.register_measurement("Fall Time", self.measure_fall_time, "s", 
                                "90% to 10% fall time")
        self.register_measurement("Pulse Width", self.measure_pulse_width, "s", 
                                "Positive pulse width")
        self.register_measurement("Duty Cycle", self.measure_duty_cycle, "%", 
                                "Duty cycle percentage")
        
        # Advanced measurements
        self.register_measurement("Overshoot", self.measure_overshoot, "%", 
                                "Overshoot percentage")
        self.register_measurement("Undershoot", self.measure_undershoot, "%", 
                                "Undershoot percentage")
        self.register_measurement("Settle Time", self.measure_settle_time, "s", 
                                "Settling time to within 2%")
        
        self.logger.info(f"Registered {len(self.measurement_functions)} standard measurements")
    
    def perform_measurement(self, measurement_name: str, data: np.ndarray, 
                          channel: str = "CH1", sample_rate: float = None) -> Optional[MeasurementResult]:
        """
        Perform a specific measurement on data
        
        Args:
            measurement_name: Name of measurement to perform
            data: Input data array
            channel: Channel identifier
            sample_rate: Sampling rate in Hz
            
        Returns:
            MeasurementResult object or None if failed
        """
        try:
            if measurement_name not in self.measurement_functions:
                raise ValueError(f"Unknown measurement: {measurement_name}")
            
            if sample_rate is None:
                sample_rate = self.sample_rate
            
            # Clean data
            clean_data = data[np.isfinite(data)]
            if len(clean_data) == 0:
                raise ValueError("No valid data points")
            
            # Perform measurement
            measurement_info = self.measurement_functions[measurement_name]
            value = measurement_info['function'](clean_data, sample_rate)
            
            # Create result
            result = MeasurementResult(
                name=measurement_name,
                value=value,
                unit=measurement_info['unit'],
                timestamp=datetime.now(),
                channel=channel,
                valid=True
            )
            
            # Add to history
            self.add_to_history(result)
            
            # Emit signal
            self.measurement_completed.emit(result)
            
            self.logger.debug(f"Measurement {measurement_name}: {value:.6f} {measurement_info['unit']}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Measurement {measurement_name} failed: {error_msg}")
            
            # Create failed result
            result = MeasurementResult(
                name=measurement_name,
                value=float('nan'),
                unit=self.measurement_functions.get(measurement_name, {}).get('unit', ''),
                timestamp=datetime.now(),
                channel=channel,
                valid=False,
                error_message=error_msg
            )
            
            self.measurement_failed.emit(measurement_name, error_msg)
            return result
    
    def add_to_history(self, result: MeasurementResult):
        """Add measurement result to history"""
        self.measurement_history.append(result)
        
        # Limit history size
        if len(self.measurement_history) > self.max_history_size:
            self.measurement_history = self.measurement_history[-self.max_history_size:]
        
        # Emit updated measurements
        self.measurements_updated.emit(self.measurement_history[-10:])  # Last 10 measurements
    
    def set_auto_measurements(self, measurement_names: List[str]):
        """Set measurements to perform automatically"""
        self.auto_measurements = measurement_names
        self.logger.info(f"Auto measurements set: {measurement_names}")
    
    def enable_auto_measurements(self, enabled: bool):
        """Enable or disable automatic measurements"""
        self.auto_measurement_enabled = enabled
        if enabled and self.auto_measurements:
            self.auto_measurement_timer.start(self.auto_measurement_interval)
            self.logger.info("Auto measurements enabled")
        else:
            self.auto_measurement_timer.stop()
            self.logger.info("Auto measurements disabled")
    
    def perform_auto_measurements(self):
        """Perform automatic measurements on current data"""
        if not self.current_data or not self.auto_measurements:
            return
        
        for channel, data in self.current_data.items():
            for measurement_name in self.auto_measurements:
                self.perform_measurement(measurement_name, data, channel)
    
    def update_data(self, channel: str, data: np.ndarray):
        """Update current data for a channel"""
        self.current_data[channel] = data
    
    # Standard measurement functions
    def measure_dc_average(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure DC average (mean) value"""
        return float(np.mean(data))
    
    def measure_rms(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure RMS value"""
        return float(np.sqrt(np.mean(data**2)))
    
    def measure_peak_to_peak(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure peak-to-peak amplitude"""
        return float(np.ptp(data))
    
    def measure_maximum(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure maximum value"""
        return float(np.max(data))
    
    def measure_minimum(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure minimum value"""
        return float(np.min(data))
    
    def measure_amplitude(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure signal amplitude"""
        return self.measure_maximum(data, sample_rate) - self.measure_minimum(data, sample_rate)
    
    def measure_period(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure signal period using zero crossings"""
        try:
            # Find zero crossings
            mean_value = np.mean(data)
            zero_crossings = np.where(np.diff(np.signbit(data - mean_value)))[0]
            
            if len(zero_crossings) < 2:
                raise ValueError("Insufficient zero crossings for period measurement")
            
            # Calculate period from consecutive positive-going zero crossings
            positive_crossings = []
            for i in zero_crossings:
                if i > 0 and i < len(data) - 1:
                    if data[i+1] > data[i-1]:  # Positive-going crossing
                        positive_crossings.append(i)
            
            if len(positive_crossings) < 2:
                raise ValueError("Insufficient positive zero crossings")
            
            # Average period
            periods = np.diff(positive_crossings) / sample_rate
            return float(np.mean(periods))
            
        except Exception:
            # Fallback: use autocorrelation method
            return self.measure_period_autocorr(data, sample_rate)
    
    def measure_period_autocorr(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure period using autocorrelation"""
        try:
            # Remove DC component
            data_ac = data - np.mean(data)
            
            # Compute autocorrelation
            autocorr = np.correlate(data_ac, data_ac, mode='full')
            autocorr = autocorr[len(autocorr)//2:]  # Take positive lags only
            
            # Find first peak after lag 0
            if len(autocorr) < 10:
                raise ValueError("Insufficient data for autocorrelation")
            
            # Look for peak starting from 1/10 of the data length
            start_idx = max(1, len(autocorr) // 10)
            peak_idx = np.argmax(autocorr[start_idx:]) + start_idx
            
            period = peak_idx / sample_rate
            return float(period)
            
        except Exception:
            raise ValueError("Period measurement failed")
    
    def measure_frequency(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure signal frequency"""
        period = self.measure_period(data, sample_rate)
        return 1.0 / period if period > 0 else 0.0
    
    def measure_rise_time(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure 10% to 90% rise time"""
        try:
            # Find rising edges
            min_val = np.min(data)
            max_val = np.max(data)
            level_10 = min_val + 0.1 * (max_val - min_val)
            level_90 = min_val + 0.9 * (max_val - min_val)
            
            # Find crossings
            crossings_10 = np.where(np.diff(np.signbit(data - level_10)))[0]
            crossings_90 = np.where(np.diff(np.signbit(data - level_90)))[0]
            
            if len(crossings_10) == 0 or len(crossings_90) == 0:
                raise ValueError("No level crossings found")
            
            # Find first positive-going crossing for each level
            pos_10 = None
            pos_90 = None
            
            for crossing in crossings_10:
                if crossing < len(data) - 1 and data[crossing + 1] > data[crossing]:
                    pos_10 = crossing
                    break
            
            for crossing in crossings_90:
                if crossing < len(data) - 1 and data[crossing + 1] > data[crossing] and crossing > pos_10:
                    pos_90 = crossing
                    break
            
            if pos_10 is None or pos_90 is None:
                raise ValueError("Could not find rise time crossings")
            
            rise_time = (pos_90 - pos_10) / sample_rate
            return float(rise_time)
            
        except Exception:
            raise ValueError("Rise time measurement failed")
    
    def measure_fall_time(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure 90% to 10% fall time"""
        try:
            # Find falling edges
            min_val = np.min(data)
            max_val = np.max(data)
            level_10 = min_val + 0.1 * (max_val - min_val)
            level_90 = min_val + 0.9 * (max_val - min_val)
            
            # Find crossings
            crossings_90 = np.where(np.diff(np.signbit(data - level_90)))[0]
            crossings_10 = np.where(np.diff(np.signbit(data - level_10)))[0]
            
            if len(crossings_10) == 0 or len(crossings_90) == 0:
                raise ValueError("No level crossings found")
            
            # Find first negative-going crossing for each level
            neg_90 = None
            neg_10 = None
            
            for crossing in crossings_90:
                if crossing < len(data) - 1 and data[crossing + 1] < data[crossing]:
                    neg_90 = crossing
                    break
            
            for crossing in crossings_10:
                if crossing < len(data) - 1 and data[crossing + 1] < data[crossing] and crossing > neg_90:
                    neg_10 = crossing
                    break
            
            if neg_90 is None or neg_10 is None:
                raise ValueError("Could not find fall time crossings")
            
            fall_time = (neg_10 - neg_90) / sample_rate
            return float(fall_time)
            
        except Exception:
            raise ValueError("Fall time measurement failed")
    
    def measure_pulse_width(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure positive pulse width at 50% level"""
        try:
            min_val = np.min(data)
            max_val = np.max(data)
            mid_level = (min_val + max_val) / 2
            
            # Find level crossings
            crossings = np.where(np.diff(np.signbit(data - mid_level)))[0]
            
            if len(crossings) < 2:
                raise ValueError("Insufficient level crossings for pulse width")
            
            # Find positive pulse (rising edge followed by falling edge)
            for i in range(len(crossings) - 1):
                rise_idx = crossings[i]
                fall_idx = crossings[i + 1]
                
                if (rise_idx < len(data) - 1 and fall_idx < len(data) - 1 and
                    data[rise_idx + 1] > data[rise_idx] and  # Rising edge
                    data[fall_idx + 1] < data[fall_idx]):    # Falling edge
                    
                    pulse_width = (fall_idx - rise_idx) / sample_rate
                    return float(pulse_width)
            
            raise ValueError("No positive pulse found")
            
        except Exception:
            raise ValueError("Pulse width measurement failed")
    
    def measure_duty_cycle(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure duty cycle percentage"""
        try:
            period = self.measure_period(data, sample_rate)
            pulse_width = self.measure_pulse_width(data, sample_rate)
            
            duty_cycle = (pulse_width / period) * 100
            return float(duty_cycle)
            
        except Exception:
            raise ValueError("Duty cycle measurement failed")
    
    def measure_overshoot(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure overshoot percentage"""
        try:
            min_val = np.min(data)
            max_val = np.max(data)
            
            # Simple overshoot calculation
            # This is a simplified implementation
            overshoot = ((max_val - np.mean(data)) / (max_val - min_val)) * 100
            return float(max(0, overshoot - 100))  # Overshoot above 100%
            
        except Exception:
            raise ValueError("Overshoot measurement failed")
    
    def measure_undershoot(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure undershoot percentage"""
        try:
            min_val = np.min(data)
            max_val = np.max(data)
            
            # Simple undershoot calculation
            undershoot = ((np.mean(data) - min_val) / (max_val - min_val)) * 100
            return float(max(0, undershoot - 100))  # Undershoot below 0%
            
        except Exception:
            raise ValueError("Undershoot measurement failed")
    
    def measure_settle_time(self, data: np.ndarray, sample_rate: float) -> float:
        """Measure settling time to within 2% of final value"""
        try:
            # This is a simplified implementation
            # In practice, this would need more sophisticated step response analysis
            final_value = np.mean(data[-len(data)//10:])  # Last 10% as final value
            tolerance = 0.02 * abs(final_value)
            
            # Find when signal stays within tolerance
            for i in range(len(data) - 1, 0, -1):
                if abs(data[i] - final_value) > tolerance:
                    settle_time = (len(data) - i) / sample_rate
                    return float(settle_time)
            
            return 0.0  # Already settled
            
        except Exception:
            raise ValueError("Settle time measurement failed")


class MeasurementWidget(QWidget):
    """Widget for measurement controls and display"""
    
    def __init__(self, measurement_engine: MeasurementEngine):
        super().__init__()
        self.measurement_engine = measurement_engine
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the measurement UI"""
        layout = QVBoxLayout(self)
        
        # Available measurements
        measurements_layout = QHBoxLayout()
        measurements_layout.addWidget(QLabel("Available Measurements:"))
        
        self.measurement_list = QListWidget()
        self.measurement_list.addItems(list(self.measurement_engine.measurement_functions.keys()))
        measurements_layout.addWidget(self.measurement_list)
        
        # Control buttons
        button_layout = QVBoxLayout()
        
        self.measure_btn = QPushButton("Measure Selected")
        button_layout.addWidget(self.measure_btn)
        
        self.auto_measure_check = QCheckBox("Auto Measurements")
        button_layout.addWidget(self.auto_measure_check)
        
        measurements_layout.addLayout(button_layout)
        layout.addLayout(measurements_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(['Measurement', 'Value', 'Unit', 'Channel', 'Time'])
        layout.addWidget(self.results_table)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.measurement_engine.measurement_completed.connect(self.add_measurement_result)
        self.measurement_engine.measurements_updated.connect(self.update_results_table)
        self.auto_measure_check.toggled.connect(self.toggle_auto_measurements)
    
    def add_measurement_result(self, result: MeasurementResult):
        """Add a measurement result to the table"""
        try:
            row_count = self.results_table.rowCount()
            self.results_table.insertRow(0)  # Insert at top
            
            self.results_table.setItem(0, 0, QTableWidgetItem(result.name))
            
            if result.valid:
                value_text = f"{result.value:.6f}"
            else:
                value_text = "ERROR"
            
            self.results_table.setItem(0, 1, QTableWidgetItem(value_text))
            self.results_table.setItem(0, 2, QTableWidgetItem(result.unit))
            self.results_table.setItem(0, 3, QTableWidgetItem(result.channel))
            self.results_table.setItem(0, 4, QTableWidgetItem(result.timestamp.strftime("%H:%M:%S")))
            
            # Limit table size
            if self.results_table.rowCount() > 50:
                self.results_table.removeRow(50)
                
        except Exception as e:
            print(f"Error adding measurement result: {e}")
    
    def update_results_table(self, results: List[MeasurementResult]):
        """Update the entire results table"""
        # This could be used for bulk updates if needed
        pass
    
    def toggle_auto_measurements(self, enabled: bool):
        """Toggle automatic measurements"""
        if enabled:
            # Get selected measurements
            selected_items = self.measurement_list.selectedItems()
            if selected_items:
                measurement_names = [item.text() for item in selected_items]
                self.measurement_engine.set_auto_measurements(measurement_names)
        
        self.measurement_engine.enable_auto_measurements(enabled)
