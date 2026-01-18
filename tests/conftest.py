"""Pytest configuration and fixtures."""

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def reset_random_seed():
    """Reset random seed before each test for reproducibility."""
    np.random.seed(42)
