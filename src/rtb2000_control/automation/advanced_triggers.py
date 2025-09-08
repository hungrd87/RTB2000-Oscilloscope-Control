#!/usr/bin/env python3
"""
RTB2000 Advanced Trigger Manager Module
=======================================

Advanced trigger system for complex measurement scenarios:
- Complex trigger conditions (pattern, sequence, protocol)
- Multi-channel trigger logic with Boolean operations
- Trigger sequences for multi-step measurements
- Event-based trigger automation
"""

import time
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QPushButton, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QGroupBox, QTabWidget, QTextEdit,
                            QTableWidget, QTableWidgetItem, QSlider,
                            QButtonGroup, QRadioButton)
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from dataclasses import dataclass, field
from enum import Enum
import json


class TriggerType(Enum):
    """Types of trigger conditions"""
    EDGE = "edge"
    LEVEL = "level"
    PULSE_WIDTH = "pulse_width"
    PATTERN = "pattern"
    SEQUENCE = "sequence"
    PROTOCOL = "protocol"
    VIDEO = "video"
    RUNT = "runt"
    TIMEOUT = "timeout"
    LOGIC = "logic"


class TriggerSlope(Enum):
    """Trigger slope options"""
    RISING = "rising"
    FALLING = "falling"
    EITHER = "either"


class TriggerCoupling(Enum):
    """Trigger coupling options"""
    DC = "dc"
    AC = "ac"
    LF_REJECT = "lf_reject"
    HF_REJECT = "hf_reject"


class LogicOperation(Enum):
    """Logic operations for multi-channel triggers"""
    AND = "and"
    OR = "or"
    XOR = "xor"
    NAND = "nand"
    NOR = "nor"


class TriggerMode(Enum):
    """Trigger modes"""
    AUTO = "auto"
    NORMAL = "normal"
    SINGLE = "single"
    FORCE = "force"


@dataclass
class TriggerCondition:
    """Single trigger condition"""
    condition_id: str
    trigger_type: TriggerType
    channel: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""


@dataclass
class AdvancedTrigger:
    """Advanced trigger configuration"""
    trigger_id: str
    name: str
    trigger_mode: TriggerMode = TriggerMode.AUTO
    conditions: List[TriggerCondition] = field(default_factory=list)
    logic_operation: LogicOperation = LogicOperation.AND
    holdoff_time: float = 0.0  # seconds
    timeout: float = 1.0  # seconds
    enabled: bool = True


class PatternTrigger:
    """Pattern trigger for digital channels"""
    
    def __init__(self):
        self.pattern: Dict[str, str] = {}  # channel -> state ('0', '1', 'X')
        self.pattern_length: int = 1
        self.pattern_type: str = "equal"  # equal, not_equal, greater, less
    
    def set_channel_pattern(self, channel: str, pattern: str):
        """Set pattern for a channel"""
        self.pattern[channel] = pattern
    
    def get_pattern_string(self) -> str:
        """Get pattern as string"""
        channels = sorted(self.pattern.keys())
        return ''.join(self.pattern.get(ch, 'X') for ch in channels)


class SequenceTrigger:
    """Sequence trigger for multi-step triggers"""
    
    def __init__(self):
        self.steps: List[TriggerCondition] = []
        self.step_timeouts: List[float] = []
        self.reset_on_timeout: bool = True
    
    def add_step(self, condition: TriggerCondition, timeout: float = 1.0):
        """Add a step to the sequence"""
        self.steps.append(condition)
        self.step_timeouts.append(timeout)
    
    def clear_steps(self):
        """Clear all steps"""
        self.steps.clear()
        self.step_timeouts.clear()


