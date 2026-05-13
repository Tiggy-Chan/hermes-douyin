"""
Hermes plugin entry point for Douyin (抖音) integration.

This file is auto-discovered by Hermes's plugin system.
It registers Douyin tools (upload, auth, status).
"""

import sys
import os

# Add src to path so we can import hermes_douyin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from hermes_douyin import register

__all__ = ["register"]
