#!/usr/bin/env python3
"""
RTB2000 Automation Package
==========================

Advanced automation capabilities for RTB2000 oscilloscope control:
- Programmable measurement sequences with conditional logic
- Advanced trigger system with pattern, sequence, and protocol triggers
- Multi-channel synchronization and coordination
- Python scripting engine for custom automation workflows

This package provides comprehensive automation features for professional
oscilloscope control and measurement automation.
"""

from .automation import (
    AutomationEngine,
    MeasurementSequence,
    MeasurementStep,
    SequenceResult,
    SequenceStatus,
    StepType,
    AutomationWidget
)

from .advanced_triggers import (
    AdvancedTriggerManager,
    AdvancedTrigger,
    TriggerCondition,
    TriggerType,
    TriggerSlope,
    TriggerCoupling,
    LogicOperation,
    TriggerMode,
    PatternTrigger,
    SequenceTrigger,
    ProtocolTrigger,
    AdvancedTriggerWidget
)

from .multi_channel import (
    MultiChannelController,
    ChannelGroup,
    ChannelConfig,
    TimingConfig,
    SyncConfig,
    MultiChannelData,
    ChannelData,
    SyncMode,
    ChannelRole,
    AcquisitionMode,
    MultiChannelWidget
)

from .scripting import (
    ScriptingEngine,
    AutomationScript,
    ScriptTemplate,
    ScriptParameter,
    ScriptResult,
    ScriptContext,
    ScriptType,
    ScriptStatus,
    ScriptTemplateManager,
    ScriptingWidget
)

__all__ = [
    # Automation Engine
    'AutomationEngine',
    'MeasurementSequence',
    'MeasurementStep',
    'SequenceResult',
    'SequenceStatus',
    'StepType',
    'AutomationWidget',
    
    # Advanced Triggers
    'AdvancedTriggerManager',
    'AdvancedTrigger',
    'TriggerCondition',
    'TriggerType',
    'TriggerSlope',
    'TriggerCoupling',
    'LogicOperation',
    'TriggerMode',
    'PatternTrigger',
    'SequenceTrigger',
    'ProtocolTrigger',
    'AdvancedTriggerWidget',
    
    # Multi-Channel Sync
    'MultiChannelController',
    'ChannelGroup',
    'ChannelConfig',
    'TimingConfig',
    'SyncConfig',
    'MultiChannelData',
    'ChannelData',
    'SyncMode',
    'ChannelRole',
    'AcquisitionMode',
    'MultiChannelWidget',
    
    # Scripting Engine
    'ScriptingEngine',
    'AutomationScript',
    'ScriptTemplate',
    'ScriptParameter',
    'ScriptResult',
    'ScriptContext',
    'ScriptType',
    'ScriptStatus',
    'ScriptTemplateManager',
    'ScriptingWidget'
]

__version__ = "1.0.0"
__author__ = "RTB2000 Development Team"
__description__ = "Advanced automation package for RTB2000 oscilloscope control"
