# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
# Copyright 2020 Huawei Technologies Co., Ltd
# Licensed under the BSD 3-Clause License  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import torch
import torch.nn as nn
import numpy as np


def mixup(alpha, num_classes, data, target):
    with torch.no_grad():
        bs = data.size(0)
        c = np.random.beta(alpha, alpha)

        perm = torch.randperm(bs).cuda()

        md = c * data + (1-c) * data[perm, :]
        mt = c * target + (1-c) * target[perm, :]
        return md, mt


class MixUpWrapper(object):
    def __init__(self, alpha, num_classes, dataloader):
        self.alpha = alpha
        self.dataloader = dataloader
        self.num_classes = num_classes

    def mixup_loader(self, loader):
        for input, target in loader:
            i, t = mixup(self.alpha, self.num_classes, input, target)
            yield i, t

    def __iter__(self):
        return self.mixup_loader(self.dataloader)


class NLLMultiLabelSmooth(nn.Module):
    def __init__(self, smoothing = 0.0):
        super(NLLMultiLabelSmooth, self).__init__()
        self.confidence = 1.0 - smoothing
        self.smoothing = smoothing

    def forward(self, x, target):
        if self.training:
            x = x.float()
            target = target.float()
            logprobs = torch.nn.functional.log_softmax(x, dim = -1)
    
            nll_loss = -logprobs * target
            nll_loss = nll_loss.sum(-1)
    
            smooth_loss = -logprobs.mean(dim=-1)
    
            loss = self.confidence * nll_loss + self.smoothing * smooth_loss
    
            return loss.mean()
        else:
            return torch.nn.functional.cross_entropy(x, target)
