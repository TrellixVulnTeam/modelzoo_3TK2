"""
make available with multi version tensorflow.
"""
import tensorflow as tf

# pylint: disable=W0611
if tf.__version__ in ("1.15.0", "2.0.0"):
    from tensorflow.compat.v1.keras import backend as K
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.layers import Conv2D, Dense, Flatten, Input, Lambda
    from tensorflow.keras.layers import concatenate, Activation
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.python.keras.callbacks import History
    from tensorflow.python.keras.losses import MSE
    from tensorflow.compat.v1 import global_variables_initializer
    from tensorflow.compat.v1.train import AdamOptimizer, Saver
    from tensorflow.compat.v1.summary import scalar as summary_scalar

elif tf.__version__ in ("1.12.0", "1.13.1", "1.14.0",):
    from tensorflow.keras import backend as K
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.layers import Conv2D, Dense, Flatten, Input, Lambda
    from tensorflow.keras.layers import concatenate, Activation
    from tensorflow.keras.models import Model
    from tensorflow.python.keras.callbacks import History
    from tensorflow import global_variables_initializer
    from tensorflow.train import AdamOptimizer, Saver
    from tensorflow.summary import scalar as summary_scalar

elif tf.__version__ in ("1.8.0", "1.4.1", "1.4.0"):
    from tensorflow.python.keras._impl.keras import backend as K
    from tensorflow.python.keras._impl.keras.optimizers import Adam
    from tensorflow.python.keras._impl.keras.layers import (
        Conv2D,
        Dense,
        Flatten,
        Input,
        Lambda,
    )
    from tensorflow.python.keras._impl.keras.layers import concatenate
    from tensorflow.python.keras._impl.keras.layers import Activation
    from tensorflow.python.keras._impl.keras.models import Model, Sequential
    from tensorflow.python.keras._impl.keras.callbacks import History
    from tensorflow import global_variables_initializer
    from tensorflow.train import AdamOptimizer, Saver

else:
    raise ValueError("non-support tensorflow version: {}".format(tf.__version__))


def loss_to_val(loss):
    """
    make keras instance into value.
    """
    if isinstance(loss, History):
        loss = loss.history.get("loss")[0]
    return loss


DTYPE_MAP = {
    "float32": tf.float32,
    "float16": tf.float16,
}
