#!/usr/bin/env python3
"""
RTB2000 FFT Analysis Module
===========================

Advanced FFT and frequency domain analysis capabilities:
- Real-time FFT computation with windowing
- Power spectral density analysis
- Frequency domain measurements
- Spectral peak detection and analysis
"""

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq, fftshift
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QSpinBox, QCheckBox
import pyqtgraph as pg
from typing import Dict, List, Tuple, Optional, Any
import logging


class FFTAnalyzer(QObject):
    """Advanced FFT and frequency domain analyzer"""
    
    # Signals
    fft_computed = pyqtSignal(dict)  # Emits FFT results
    peak_detected = pyqtSignal(list)  # Emits detected peaks
    analysis_complete = pyqtSignal(dict)  # Emits complete analysis
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # FFT parameters
        self.window_type = 'hann'
        self.fft_size = 1024
        self.overlap_ratio = 0.5
        self.zero_padding = True
        
        # Analysis parameters
        self.enable_peak_detection = True
        self.peak_threshold = -20  # dB
        self.min_peak_distance = 10  # samples
        
        # Window functions available
        self.window_functions = {
            'rectangular': np.ones,
            'hann': np.hanning,
            'hamming': np.hamming,
            'blackman': np.blackman,
            'kaiser': lambda N: np.kaiser(N, 8.6),
            'flattop': lambda N: signal.windows.flattop(N)
        }
        
        # Frequency domain data
        self.last_fft_data = None
        self.last_frequencies = None
        self.sample_rate = 1e6  # Default 1 MHz
        
        self.logger.info("FFT Analyzer initialized")
    
    def set_parameters(self, window_type: str = None, fft_size: int = None, 
                      overlap_ratio: float = None, sample_rate: float = None):
        """Set FFT analysis parameters"""
        if window_type and window_type in self.window_functions:
            self.window_type = window_type
            
        if fft_size and fft_size > 0:
            self.fft_size = fft_size
            
        if overlap_ratio and 0 <= overlap_ratio < 1:
            self.overlap_ratio = overlap_ratio
            
        if sample_rate and sample_rate > 0:
            self.sample_rate = sample_rate
            
        self.logger.info(f"FFT parameters updated: window={self.window_type}, "
                        f"size={self.fft_size}, overlap={self.overlap_ratio}")
    
    def compute_fft(self, time_data: np.ndarray, sample_rate: float = None) -> Dict[str, Any]:
        """
        Compute FFT with windowing and return frequency domain data
        
        Args:
            time_data: Input time domain signal
            sample_rate: Sampling rate in Hz
            
        Returns:
            Dictionary containing FFT results
        """
        try:
            if sample_rate:
                self.sample_rate = sample_rate
                
            # Validate input
            if len(time_data) < self.fft_size:
                # Zero pad if data is shorter than FFT size
                padded_data = np.zeros(self.fft_size)
                padded_data[:len(time_data)] = time_data
                time_data = padded_data
            
            # Apply window function
            window = self.window_functions[self.window_type](self.fft_size)
            windowed_data = time_data[:self.fft_size] * window
            
            # Compute FFT
            fft_data = fft(windowed_data)
            frequencies = fftfreq(self.fft_size, 1/self.sample_rate)
            
            # Take positive frequencies only
            n_positive = self.fft_size // 2
            positive_freqs = frequencies[:n_positive]
            positive_fft = fft_data[:n_positive]
            
            # Compute magnitude and phase
            magnitude = np.abs(positive_fft)
            magnitude_db = 20 * np.log10(magnitude + 1e-12)  # Avoid log(0)
            phase = np.angle(positive_fft)
            phase_degrees = np.degrees(phase)
            
            # Compute power spectral density
            psd = magnitude**2 / (self.sample_rate * np.sum(window**2))
            psd_db = 10 * np.log10(psd + 1e-12)
            
            # Store results
            self.last_fft_data = positive_fft
            self.last_frequencies = positive_freqs
            
            results = {
                'frequencies': positive_freqs,
                'magnitude': magnitude,
                'magnitude_db': magnitude_db,
                'phase': phase,
                'phase_degrees': phase_degrees,
                'psd': psd,
                'psd_db': psd_db,
                'complex_data': positive_fft,
                'window_type': self.window_type,
                'fft_size': self.fft_size,
                'sample_rate': self.sample_rate
            }
            
            # Detect peaks if enabled
            if self.enable_peak_detection:
                peaks = self.detect_peaks(magnitude_db, positive_freqs)
                results['peaks'] = peaks
                self.peak_detected.emit(peaks)
            
            self.fft_computed.emit(results)
            self.logger.debug(f"FFT computed: {len(positive_freqs)} frequency bins")
            
            return results
            
        except Exception as e:
            self.logger.error(f"FFT computation failed: {e}")
            return {}
    
    def detect_peaks(self, magnitude_db: np.ndarray, frequencies: np.ndarray) -> List[Dict]:
        """
        Detect spectral peaks in the FFT data
        
        Args:
            magnitude_db: Magnitude spectrum in dB
            frequencies: Frequency array
            
        Returns:
            List of detected peaks with frequency and amplitude
        """
        try:
            # Find peaks above threshold
            peak_indices, properties = signal.find_peaks(
                magnitude_db,
                height=self.peak_threshold,
                distance=self.min_peak_distance
            )
            
            peaks = []
            for idx in peak_indices:
                peak_info = {
                    'frequency': frequencies[idx],
                    'amplitude_db': magnitude_db[idx],
                    'amplitude_linear': 10**(magnitude_db[idx]/20),
                    'index': idx
                }
                peaks.append(peak_info)
            
            # Sort peaks by amplitude (descending)
            peaks.sort(key=lambda x: x['amplitude_db'], reverse=True)
            
            self.logger.debug(f"Detected {len(peaks)} spectral peaks")
            return peaks
            
        except Exception as e:
            self.logger.error(f"Peak detection failed: {e}")
            return []
    
    def compute_spectrogram(self, time_data: np.ndarray, nperseg: int = None) -> Dict[str, Any]:
        """
        Compute spectrogram for time-frequency analysis
        
        Args:
            time_data: Input time domain signal
            nperseg: Length of each segment for STFT
            
        Returns:
            Dictionary containing spectrogram data
        """
        try:
            if nperseg is None:
                nperseg = min(256, len(time_data) // 8)
            
            # Compute spectrogram using STFT
            frequencies, times, spectrogram = signal.spectrogram(
                time_data,
                fs=self.sample_rate,
                window=self.window_type,
                nperseg=nperseg,
                noverlap=int(nperseg * self.overlap_ratio)
            )
            
            # Convert to dB
            spectrogram_db = 10 * np.log10(spectrogram + 1e-12)
            
            results = {
                'frequencies': frequencies,
                'times': times,
                'spectrogram': spectrogram,
                'spectrogram_db': spectrogram_db,
                'nperseg': nperseg,
                'sample_rate': self.sample_rate
            }
            
            self.logger.debug(f"Spectrogram computed: {spectrogram.shape}")
            return results
            
        except Exception as e:
            self.logger.error(f"Spectrogram computation failed: {e}")
            return {}
    
    def analyze_harmonic_distortion(self, fundamental_freq: float) -> Dict[str, Any]:
        """
        Analyze harmonic distortion in the signal
        
        Args:
            fundamental_freq: Fundamental frequency in Hz
            
        Returns:
            Dictionary containing THD analysis
        """
        try:
            if self.last_fft_data is None or self.last_frequencies is None:
                raise ValueError("No FFT data available for analysis")
            
            # Find fundamental frequency bin
            fund_idx = np.argmin(np.abs(self.last_frequencies - fundamental_freq))
            fund_amplitude = np.abs(self.last_fft_data[fund_idx])
            
            # Find harmonics (2f, 3f, 4f, 5f)
            harmonics = []
            harmonic_power = 0
            
            for n in range(2, 6):  # 2nd to 5th harmonics
                harmonic_freq = n * fundamental_freq
                if harmonic_freq < self.last_frequencies[-1]:
                    harm_idx = np.argmin(np.abs(self.last_frequencies - harmonic_freq))
                    harm_amplitude = np.abs(self.last_fft_data[harm_idx])
                    
                    harmonics.append({
                        'order': n,
                        'frequency': harmonic_freq,
                        'amplitude': harm_amplitude,
                        'amplitude_db': 20 * np.log10(harm_amplitude / fund_amplitude)
                    })
                    
                    harmonic_power += harm_amplitude**2
            
            # Calculate THD
            thd_ratio = np.sqrt(harmonic_power) / fund_amplitude
            thd_percent = thd_ratio * 100
            thd_db = 20 * np.log10(thd_ratio)
            
            results = {
                'fundamental_frequency': fundamental_freq,
                'fundamental_amplitude': fund_amplitude,
                'harmonics': harmonics,
                'thd_ratio': thd_ratio,
                'thd_percent': thd_percent,
                'thd_db': thd_db
            }
            
            self.logger.info(f"THD analysis: {thd_percent:.2f}% ({thd_db:.1f} dB)")
            return results
            
        except Exception as e:
            self.logger.error(f"Harmonic distortion analysis failed: {e}")
            return {}
    
    def get_frequency_response(self, input_signal: np.ndarray, 
                             output_signal: np.ndarray) -> Dict[str, Any]:
        """
        Calculate frequency response between input and output signals
        
        Args:
            input_signal: Input time domain signal
            output_signal: Output time domain signal
            
        Returns:
            Dictionary containing frequency response data
        """
        try:
            # Ensure signals are same length
            min_length = min(len(input_signal), len(output_signal))
            input_signal = input_signal[:min_length]
            output_signal = output_signal[:min_length]
            
            # Compute cross-power spectral density
            frequencies, h_response = signal.csd(
                input_signal, output_signal,
                fs=self.sample_rate,
                window=self.window_type,
                nperseg=self.fft_size
            )
            
            # Compute input power spectral density
            _, input_psd = signal.welch(
                input_signal,
                fs=self.sample_rate,
                window=self.window_type,
                nperseg=self.fft_size
            )
            
            # Calculate frequency response
            freq_response = h_response / (input_psd + 1e-12)
            
            # Magnitude and phase
            magnitude = np.abs(freq_response)
            magnitude_db = 20 * np.log10(magnitude + 1e-12)
            phase = np.angle(freq_response)
            phase_degrees = np.degrees(phase)
            
            results = {
                'frequencies': frequencies,
                'magnitude': magnitude,
                'magnitude_db': magnitude_db,
                'phase': phase,
                'phase_degrees': phase_degrees,
                'complex_response': freq_response
            }
            
            self.logger.debug(f"Frequency response calculated: {len(frequencies)} points")
            return results
            
        except Exception as e:
            self.logger.error(f"Frequency response calculation failed: {e}")
            return {}


class FFTWidget(QWidget):
    """Widget for FFT analysis controls and display"""
    
    def __init__(self, fft_analyzer: FFTAnalyzer):
        super().__init__()
        self.fft_analyzer = fft_analyzer
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the FFT control UI"""
        layout = QVBoxLayout(self)
        
        # FFT Parameters
        params_layout = QHBoxLayout()
        
        # Window type
        params_layout.addWidget(QLabel("Window:"))
        self.window_combo = QComboBox()
        self.window_combo.addItems(['hann', 'hamming', 'blackman', 'kaiser', 'flattop'])
        params_layout.addWidget(self.window_combo)
        
        # FFT size
        params_layout.addWidget(QLabel("FFT Size:"))
        self.fft_size_spin = QSpinBox()
        self.fft_size_spin.setRange(256, 8192)
        self.fft_size_spin.setValue(1024)
        self.fft_size_spin.setSingleStep(256)
        params_layout.addWidget(self.fft_size_spin)
        
        # Peak detection
        self.peak_detection_check = QCheckBox("Peak Detection")
        self.peak_detection_check.setChecked(True)
        params_layout.addWidget(self.peak_detection_check)
        
        layout.addLayout(params_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.compute_btn = QPushButton("Compute FFT")
        button_layout.addWidget(self.compute_btn)
        
        self.spectrogram_btn = QPushButton("Spectrogram")
        button_layout.addWidget(self.spectrogram_btn)
        
        self.thd_btn = QPushButton("THD Analysis")
        button_layout.addWidget(self.thd_btn)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.window_combo.currentTextChanged.connect(self.update_window_type)
        self.fft_size_spin.valueChanged.connect(self.update_fft_size)
        self.peak_detection_check.toggled.connect(self.update_peak_detection)
    
    def update_window_type(self, window_type: str):
        """Update FFT window type"""
        self.fft_analyzer.set_parameters(window_type=window_type)
    
    def update_fft_size(self, fft_size: int):
        """Update FFT size"""
        self.fft_analyzer.set_parameters(fft_size=fft_size)
    
    def update_peak_detection(self, enabled: bool):
        """Update peak detection setting"""
        self.fft_analyzer.enable_peak_detection = enabled
