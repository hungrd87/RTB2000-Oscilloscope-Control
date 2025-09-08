#!/usr/bin/env python3
"""
RTB2000 Multi-Channel Controller Module
=======================================

Advanced multi-channel synchronization and control:
- Synchronized data acquisition across channels
- Cross-channel timing alignment and correlation
- Multi-channel measurement automation
- Channel group management and coordination
"""

import time
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QPushButton, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QGroupBox, QTabWidget, QTextEdit,
                            QTableWidget, QTableWidgetItem, QSlider,
                            QListWidget, QProgressBar, QSplitter)
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import logging
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from collections import defaultdict


class SyncMode(Enum):
    """Synchronization modes for multi-channel operations"""
    INDEPENDENT = "independent"
    TRIGGER_SYNC = "trigger_sync"
    SAMPLE_SYNC = "sample_sync"
    TIME_SYNC = "time_sync"
    PHASE_SYNC = "phase_sync"


class ChannelRole(Enum):
    """Roles for channels in synchronized operations"""
    MASTER = "master"
    SLAVE = "slave"
    REFERENCE = "reference"
    TRIGGER = "trigger"


class AcquisitionMode(Enum):
    """Data acquisition modes"""
    CONTINUOUS = "continuous"
    SINGLE_SHOT = "single_shot"
    SEGMENTED = "segmented"
    ROLL = "roll"


@dataclass
class ChannelConfig:
    """Configuration for a single channel"""
    channel_id: str
    enabled: bool = True
    role: ChannelRole = ChannelRole.SLAVE
    vertical_scale: float = 1.0  # V/div
    vertical_offset: float = 0.0  # V
    coupling: str = "DC"  # DC, AC, GND
    bandwidth_limit: Optional[float] = None  # Hz
    probe_attenuation: float = 1.0
    invert: bool = False
    label: str = ""


@dataclass
class TimingConfig:
    """Timing configuration for synchronized acquisition"""
    timebase: float = 1e-3  # s/div
    sample_rate: float = 1e6  # samples/second
    record_length: int = 1000  # samples
    delay: float = 0.0  # seconds
    pretrigger: float = 10.0  # percent
    acquisition_mode: AcquisitionMode = AcquisitionMode.SINGLE_SHOT


@dataclass
class SyncConfig:
    """Synchronization configuration"""
    sync_mode: SyncMode
    master_channel: str
    timing_tolerance: float = 1e-9  # seconds
    phase_alignment: bool = False
    trigger_coupling: bool = True
    auto_skew_correction: bool = True


@dataclass
class ChannelData:
    """Data from a single channel"""
    channel_id: str
    timestamp: datetime
    time_axis: np.ndarray
    voltage_data: np.ndarray
    sample_rate: float
    trigger_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiChannelData:
    """Synchronized data from multiple channels"""
    acquisition_id: str
    timestamp: datetime
    channels: Dict[str, ChannelData]
    sync_config: SyncConfig
    timing_config: TimingConfig
    trigger_info: Dict[str, Any] = field(default_factory=dict)
    sync_quality: Dict[str, float] = field(default_factory=dict)


