#!/usr/bin/env python3
"""
RTB2000 Statistical Analysis Module
===================================

Advanced statistical analysis capabilities for oscilloscope data:
- Basic statistics (mean, std, min, max, etc.)
- Advanced statistical measurements
- Histogram analysis
- Distribution fitting and analysis
"""

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem
import pyqtgraph as pg
from typing import Dict, List, Tuple, Optional, Any
import logging


class StatisticalAnalyzer(QObject):
    """Advanced statistical analyzer for oscilloscope data"""
    
    # Signals
    statistics_computed = pyqtSignal(dict)  # Emits statistical results
    histogram_updated = pyqtSignal(dict)  # Emits histogram data
    analysis_complete = pyqtSignal(dict)  # Emits complete analysis
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Statistical parameters
        self.histogram_bins = 100
        self.confidence_level = 0.95
        
        # Last computed statistics
        self.last_statistics = None
        self.last_histogram = None
        
        self.logger.info("Statistical Analyzer initialized")
    
    def compute_basic_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """
        Compute basic statistical measurements
        
        Args:
            data: Input data array
            
        Returns:
            Dictionary containing basic statistics
        """
        try:
            if len(data) == 0:
                raise ValueError("Empty data array")
            
            # Remove any NaN or infinite values
            clean_data = data[np.isfinite(data)]
            
            if len(clean_data) == 0:
                raise ValueError("No valid data points")
            
            # Basic statistics
            statistics = {
                'count': len(clean_data),
                'mean': float(np.mean(clean_data)),
                'std': float(np.std(clean_data)),
                'var': float(np.var(clean_data)),
                'min': float(np.min(clean_data)),
                'max': float(np.max(clean_data)),
                'range': float(np.ptp(clean_data)),
                'median': float(np.median(clean_data)),
                'rms': float(np.sqrt(np.mean(clean_data**2))),
                'peak_to_peak': float(np.ptp(clean_data))
            }
            
            # Percentiles
            percentiles = [5, 10, 25, 75, 90, 95]
            for p in percentiles:
                statistics[f'percentile_{p}'] = float(np.percentile(clean_data, p))
            
            # Additional statistical measures
            statistics['skewness'] = self.compute_skewness(clean_data)
            statistics['kurtosis'] = self.compute_kurtosis(clean_data)
            statistics['coefficient_of_variation'] = statistics['std'] / abs(statistics['mean']) if statistics['mean'] != 0 else float('inf')
            
            self.last_statistics = statistics
            self.statistics_computed.emit(statistics)
            
            self.logger.debug(f"Basic statistics computed for {len(clean_data)} points")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Basic statistics computation failed: {e}")
            return {}
    
    def compute_skewness(self, data: np.ndarray) -> float:
        """Compute skewness (asymmetry) of the data"""
        try:
            n = len(data)
            if n < 3:
                return 0.0
                
            mean = np.mean(data)
            std = np.std(data)
            
            if std == 0:
                return 0.0
            
            # Sample skewness
            skewness = np.sum(((data - mean) / std) ** 3) / n
            return float(skewness)
            
        except Exception:
            return 0.0
    
    def compute_kurtosis(self, data: np.ndarray) -> float:
        """Compute kurtosis (tail heaviness) of the data"""
        try:
            n = len(data)
            if n < 4:
                return 0.0
                
            mean = np.mean(data)
            std = np.std(data)
            
            if std == 0:
                return 0.0
            
            # Sample kurtosis (excess kurtosis, normal distribution = 0)
            kurtosis = np.sum(((data - mean) / std) ** 4) / n - 3
            return float(kurtosis)
            
        except Exception:
            return 0.0
    
    def compute_histogram(self, data: np.ndarray, bins: int = None) -> Dict[str, Any]:
        """
        Compute histogram of the data
        
        Args:
            data: Input data array
            bins: Number of histogram bins
            
        Returns:
            Dictionary containing histogram data
        """
        try:
            if bins is None:
                bins = self.histogram_bins
            
            # Remove any NaN or infinite values
            clean_data = data[np.isfinite(data)]
            
            if len(clean_data) == 0:
                raise ValueError("No valid data points")
            
            # Compute histogram
            counts, bin_edges = np.histogram(clean_data, bins=bins)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            bin_width = bin_edges[1] - bin_edges[0]
            
            # Normalize to probability density
            total_area = np.sum(counts) * bin_width
            probability_density = counts / total_area if total_area > 0 else counts
            
            # Find mode (most frequent value)
            mode_idx = np.argmax(counts)
            mode_value = bin_centers[mode_idx]
            
            histogram_data = {
                'counts': counts,
                'bin_edges': bin_edges,
                'bin_centers': bin_centers,
                'bin_width': bin_width,
                'probability_density': probability_density,
                'mode': float(mode_value),
                'mode_count': int(counts[mode_idx]),
                'total_count': int(np.sum(counts))
            }
            
            self.last_histogram = histogram_data
            self.histogram_updated.emit(histogram_data)
            
            self.logger.debug(f"Histogram computed with {bins} bins")
            return histogram_data
            
        except Exception as e:
            self.logger.error(f"Histogram computation failed: {e}")
            return {}
    
    def analyze_signal_quality(self, data: np.ndarray, sample_rate: float = 1.0) -> Dict[str, Any]:
        """
        Analyze signal quality metrics
        
        Args:
            data: Input signal data
            sample_rate: Sampling rate in Hz
            
        Returns:
            Dictionary containing signal quality metrics
        """
        try:
            clean_data = data[np.isfinite(data)]
            
            if len(clean_data) == 0:
                raise ValueError("No valid data points")
            
            # Basic statistics
            stats = self.compute_basic_statistics(clean_data)
            
            # Signal-to-noise ratio estimation
            # Simple method: assume noise is high-frequency variation
            # Use a simple derivative-based noise estimation
            if len(clean_data) > 1:
                diff = np.diff(clean_data)
                noise_estimate = np.std(diff) / np.sqrt(2)  # Account for differentiation
                signal_power = stats['rms']
                snr_estimate = 20 * np.log10(signal_power / noise_estimate) if noise_estimate > 0 else float('inf')
            else:
                snr_estimate = float('inf')
            
            # Effective number of bits (ENOB) estimation
            # ENOB = (SNR - 1.76) / 6.02
            enob = (snr_estimate - 1.76) / 6.02 if snr_estimate != float('inf') else 0
            
            # Dynamic range
            dynamic_range = 20 * np.log10(stats['max'] / (noise_estimate + 1e-12)) if 'max' in stats else 0
            
            # Crest factor (peak-to-RMS ratio)
            crest_factor = stats['max'] / stats['rms'] if stats['rms'] > 0 else float('inf')
            crest_factor_db = 20 * np.log10(crest_factor) if crest_factor != float('inf') else float('inf')
            
            quality_metrics = {
                'snr_estimate_db': float(snr_estimate),
                'noise_estimate': float(noise_estimate),
                'enob': float(enob),
                'dynamic_range_db': float(dynamic_range),
                'crest_factor': float(crest_factor),
                'crest_factor_db': float(crest_factor_db),
                'data_points': len(clean_data),
                'sample_rate': sample_rate
            }
            
            self.logger.info(f"Signal quality: SNR={snr_estimate:.1f}dB, ENOB={enob:.1f}bits")
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"Signal quality analysis failed: {e}")
            return {}
    
    def compute_correlation(self, data1: np.ndarray, data2: np.ndarray) -> Dict[str, Any]:
        """
        Compute correlation between two signals
        
        Args:
            data1: First signal
            data2: Second signal
            
        Returns:
            Dictionary containing correlation results
        """
        try:
            # Ensure same length
            min_length = min(len(data1), len(data2))
            data1 = data1[:min_length]
            data2 = data2[:min_length]
            
            # Remove NaN values
            valid_mask = np.isfinite(data1) & np.isfinite(data2)
            data1_clean = data1[valid_mask]
            data2_clean = data2[valid_mask]
            
            if len(data1_clean) < 2:
                raise ValueError("Insufficient valid data points")
            
            # Pearson correlation coefficient
            correlation_matrix = np.corrcoef(data1_clean, data2_clean)
            pearson_correlation = correlation_matrix[0, 1]
            
            # Cross-correlation
            cross_correlation = np.correlate(data1_clean, data2_clean, mode='full')
            max_correlation = np.max(cross_correlation)
            max_correlation_lag = np.argmax(cross_correlation) - len(data2_clean) + 1
            
            # Covariance
            covariance = np.cov(data1_clean, data2_clean)[0, 1]
            
            correlation_results = {
                'pearson_correlation': float(pearson_correlation),
                'covariance': float(covariance),
                'cross_correlation': cross_correlation,
                'max_cross_correlation': float(max_correlation),
                'max_correlation_lag': int(max_correlation_lag),
                'valid_points': len(data1_clean)
            }
            
            self.logger.debug(f"Correlation computed: r={pearson_correlation:.3f}")
            return correlation_results
            
        except Exception as e:
            self.logger.error(f"Correlation computation failed: {e}")
            return {}
    
    def analyze_trend(self, data: np.ndarray, time_data: np.ndarray = None) -> Dict[str, Any]:
        """
        Analyze trend in the data
        
        Args:
            data: Input data values
            time_data: Time values (optional)
            
        Returns:
            Dictionary containing trend analysis
        """
        try:
            clean_data = data[np.isfinite(data)]
            
            if len(clean_data) < 2:
                raise ValueError("Insufficient data for trend analysis")
            
            if time_data is None:
                time_data = np.arange(len(clean_data))
            else:
                time_data = time_data[:len(clean_data)]
            
            # Linear regression for trend
            coefficients = np.polyfit(time_data, clean_data, 1)
            slope = coefficients[0]
            intercept = coefficients[1]
            
            # R-squared (coefficient of determination)
            fitted_values = slope * time_data + intercept
            ss_res = np.sum((clean_data - fitted_values) ** 2)
            ss_tot = np.sum((clean_data - np.mean(clean_data)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Trend classification
            if abs(slope) < 1e-10:
                trend_type = "No trend"
            elif slope > 0:
                trend_type = "Increasing"
            else:
                trend_type = "Decreasing"
            
            trend_analysis = {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_squared),
                'trend_type': trend_type,
                'fitted_values': fitted_values,
                'data_points': len(clean_data)
            }
            
            self.logger.debug(f"Trend analysis: {trend_type}, R²={r_squared:.3f}")
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return {}


class StatisticsWidget(QWidget):
    """Widget for displaying statistical analysis results"""
    
    def __init__(self, statistical_analyzer: StatisticalAnalyzer):
        super().__init__()
        self.statistical_analyzer = statistical_analyzer
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the statistics display UI"""
        layout = QVBoxLayout(self)
        
        # Statistics table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(['Measurement', 'Value'])
        self.stats_table.setAlternatingRowColors(True)
        layout.addWidget(self.stats_table)
        
        # Histogram plot
        self.histogram_plot = pg.PlotWidget(title="Data Histogram")
        self.histogram_plot.setLabel('left', 'Count')
        self.histogram_plot.setLabel('bottom', 'Value')
        layout.addWidget(self.histogram_plot)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.statistical_analyzer.statistics_computed.connect(self.update_statistics_table)
        self.statistical_analyzer.histogram_updated.connect(self.update_histogram_plot)
    
    def update_statistics_table(self, statistics: Dict[str, float]):
        """Update the statistics table with new data"""
        try:
            self.stats_table.setRowCount(len(statistics))
            
            for row, (key, value) in enumerate(statistics.items()):
                # Format the key name
                formatted_key = key.replace('_', ' ').title()
                self.stats_table.setItem(row, 0, QTableWidgetItem(formatted_key))
                
                # Format the value
                if isinstance(value, float):
                    if abs(value) < 1e-3 or abs(value) > 1e6:
                        formatted_value = f"{value:.3e}"
                    else:
                        formatted_value = f"{value:.6f}"
                else:
                    formatted_value = str(value)
                
                self.stats_table.setItem(row, 1, QTableWidgetItem(formatted_value))
            
            self.stats_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating statistics table: {e}")
    
    def update_histogram_plot(self, histogram_data: Dict[str, Any]):
        """Update the histogram plot with new data"""
        try:
            self.histogram_plot.clear()
            
            counts = histogram_data['counts']
            bin_centers = histogram_data['bin_centers']
            bin_width = histogram_data['bin_width']
            
            # Create bar graph
            bargraph = pg.BarGraphItem(
                x=bin_centers,
                height=counts,
                width=bin_width * 0.8,
                brush='lightblue',
                pen='blue'
            )
            
            self.histogram_plot.addItem(bargraph)
            
        except Exception as e:
            print(f"Error updating histogram plot: {e}")
