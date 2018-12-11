import shutil
import os

import machine
from machine.util.checkpoint import Checkpoint
from machine.util.callbacks import Callback


class ModelCheckpoint(Callback):
    """
    Model checkpoint to save weights during training. 
    This callback is automatically applied for every model that
    is trained with the SupervisedTrainer.
    """

    def __init__(self, top_k=5, monitor='val',
                 save_best_only=True):
        super(ModelCheckpoint, self).__init__()
        self.top_k = top_k
        self.monitor = monitor
        self.save_best_only = save_best_only

    def set_trainer(self, trainer):
        self.trainer = trainer
        self.checkpoint_every = trainer.checkpoint_every
        self.expt_dir = trainer.expt_dir

    def on_epoch_begin(self, epoch, info=None):
        pass

    def on_epoch_end(self, epoch, info=None):
        pass

    def on_batch_begin(self, batch, info=None):
        pass

    def on_batch_end(self, batch, info=None):

        # this check is also hacky, occurs also in
        # supervised trainer to not compute the dev
        # loss too often
        if info['step'] % self.checkpoint_every == 0 or \
                info['step'] == info['total_steps']:
            total_loss, log_msg, model_name = \
                self.get_losses(self.trainer.losses,
                                self.trainer.metrics, info['step'])

            max_eval_loss = max(self.loss_best)

            if total_loss < max_eval_loss:
                index_max = self.loss_best.index(max_eval_loss)
                # rm prev model
                if self.best_checkpoints[index_max] is not None:
                    shutil.rmtree(os.path.join(
                        self.expt_dir, self.best_checkpoints[index_max]))
                self.best_checkpoints[index_max] = model_name
                self.loss_best[index_max] = total_loss

                # save model
                Checkpoint(model=self.trainer.model,
                           optimizer=self.trainer.optimizer,
                           epoch=info['epoch'], step=info['step'],
                           input_vocab=self.trainer.data.fields[machine.src_field_name].vocab,
                           output_vocab=self.trainer.data.fields[machine.tgt_field_name].vocab).save(self.expt_dir, name=model_name)

    def on_train_begin(self, info):

        total_loss, _, model_name = self.get_losses(self.trainer.losses,
                                                    self.trainer.metrics,
                                                    info['step'])

        self.loss_best = self.top_k*[total_loss]
        self.best_checkpoints = self.top_k*[None]
        self.best_checkpoints[0] = model_name

        # store first model

        Checkpoint(model=self.trainer.model,
                   optimizer=self.trainer.optimizer,
                   epoch=info['start_epoch'], step=info['start_step'],
                   input_vocab=self.trainer.data.fields[machine.src_field_name].vocab,
                   output_vocab=self.trainer.data.fields[machine.tgt_field_name].vocab).save(self.expt_dir, name=model_name)

    def on_train_end(self, info=None):
        # TODO perhaps here also the model should be saved?
        pass

    def save(self, name):
        """
        Saves the current model and related training parameters into a
        subdirectory of the directory stored in self.experiment_dir.

        name (str): alternative name for the model

        Returns:
             str: path to the saved checkpoint subdirectory
        """

        return NotImplementedError()