class ChannelGroup(QObject):
    """Group of synchronized channels"""
    
    # Signals
    data_acquired = pyqtSignal(object)  # MultiChannelData
    sync_error = pyqtSignal(str, str)  # group_id, error_message
    status_changed = pyqtSignal(str, str)  # group_id, status
    
    def __init__(self, group_id: str, name: str = ""):
        super().__init__()
        self.group_id = group_id
        self.name = name or group_id
        self.logger = logging.getLogger(__name__)
        
        # Channel management
        self.channels: Dict[str, ChannelConfig] = {}
        self.sync_config = SyncConfig(
            sync_mode=SyncMode.TRIGGER_SYNC,
            master_channel="CH1"
        )
        self.timing_config = TimingConfig()
        
        # Acquisition state
        self.is_acquiring = False
        self.acquisition_thread: Optional[QThread] = None
        
        # Data storage
        self.last_acquisition: Optional[MultiChannelData] = None
        self.data_buffer: List[MultiChannelData] = []
        self.max_buffer_size = 100
        
        # Dependencies
        self.oscilloscope = None
        
        self.logger.info(f"Channel group '{self.name}' created")
    
    def add_channel(self, channel_config: ChannelConfig) -> bool:
        """Add a channel to the group"""
        try:
            if channel_config.channel_id in self.channels:
                raise ValueError(f"Channel '{channel_config.channel_id}' already in group")
            
            self.channels[channel_config.channel_id] = channel_config
            
            # Set first enabled channel as master if none exists
            if not self.sync_config.master_channel and channel_config.enabled:
                self.sync_config.master_channel = channel_config.channel_id
                channel_config.role = ChannelRole.MASTER
            
            self.logger.info(f"Added channel '{channel_config.channel_id}' to group '{self.name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add channel: {e}")
            return False
    
    def remove_channel(self, channel_id: str) -> bool:
        """Remove a channel from the group"""
        if channel_id in self.channels:
            del self.channels[channel_id]
            
            # Update master channel if removed
            if self.sync_config.master_channel == channel_id:
                enabled_channels = [ch_id for ch_id, config in self.channels.items() 
                                  if config.enabled]
                if enabled_channels:
                    self.sync_config.master_channel = enabled_channels[0]
                    self.channels[enabled_channels[0]].role = ChannelRole.MASTER
                else:
                    self.sync_config.master_channel = ""
            
            self.logger.info(f"Removed channel '{channel_id}' from group '{self.name}'")
            return True
        
        return False
    
    def set_sync_config(self, sync_config: SyncConfig) -> bool:
        """Set synchronization configuration"""
        try:
            # Validate master channel
            if (sync_config.master_channel and 
                sync_config.master_channel not in self.channels):
                raise ValueError(f"Master channel '{sync_config.master_channel}' not in group")
            
            self.sync_config = sync_config
            
            # Update channel roles
            for channel_id, config in self.channels.items():
                if channel_id == sync_config.master_channel:
                    config.role = ChannelRole.MASTER
                else:
                    config.role = ChannelRole.SLAVE
            
            self.logger.info(f"Updated sync config for group '{self.name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set sync config: {e}")
            return False
    
    def set_timing_config(self, timing_config: TimingConfig) -> bool:
        """Set timing configuration"""
        self.timing_config = timing_config
        self.logger.info(f"Updated timing config for group '{self.name}'")
        return True
    
    def start_acquisition(self) -> bool:
        """Start synchronized data acquisition"""
        try:
            if self.is_acquiring:
                raise ValueError("Acquisition already in progress")
            
            if not self.channels:
                raise ValueError("No channels configured")
            
            enabled_channels = [ch_id for ch_id, config in self.channels.items() 
                              if config.enabled]
            if not enabled_channels:
                raise ValueError("No enabled channels")
            
            # Setup oscilloscope for synchronized acquisition
            self._setup_synchronized_acquisition()
            
            # Start acquisition thread
            self.acquisition_thread = MultiChannelAcquisitionThread(self)
            self.acquisition_thread.data_acquired.connect(self._on_data_acquired)
            self.acquisition_thread.acquisition_error.connect(self._on_acquisition_error)
            self.acquisition_thread.start()
            
            self.is_acquiring = True
            self.status_changed.emit(self.group_id, "acquiring")
            
            self.logger.info(f"Started acquisition for group '{self.name}'")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start acquisition: {e}"
            self.logger.error(error_msg)
            self.sync_error.emit(self.group_id, error_msg)
            return False
    
    def stop_acquisition(self) -> bool:
        """Stop data acquisition"""
        if self.is_acquiring and self.acquisition_thread:
            self.acquisition_thread.stop()
            self.acquisition_thread.wait()
            self.acquisition_thread = None
            
            self.is_acquiring = False
            self.status_changed.emit(self.group_id, "stopped")
            
            self.logger.info(f"Stopped acquisition for group '{self.name}'")
            return True
        
        return False
    
    def acquire_single(self) -> Optional[MultiChannelData]:
        """Acquire a single synchronized measurement"""
        if self.is_acquiring:
            self.logger.warning("Cannot perform single acquisition while continuous acquisition is running")
            return None
        
        try:
            # Setup for single acquisition
            self._setup_synchronized_acquisition()
            
            # Perform acquisition
            acquisition_id = f"{self.group_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            data = self._perform_synchronized_acquisition(acquisition_id)
            
            if data:
                self.last_acquisition = data
                self._add_to_buffer(data)
                self.data_acquired.emit(data)
            
            return data
            
        except Exception as e:
            error_msg = f"Single acquisition failed: {e}"
            self.logger.error(error_msg)
            self.sync_error.emit(self.group_id, error_msg)
            return None
    
    def _setup_synchronized_acquisition(self):
        """Setup oscilloscope for synchronized acquisition"""
        if not self.oscilloscope:
            raise ValueError("No oscilloscope connected")
        
        # Configure timing
        self._configure_timebase()
        
        # Configure channels
        self._configure_channels()
        
        # Configure synchronization
        self._configure_synchronization()
        
        self.logger.debug(f"Configured synchronized acquisition for group '{self.name}'")
    
    def _configure_timebase(self):
        """Configure timebase and sampling"""
        # Set timebase
        if hasattr(self.oscilloscope, 'set_timebase'):
            self.oscilloscope.set_timebase(self.timing_config.timebase)
        
        # Set record length
        if hasattr(self.oscilloscope, 'set_record_length'):
            self.oscilloscope.set_record_length(self.timing_config.record_length)
        
        # Set sample rate
        if hasattr(self.oscilloscope, 'set_sample_rate'):
            self.oscilloscope.set_sample_rate(self.timing_config.sample_rate)
        
        self.logger.debug("Configured timebase")
    
    def _configure_channels(self):
        """Configure individual channels"""
        for channel_id, config in self.channels.items():
            if not config.enabled:
                continue
            
            # Set vertical scale
            if hasattr(self.oscilloscope, 'set_vertical_scale'):
                self.oscilloscope.set_vertical_scale(channel_id, config.vertical_scale)
            
            # Set vertical offset
            if hasattr(self.oscilloscope, 'set_vertical_offset'):
                self.oscilloscope.set_vertical_offset(channel_id, config.vertical_offset)
            
            # Set coupling
            if hasattr(self.oscilloscope, 'set_coupling'):
                self.oscilloscope.set_coupling(channel_id, config.coupling)
            
            # Set probe attenuation
            if hasattr(self.oscilloscope, 'set_probe_attenuation'):
                self.oscilloscope.set_probe_attenuation(channel_id, config.probe_attenuation)
            
            self.logger.debug(f"Configured channel {channel_id}")
    
    def _configure_synchronization(self):
        """Configure synchronization settings"""
        if self.sync_config.sync_mode == SyncMode.TRIGGER_SYNC:
            self._configure_trigger_sync()
        elif self.sync_config.sync_mode == SyncMode.SAMPLE_SYNC:
            self._configure_sample_sync()
        elif self.sync_config.sync_mode == SyncMode.TIME_SYNC:
            self._configure_time_sync()
        elif self.sync_config.sync_mode == SyncMode.PHASE_SYNC:
            self._configure_phase_sync()
        
        self.logger.debug(f"Configured {self.sync_config.sync_mode.value} synchronization")
    
    def _configure_trigger_sync(self):
        """Configure trigger-based synchronization"""
        # Set master channel as trigger source
        if hasattr(self.oscilloscope, 'set_trigger_source'):
            self.oscilloscope.set_trigger_source(self.sync_config.master_channel)
        
        # Enable all channels for simultaneous acquisition
        for channel_id, config in self.channels.items():
            if config.enabled and hasattr(self.oscilloscope, 'enable_channel'):
                self.oscilloscope.enable_channel(channel_id, True)
    
    def _configure_sample_sync(self):
        """Configure sample-based synchronization"""
        # Ensure all channels use the same sample rate
        for channel_id, config in self.channels.items():
            if config.enabled and hasattr(self.oscilloscope, 'set_sample_rate'):
                self.oscilloscope.set_sample_rate(self.timing_config.sample_rate, channel_id)
    
    def _configure_time_sync(self):
        """Configure time-based synchronization"""
        # Set precise timing alignment
        reference_time = datetime.now()
        
        for channel_id, config in self.channels.items():
            if config.enabled and hasattr(self.oscilloscope, 'set_timing_reference'):
                self.oscilloscope.set_timing_reference(channel_id, reference_time)
    
    def _configure_phase_sync(self):
        """Configure phase-based synchronization"""
        # Set phase alignment for AC signals
        if hasattr(self.oscilloscope, 'enable_phase_sync'):
            self.oscilloscope.enable_phase_sync(True)
            self.oscilloscope.set_phase_reference(self.sync_config.master_channel)
    
    def _perform_synchronized_acquisition(self, acquisition_id: str) -> Optional[MultiChannelData]:
        """Perform synchronized data acquisition"""
        try:
            # Trigger acquisition
            if hasattr(self.oscilloscope, 'trigger_single'):
                self.oscilloscope.trigger_single()
            
            # Wait for acquisition to complete
            timeout = 10.0  # seconds
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if hasattr(self.oscilloscope, 'is_acquisition_complete'):
                    if self.oscilloscope.is_acquisition_complete():
                        break
                time.sleep(0.01)
            else:
                raise TimeoutError("Acquisition timeout")
            
            # Collect data from all enabled channels
            channels_data = {}
            acquisition_time = datetime.now()
            
            for channel_id, config in self.channels.items():
                if not config.enabled:
                    continue
                
                # Get channel data
                if hasattr(self.oscilloscope, 'get_waveform_data'):
                    time_axis, voltage_data = self.oscilloscope.get_waveform_data(channel_id)
                else:
                    # Simulate data for testing
                    time_axis = np.linspace(0, self.timing_config.timebase * 10, 
                                          self.timing_config.record_length)
                    voltage_data = np.random.random(self.timing_config.record_length) * config.vertical_scale
                
                # Create channel data
                channel_data = ChannelData(
                    channel_id=channel_id,
                    timestamp=acquisition_time,
                    time_axis=time_axis,
                    voltage_data=voltage_data,
                    sample_rate=self.timing_config.sample_rate,
                    metadata={
                        'vertical_scale': config.vertical_scale,
                        'vertical_offset': config.vertical_offset,
                        'coupling': config.coupling,
                        'probe_attenuation': config.probe_attenuation
                    }
                )
                
                channels_data[channel_id] = channel_data
            
            # Perform synchronization analysis
            sync_quality = self._analyze_synchronization(channels_data)
            
            # Create multi-channel data
            multi_data = MultiChannelData(
                acquisition_id=acquisition_id,
                timestamp=acquisition_time,
                channels=channels_data,
                sync_config=self.sync_config,
                timing_config=self.timing_config,
                sync_quality=sync_quality
            )
            
            return multi_data
            
        except Exception as e:
            self.logger.error(f"Acquisition failed: {e}")
            return None
    
    def _analyze_synchronization(self, channels_data: Dict[str, ChannelData]) -> Dict[str, float]:
        """Analyze synchronization quality"""
        sync_quality = {}
        
        if len(channels_data) < 2:
            return sync_quality
        
        # Get reference channel (master)
        ref_channel_id = self.sync_config.master_channel
        if ref_channel_id not in channels_data:
            ref_channel_id = list(channels_data.keys())[0]
        
        ref_data = channels_data[ref_channel_id]
        
        # Analyze timing alignment
        for channel_id, channel_data in channels_data.items():
            if channel_id == ref_channel_id:
                sync_quality[f"{channel_id}_timing"] = 1.0
                continue
            
            # Calculate cross-correlation for timing alignment
            correlation = np.correlate(ref_data.voltage_data, 
                                     channel_data.voltage_data, mode='full')
            max_corr_idx = np.argmax(np.abs(correlation))
            
            # Calculate timing offset
            time_offset = (max_corr_idx - len(ref_data.voltage_data) + 1) / ref_data.sample_rate
            
            # Calculate sync quality (inverse of timing offset)
            timing_quality = 1.0 / (1.0 + abs(time_offset) / self.sync_config.timing_tolerance)
            sync_quality[f"{channel_id}_timing"] = timing_quality
            
            # Calculate amplitude correlation
            amplitude_corr = np.corrcoef(ref_data.voltage_data, channel_data.voltage_data)[0, 1]
            sync_quality[f"{channel_id}_amplitude"] = abs(amplitude_corr)
        
        return sync_quality
    
    def _add_to_buffer(self, data: MultiChannelData):
        """Add data to buffer"""
        self.data_buffer.append(data)
        
        # Maintain buffer size
        if len(self.data_buffer) > self.max_buffer_size:
            self.data_buffer.pop(0)
    
    def _on_data_acquired(self, data: MultiChannelData):
        """Handle data acquired from thread"""
        self.last_acquisition = data
        self._add_to_buffer(data)
        self.data_acquired.emit(data)
    
    def _on_acquisition_error(self, error: str):
        """Handle acquisition error from thread"""
        self.sync_error.emit(self.group_id, error)
    
    def get_enabled_channels(self) -> List[str]:
        """Get list of enabled channels"""
        return [ch_id for ch_id, config in self.channels.items() if config.enabled]
    
    def get_sync_quality_summary(self) -> Dict[str, float]:
        """Get sync quality summary from last acquisition"""
        if not self.last_acquisition:
            return {}
        
        return self.last_acquisition.sync_quality
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export group configuration"""
        return {
            'group_id': self.group_id,
            'name': self.name,
            'channels': {
                ch_id: {
                    'channel_id': config.channel_id,
                    'enabled': config.enabled,
                    'role': config.role.value,
                    'vertical_scale': config.vertical_scale,
                    'vertical_offset': config.vertical_offset,
                    'coupling': config.coupling,
                    'bandwidth_limit': config.bandwidth_limit,
                    'probe_attenuation': config.probe_attenuation,
                    'invert': config.invert,
                    'label': config.label
                }
                for ch_id, config in self.channels.items()
            },
            'sync_config': {
                'sync_mode': self.sync_config.sync_mode.value,
                'master_channel': self.sync_config.master_channel,
                'timing_tolerance': self.sync_config.timing_tolerance,
                'phase_alignment': self.sync_config.phase_alignment,
                'trigger_coupling': self.sync_config.trigger_coupling,
                'auto_skew_correction': self.sync_config.auto_skew_correction
            },
            'timing_config': {
                'timebase': self.timing_config.timebase,
                'sample_rate': self.timing_config.sample_rate,
                'record_length': self.timing_config.record_length,
                'delay': self.timing_config.delay,
                'pretrigger': self.timing_config.pretrigger,
                'acquisition_mode': self.timing_config.acquisition_mode.value
            }
        }


class MultiChannelAcquisitionThread(QThread):
    """Thread for continuous multi-channel acquisition"""
    
    data_acquired = pyqtSignal(object)  # MultiChannelData
    acquisition_error = pyqtSignal(str)  # error_message
    
    def __init__(self, channel_group: ChannelGroup):
        super().__init__()
        self.channel_group = channel_group
        self.logger = logging.getLogger(__name__)
        self.running = True
        
    def run(self):
        """Run continuous acquisition"""
        acquisition_count = 0
        
        while self.running:
            try:
                # Perform acquisition
                acquisition_id = f"{self.channel_group.group_id}_{acquisition_count}"
                data = self.channel_group._perform_synchronized_acquisition(acquisition_id)
                
                if data:
                    self.data_acquired.emit(data)
                    acquisition_count += 1
                
                # Short delay between acquisitions
                self.msleep(100)
                
            except Exception as e:
                error_msg = f"Acquisition error: {e}"
                self.logger.error(error_msg)
                self.acquisition_error.emit(error_msg)
                self.msleep(1000)  # Wait longer after error
    
    def stop(self):
        """Stop the acquisition thread"""
        self.running = False


class MultiChannelController(QObject):
    """Controller for managing multiple channel groups"""
    
    # Signals
    group_registered = pyqtSignal(str)  # group_id
    group_data_acquired = pyqtSignal(str, object)  # group_id, MultiChannelData
    group_error = pyqtSignal(str, str)  # group_id, error_message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Group management
        self.channel_groups: Dict[str, ChannelGroup] = {}
        
        # Global settings
        self.global_sync_enabled = False
        self.master_group: Optional[str] = None
        
        # Dependencies
        self.oscilloscope = None
        
        self.logger.info("Multi-Channel Controller initialized")
    
    def create_channel_group(self, group_id: str, name: str = "") -> Optional[ChannelGroup]:
        """Create a new channel group"""
        try:
            if group_id in self.channel_groups:
                raise ValueError(f"Group '{group_id}' already exists")
            
            group = ChannelGroup(group_id, name)
            group.oscilloscope = self.oscilloscope
            
            # Connect signals
            group.data_acquired.connect(lambda data: self.group_data_acquired.emit(group_id, data))
            group.sync_error.connect(lambda error: self.group_error.emit(group_id, error))
            
            self.channel_groups[group_id] = group
            self.group_registered.emit(group_id)
            
            self.logger.info(f"Created channel group '{name or group_id}'")
            return group
            
        except Exception as e:
            self.logger.error(f"Failed to create channel group: {e}")
            return None
    
    def get_channel_group(self, group_id: str) -> Optional[ChannelGroup]:
        """Get a channel group"""
        return self.channel_groups.get(group_id)
    
    def remove_channel_group(self, group_id: str) -> bool:
        """Remove a channel group"""
        if group_id in self.channel_groups:
            group = self.channel_groups[group_id]
            group.stop_acquisition()
            del self.channel_groups[group_id]
            
            self.logger.info(f"Removed channel group '{group_id}'")
            return True
        
        return False
    
    def list_channel_groups(self) -> List[str]:
        """List all channel groups"""
        return list(self.channel_groups.keys())
    
    def start_all_acquisitions(self) -> Dict[str, bool]:
        """Start acquisition for all groups"""
        results = {}
        
        for group_id, group in self.channel_groups.items():
            results[group_id] = group.start_acquisition()
        
        return results
    
    def stop_all_acquisitions(self) -> Dict[str, bool]:
        """Stop acquisition for all groups"""
        results = {}
        
        for group_id, group in self.channel_groups.items():
            results[group_id] = group.stop_acquisition()
        
        return results
    
    def get_all_sync_quality(self) -> Dict[str, Dict[str, float]]:
        """Get sync quality for all groups"""
        quality_data = {}
        
        for group_id, group in self.channel_groups.items():
            quality_data[group_id] = group.get_sync_quality_summary()
        
        return quality_data


class MultiChannelWidget(QWidget):
    """Widget for multi-channel control"""
    
    def __init__(self, controller: MultiChannelController):
        super().__init__()
        self.controller = controller
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the multi-channel UI"""
        layout = QVBoxLayout(self)
        
        # Create splitter for groups and details
        splitter = QSplitter()
        
        # Groups panel
        groups_widget = QWidget()
        self.setup_groups_panel(groups_widget)
        splitter.addWidget(groups_widget)
        
        # Details panel
        details_widget = QWidget()
        self.setup_details_panel(details_widget)
        splitter.addWidget(details_widget)
        
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_all_btn = QPushButton("Start All")
        control_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QPushButton("Stop All")
        control_layout.addWidget(self.stop_all_btn)
        
        control_layout.addStretch()
        
        self.create_group_btn = QPushButton("Create Group")
        control_layout.addWidget(self.create_group_btn)
        
        layout.addLayout(control_layout)
    
    def setup_groups_panel(self, parent):
        """Setup groups panel"""
        layout = QVBoxLayout(parent)
        
        layout.addWidget(QLabel("Channel Groups:"))
        
        self.groups_list = QListWidget()
        layout.addWidget(self.groups_list)
        
        # Group controls
        group_controls = QHBoxLayout()
        
        self.start_group_btn = QPushButton("Start")
        group_controls.addWidget(self.start_group_btn)
        
        self.stop_group_btn = QPushButton("Stop")
        group_controls.addWidget(self.stop_group_btn)
        
        self.remove_group_btn = QPushButton("Remove")
        group_controls.addWidget(self.remove_group_btn)
        
        layout.addLayout(group_controls)
    
    def setup_details_panel(self, parent):
        """Setup details panel"""
        layout = QVBoxLayout(parent)
        
        # Create tabs for different views
        tab_widget = QTabWidget()
        
        # Channels tab
        channels_tab = QWidget()
        self.setup_channels_tab(channels_tab)
        tab_widget.addTab(channels_tab, "Channels")
        
        # Sync Quality tab
        sync_tab = QWidget()
        self.setup_sync_tab(sync_tab)
        tab_widget.addTab(sync_tab, "Sync Quality")
        
        # Configuration tab
        config_tab = QWidget()
        self.setup_config_tab(config_tab)
        tab_widget.addTab(config_tab, "Configuration")
        
        layout.addWidget(tab_widget)
    
    def setup_channels_tab(self, parent):
        """Setup channels configuration tab"""
        layout = QVBoxLayout(parent)
        
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(6)
        self.channels_table.setHorizontalHeaderLabels([
            'Channel', 'Enabled', 'Role', 'Scale', 'Offset', 'Coupling'
        ])
        layout.addWidget(self.channels_table)
    
    def setup_sync_tab(self, parent):
        """Setup sync quality tab"""
        layout = QVBoxLayout(parent)
        
        self.sync_table = QTableWidget()
        self.sync_table.setColumnCount(3)
        self.sync_table.setHorizontalHeaderLabels([
            'Channel', 'Timing Quality', 'Amplitude Correlation'
        ])
        layout.addWidget(self.sync_table)
        
        # Sync quality summary
        self.sync_summary = QTextEdit()
        self.sync_summary.setMaximumHeight(100)
        self.sync_summary.setReadOnly(True)
        layout.addWidget(self.sync_summary)
    
    def setup_config_tab(self, parent):
        """Setup configuration tab"""
        layout = QVBoxLayout(parent)
        
        # Sync mode selection
        sync_layout = QHBoxLayout()
        sync_layout.addWidget(QLabel("Sync Mode:"))
        
        self.sync_mode_combo = QComboBox()
        self.sync_mode_combo.addItems([
            "Independent", "Trigger Sync", "Sample Sync", "Time Sync", "Phase Sync"
        ])
        sync_layout.addWidget(self.sync_mode_combo)
        
        layout.addLayout(sync_layout)
        
        # Master channel selection
        master_layout = QHBoxLayout()
        master_layout.addWidget(QLabel("Master Channel:"))
        
        self.master_channel_combo = QComboBox()
        master_layout.addWidget(self.master_channel_combo)
        
        layout.addLayout(master_layout)
        
        # Timing configuration
        timing_group = QGroupBox("Timing Configuration")
        timing_layout = QVBoxLayout(timing_group)
        
        # Timebase
        timebase_layout = QHBoxLayout()
        timebase_layout.addWidget(QLabel("Timebase (s/div):"))
        
        self.timebase_spin = QDoubleSpinBox()
        self.timebase_spin.setRange(1e-9, 10.0)
        self.timebase_spin.setValue(1e-3)
        self.timebase_spin.setDecimals(9)
        timebase_layout.addWidget(self.timebase_spin)
        
        timing_layout.addLayout(timebase_layout)
        
        # Sample rate
        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("Sample Rate (S/s):"))
        
        self.sample_rate_spin = QDoubleSpinBox()
        self.sample_rate_spin.setRange(1e3, 1e9)
        self.sample_rate_spin.setValue(1e6)
        sample_rate_layout.addWidget(self.sample_rate_spin)
        
        timing_layout.addLayout(sample_rate_layout)
        
        layout.addWidget(timing_group)
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        # Controller signals
        self.controller.group_registered.connect(self.update_groups_list)
        self.controller.group_data_acquired.connect(self.on_group_data_acquired)
        self.controller.group_error.connect(self.on_group_error)
        
        # Button connections
        self.start_all_btn.clicked.connect(self.start_all_groups)
        self.stop_all_btn.clicked.connect(self.stop_all_groups)
        self.create_group_btn.clicked.connect(self.create_new_group)
        
        # Group list selection
        self.groups_list.currentTextChanged.connect(self.on_group_selected)
    
    def update_groups_list(self):
        """Update the groups list"""
        self.groups_list.clear()
        groups = self.controller.list_channel_groups()
        self.groups_list.addItems(groups)
    
    def start_all_groups(self):
        """Start acquisition for all groups"""
        results = self.controller.start_all_acquisitions()
        success_count = sum(1 for success in results.values() if success)
        self.sync_summary.append(f"Started {success_count}/{len(results)} groups")
    
    def stop_all_groups(self):
        """Stop acquisition for all groups"""
        results = self.controller.stop_all_acquisitions()
        success_count = sum(1 for success in results.values() if success)
        self.sync_summary.append(f"Stopped {success_count}/{len(results)} groups")
    
    def create_new_group(self):
        """Create a new channel group"""
        import random
        group_id = f"group_{random.randint(1000, 9999)}"
        group = self.controller.create_channel_group(group_id, f"Group {group_id}")
        
        if group:
            # Add some default channels
            for ch_id in ["CH1", "CH2"]:
                config = ChannelConfig(channel_id=ch_id, enabled=True)
                group.add_channel(config)
            
            self.sync_summary.append(f"Created group: {group_id}")
    
    def on_group_selected(self, group_id: str):
        """Handle group selection"""
        if not group_id:
            return
        
        group = self.controller.get_channel_group(group_id)
        if group:
            self.update_channels_display(group)
            self.update_sync_quality_display(group)
    
    def update_channels_display(self, group: ChannelGroup):
        """Update channels display"""
        channels = group.channels
        
        self.channels_table.setRowCount(len(channels))
        
        for row, (channel_id, config) in enumerate(channels.items()):
            self.channels_table.setItem(row, 0, QTableWidgetItem(channel_id))
            
            enabled_item = QTableWidgetItem("Yes" if config.enabled else "No")
            self.channels_table.setItem(row, 1, enabled_item)
            
            self.channels_table.setItem(row, 2, QTableWidgetItem(config.role.value))
            self.channels_table.setItem(row, 3, QTableWidgetItem(f"{config.vertical_scale:.3f}"))
            self.channels_table.setItem(row, 4, QTableWidgetItem(f"{config.vertical_offset:.3f}"))
            self.channels_table.setItem(row, 5, QTableWidgetItem(config.coupling))
        
        self.channels_table.resizeColumnsToContents()
    
    def update_sync_quality_display(self, group: ChannelGroup):
        """Update sync quality display"""
        sync_quality = group.get_sync_quality_summary()
        
        # Extract channel data
        channels = set()
        for key in sync_quality.keys():
            if '_' in key:
                channel = key.split('_')[0]
                channels.add(channel)
        
        channels = sorted(channels)
        self.sync_table.setRowCount(len(channels))
        
        for row, channel in enumerate(channels):
            timing_key = f"{channel}_timing"
            amplitude_key = f"{channel}_amplitude"
            
            self.sync_table.setItem(row, 0, QTableWidgetItem(channel))
            
            timing_quality = sync_quality.get(timing_key, 0.0)
            self.sync_table.setItem(row, 1, QTableWidgetItem(f"{timing_quality:.3f}"))
            
            amplitude_corr = sync_quality.get(amplitude_key, 0.0)
            self.sync_table.setItem(row, 2, QTableWidgetItem(f"{amplitude_corr:.3f}"))
        
        self.sync_table.resizeColumnsToContents()
    
    def on_group_data_acquired(self, group_id: str, data: MultiChannelData):
        """Handle group data acquired"""
        # Update displays if this group is selected
        current_group = self.groups_list.currentItem()
        if current_group and current_group.text() == group_id:
            group = self.controller.get_channel_group(group_id)
            if group:
                self.update_sync_quality_display(group)
    
    def on_group_error(self, group_id: str, error: str):
        """Handle group error"""
        self.sync_summary.append(f"Error in {group_id}: {error}")
