"""Comprehensive test suite for GOD CLI."""
import subprocess
import sys
import pytest

def run(args, timeout=15):
    """Run GOD CLI command."""
    return subprocess.run(
        [sys.executable, "-m", "god"] + args, 
        capture_output=True, 
        text=True, 
        timeout=timeout
    )

def test_version_flag():
    """Test version command."""
    r = run(["--version"])
    assert r.returncode == 0
    assert "GOD v1.0.0" in r.stdout

def test_help_flag():
    """Test help command."""
    r = run(["--help"])
    assert r.returncode == 0
    assert "Global Operations Deity" in r.stdout

def test_build_console():
    """Test build command with console output."""
    r = run(["build", "-f", "console", "--limit", "3"])
    assert r.returncode == 0

def test_blux_group_exists():
    """Test BLUX integration."""
    r = run(["blux", "--help"])
    assert r.returncode == 0

def test_search_command():
    """Test search functionality."""
    r = run(["search", "--names-only", "python"])
    assert r.returncode == 0

def test_stats_command():
    """Test stats functionality."""
    r = run(["stats"])
    assert r.returncode == 0

def test_info_command():
    """Test info functionality."""
    r = run(["info", "python", "--timeout", "1.0"])
    assert r.returncode in [0, 1]

@pytest.mark.slow
def test_build_with_workers():
    """Test parallel processing."""
    r = run(["build", "-f", "console", "--limit", "5", "--max-workers", "2"])
    assert r.returncode == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
