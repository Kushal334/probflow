"""
The utils.settings module contains global settings about the backend to use,
what sampling method to use, the default device, and default datatype.


Backend
-------

Which backend to use.  Can be either
`TensorFlow 2.0 <http://www.tensorflow.org/beta/>`_
or `PyTorch <http://pytorch.org/>`_.

* :func:`.get_backend`
* :func:`.set_backend`


Datatype
--------

Which datatype to use as the default for parameters.  Depending on your model,
you might have to set the default datatype to match the datatype of your data.

* :func:`.get_datatype`
* :func:`.set_datatype`


Samples
-------

Whether and how many samples to draw from parameter posterior distributions.
If ``None``, the maximum a posteriori estimate of each parameter will be used.
If an integer greater than 0, that many samples from each parameter's posterior
distribution will be used.

* :func:`.get_samples`
* :func:`.set_samples`


Flipout
-------

Whether to use `Flipout <https://arxiv.org/abs/1803.04386>`_ where possible.

* :func:`.get_flipout`
* :func:`.set_flipout`


Static posterior sampling
-------------------------

Whether or not to use static posterior sampling (i.e., take a random sample
from the posterior, but take the same random sample on repeated calls), and
control the UUID of the current static sampling regime.

* :func:`.get_static_sampling_uuid`
* :func:`.set_static_sampling_uuid`


Sampling context manager
------------------------

A context manager which controls how |Parameters| sample from their
variational distributions while inside the context manager.

* :class:`.Sampling`


"""


import uuid

__all__ = [
    "get_backend",
    "set_backend",
    "get_datatype",
    "set_datatype",
    "get_samples",
    "set_samples",
    "get_flipout",
    "set_flipout",
    "get_static_sampling_uuid",
    "set_static_sampling_uuid",
    "Sampling",
]


class _Settings:
    """Class to store ProbFlow global settings

    Attributes
    ----------
    _BACKEND : str {'tensorflow' or 'pytorch'}
        What backend to use
    _SAMPLES : |None| or int > 0
        How many samples to take from |Parameter| variational posteriors.
        If |None|, will use MAP estimates.
    _FLIPOUT : bool
        Whether to use flipout where possible
    _DATATYPE : tf.dtype or torch.dtype
        Default datatype to use for tensors
    _STATIC_SAMPLING_UUID : None or uuid.UUID
        UUID of the current static sampling regime
    """

    def __init__(self):
        self._BACKEND = "tensorflow"
        self._SAMPLES = None
        self._FLIPOUT = False
        self._DATATYPE = None
        self._STATIC_SAMPLING_UUID = None


# Global ProbFlow settings
__SETTINGS__ = _Settings()


def get_backend():
    """Get which backend is currently being used.

    Returns
    -------
    backend : str {'tensorflow' or 'pytorch'}
        The current backend
    """
    return __SETTINGS__._BACKEND


def set_backend(backend):
    """Set which backend is currently being used.

    Parameters
    ----------
    backend : str {'tensorflow' or 'pytorch'}
        The backend to use
    """
    if isinstance(backend, str):
        if backend in ["tensorflow", "pytorch"]:
            __SETTINGS__._BACKEND = backend
        else:
            raise ValueError("backend must be either tensorflow or pytorch")
    else:
        raise TypeError("backend must be a string")


def get_datatype():
    """Get the default datatype used for Tensors

    Returns
    -------
    dtype : tf.dtype or torch.dtype
        The current default datatype
    """
    if __SETTINGS__._DATATYPE is None:
        if get_backend() == "pytorch":
            import torch

            return torch.float32
        else:
            import tensorflow as tf

            return tf.dtypes.float32
    else:
        return __SETTINGS__._DATATYPE


def set_datatype(datatype):
    """Set the datatype to use for Tensors

    Parameters
    ----------
    datatype : tf.dtype or torch.dtype
        The default datatype to use
    """
    if get_backend() == "pytorch":
        import torch

        if datatype is None or isinstance(datatype, torch.dtype):
            __SETTINGS__._DATATYPE = datatype
        else:
            raise TypeError("datatype must be a torch.dtype")
    else:
        import tensorflow as tf

        if datatype is None or isinstance(datatype, tf.dtypes.DType):
            __SETTINGS__._DATATYPE = datatype
        else:
            raise TypeError("datatype must be a tf.dtypes.DType")


