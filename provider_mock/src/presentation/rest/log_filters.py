"""Logging filters for REST API.

This module provides custom logging filters to control log output
for specific routes or patterns, helping to reduce noise in logs
for health checks and other routine operations.
"""

import logging


__all__ = ('ByRouteNameFilter',)


class ByRouteNameFilter(logging.Filter):
    """Logging filter to exclude specific routes from log output.

    Filters out log messages containing specified route patterns,
    useful for suppressing health check logs and other routine operations.

    Attributes:
        _filter_routes: List of route patterns to filter out
    """

    def __init__(self, filter_routes: list[str], *args, **kwargs):
        """Initialize the route filter.

        Args:
            filter_routes: List of route patterns to exclude from logs
            *args: Additional positional arguments for logging.Filter
            **kwargs: Additional keyword arguments for logging.Filter
        """
        self._filter_routes = filter_routes
        super().__init__(*args, **kwargs)

    def filter(self, record):
        """Filter log records based on route patterns.

        Args:
            record: LogRecord instance to evaluate

        Returns:
            bool: False if the record should be filtered out, True otherwise
        """
        for filter_route in self._filter_routes:
            if filter_route in record.getMessage():
                return False
        return True
