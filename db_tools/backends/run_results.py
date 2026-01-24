import numpy as np


class AttrDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class RunResults:
    """generic class for storing run results"""


def allow_exactly_one_fileroot(fileroots):
    if isinstance(fileroots, str):
        return fileroots

    if isinstance(fileroots, list):
        n_fileroots = len(fileroots)

        if n_fileroots == 1:
            return fileroots[0]

        if n_fileroots == 0:
            raise NoMatchError("The DBTools instance does not have any fileroots")
        else:
            raise MultipleMatchesError("The DBTools instance has multiple fileroots")

    else:
        raise TypeError("Fileroots must be of type 'str' or 'list'")


def unwrap_0d_arrays(d):
    ret = {}
    for key, val in d.items():
        if isinstance(val, np.ndarray) and val.ndim == 0:
            ret[key] = val.item()
        else:
            ret[key] = val

    return ret
