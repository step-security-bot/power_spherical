# SPDX-FileCopyrightText: 2024 Bernd Doser
# SPDX-FileCopyrightText: 2024 Andreas Fehlner
#
# SPDX-License-Identifier: MIT

import os
import random
import sys

import numpy as np
import pytest
import quadpy
import torch
from power_spherical import HypersphericalUniform, PowerSpherical


def test_power_spherical_2d():
    dist = PowerSpherical(torch.Tensor([0.0, 0.0]), torch.Tensor([1.0]))

    assert dist.has_rsample == True
    assert torch.allclose(dist.rsample(), torch.Tensor([-0.9971, 0.0766]), rtol=1e-3)
    assert torch.allclose(dist.rsample(), torch.Tensor([-0.5954, 0.8034]), rtol=1e-3)


def test_power_spherical_large_scale():
    z_mean = torch.Tensor([1.0, 0.0, 0.0])
    z_mean = torch.nn.functional.normalize(z_mean, p=2.0, dim=0)
    z_scale = torch.Tensor([1.0e38])
    z_scale = torch.nn.functional.softplus(z_scale) + 1
    dist = PowerSpherical(z_mean, z_scale)

    assert torch.allclose(
        dist.rsample(), torch.Tensor([1.0000e00, -2.9921e-04, -3.8586e-04])
    )
    assert torch.allclose(
        dist.rsample(), torch.Tensor([1.0000e00, -4.6703e-04, 1.4249e-04])
    )


def test_power_spherical_2d_batch():
    batch_size = 32
    loc = torch.randn(batch_size, 3)
    scale = torch.ones(batch_size)
    dist = PowerSpherical(loc, scale)

    sample = dist.rsample()
    assert sample.shape == torch.Size([batch_size, 3])


def test_kl_divergence():
    dim = 8
    loc = torch.tensor([0.0] * (dim - 1) + [1.0])
    scale = torch.tensor(10.0)

    dist1 = PowerSpherical(loc, scale)
    dist2 = HypersphericalUniform(dim)
    x = dist1.sample((100000,))

    assert torch.allclose(
        (dist1.log_prob(x) - dist2.log_prob(x)).mean(),
        torch.distributions.kl_divergence(dist1, dist2),
        atol=1e-2,
    )


def test_dynamo_export_normal(tmp_path):
    class Model(torch.nn.Module):
        def __init__(self):
            self.normal = torch.distributions.normal.Normal(0, 1)
            super().__init__()

        def forward(self, x):
            return self.normal.sample(x.shape)

    x = torch.randn(2, 3)
    exported_program = torch.export.export(Model(), args=(x,))
    onnx_program = torch.onnx.dynamo_export(
        exported_program,
        x,
    )
    onnx_program.save(str(tmp_path) + os.sep + "normal.onnx")

def test_dynamo_export_power_spherical_githubexample(tmp_path):
    class PowerModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            batch_size = 32
            cloc = torch.randn(batch_size, 3)
            cscale = torch.ones(batch_size)
            self.power_spherical = PowerSpherical(loc=cloc, scale=cscale)

        def forward(self, x):
            return self.power_spherical.rsample()


    exported_program = torch.export.export(PowerModel() , args=(torch.randn(1),))
    


def test_dynamo_export_power_githubexample_onnx_dynamic_shapes(tmp_path):
    class PowerModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            batch_size = 32
            cloc = torch.randn(batch_size, 3)
            cscale = torch.ones(batch_size)
            self.power_spherical = PowerSpherical(loc=cloc, scale=cscale)

        def forward(self, x):
            return self.power_spherical.rsample()


    exported_program = torch.export.export(PowerModel() , args=(torch.randn(1),))
    x = torch.randn(2, 3)


    export_options = torch.onnx.ExportOptions(dynamic_shapes=True)

    onnx_program = torch.onnx.dynamo_export(
        exported_program,
        x,
        export_options=export_options
    )
    onnx_program.save(str(tmp_path) + os.sep + "powerspherical_dyn.onnx")

#@pytest.mark.xfail(reason="not supported feature of ONNX")
def test_dynamo_export_power_spherical():
    class Model(torch.nn.Module):
        def __init__(self):
            self.spherical = PowerSpherical(
                torch.Tensor([0.0, 1.0]), torch.Tensor([1.0])
            )
            super().__init__()

        def forward(self, x):
            return self.spherical.sample(x.shape)

    x = torch.randn(2, 3)
    exported_program = torch.export.export(Model(), args=(x,))
    _ = torch.onnx.dynamo_export(
        exported_program,
        x,
    )

#def test_quadpy():
#    d = 5
#    loc = torch.tensor([1.] + [0.] * (d - 1))
#    scale = torch.tensor(5.)
#    dist = PowerSpherical(loc, scale)#
#
#    scheme = quadpy.nsphere.stroud_1969(d)
#
#    def f(x):
#        return dist.log_prob(torch.tensor(x.T, dtype=torch.float32)).exp().detach().numpy()
#
#    assert np.isclose(
#        scheme.integrate(f, [0.] * d, radius=1),
#        1,
#        atol=1e-2)

# # https://github.com/pytorch/pytorch/issues/116336
# #@pytest.mark.xfail(reason="not supported feature of ONNX")
# def test_dynamo_export_power_spherical():
#     class PowerModel(torch.nn.Module):
#         def __init__(self):
#             super().__init__()
#             batch_size = 32
#             cloc = torch.randn(batch_size, 3)
#             cscale = torch.ones(batch_size)
#             self.power_spherical = PowerSpherical(loc=cloc, scale=cscale)

#         def forward(self, x):
#             return self.power_spherical.rsample()


#     x = torch.randn(1)
#     exported_program = torch.export.export(PowerModel() , args=(x,))

