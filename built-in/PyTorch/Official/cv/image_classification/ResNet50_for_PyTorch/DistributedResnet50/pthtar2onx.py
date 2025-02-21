'''
# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the BSD 3-Clause License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://spdx.org/licenses/BSD-3-Clause.html
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
import torch
from image_classfication import resnet
from image_classfication.resnet import resnet_version
import torch.onnx

from collections import OrderedDict

def proc_node_module(checkpoint,AttrName):
    new_state_dict = OrderedDict()
    for k,v in checkpoint[AttrName].items():
        if(k[0:7] == "module."):
            name = k[7:]
        else:
            name = k[0:]
        new_state_dict[name] = v
    return new_state_dict
def convert():
    checkpoint = torch.load("./resnet50checkpoint.pth.tar", map_location='cpu')
    checkpoint['state_dict'] = proc_nodes_module(checkpoint, 'state_dict')
    model = resnet.build_resnet("resnet50","classic")
    model.load_state_dict(checkpoint['state_dict'])
    model.eval();
    print(model)

    input_names = ["actual_input_1"]
    output_names = ["output1"]
    dummy_input = torch.randn(16,3,224,224)
    torch.onnx.export(model,dummy_input,"resnet50_npu_16.onnx", input_names = input_names, output_names = output_names, opset_version=11)
if __name__ == "__main__":
    convert()