class ProtocolTrigger:
    """Protocol-specific trigger"""
    
    def __init__(self, protocol: str):
        self.protocol = protocol  # I2C, SPI, UART, CAN, etc.
        self.protocol_settings: Dict[str, Any] = {}
        self.trigger_condition: str = "start"  # start, stop, address, data, error
        self.data_pattern: str = ""
        self.address_pattern: str = ""
    
    def set_i2c_settings(self, sda_channel: str, scl_channel: str, 
                        address: str = "", data: str = ""):
        """Configure I2C trigger settings"""
        self.protocol_settings = {
            'sda_channel': sda_channel,
            'scl_channel': scl_channel,
            'address': address,
            'data': data
        }
    
    def set_spi_settings(self, miso_channel: str, mosi_channel: str,
                        clk_channel: str, cs_channel: str = "", data: str = ""):
        """Configure SPI trigger settings"""
        self.protocol_settings = {
            'miso_channel': miso_channel,
            'mosi_channel': mosi_channel,
            'clk_channel': clk_channel,
            'cs_channel': cs_channel,
            'data': data
        }
    
    def set_uart_settings(self, data_channel: str, baud_rate: int,
                         data_bits: int = 8, parity: str = "none",
                         stop_bits: int = 1, data_pattern: str = ""):
        """Configure UART trigger settings"""
        self.protocol_settings = {
            'data_channel': data_channel,
            'baud_rate': baud_rate,
            'data_bits': data_bits,
            'parity': parity,
            'stop_bits': stop_bits,
            'data_pattern': data_pattern
        }


