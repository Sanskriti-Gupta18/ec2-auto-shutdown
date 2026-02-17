"""
Unit tests for data models
"""

import pytest
from src.models import InstanceInfo, ShutdownResult


def test_instance_info_creation():
    """Test that InstanceInfo can be created with all fields"""
    instance = InstanceInfo(
        instance_id="i-1234567890abcdef0",
        instance_name="web-server-01",
        state="running"
    )
    
    assert instance.instance_id == "i-1234567890abcdef0"
    assert instance.instance_name == "web-server-01"
    assert instance.state == "running"


def test_instance_info_empty_name():
    """Test that InstanceInfo can be created with empty instance name"""
    instance = InstanceInfo(
        instance_id="i-abcdef1234567890",
        instance_name="",
        state="stopped"
    )
    
    assert instance.instance_id == "i-abcdef1234567890"
    assert instance.instance_name == ""
    assert instance.state == "stopped"


def test_instance_info_various_states():
    """Test that InstanceInfo can represent various instance states"""
    states = ["running", "stopped", "stopping", "terminated", "terminating", "pending"]
    
    for state in states:
        instance = InstanceInfo(
            instance_id=f"i-{state}",
            instance_name=f"instance-{state}",
            state=state
        )
        assert instance.state == state



def test_shutdown_result_creation():
    """Test that ShutdownResult can be created with all fields"""
    result = ShutdownResult(
        total_instances=5,
        successful_stops=4,
        failed_stops=1,
        errors=["Failed to stop i-abc123: InsufficientInstanceCapacity"]
    )
    
    assert result.total_instances == 5
    assert result.successful_stops == 4
    assert result.failed_stops == 1
    assert len(result.errors) == 1
    assert result.errors[0] == "Failed to stop i-abc123: InsufficientInstanceCapacity"


def test_shutdown_result_no_errors():
    """Test that ShutdownResult can be created with empty errors list"""
    result = ShutdownResult(
        total_instances=3,
        successful_stops=3,
        failed_stops=0,
        errors=[]
    )
    
    assert result.total_instances == 3
    assert result.successful_stops == 3
    assert result.failed_stops == 0
    assert result.errors == []


def test_shutdown_result_multiple_errors():
    """Test that ShutdownResult can handle multiple error messages"""
    errors = [
        "Failed to stop i-111: PermissionDenied",
        "Failed to stop i-222: InstanceNotFound",
        "Failed to stop i-333: InternalError"
    ]
    result = ShutdownResult(
        total_instances=5,
        successful_stops=2,
        failed_stops=3,
        errors=errors
    )
    
    assert result.total_instances == 5
    assert result.successful_stops == 2
    assert result.failed_stops == 3
    assert len(result.errors) == 3
    assert result.errors == errors
