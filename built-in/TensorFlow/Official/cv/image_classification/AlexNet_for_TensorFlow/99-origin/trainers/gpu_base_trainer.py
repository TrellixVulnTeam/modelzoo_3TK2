import tensorflow as tf
import math
import time
from . import train_helper
from .train_helper import stage
from utils.logger import rank0log

# add for MultiGPU
import horovod.tensorflow as hvd

class GPUBaseTrain(object):
    def __init__(self, session, config, data, model, logger):
        self.sess = session
        self.config = config
        self.data = data
        self.model = model
        self.logger = logger
        self.print_logger = self.logger.logger
        self.all_preds = []
        self.all_targets = []
        self.classifier, self.training_hook = self.get_classifier()

        

    def get_classifier(self):
        classifier = tf.estimator.Estimator(
            model_fn=self.model.get_estimator_model_func,
            model_dir=self.config['log_dir'],
            config = tf.estimator.RunConfig( 
                    session_config=self.sess.get_config(), 
                    save_summary_steps=self.config['save_summary_steps'] if self.config['do_checkpoint'] else None,
                    save_checkpoints_steps=self.config['save_checkpoints_steps'] if self.config['do_checkpoint'] else None,
                    keep_checkpoint_max=None
                     )
            )

        training_hooks = [train_helper.PrefillStagingAreasHook()]
        training_hooks.append(self.logger)

        # add for MultiGPU
        training_hooks.append(hvd.BroadcastGlobalVariablesHook(0))

        return classifier, training_hooks


    def train(self):
        print ('training steps: %d' % self.config['nstep'])
        self.classifier.train( input_fn=lambda:self.data.get_train_input_fn(),
                               max_steps = self.config['nstep'],
                               hooks = self.training_hook
                              )


    def evaluate(self):
        rank0log(self.print_logger, "Evaluating")
        rank0log(self.print_logger, "Validation dataset size: {}".format(self.config['num_evaluating_samples'] ))
        time.sleep(5)  # a little extra margin...
        try:
            ckpts = train_helper.sort_and_load_ckpts(self.config['log_dir'])
            print("=========ckpt==========")
            print(ckpts)
            print("=========ckpt==========")
            for i, c in enumerate(ckpts):
                if i < len(ckpts) - 1:
                    if i % self.config['eval_interval'] != 0:
                        continue
                eval_result = self.classifier.evaluate(
                    input_fn=lambda: self.data.get_eval_input_fn(),
                    checkpoint_path=c['path'])
                c['epoch'] = math.ceil(c['step'] / (self.config['num_training_samples']/ (self.config['batch_size'])))
                c['top1'] = eval_result['val-top1acc']
                c['top5'] = eval_result['val-top5acc']
                c['loss'] = eval_result['loss']

            rank0log(self.print_logger, ' step  epoch  top1    top5     loss   checkpoint_time(UTC)')
            for i, c in enumerate(ckpts):
                if 'top1' not in c:
                    continue
                rank0log(self.print_logger,'{:5d}  {:5.1f}  {:5.3f}  {:6.2f}  {:6.2f}  {time}'
                         .format(c['step'],
                                 c['epoch'],
                                 c['top1'] * 100,
                                 c['top5'] * 100,
                                 c['loss'],
                                 time=time.strftime('%Y-%m-%d %H:%M:%S', 
                                    time.localtime(c['mtime']))))
            rank0log(self.print_logger, "Finished evaluation")
        except KeyboardInterrupt:
            self.print_logger.error("Keyboard interrupt")

    def train_and_evaluate(self):
        epochs_between_evals = self.config.get('epochs_between_evals', 4)


        for i in range(self.config['num_epochs'] // epochs_between_evals):
        #for i in range(1):
            rank0log(self.print_logger, "Starting a training cycle")

            self.classifier.train(input_fn=lambda:self.data.get_train_input_fn(),
            #self.classifier.train(input_fn=lambda:self.data.get_train_input_fn_synthetic(),
                            steps = self.config['nsteps_per_epoch']*epochs_between_evals,
                            # steps = 4000,
                            hooks = self.training_hook )

            rank0log(self.print_logger, "Starting to evaluate")
            rank0log(self.print_logger, "Validation dataset size: {}".format(self.config['num_evaluating_samples'] ))
            time.sleep(5)  # a little extra margin...
  
            ckpts = train_helper.sort_and_load_ckpts(self.config['log_dir'])
            c = ckpts[-1]
            eval_result = self.classifier.evaluate(
                input_fn=lambda: self.data.get_eval_input_fn(),
                checkpoint_path=c['path'])

            c['epoch'] = math.ceil(c['step'] / (self.config['num_training_samples'] / (self.config['batch_size'] * self.config['rank_size'])))
            c['top1'] = eval_result['val-top1acc']
            c['top5'] = eval_result['val-top5acc']
            c['loss'] = eval_result['loss']

            rank0log(self.print_logger, ' step  epoch  top1    top5     loss   checkpoint_time(UTC)')

            rank0log(self.print_logger,'{:5d}  {:5.1f}  {:5.3f}  {:6.2f}  {:6.2f}  {time}'
                    .format(c['step'],
                            c['epoch'],
                            c['top1'] * 100,
                            c['top5'] * 100,
                            c['loss'],
                            time=time.strftime('%Y-%m-%d %H:%M:%S',
                                time.localtime(c['mtime']))))



