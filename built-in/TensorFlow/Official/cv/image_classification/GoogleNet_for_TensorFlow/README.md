# Training GoogleNet for Tensorflow 

This repository provides a script and recipe to train the GoogleNet model.

## Table Of Contents

* [Model overview](#model-overview)
  * [Model Architecture](#model-architecture)  
  * [Default configuration](#default-configuration)
* [Data augmentation](#data-augmentation)
* [Setup](#setup)
  * [Requirements](#requirements)
* [Quick start guide](#quick-start-guide)
* [Advanced](#advanced)
  * [Command line arguments](#command-line-arguments)
  * [Training process](#training-process)
* [Performance](#performance)
  * [Results](#results)
    * [Training accuracy results](#training-accuracy-results)
    * [Training performance results](#training-performance-results)


    

## Model overview

In this repository, we implement GoogleNet from paper [Christian Szegedy, Wei Liu, Yangqing Jia. " Going Deeper with Convolutions".](https://arxiv.org/abs/1409.4842).

Googlenet is a convolutional neural network architecture. This is an implementation of the official GoogleNet network as is Google ModelZoo, written in Tensorflow 1.15.0 and run on Ascend 910.

### Model architecture

The model architecture can be found from the reference paper.

### Default configuration

The following sections introduce the default configurations and hyperparameters for GoogleNet model.

#### Optimizer

This model uses the Momentum optimizer with following hyperparameters:

- Momentum: 0.9
- Origin learning rate: 0.01
- LR schedule: cosine_annealing
- Batch size : 1P (256), 8 P(64 * 8) 
- Weight decay :  0.0004. 
- Label smoothing = 0.1
- We train for:
  - 200 epochs for a standard training process using official TFRecord dataset of ImageNet2012

#### Data augmentation

This model uses the following data augmentation:

- For training:
  - Resized: (224, 224, 3)
  - RandomResizeCrop: scale=(0.05, 1.0), ratio=(0.75, 1.33)
  - Distort colour: random brightness, random saturation, random hue, random contrast
  - Normalized to [-1, 1]
- For inference:
  - Resized: (224, 224, 3)
  - CenterCrop
  - Normalized to [-1, 1]

## Setup
The following section lists the requirements to train the GoogleNet network.
### Requirements

Tensorflow 1.15.0

## Quick Start Guide

### 1. Clone the respository

```shell
git clone xxx
cd modelzoo_GoogleNet_TF
```

### 2. Download and preprocess the dataset

1. Download the ImageNet2012 dataset.The model is compatible with the datasets on tensorflow official website.
2. Generate tfrecord files following [Tensorflow-Slim](https://github.com/tensorflow/models/tree/master/research/slim).
3. The train and validation tfrecord files are under the path/data directories.

### check json
Check whether there is a JSON configuration file "8P rank_table json" for 8 Card IP in the scripts/ directory.
The content of the 8p configuration file:
```
{"group_count": "1","group_list": 
                    [{"group_name": "worker","device_count": "8","instance_count": "1", "instance_list": 
                    [{"devices":                    
                                   [{"device_id":"0","device_ip":"192.168.100.101"},
                                    {"device_id":"1","device_ip":"192.168.101.101"},
                                    {"device_id":"2","device_ip":"192.168.102.101"},
                                    {"device_id":"3","device_ip":"192.168.103.101"},
                                    {"device_id":"4","device_ip":"192.168.100.100"},      
                                    {"device_id":"5","device_ip":"192.168.101.100"},        
                                    {"device_id":"6","device_ip":"192.168.102.100"},     
                                    {"device_id":"7","device_ip":"192.168.103.100"}],      
                                    "pod_name":"npu8p",        "server_id":"127.0.0.1"}]}],"status": "completed"}
```

### 3. Train

Before starting the training, first configure the environment variables related to the program running. For environment variable configuration information, see:
- [Ascend 910训练平台环境变量设置](https://github.com/Huawei-Ascend/modelzoo/wikis/Ascend%20910%E8%AE%AD%E7%BB%83%E5%B9%B3%E5%8F%B0%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F%E8%AE%BE%E7%BD%AE?sort_id=3148819)

- train on a single NPU
    - **edit** *scripts/run_1p.sh* and *scripts/train_1p.sh* (see example below)
    - ./run_1p.sh
- train on 8 NPUs
    - **edit** *scripts/run_8p.sh* and *scripts/train_8p.sh* (see example below)
    - ./run_8p.sh 

Examples:
- Case for single NPU
    - Modify the ID of NPU in *device_group* in *scripts/run_1p.sh*, default ID is *0*.
    - In *scripts/train_1p.sh* , python scripts part should look like as follows. For more detailed command lines arguments, please refer to [Command line arguments](#command-line-arguments)
        ```shell
        python3.7 ${dname}/train.py --rank_size=1 \
            --mode=train \
            --max_epoches=100 \
            --iterations_per_loop=10 \
            --data_dir=/opt/npu/data_PATH \
            --display_every=10 \
            --log_dir=./model \
            --log_name=googlenet.log
        ```
    - Run the program  
        ```
        ./run_1p.sh
        ```
- Case for 8 NPUs
    - Modify the ID of NPU in *device_group* in *scripts/run_8p.sh*, default ID is *0,1,2,3,4,5,6,7*.
    - In *scripts/train_8p.sh* , python scripts part should look like as follows.
        ```shell 
        python3.7 ${dname}/train.py --rank_size=8 \
            --mode=train \
            --max_epochs=200 \
            --iterations_per_loop=10 \
            --epochs_between_evals=1 \
            --data_dir=/opt/npu/data_PATH \
            --lr=0.01 \
            --log_dir=./model \
            --log_name=googlenet.log
        ```
    - Run the program  
        ```
        ./run_8p.sh
        ```

### 4. Test
- Same procedure as training except 2 following modifications
    - change `--mode=train` to `--mode=evaluate`
    - add `--eval_dir=path/eval`
     ```shell 
    python3.7 ${dname}/train.py --rank_size=1 \
        --mode=evaluate \
        --data_dir=/opt/npu/data_PATH \
        --eval_dir=${dname}/scripts/result/8p/0/model \
        --log_dir=./ \
        --log_name=eval_googlenet.log > eval.log
    ```
    run the program  
    ```
    ./test.sh
    ```


## Advanced
### Commmand-line options

```
  --rank_size                       number of NPUs to use (default: 1)
  --mode                            mode to run the program (default: train_and_evaluate)
  --max_train_steps                 max number of training steps (default: 100)
  --iterations_per_loop             number of steps to run in each iteration (default: 10)
  --max_epochs                      number of epochs to train the model (default: 200)
  --epochs_between_evals            the interval between train and evaluation (default: 1)
  --data_dir                        directory of dataset (default: path/data)
  --eval_dir                        path of checkpoint files for evaluation (default: path/eval)
  --dtype                           data type of the inputs of the network (default: tf.float32)
  --use_nesterov                    whether to use Nesterov in momentum (dafault: True)
  --label_smoothing                 use label smooth in cross entropy (default 0.1)
  --weight_decay                    weight decay for regularization loss (default: 0.0004)
  --batch_size                      batch size per npu (default: 256)
  --lr                              initial learning rate (default: 0.01)
  --T_max                           T_max value in cosine annealing learning rate (default: 200)
  --momentum                        momentum value used in optimizer (default: 0.9)
  --display_every                   frequency to display infomation (default: 100)
  --log_name                        name of log file (default: googlenet.log)
  --log_dir                         path to save checkpoint and log (default: ./model)  
```

### Training process

All the results and training ckpt models of the training will be stored in the directory `log_dir`.
 
## Performance

### Result

Our result were obtained by running the applicable training script. To achieve the same results, follow the steps in the Quick Start Guide.

#### Training accuracy results

| **epochs** |    Top1/Top5   |
| :--------: | :------------: |
|    200     | 70.2 %/89.8 %  |

#### Training performance results
| **NPUs** | train performance |
| :------: | :---------------: |
|    1     |     1300 img/s    |

| **NPUs** | train performance |
| :------: | :---------------: |
|    8     |     6000 img/s    |











