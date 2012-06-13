"""Bcfg2 errors for reporting why a process exited"""

# Generic errors
NO_ERROR = 0
SYNTAX_ERROR = 1
SIGNAL_INTERRUPT = 2
FATAL_ERROR = 3

# Client errors
NO_PROFILE = 100

PROBE_EXECUTE_FAILURE = 101
PROBE_DOWNLOAD_FAILURE = 102
PROBE_UPLOAD_FAILURE = 103

DECISION_FAILURE = 104
CONFIGURATION_DOWNLOAD_FAILURE = 105
STATISTICS_UPLOAD_FAILURE = 106

