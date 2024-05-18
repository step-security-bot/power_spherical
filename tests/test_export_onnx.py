import torch
from distributions import HypersphericalUniform, MarginalTDistribution, PowerSpherical

class PowerModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        batch_size = 32
        cloc = torch.randn(batch_size, 3)
        cscale = torch.ones(batch_size)
        self.psher = PowerSpherical(loc=cloc, scale=cscale)

    def forward(self):
        return self.psher.rsample()



exported_program = torch.export.export(PowerModel() , args=())


print(exported_program)

_ = torch.onnx.dynamo_export( exported_program, )