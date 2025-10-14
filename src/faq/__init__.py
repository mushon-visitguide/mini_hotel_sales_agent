"""FAQ (Frequently Asked Questions) Module for The Way Inn

This module provides FAQ responses for hotel guests and AI agents.
It's designed to be AI agent agnostic - each method can be called independently
as a tool to provide specific information sections.
"""

from .faq_client import FAQClient

__all__ = ["FAQClient"]
