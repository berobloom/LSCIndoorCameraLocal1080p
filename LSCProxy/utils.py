"""
Module Description: This module provides utility functions related to time.

Contents:
- usleep(u_seconds): Sleeps for a specified duration in microseconds.

Note: This module uses the 'time' module.
"""
import time

def usleep(u_seconds):
    """
    Sleep for a specified duration in microseconds.

    Args:
    - u_seconds (int): The duration to sleep in microseconds.

    Example:
    >>> usleep(500000)  # Sleep for 0.5 seconds
    """
    time.sleep(u_seconds / 1e6)
