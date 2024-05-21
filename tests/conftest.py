# SPDX-FileCopyrightText: 2024 Bernd Doser
#
# SPDX-License-Identifier: MIT

import random

import numpy as np
import pytest
import torch


@pytest.hookimpl
def pytest_runtest_setup():
    np.random.seed(0)
    random.seed(0)
    torch.manual_seed(0)
