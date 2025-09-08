"""
Configuration Management System for RTB2000
Version 2.0 - September 8, 2025

Handles saving, loading, and managing instrument configurations
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ChannelConfig:
    """Configuration for a single channel"""
    enabled: bool = False
    scale: float = 1.0  # V/div
    position: float = 0.0  # divisions
    coupling: str = "DC"  # DC, AC, GND
    color: str = "#FFFF00"  # Display color
    label: str = ""  # Custom label
    
    
@dataclass 
class TimebaseConfig:
    """Timebase configuration"""
    scale: float = 1e-3  # s/div
    position: float = 0.0  # seconds
    mode: str = "MAIN"  # MAIN, ZOOM, ROLL
    reference: str = "CENTER"  # LEFT, CENTER, RIGHT


@dataclass
class TriggerConfig:
    """Trigger configuration"""
    source: str = "CH1"  # CH1, CH2, CH3, CH4, EXT, LINE
    level: float = 0.0  # volts
    slope: str = "POS"  # POS, NEG
    mode: str = "EDGE"  # EDGE, PULSE, VIDEO
    coupling: str = "DC"  # DC, AC, HF, LF
    holdoff: float = 0.0  # seconds


@dataclass
class DisplayConfig:
    """Display configuration"""
    grid_enabled: bool = True
    crosshair_enabled: bool = False
    persistence_enabled: bool = False
    cursors_enabled: bool = False
    measurement_mode: str = "None"
    max_points: int = 10000
    update_rate: int = 30
    theme: str = "dark"  # dark, light
    

@dataclass
class AcquisitionConfig:
    """Acquisition configuration"""
    mode: str = "NORMAL"  # NORMAL, AVERAGE, PEAK_DETECT
    sample_rate: float = 1e9  # Sa/s
    memory_depth: int = 1000000  # samples
    averages: int = 16  # for average mode


@dataclass
class RTB2000Configuration:
    """Complete RTB2000 configuration"""
    name: str = "Default"
    description: str = ""
    created: str = ""
    modified: str = ""
    version: str = "2.0"
    
    # Instrument settings
    channels: Dict[int, ChannelConfig] = None
    timebase: TimebaseConfig = None
    trigger: TriggerConfig = None
    acquisition: AcquisitionConfig = None
    display: DisplayConfig = None
    
    # Connection settings
    visa_resource: str = ""
    connection_timeout: int = 5000
    
    def __post_init__(self):
        """Initialize default configurations"""
        if self.channels is None:
            self.channels = {
                1: ChannelConfig(enabled=True, color="#FFFF00"),  # Yellow
                2: ChannelConfig(enabled=False, color="#00FFFF"), # Cyan
                3: ChannelConfig(enabled=False, color="#FF00FF"), # Magenta
                4: ChannelConfig(enabled=False, color="#00FF00")  # Green
            }
        
        if self.timebase is None:
            self.timebase = TimebaseConfig()
            
        if self.trigger is None:
            self.trigger = TriggerConfig()
            
        if self.acquisition is None:
            self.acquisition = AcquisitionConfig()
            
        if self.display is None:
            self.display = DisplayConfig()
            
        if not self.created:
            self.created = datetime.now().isoformat()
            
        self.modified = datetime.now().isoformat()


class ConfigurationManager:
    """Manages RTB2000 configurations"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory to store configurations
        """
        if config_dir is None:
            # Default to user's config directory
            config_dir = os.path.join(
                os.path.expanduser("~"), 
                ".rtb2000", 
                "configurations"
            )
            
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.current_config_file = self.config_dir / "current.json"
        self.presets_dir = self.config_dir / "presets"
        self.presets_dir.mkdir(exist_ok=True)
        
        # Current configuration
        self.current_config = RTB2000Configuration()
        
        # Load last configuration
        self.load_current()
        
    def save_current(self) -> bool:
        """
        Save current configuration
        
        Returns:
            bool: Success status
        """
        try:
            self.current_config.modified = datetime.now().isoformat()
            
            config_dict = self._config_to_dict(self.current_config)
            
            with open(self.current_config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error saving current configuration: {e}")
            return False
            
    def load_current(self) -> bool:
        """
        Load current configuration
        
        Returns:
            bool: Success status
        """
        try:
            if self.current_config_file.exists():
                with open(self.current_config_file, 'r') as f:
                    config_dict = json.load(f)
                    
                self.current_config = self._dict_to_config(config_dict)
                return True
            else:
                # Create default configuration
                self.current_config = RTB2000Configuration()
                self.save_current()
                return True
                
        except Exception as e:
            print(f"Error loading current configuration: {e}")
            self.current_config = RTB2000Configuration()
            return False
            
    def save_preset(self, name: str, description: str = "") -> bool:
        """
        Save current configuration as preset
        
        Args:
            name: Preset name
            description: Preset description
            
        Returns:
            bool: Success status
        """
        try:
            # Create preset configuration
            preset_config = RTB2000Configuration(
                name=name,
                description=description,
                channels=self.current_config.channels.copy(),
                timebase=self.current_config.timebase,
                trigger=self.current_config.trigger,
                acquisition=self.current_config.acquisition,
                display=self.current_config.display
            )
            
            # Save to preset file
            preset_file = self.presets_dir / f"{name}.json"
            config_dict = self._config_to_dict(preset_config)
            
            with open(preset_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error saving preset '{name}': {e}")
            return False
            
    def load_preset(self, name: str) -> bool:
        """
        Load preset configuration
        
        Args:
            name: Preset name
            
        Returns:
            bool: Success status
        """
        try:
            preset_file = self.presets_dir / f"{name}.json"
            
            if not preset_file.exists():
                return False
                
            with open(preset_file, 'r') as f:
                config_dict = json.load(f)
                
            preset_config = self._dict_to_config(config_dict)
            
            # Apply preset to current configuration
            self.current_config.channels = preset_config.channels
            self.current_config.timebase = preset_config.timebase
            self.current_config.trigger = preset_config.trigger
            self.current_config.acquisition = preset_config.acquisition
            self.current_config.display = preset_config.display
            
            # Update metadata
            self.current_config.modified = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            print(f"Error loading preset '{name}': {e}")
            return False
            
    def delete_preset(self, name: str) -> bool:
        """
        Delete preset configuration
        
        Args:
            name: Preset name
            
        Returns:
            bool: Success status
        """
        try:
            preset_file = self.presets_dir / f"{name}.json"
            
            if preset_file.exists():
                preset_file.unlink()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error deleting preset '{name}': {e}")
            return False
            
    def list_presets(self) -> List[Dict[str, Any]]:
        """
        List all available presets
        
        Returns:
            List of preset information dictionaries
        """
        presets = []
        
        try:
            for preset_file in self.presets_dir.glob("*.json"):
                with open(preset_file, 'r') as f:
                    config_dict = json.load(f)
                    
                preset_info = {
                    'name': config_dict.get('name', preset_file.stem),
                    'description': config_dict.get('description', ''),
                    'created': config_dict.get('created', ''),
                    'modified': config_dict.get('modified', ''),
                    'file': str(preset_file)
                }
                
                presets.append(preset_info)
                
        except Exception as e:
            print(f"Error listing presets: {e}")
            
        return sorted(presets, key=lambda x: x['name'])
        
    def export_configuration(self, filepath: str, include_presets: bool = False) -> bool:
        """
        Export configuration to file
        
        Args:
            filepath: Export file path
            include_presets: Whether to include all presets
            
        Returns:
            bool: Success status
        """
        try:
            export_data = {
                'current_config': self._config_to_dict(self.current_config),
                'export_date': datetime.now().isoformat(),
                'version': '2.0'
            }
            
            if include_presets:
                export_data['presets'] = []
                for preset_info in self.list_presets():
                    with open(preset_info['file'], 'r') as f:
                        preset_data = json.load(f)
                    export_data['presets'].append(preset_data)
                    
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False
            
    def import_configuration(self, filepath: str, import_presets: bool = False) -> bool:
        """
        Import configuration from file
        
        Args:
            filepath: Import file path
            import_presets: Whether to import presets
            
        Returns:
            bool: Success status
        """
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
                
            # Import current configuration
            if 'current_config' in import_data:
                self.current_config = self._dict_to_config(import_data['current_config'])
                
            # Import presets if requested
            if import_presets and 'presets' in import_data:
                for preset_data in import_data['presets']:
                    preset_name = preset_data.get('name', 'Imported')
                    preset_file = self.presets_dir / f"{preset_name}.json"
                    
                    with open(preset_file, 'w') as f:
                        json.dump(preset_data, f, indent=2)
                        
            return True
            
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False
            
    def get_current_config(self) -> RTB2000Configuration:
        """Get current configuration"""
        return self.current_config
        
    def update_channel_config(self, channel: int, **kwargs):
        """Update channel configuration"""
        if channel in self.current_config.channels:
            for key, value in kwargs.items():
                if hasattr(self.current_config.channels[channel], key):
                    setattr(self.current_config.channels[channel], key, value)
                    
    def update_timebase_config(self, **kwargs):
        """Update timebase configuration"""
        for key, value in kwargs.items():
            if hasattr(self.current_config.timebase, key):
                setattr(self.current_config.timebase, key, value)
                
    def update_trigger_config(self, **kwargs):
        """Update trigger configuration"""
        for key, value in kwargs.items():
            if hasattr(self.current_config.trigger, key):
                setattr(self.current_config.trigger, key, value)
                
    def update_display_config(self, **kwargs):
        """Update display configuration"""
        for key, value in kwargs.items():
            if hasattr(self.current_config.display, key):
                setattr(self.current_config.display, key, value)
                
    def _config_to_dict(self, config: RTB2000Configuration) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        config_dict = asdict(config)
        
        # Convert channel configs
        config_dict['channels'] = {
            str(k): asdict(v) for k, v in config.channels.items()
        }
        
        return config_dict
        
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> RTB2000Configuration:
        """Convert dictionary to configuration"""
        # Handle channels separately
        channels_data = config_dict.pop('channels', {})
        channels = {}
        
        for ch_str, ch_data in channels_data.items():
            ch_num = int(ch_str)
            channels[ch_num] = ChannelConfig(**ch_data)
            
        # Create other configs
        timebase = TimebaseConfig(**config_dict.pop('timebase', {}))
        trigger = TriggerConfig(**config_dict.pop('trigger', {}))
        acquisition = AcquisitionConfig(**config_dict.pop('acquisition', {}))
        display = DisplayConfig(**config_dict.pop('display', {}))
        
        # Create main config
        config = RTB2000Configuration(
            channels=channels,
            timebase=timebase,
            trigger=trigger,
            acquisition=acquisition,
            display=display,
            **config_dict
        )
        
        return config
