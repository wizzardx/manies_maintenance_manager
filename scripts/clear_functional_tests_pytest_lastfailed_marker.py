#!/usr/bin/env python

"""Remove the pytest lastfailed file if it is functional test-related."""

import clear_pytest_lastfailed_marker_lib as clear_lib

clear_lib.clear_file(clear_when_functional_test=True)
