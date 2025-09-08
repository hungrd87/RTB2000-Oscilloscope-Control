"""
Data Export System for RTB2000
Version 2.0 - September 8, 2025

Handles exporting waveform data, measurements, and screenshots
in various formats
"""

import csv
import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    import h5py
    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ExportFormat(Enum):
    """Supported export formats"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "xlsx"
    MATLAB = "mat"
    HDF5 = "h5"
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    TEXT = "txt"


@dataclass
class WaveformData:
    """Container for waveform data"""
    channel: int
    time: np.ndarray
    voltage: np.ndarray
    sample_rate: float
    scale: float
    offset: float
    units: str = "V"
    label: str = ""
    color: str = "#FFFF00"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MeasurementData:
    """Container for measurement data"""
    name: str
    value: float
    unit: str
    channel: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ScreenshotData:
    """Container for screenshot data"""
    image_data: np.ndarray
    format: str
    width: int
    height: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DataExporter:
    """Advanced data export system"""
    
    def __init__(self, default_dir: str = None):
        """
        Initialize data exporter
        
        Args:
            default_dir: Default export directory
        """
        if default_dir is None:
            default_dir = os.path.join(
                os.path.expanduser("~"), 
                "RTB2000_Exports"
            )
            
        self.default_dir = Path(default_dir)
        self.default_dir.mkdir(parents=True, exist_ok=True)
        
        # Supported formats
        self.supported_formats = {
            ExportFormat.CSV: self._export_csv,
            ExportFormat.JSON: self._export_json,
            ExportFormat.EXCEL: self._export_excel,
            ExportFormat.TEXT: self._export_text,
            ExportFormat.PNG: self._export_png,
            ExportFormat.SVG: self._export_svg,
            ExportFormat.PDF: self._export_pdf
        }
        
        if HDF5_AVAILABLE:
            self.supported_formats[ExportFormat.HDF5] = self._export_hdf5
            
        # Export session data
        self.session_data = {
            'waveforms': [],
            'measurements': [],
            'screenshots': [],
            'session_start': datetime.now(),
            'export_count': 0
        }
        
    def export_waveforms(self, 
                        waveforms: List[WaveformData], 
                        filepath: str,
                        format: ExportFormat,
                        metadata: Dict[str, Any] = None) -> bool:
        """
        Export waveform data
        
        Args:
            waveforms: List of waveform data
            filepath: Output file path
            format: Export format
            metadata: Additional metadata
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Add to session data
            self.session_data['waveforms'].extend(waveforms)
            self.session_data['export_count'] += 1
            
            # Export using appropriate method
            if format in self.supported_formats:
                return self.supported_formats[format](waveforms, filepath, metadata)
            else:
                print(f"Unsupported format: {format}")
                return False
                
        except Exception as e:
            print(f"Error exporting waveforms: {e}")
            return False
            
    def export_measurements(self,
                           measurements: List[MeasurementData],
                           filepath: str,
                           format: ExportFormat = ExportFormat.CSV) -> bool:
        """
        Export measurement data
        
        Args:
            measurements: List of measurements
            filepath: Output file path
            format: Export format
            
        Returns:
            bool: Success status
        """
        try:
            # Add to session data
            self.session_data['measurements'].extend(measurements)
            
            if format == ExportFormat.CSV:
                return self._export_measurements_csv(measurements, filepath)
            elif format == ExportFormat.JSON:
                return self._export_measurements_json(measurements, filepath)
            elif format == ExportFormat.EXCEL:
                return self._export_measurements_excel(measurements, filepath)
            else:
                print(f"Unsupported format for measurements: {format}")
                return False
                
        except Exception as e:
            print(f"Error exporting measurements: {e}")
            return False
            
    def export_screenshot(self,
                         screenshot: ScreenshotData,
                         filepath: str) -> bool:
        """
        Export screenshot
        
        Args:
            screenshot: Screenshot data
            filepath: Output file path
            
        Returns:
            bool: Success status
        """
        try:
            if not PIL_AVAILABLE:
                print("PIL not available for screenshot export")
                return False
                
            # Add to session data
            self.session_data['screenshots'].append(screenshot)
            
            # Convert and save image
            img = Image.fromarray(screenshot.image_data)
            img.save(filepath)
            
            return True
            
        except Exception as e:
            print(f"Error exporting screenshot: {e}")
            return False
            
    def create_session_report(self, filepath: str) -> bool:
        """
        Create comprehensive session report
        
        Args:
            filepath: Report file path
            
        Returns:
            bool: Success status
        """
        try:
            report_data = {
                'session_info': {
                    'start_time': self.session_data['session_start'].isoformat(),
                    'export_time': datetime.now().isoformat(),
                    'duration': str(datetime.now() - self.session_data['session_start']),
                    'export_count': self.session_data['export_count']
                },
                'statistics': {
                    'total_waveforms': len(self.session_data['waveforms']),
                    'total_measurements': len(self.session_data['measurements']),
                    'total_screenshots': len(self.session_data['screenshots']),
                    'channels_used': list(set(w.channel for w in self.session_data['waveforms']))
                },
                'waveforms': [
                    {
                        'channel': w.channel,
                        'sample_count': len(w.time),
                        'duration': float(w.time[-1] - w.time[0]) if len(w.time) > 1 else 0,
                        'sample_rate': w.sample_rate,
                        'timestamp': w.timestamp.isoformat(),
                        'label': w.label
                    } for w in self.session_data['waveforms']
                ],
                'measurements': [
                    {
                        'name': m.name,
                        'value': m.value,
                        'unit': m.unit,
                        'channel': m.channel,
                        'timestamp': m.timestamp.isoformat()
                    } for m in self.session_data['measurements']
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error creating session report: {e}")
            return False
            
    def _export_csv(self, waveforms: List[WaveformData], filepath: str, metadata: Dict = None) -> bool:
        """Export to CSV format"""
        with open(filepath, 'w', newline='') as csvfile:
            # Write metadata as comments
            if metadata:
                csvfile.write(f"# Export Date: {datetime.now().isoformat()}\n")
                for key, value in metadata.items():
                    csvfile.write(f"# {key}: {value}\n")
                csvfile.write("#\n")
                
            # Determine time base (use longest waveform)
            max_samples = max(len(w.time) for w in waveforms)
            base_waveform = next(w for w in waveforms if len(w.time) == max_samples)
            
            # Create header
            headers = ['Time']
            for w in waveforms:
                headers.append(f'CH{w.channel}_Voltage')
                
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            # Write data
            for i in range(len(base_waveform.time)):
                row = [base_waveform.time[i]]
                
                for w in waveforms:
                    if i < len(w.voltage):
                        row.append(w.voltage[i])
                    else:
                        row.append('')  # Empty for shorter waveforms
                        
                writer.writerow(row)
                
        return True
        
    def _export_json(self, waveforms: List[WaveformData], filepath: str, metadata: Dict = None) -> bool:
        """Export to JSON format"""
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'format_version': '2.0',
                **(metadata or {})
            },
            'waveforms': []
        }
        
        for w in waveforms:
            waveform_data = {
                'channel': w.channel,
                'label': w.label,
                'color': w.color,
                'sample_rate': w.sample_rate,
                'scale': w.scale,
                'offset': w.offset,
                'units': w.units,
                'timestamp': w.timestamp.isoformat(),
                'time': w.time.tolist(),
                'voltage': w.voltage.tolist()
            }
            export_data['waveforms'].append(waveform_data)
            
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        return True
        
    def _export_excel(self, waveforms: List[WaveformData], filepath: str, metadata: Dict = None) -> bool:
        """Export to Excel format"""
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Metadata sheet
                if metadata:
                    meta_df = pd.DataFrame(list(metadata.items()), columns=['Parameter', 'Value'])
                    meta_df.to_excel(writer, sheet_name='Metadata', index=False)
                    
                # Waveforms sheet
                waveform_dict = {}
                max_samples = max(len(w.time) for w in waveforms)
                base_waveform = next(w for w in waveforms if len(w.time) == max_samples)
                
                waveform_dict['Time'] = base_waveform.time
                
                for w in waveforms:
                    # Pad shorter waveforms with NaN
                    voltage_padded = np.full(max_samples, np.nan)
                    voltage_padded[:len(w.voltage)] = w.voltage
                    waveform_dict[f'CH{w.channel}_Voltage'] = voltage_padded
                    
                df = pd.DataFrame(waveform_dict)
                df.to_excel(writer, sheet_name='Waveforms', index=False)
                
                # Summary sheet
                summary_data = []
                for w in waveforms:
                    summary_data.append({
                        'Channel': w.channel,
                        'Label': w.label,
                        'Sample_Rate': w.sample_rate,
                        'Sample_Count': len(w.voltage),
                        'Min_Voltage': np.min(w.voltage),
                        'Max_Voltage': np.max(w.voltage),
                        'Mean_Voltage': np.mean(w.voltage),
                        'RMS_Voltage': np.sqrt(np.mean(w.voltage**2))
                    })
                    
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
            
    def _export_hdf5(self, waveforms: List[WaveformData], filepath: str, metadata: Dict = None) -> bool:
        """Export to HDF5 format"""
        try:
            with h5py.File(filepath, 'w') as f:
                # Create groups
                waveforms_group = f.create_group('waveforms')
                metadata_group = f.create_group('metadata')
                
                # Store metadata
                if metadata:
                    for key, value in metadata.items():
                        metadata_group.attrs[key] = value
                        
                metadata_group.attrs['export_date'] = datetime.now().isoformat()
                metadata_group.attrs['format_version'] = '2.0'
                
                # Store waveforms
                for w in waveforms:
                    ch_group = waveforms_group.create_group(f'channel_{w.channel}')
                    
                    # Store data
                    ch_group.create_dataset('time', data=w.time)
                    ch_group.create_dataset('voltage', data=w.voltage)
                    
                    # Store attributes
                    ch_group.attrs['label'] = w.label
                    ch_group.attrs['color'] = w.color
                    ch_group.attrs['sample_rate'] = w.sample_rate
                    ch_group.attrs['scale'] = w.scale
                    ch_group.attrs['offset'] = w.offset
                    ch_group.attrs['units'] = w.units
                    ch_group.attrs['timestamp'] = w.timestamp.isoformat()
                    
            return True
            
        except Exception as e:
            print(f"Error exporting to HDF5: {e}")
            return False
            
    def _export_text(self, waveforms: List[WaveformData], filepath: str, metadata: Dict = None) -> bool:
        """Export to text format"""
        with open(filepath, 'w') as f:
            # Write header
            f.write("RTB2000 Waveform Data Export\n")
            f.write("=" * 40 + "\n")
            f.write(f"Export Date: {datetime.now().isoformat()}\n")
            
            if metadata:
                f.write("\nMetadata:\n")
                for key, value in metadata.items():
                    f.write(f"  {key}: {value}\n")
                    
            f.write("\nChannels:\n")
            for w in waveforms:
                f.write(f"  Channel {w.channel}: {len(w.voltage)} samples @ {w.sample_rate} Sa/s\n")
                
            f.write("\n" + "=" * 40 + "\n\n")
            
            # Write data
            max_samples = max(len(w.time) for w in waveforms)
            base_waveform = next(w for w in waveforms if len(w.time) == max_samples)
            
            # Header line
            header = "Time".ljust(15)
            for w in waveforms:
                header += f"CH{w.channel}_Voltage".ljust(15)
            f.write(header + "\n")
            f.write("-" * len(header) + "\n")
            
            # Data lines
            for i in range(len(base_waveform.time)):
                line = f"{base_waveform.time[i]:14.6e} "
                
                for w in waveforms:
                    if i < len(w.voltage):
                        line += f"{w.voltage[i]:14.6e} "
                    else:
                        line += " " * 15
                        
                f.write(line + "\n")
                
        return True
        
    def _export_png(self, waveforms: List[WaveformData], filepath: str, metadata: Dict = None) -> bool:
        """Export as PNG plot"""
        plt.figure(figsize=(12, 8))
        
        for w in waveforms:
            plt.plot(w.time, w.voltage, label=f'CH{w.channel}', color=w.color)
            
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        plt.title('RTB2000 Waveform Export')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if metadata:
            plt.figtext(0.02, 0.02, f"Export: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fontsize=8)
            
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return True
        
    def _export_svg(self, waveforms: List[WaveformData], filepath: str, metadata: Dict = None) -> bool:
        """Export as SVG plot"""
        plt.figure(figsize=(12, 8))
        
        for w in waveforms:
            plt.plot(w.time, w.voltage, label=f'CH{w.channel}', color=w.color)
            
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        plt.title('RTB2000 Waveform Export')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filepath, format='svg', bbox_inches='tight')
        plt.close()
        
        return True
        
    def _export_pdf(self, waveforms: List[WaveformData], filepath: str, metadata: Dict = None) -> bool:
        """Export as PDF plot"""
        plt.figure(figsize=(12, 8))
        
        for w in waveforms:
            plt.plot(w.time, w.voltage, label=f'CH{w.channel}', color=w.color)
            
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        plt.title('RTB2000 Waveform Export')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if metadata:
            plt.figtext(0.02, 0.02, f"Export: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fontsize=8)
            
        plt.tight_layout()
        plt.savefig(filepath, format='pdf', bbox_inches='tight')
        plt.close()
        
        return True
        
    def _export_measurements_csv(self, measurements: List[MeasurementData], filepath: str) -> bool:
        """Export measurements to CSV"""
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Name', 'Value', 'Unit', 'Channel'])
            
            for m in measurements:
                writer.writerow([
                    m.timestamp.isoformat(),
                    m.name,
                    m.value,
                    m.unit,
                    m.channel
                ])
                
        return True
        
    def _export_measurements_json(self, measurements: List[MeasurementData], filepath: str) -> bool:
        """Export measurements to JSON"""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'measurements': [
                {
                    'name': m.name,
                    'value': m.value,
                    'unit': m.unit,
                    'channel': m.channel,
                    'timestamp': m.timestamp.isoformat()
                } for m in measurements
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        return True
        
    def _export_measurements_excel(self, measurements: List[MeasurementData], filepath: str) -> bool:
        """Export measurements to Excel"""
        try:
            data = []
            for m in measurements:
                data.append({
                    'Timestamp': m.timestamp,
                    'Name': m.name,
                    'Value': m.value,
                    'Unit': m.unit,
                    'Channel': m.channel
                })
                
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting measurements to Excel: {e}")
            return False
            
    def get_supported_formats(self) -> List[ExportFormat]:
        """Get list of supported export formats"""
        return list(self.supported_formats.keys())
        
    def clear_session_data(self):
        """Clear session data"""
        self.session_data = {
            'waveforms': [],
            'measurements': [],
            'screenshots': [],
            'session_start': datetime.now(),
            'export_count': 0
        }
