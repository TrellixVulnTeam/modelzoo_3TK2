# BERT-Base for TensorFlow

## 简述

BERT是谷歌2018年推出的预训练语言模型结构，通过自监督训练实现对语义语境相关的编码，是目前众多NLP应用的基石。

参考论文：Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805.

参考实现：https://github.com/NVIDIA/DeepLearningExamples/tree/master/TensorFlow/LanguageModeling/BERT 

## 默认配置
网络结构
学习率为1e-5，使用polynomial decay
优化器：Adam
优化器Weight decay为0.01
优化器epsilon设置为1e-4
单卡batchsize：128
32卡batchsize：128*32
总step数设置为500000
Warmup step设置为10000
训练数据集预处理（以wikipedia为例，仅作为用户参考示例）：
Sequence Length原则上用户可以自行定义
以常见的设置128为例，mask其中的20个tokens作为自编码恢复的目标。
下游任务预处理以用户需要为准。
测试数据集预处理（以wikipedia为例，仅作为用户参考示例）：
和训练数据集处理一致。

## 快速上手
 
数据集准备。该模型兼容tensorflow官网上的数据集。
数据集以文本格式表示，每段之间以空行隔开。源码包目录下`data/pretrain-toy/`给出了sample_text以及处理后的样例tfrecord数据集，如wikipedia。
运行如下命令，将数据集转换为tfrecord格式。
```
python utils/create_pretraining_data.py \   
  --input_file=./your/path/some_input_data.txt \   
  --output_file=/data/some_output_data.tfrecord \   
  --vocab_file=./your/path/vocab.txt \   
  --do_lower_case=True \   
  --max_seq_length=128 \   
  --max_predictions_per_seq=20 \   
  --masked_lm_prob=0.15 \   
  --random_seed=12345 \   
  --dupe_factor=5
```
## 环境配置

启动训练之前，首先要配置程序运行相关环境变量。环境变量配置信息参见：

- [Ascend 910训练平台环境变量设置](https://github.com/Huawei-Ascend/modelzoo/wikis/Ascend%20910%E8%AE%AD%E7%BB%83%E5%B9%B3%E5%8F%B0%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F%E8%AE%BE%E7%BD%AE?sort_id=3148819)


## 开始训练
1.单卡训练
```
cd scripts

./run_pretraining.sh
```
2.8卡训练
```
cd scripts

./run_8p.sh
```

## 下游任务Finetune。
提供三个脚本，分别是文本分类任务，序列标注任务，阅读理解任务，并且提供了XNLI，LCQMC，CHNSENTI，NER，CMRC的数据处理方法示例，用户可根据自己的下游任务需要改写和处理数据。然后运行脚本，参考超参已经写入脚本供用户参考。

执行命令：

bash scripts/run_downstream_classifier.sh进行分类下游任务。

bash scripts/run_downstream_ner.sh进行序列标注下游任务。

bash scripts/run_downstream_reading.sh进行阅读理解下游任务。

执行命令前请先阅读相应bash脚本，补充相应文件路径。