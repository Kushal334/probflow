import probflow.utils.ops as O
from probflow.modules.module import Module
from probflow.parameters import DeterministicParameter, Parameter
from probflow.utils.casting import to_tensor
from probflow.utils.settings import get_flipout, get_samples


class Dense(Module):
    """Dense neural network layer.

    TODO

    .. admonition:: Will not use flipout when n_mc>1

        Note that this module uses the flipout estimator by default, but will
        not use the flipout estimator when we are taking multiple monte carlo
        samples per batch (when `n_mc` > 1).  See :meth:`.Model.fit` for more
        info on setting the value of `n_mc`.


    Parameters
    ----------
    d_in : int
        Number of input dimensions.
    d_out : int
        Number of output dimensions (number of "units").
    probabilistic : bool
        Whether variational posteriors for the weights and biases should be
        probabilistic.  If True (the default), will use Normal distributions
        for the variational posteriors.  If False, will use Deterministic
        distributions.
    flipout: bool
        Whether to use the flipout estimator for this layer.  Default is True.
        Usually, when the global flipout setting is set to True, will use
        flipout during training but not during inference.  If this kwarg is set
        to False, will not use flipout even during training.
    weight_kwargs : dict
        Additional kwargs to pass to the Parameter constructor for the weight
        parameters.  Default is an empty dict.
    bias_kwargs : dict
        Additional kwargs to pass to the Parameter constructor for the bias
        parameters.  Default is an empty dict.
    name : str
        Name of this layer
    """

    def __init__(
        self,
        d_in: int,
        d_out: int = 1,
        probabilistic: bool = True,
        flipout: bool = True,
        weight_kwargs: dict = {},
        bias_kwargs: dict = {},
        name: str = "Dense",
    ):

        # Check values
        if d_in < 1:
            raise ValueError("d_in must be >0")
        if d_out < 1:
            raise ValueError("d_out must be >0")

        # Determine what parameter class to use
        ParameterClass = Parameter if probabilistic else DeterministicParameter

        # Create the parameters
        self.probabilistic = probabilistic
        self.flipout = flipout
        self.d_in = d_in
        self.d_out = d_out
        self.weights = ParameterClass(
            shape=[d_in, d_out], name=name + "_weights", **weight_kwargs
        )
        self.bias = ParameterClass(
            shape=[1, d_out], name=name + "_bias", **bias_kwargs
        )

    def __call__(self, x):
        """Perform the forward pass"""

        x = to_tensor(x)

        # Using the Flipout estimator
        if (
            get_flipout()
            and self.flipout
            and self.probabilistic
            and get_samples() is not None
            and get_samples() == 1
        ):

            # Flipout-estimated weight samples
            s = O.rand_rademacher(O.shape(x))
            r = O.rand_rademacher([O.shape(x)[0], self.d_out])
            norm_samples = O.randn([self.d_in, self.d_out])
            w_samples = self.weights.variables["scale"] * norm_samples
            w_noise = r * ((x * s) @ w_samples)
            w_outputs = x @ self.weights.variables["loc"] + w_noise

            # Flipout-estimated bias samples
            r = O.rand_rademacher([O.shape(x)[0], self.d_out])
            norm_samples = O.randn([self.d_out])
            b_samples = self.bias.variables["scale"] * norm_samples
            b_outputs = self.bias.variables["loc"] + r * b_samples

            return w_outputs + b_outputs

        # Without Flipout
        else:
            return x @ self.weights() + self.bias()
