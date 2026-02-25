"""
Pytest configuration for Remember-Me AI test suite.
Registers the 'integration' marker and adds the --model-path CLI option.
"""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--model-path",
        action="store",
        default=None,
        help="Absolute path to a .gguf model file for integration tests"
    )
    parser.addoption(
        "--llama-server",
        action="store",
        default=None,
        help="Absolute path to llama-server.exe for integration tests"
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests that require a real LLM server (deselect with '-m \"not integration\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-skip integration tests unless --model-path is provided."""
    if config.getoption("--model-path"):
        return  # Don't skip if model path provided

    skip_integration = pytest.mark.skip(reason="needs --model-path to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