class AdvancedTriggerManager(QObject):
    """Manager for advanced trigger configurations"""
    
    # Signals
    trigger_registered = pyqtSignal(str)  # trigger_id
    trigger_activated = pyqtSignal(str)  # trigger_id
    trigger_fired = pyqtSignal(str, dict)  # trigger_id, event_data
    trigger_timeout = pyqtSignal(str)  # trigger_id
    trigger_error = pyqtSignal(str, str)  # trigger_id, error_message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Trigger management
        self.triggers: Dict[str, AdvancedTrigger] = {}
        self.active_trigger: Optional[str] = None
        
        # Pattern triggers
        self.pattern_triggers: Dict[str, PatternTrigger] = {}
        
        # Sequence triggers
        self.sequence_triggers: Dict[str, SequenceTrigger] = {}
        
        # Protocol triggers
        self.protocol_triggers: Dict[str, ProtocolTrigger] = {}
        
        # Monitoring
        self.trigger_timer = QTimer()
        self.trigger_timer.timeout.connect(self._check_trigger_conditions)
        
        # Dependencies
        self.oscilloscope = None
        
        self.logger.info("Advanced Trigger Manager initialized")
    
    def register_trigger(self, trigger: AdvancedTrigger) -> bool:
        """Register an advanced trigger"""
        try:
            if trigger.trigger_id in self.triggers:
                raise ValueError(f"Trigger '{trigger.trigger_id}' already registered")
            
            self.triggers[trigger.trigger_id] = trigger
            self.trigger_registered.emit(trigger.trigger_id)
            
            self.logger.info(f"Registered trigger '{trigger.name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register trigger: {e}")
            return False
    
    def activate_trigger(self, trigger_id: str) -> bool:
        """Activate a trigger"""
        try:
            if trigger_id not in self.triggers:
                raise ValueError(f"Trigger '{trigger_id}' not found")
            
            trigger = self.triggers[trigger_id]
            if not trigger.enabled:
                raise ValueError(f"Trigger '{trigger_id}' is disabled")
            
            # Deactivate current trigger
            if self.active_trigger:
                self.deactivate_trigger()
            
            # Setup trigger conditions
            self._setup_trigger_conditions(trigger)
            
            self.active_trigger = trigger_id
            self.trigger_activated.emit(trigger_id)
            
            # Start monitoring
            self.trigger_timer.start(50)  # Check every 50ms
            
            self.logger.info(f"Activated trigger '{trigger.name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate trigger: {e}")
            return False
    
    def deactivate_trigger(self) -> bool:
        """Deactivate the current trigger"""
        if self.active_trigger:
            self.trigger_timer.stop()
            self.active_trigger = None
            self.logger.info("Deactivated trigger")
            return True
        return False
    
    def create_edge_trigger(self, trigger_id: str, name: str, channel: str,
                          slope: TriggerSlope, level: float,
                          coupling: TriggerCoupling = TriggerCoupling.DC) -> AdvancedTrigger:
        """Create an edge trigger"""
        condition = TriggerCondition(
            condition_id=f"{trigger_id}_edge",
            trigger_type=TriggerType.EDGE,
            channel=channel,
            parameters={
                'slope': slope.value,
                'level': level,
                'coupling': coupling.value
            }
        )
        
        trigger = AdvancedTrigger(
            trigger_id=trigger_id,
            name=name,
            conditions=[condition]
        )
        
        return trigger
    
    def create_pulse_width_trigger(self, trigger_id: str, name: str, channel: str,
                                 condition: str, width_min: float, width_max: float,
                                 level: float) -> AdvancedTrigger:
        """Create a pulse width trigger"""
        condition_obj = TriggerCondition(
            condition_id=f"{trigger_id}_pulse",
            trigger_type=TriggerType.PULSE_WIDTH,
            channel=channel,
            parameters={
                'condition': condition,  # greater, less, between, outside
                'width_min': width_min,
                'width_max': width_max,
                'level': level
            }
        )
        
        trigger = AdvancedTrigger(
            trigger_id=trigger_id,
            name=name,
            conditions=[condition_obj]
        )
        
        return trigger
    
    def create_pattern_trigger(self, trigger_id: str, name: str,
                             pattern: PatternTrigger) -> AdvancedTrigger:
        """Create a pattern trigger"""
        condition = TriggerCondition(
            condition_id=f"{trigger_id}_pattern",
            trigger_type=TriggerType.PATTERN,
            channel="DIGITAL",
            parameters={
                'pattern': pattern.get_pattern_string(),
                'pattern_type': pattern.pattern_type,
                'channels': list(pattern.pattern.keys())
            }
        )
        
        trigger = AdvancedTrigger(
            trigger_id=trigger_id,
            name=name,
            conditions=[condition]
        )
        
        self.pattern_triggers[trigger_id] = pattern
        return trigger
    
    def create_sequence_trigger(self, trigger_id: str, name: str,
                              sequence: SequenceTrigger) -> AdvancedTrigger:
        """Create a sequence trigger"""
        trigger = AdvancedTrigger(
            trigger_id=trigger_id,
            name=name,
            conditions=sequence.steps.copy()
        )
        
        self.sequence_triggers[trigger_id] = sequence
        return trigger
    
    def create_protocol_trigger(self, trigger_id: str, name: str,
                              protocol: ProtocolTrigger) -> AdvancedTrigger:
        """Create a protocol trigger"""
        condition = TriggerCondition(
            condition_id=f"{trigger_id}_protocol",
            trigger_type=TriggerType.PROTOCOL,
            channel="PROTOCOL",
            parameters={
                'protocol': protocol.protocol,
                'condition': protocol.trigger_condition,
                'settings': protocol.protocol_settings,
                'data_pattern': protocol.data_pattern,
                'address_pattern': protocol.address_pattern
            }
        )
        
        trigger = AdvancedTrigger(
            trigger_id=trigger_id,
            name=name,
            conditions=[condition]
        )
        
        self.protocol_triggers[trigger_id] = protocol
        return trigger
    
    def create_multi_channel_trigger(self, trigger_id: str, name: str,
                                   conditions: List[TriggerCondition],
                                   logic_op: LogicOperation) -> AdvancedTrigger:
        """Create a multi-channel logic trigger"""
        trigger = AdvancedTrigger(
            trigger_id=trigger_id,
            name=name,
            conditions=conditions,
            logic_operation=logic_op
        )
        
        return trigger
    
    def _setup_trigger_conditions(self, trigger: AdvancedTrigger):
        """Setup trigger conditions on oscilloscope"""
        # This would interface with the actual oscilloscope
        # For now, we'll simulate the setup
        self.logger.debug(f"Setting up trigger conditions for '{trigger.name}'")
        
        for condition in trigger.conditions:
            self._setup_single_condition(condition)
    
    def _setup_single_condition(self, condition: TriggerCondition):
        """Setup a single trigger condition"""
        if condition.trigger_type == TriggerType.EDGE:
            self._setup_edge_trigger(condition)
        elif condition.trigger_type == TriggerType.PULSE_WIDTH:
            self._setup_pulse_width_trigger(condition)
        elif condition.trigger_type == TriggerType.PATTERN:
            self._setup_pattern_trigger(condition)
        elif condition.trigger_type == TriggerType.PROTOCOL:
            self._setup_protocol_trigger(condition)
        # Add more trigger types as needed
    
    def _setup_edge_trigger(self, condition: TriggerCondition):
        """Setup edge trigger on oscilloscope"""
        params = condition.parameters
        # Simulate SCPI commands
        commands = [
            f"TRIG:SOUR {condition.channel}",
            f"TRIG:EDGE:SLOP {params['slope']}",
            f"TRIG:LEV {params['level']}",
            f"TRIG:COUP {params['coupling']}"
        ]
        self.logger.debug(f"Edge trigger setup: {commands}")
    
    def _setup_pulse_width_trigger(self, condition: TriggerCondition):
        """Setup pulse width trigger on oscilloscope"""
        params = condition.parameters
        commands = [
            f"TRIG:SOUR {condition.channel}",
            "TRIG:TYPE PWID",
            f"TRIG:PWID:COND {params['condition']}",
            f"TRIG:PWID:WMIN {params['width_min']}",
            f"TRIG:PWID:WMAX {params['width_max']}",
            f"TRIG:LEV {params['level']}"
        ]
        self.logger.debug(f"Pulse width trigger setup: {commands}")
    
    def _setup_pattern_trigger(self, condition: TriggerCondition):
        """Setup pattern trigger on oscilloscope"""
        params = condition.parameters
        commands = [
            "TRIG:TYPE PATT",
            f"TRIG:PATT:PATT '{params['pattern']}'",
            f"TRIG:PATT:COND {params['pattern_type']}"
        ]
        self.logger.debug(f"Pattern trigger setup: {commands}")
    
    def _setup_protocol_trigger(self, condition: TriggerCondition):
        """Setup protocol trigger on oscilloscope"""
        params = condition.parameters
        protocol = params['protocol']
        
        if protocol.upper() == 'I2C':
            commands = [
                "TRIG:TYPE PROT",
                "TRIG:PROT:TYPE I2C",
                f"TRIG:PROT:I2C:SDA {params['settings']['sda_channel']}",
                f"TRIG:PROT:I2C:SCL {params['settings']['scl_channel']}",
                f"TRIG:PROT:I2C:COND {params['condition']}"
            ]
        elif protocol.upper() == 'SPI':
            commands = [
                "TRIG:TYPE PROT",
                "TRIG:PROT:TYPE SPI",
                f"TRIG:PROT:SPI:MISO {params['settings']['miso_channel']}",
                f"TRIG:PROT:SPI:MOSI {params['settings']['mosi_channel']}",
                f"TRIG:PROT:SPI:CLK {params['settings']['clk_channel']}"
            ]
        else:
            commands = [f"# Unknown protocol: {protocol}"]
        
        self.logger.debug(f"Protocol trigger setup: {commands}")
    
    def _check_trigger_conditions(self):
        """Check if trigger conditions are met"""
        if not self.active_trigger:
            return
        
        trigger = self.triggers[self.active_trigger]
        
        # Simulate trigger checking
        # In real implementation, this would query the oscilloscope
        if self._simulate_trigger_check(trigger):
            event_data = {
                'trigger_id': self.active_trigger,
                'timestamp': datetime.now().isoformat(),
                'conditions_met': [c.condition_id for c in trigger.conditions]
            }
            
            self.trigger_fired.emit(self.active_trigger, event_data)
            
            # Single shot triggers stop after firing
            if trigger.trigger_mode == TriggerMode.SINGLE:
                self.deactivate_trigger()
    
    def _simulate_trigger_check(self, trigger: AdvancedTrigger) -> bool:
        """Simulate trigger condition checking"""
        # Simulate random trigger events for testing
        import random
        return random.random() < 0.01  # 1% chance per check
    
    def get_trigger_list(self) -> List[str]:
        """Get list of registered triggers"""
        return list(self.triggers.keys())
    
    def get_trigger_info(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """Get trigger information"""
        if trigger_id not in self.triggers:
            return None
        
        trigger = self.triggers[trigger_id]
        return {
            'trigger_id': trigger_id,
            'name': trigger.name,
            'type': [c.trigger_type.value for c in trigger.conditions],
            'channels': [c.channel for c in trigger.conditions],
            'enabled': trigger.enabled,
            'mode': trigger.trigger_mode.value,
            'logic_operation': trigger.logic_operation.value
        }
    
    def export_trigger_config(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """Export trigger configuration"""
        if trigger_id not in self.triggers:
            return None
        
        trigger = self.triggers[trigger_id]
        config = {
            'trigger_id': trigger.trigger_id,
            'name': trigger.name,
            'trigger_mode': trigger.trigger_mode.value,
            'logic_operation': trigger.logic_operation.value,
            'holdoff_time': trigger.holdoff_time,
            'timeout': trigger.timeout,
            'enabled': trigger.enabled,
            'conditions': [
                {
                    'condition_id': c.condition_id,
                    'trigger_type': c.trigger_type.value,
                    'channel': c.channel,
                    'parameters': c.parameters,
                    'enabled': c.enabled,
                    'description': c.description
                }
                for c in trigger.conditions
            ]
        }
        
        # Add specialized trigger data
        if trigger_id in self.pattern_triggers:
            config['pattern_data'] = {
                'pattern': self.pattern_triggers[trigger_id].pattern,
                'pattern_length': self.pattern_triggers[trigger_id].pattern_length,
                'pattern_type': self.pattern_triggers[trigger_id].pattern_type
            }
        
        if trigger_id in self.sequence_triggers:
            seq = self.sequence_triggers[trigger_id]
            config['sequence_data'] = {
                'step_count': len(seq.steps),
                'step_timeouts': seq.step_timeouts,
                'reset_on_timeout': seq.reset_on_timeout
            }
        
        if trigger_id in self.protocol_triggers:
            prot = self.protocol_triggers[trigger_id]
            config['protocol_data'] = {
                'protocol': prot.protocol,
                'protocol_settings': prot.protocol_settings,
                'trigger_condition': prot.trigger_condition,
                'data_pattern': prot.data_pattern,
                'address_pattern': prot.address_pattern
            }
        
        return config
    
    def import_trigger_config(self, config: Dict[str, Any]) -> bool:
        """Import trigger configuration"""
        try:
            # Create trigger from config
            trigger = AdvancedTrigger(
                trigger_id=config['trigger_id'],
                name=config['name'],
                trigger_mode=TriggerMode(config['trigger_mode']),
                logic_operation=LogicOperation(config['logic_operation']),
                holdoff_time=config.get('holdoff_time', 0.0),
                timeout=config.get('timeout', 1.0),
                enabled=config.get('enabled', True)
            )
            
            # Add conditions
            for cond_data in config.get('conditions', []):
                condition = TriggerCondition(
                    condition_id=cond_data['condition_id'],
                    trigger_type=TriggerType(cond_data['trigger_type']),
                    channel=cond_data['channel'],
                    parameters=cond_data.get('parameters', {}),
                    enabled=cond_data.get('enabled', True),
                    description=cond_data.get('description', '')
                )
                trigger.conditions.append(condition)
            
            # Handle specialized trigger data
            if 'pattern_data' in config:
                pattern = PatternTrigger()
                pattern.pattern = config['pattern_data']['pattern']
                pattern.pattern_length = config['pattern_data']['pattern_length']
                pattern.pattern_type = config['pattern_data']['pattern_type']
                self.pattern_triggers[trigger.trigger_id] = pattern
            
            if 'sequence_data' in config:
                sequence = SequenceTrigger()
                sequence.steps = trigger.conditions.copy()
                sequence.step_timeouts = config['sequence_data']['step_timeouts']
                sequence.reset_on_timeout = config['sequence_data']['reset_on_timeout']
                self.sequence_triggers[trigger.trigger_id] = sequence
            
            if 'protocol_data' in config:
                prot_data = config['protocol_data']
                protocol = ProtocolTrigger(prot_data['protocol'])
                protocol.protocol_settings = prot_data['protocol_settings']
                protocol.trigger_condition = prot_data['trigger_condition']
                protocol.data_pattern = prot_data['data_pattern']
                protocol.address_pattern = prot_data['address_pattern']
                self.protocol_triggers[trigger.trigger_id] = protocol
            
            return self.register_trigger(trigger)
            
        except Exception as e:
            self.logger.error(f"Failed to import trigger config: {e}")
            return False


class AdvancedTriggerWidget(QWidget):
    """Widget for advanced trigger control"""
    
    def __init__(self, trigger_manager: AdvancedTriggerManager):
        super().__init__()
        self.trigger_manager = trigger_manager
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the trigger UI"""
        layout = QVBoxLayout(self)
        
        # Create tabs for different trigger types
        tab_widget = QTabWidget()
        
        # Basic Triggers tab
        basic_tab = QWidget()
        self.setup_basic_tab(basic_tab)
        tab_widget.addTab(basic_tab, "Basic")
        
        # Pattern Triggers tab
        pattern_tab = QWidget()
        self.setup_pattern_tab(pattern_tab)
        tab_widget.addTab(pattern_tab, "Pattern")
        
        # Protocol Triggers tab
        protocol_tab = QWidget()
        self.setup_protocol_tab(protocol_tab)
        tab_widget.addTab(protocol_tab, "Protocol")
        
        # Sequence Triggers tab
        sequence_tab = QWidget()
        self.setup_sequence_tab(sequence_tab)
        tab_widget.addTab(sequence_tab, "Sequence")
        
        layout.addWidget(tab_widget)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.activate_btn = QPushButton("Activate")
        control_layout.addWidget(self.activate_btn)
        
        self.deactivate_btn = QPushButton("Deactivate")
        control_layout.addWidget(self.deactivate_btn)
        
        control_layout.addStretch()
        
        self.export_btn = QPushButton("Export...")
        control_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("Import...")
        control_layout.addWidget(self.import_btn)
        
        layout.addLayout(control_layout)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
    
    def setup_basic_tab(self, parent):
        """Setup basic trigger tab"""
        layout = QVBoxLayout(parent)
        
        # Edge trigger group
        edge_group = QGroupBox("Edge Trigger")
        edge_layout = QVBoxLayout(edge_group)
        
        # Channel selection
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channel:"))
        
        self.edge_channel_combo = QComboBox()
        self.edge_channel_combo.addItems(["CH1", "CH2", "CH3", "CH4"])
        channel_layout.addWidget(self.edge_channel_combo)
        
        edge_layout.addLayout(channel_layout)
        
        # Slope selection
        slope_layout = QHBoxLayout()
        slope_layout.addWidget(QLabel("Slope:"))
        
        self.slope_combo = QComboBox()
        self.slope_combo.addItems(["Rising", "Falling", "Either"])
        slope_layout.addWidget(self.slope_combo)
        
        edge_layout.addLayout(slope_layout)
        
        # Level setting
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level (V):"))
        
        self.level_spin = QDoubleSpinBox()
        self.level_spin.setRange(-10.0, 10.0)
        self.level_spin.setSingleStep(0.1)
        level_layout.addWidget(self.level_spin)
        
        edge_layout.addLayout(level_layout)
        
        # Create edge trigger button
        self.create_edge_btn = QPushButton("Create Edge Trigger")
        edge_layout.addWidget(self.create_edge_btn)
        
        layout.addWidget(edge_group)
        
        # Pulse width trigger group
        pulse_group = QGroupBox("Pulse Width Trigger")
        pulse_layout = QVBoxLayout(pulse_group)
        
        # Add pulse width controls here
        self.create_pulse_btn = QPushButton("Create Pulse Width Trigger")
        pulse_layout.addWidget(self.create_pulse_btn)
        
        layout.addWidget(pulse_group)
        
        layout.addStretch()
    
    def setup_pattern_tab(self, parent):
        """Setup pattern trigger tab"""
        layout = QVBoxLayout(parent)
        
        pattern_group = QGroupBox("Digital Pattern Trigger")
        pattern_layout = QVBoxLayout(pattern_group)
        
        # Pattern input
        pattern_input_layout = QHBoxLayout()
        pattern_input_layout.addWidget(QLabel("Pattern:"))
        
        self.pattern_edit = QTextEdit()
        self.pattern_edit.setMaximumHeight(60)
        pattern_input_layout.addWidget(self.pattern_edit)
        
        pattern_layout.addLayout(pattern_input_layout)
        
        # Create pattern trigger button
        self.create_pattern_btn = QPushButton("Create Pattern Trigger")
        pattern_layout.addWidget(self.create_pattern_btn)
        
        layout.addWidget(pattern_group)
        layout.addStretch()
    
    def setup_protocol_tab(self, parent):
        """Setup protocol trigger tab"""
        layout = QVBoxLayout(parent)
        
        # Protocol selection
        protocol_layout = QHBoxLayout()
        protocol_layout.addWidget(QLabel("Protocol:"))
        
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["I2C", "SPI", "UART", "CAN"])
        protocol_layout.addWidget(self.protocol_combo)
        
        layout.addLayout(protocol_layout)
        
        # Protocol-specific settings (will be dynamic)
        self.protocol_settings_widget = QWidget()
        layout.addWidget(self.protocol_settings_widget)
        
        # Create protocol trigger button
        self.create_protocol_btn = QPushButton("Create Protocol Trigger")
        layout.addWidget(self.create_protocol_btn)
        
        layout.addStretch()
    
    def setup_sequence_tab(self, parent):
        """Setup sequence trigger tab"""
        layout = QVBoxLayout(parent)
        
        sequence_group = QGroupBox("Trigger Sequence")
        sequence_layout = QVBoxLayout(sequence_group)
        
        # Sequence steps table
        self.sequence_table = QTableWidget()
        self.sequence_table.setColumnCount(3)
        self.sequence_table.setHorizontalHeaderLabels(['Step', 'Condition', 'Timeout'])
        sequence_layout.addWidget(self.sequence_table)
        
        # Add step controls
        step_controls = QHBoxLayout()
        
        self.add_step_btn = QPushButton("Add Step")
        step_controls.addWidget(self.add_step_btn)
        
        self.remove_step_btn = QPushButton("Remove Step")
        step_controls.addWidget(self.remove_step_btn)
        
        sequence_layout.addLayout(step_controls)
        
        # Create sequence trigger button
        self.create_sequence_btn = QPushButton("Create Sequence Trigger")
        sequence_layout.addWidget(self.create_sequence_btn)
        
        layout.addWidget(sequence_group)
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        # Trigger manager signals
        self.trigger_manager.trigger_registered.connect(self.on_trigger_registered)
        self.trigger_manager.trigger_activated.connect(self.on_trigger_activated)
        self.trigger_manager.trigger_fired.connect(self.on_trigger_fired)
        
        # Button connections
        self.activate_btn.clicked.connect(self.activate_trigger)
        self.deactivate_btn.clicked.connect(self.deactivate_trigger)
        self.create_edge_btn.clicked.connect(self.create_edge_trigger)
    
    def create_edge_trigger(self):
        """Create an edge trigger"""
        try:
            channel = self.edge_channel_combo.currentText()
            slope_text = self.slope_combo.currentText()
            level = self.level_spin.value()
            
            # Map slope text to enum
            slope_map = {
                "Rising": TriggerSlope.RISING,
                "Falling": TriggerSlope.FALLING,
                "Either": TriggerSlope.EITHER
            }
            slope = slope_map[slope_text]
            
            # Create trigger
            trigger_id = f"edge_{len(self.trigger_manager.triggers)}"
            trigger = self.trigger_manager.create_edge_trigger(
                trigger_id=trigger_id,
                name=f"Edge {channel} {slope_text}",
                channel=channel,
                slope=slope,
                level=level
            )
            
            if self.trigger_manager.register_trigger(trigger):
                self.status_text.append(f"Created edge trigger: {trigger.name}")
            else:
                self.status_text.append("Failed to create edge trigger")
                
        except Exception as e:
            self.status_text.append(f"Error creating edge trigger: {e}")
    
    def activate_trigger(self):
        """Activate selected trigger"""
        # For now, activate the first available trigger
        triggers = self.trigger_manager.get_trigger_list()
        if triggers:
            trigger_id = triggers[0]
            if self.trigger_manager.activate_trigger(trigger_id):
                self.status_text.append(f"Activated trigger: {trigger_id}")
            else:
                self.status_text.append(f"Failed to activate trigger: {trigger_id}")
    
    def deactivate_trigger(self):
        """Deactivate current trigger"""
        if self.trigger_manager.deactivate_trigger():
            self.status_text.append("Deactivated trigger")
        else:
            self.status_text.append("No active trigger to deactivate")
    
    def on_trigger_registered(self, trigger_id: str):
        """Handle trigger registered"""
        self.status_text.append(f"Trigger registered: {trigger_id}")
    
    def on_trigger_activated(self, trigger_id: str):
        """Handle trigger activated"""
        self.status_text.append(f"Trigger activated: {trigger_id}")
    
    def on_trigger_fired(self, trigger_id: str, event_data: dict):
        """Handle trigger fired"""
        timestamp = event_data.get('timestamp', 'Unknown')
        self.status_text.append(f"TRIGGER FIRED: {trigger_id} at {timestamp}")
