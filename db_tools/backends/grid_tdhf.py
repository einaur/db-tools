import numpy as np

from db_tools import DBTools
from .run_results import (
    RunResults,
    AttrDict,
    allow_exactly_one_fileroot,
    unwrap_0d_arrays,
)


class GridTDHFResults(RunResults):
    def __init__(self, fileroot, info, samples, state):
        self.fileroot = fileroot
        self.info = AttrDict(unwrap_0d_arrays(info))
        self.samples = AttrDict(samples)
        if state is None:
            self.state = None
        else:
            self.state = AttrDict(state)


class DBGridTDHF(DBTools):
    def load(self, load_state=True):
        fileroot = allow_exactly_one_fileroot(self.fileroots)
        info = np.load(f"{self.prefix}/{fileroot}_info.npz", allow_pickle=True)
        samples = np.load(f"{self.prefix}/{fileroot}_samples.npz", allow_pickle=True)
        if load_state:
            state = np.load(f"{self.prefix}/{fileroot}_state.npz", allow_pickle=True)

        return GridTDHFResults(fileroot, info, samples, state)