def get_samples():
    """Get how many samples (if any) are being drawn from parameter posteriors

    Returns
    -------
    n : None or int > 0
        Number of samples (if any) to draw from parameters' posteriors.
        Default = None (ie, use the Maximum a posteriori estimate)
    """
    return __SETTINGS__._SAMPLES


def set_samples(samples):
    """Set how many samples (if any) to draw from parameter posteriors

    Parameters
    ----------
    samples : None or int > 0
        Number of samples (if any) to draw from parameters' posteriors.
    """
    if samples is not None and not isinstance(samples, int):
        raise TypeError("samples must be an int or None")
    elif isinstance(samples, int) and samples < 1:
        raise ValueError("samples must be positive")
    else:
        __SETTINGS__._SAMPLES = samples


def get_flipout():
    """Get whether flipout is currently being used where possible.

    Returns
    -------
    flipout : bool
        Whether flipout is currently being used where possible while sampling
        during training.
    """
    return __SETTINGS__._FLIPOUT


def set_flipout(flipout):
    """Set whether to use flipout where possible while sampling during training

    Parameters
    ----------
    flipout : bool
        Whether to use flipout where possible while sampling during training.
    """
    if isinstance(flipout, bool):
        __SETTINGS__._FLIPOUT = flipout
    else:
        raise TypeError("flipout must be True or False")


def get_static_sampling_uuid():
    """Get the current static sampling UUID"""
    return __SETTINGS__._STATIC_SAMPLING_UUID


def set_static_sampling_uuid(uuid_value):
    """Set the current static sampling UUID"""
    if uuid_value is None or isinstance(uuid_value, uuid.UUID):
        __SETTINGS__._STATIC_SAMPLING_UUID = uuid_value
    else:
        raise TypeError("must be a uuid or None")


class Sampling:
    """Use sampling while within this context manager.


    Keyword Arguments
    -----------------
    n : None or int > 0
        Number of samples (if any) to draw from parameters' posteriors.
        Default = 1
    flipout : bool
        Whether to use flipout where possible while sampling during training.
        Default = False


    Example
    -------

    To use maximum a posteriori estimates of the parameter values, don't use
    the sampling context manager:

    .. code-block:: pycon

        >>> import probflow as pf
        >>> param = pf.Parameter()
        >>> param()
        [0.07226744]
        >>> param() # MAP estimate is always the same
        [0.07226744]

    To use a single sample, use the sampling context manager with ``n=1``:

    .. code-block:: pycon

        >>> with pf.Sampling(n=1):
        >>>     param()
        [-2.2228503]
        >>> with pf.Sampling(n=1):
        >>>     param() #samples are different
        [1.3473024]

    To use multiple samples, use the sampling context manager and set the
    number of samples to take with the ``n`` keyword argument:

    .. code-block:: pycon

        >>> with pf.Sampling(n=3):
        >>>     param()
        [[ 0.10457394]
         [ 0.14018342]
         [-1.8649881 ]]
        >>> with pf.Sampling(n=5):
        >>>     param()
        [[ 2.1035051]
         [-2.641631 ]
         [-2.9091313]
         [ 3.5294306]
         [ 1.6596333]]

    To use static samples - that is, to always return the same samples while in
    the same context manager - use the sampling context manager with the
    ``static`` keyword argument set to ``True``:

    .. code-block:: pycon

        >>> with pf.Sampling(static=True):
        >>>     param()
        [ 0.10457394]
        >>>     param()  # repeated samples yield the same value
        [ 0.10457394]
        >>> with pf.Sampling(static=True):
        >>>     param()  # under a new context manager they yield new samples
        [-2.641631]
        >>>     param()  # but remain the same while under the same context
        [-2.641631]

    """

    def __init__(self, n=None, flipout=None, static=None):
        self._n = n
        self._flipout = flipout
        self._static = static

    def __enter__(self):
        """Begin sampling."""
        if self._n is not None:
            set_samples(self._n)
        if self._flipout is not None:
            set_flipout(self._flipout)
        if self._static is not None:
            set_static_sampling_uuid(uuid.uuid4())

    def __exit__(self, _type, _val, _tb):
        """End sampling and reset sampling settings to defaults"""
        if self._n is not None:
            set_samples(None)
        if self._flipout is not None:
            set_flipout(False)
        if self._static is not None:
            set_static_sampling_uuid(None)
