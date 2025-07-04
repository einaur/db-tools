"""
example: plotting simulation results from grid-tdhf using db-tools
"""

from db_tools import DBTools

import numpy as np
import matplotlib.pyplot as plt

# set up DBTools instance
output_dir = "output"
dbtools = DBTools(prefix=output_dir)

# optional: set base filters which will be included in
# every subsequent .search() call unless you override it
dbtools.set_base_filters(
    comment="example_runs",
    E0=1.0,
    dt=0.1,
    omega=0.2,
)

# search for runs by their parameters
fileroot1 = dbtools.search(r_max=20, N=30)[0]
fileroot2 = dbtools.search(r_max=30, N=45)[0]
fileroot3 = dbtools.search(r_max=40, N=60)[0]

# fetch and print input parameters for a run
inputs1 = dbtools.get_inputs(fileroot1)[0]
print("omega:", inputs1["omega"])
print("l_max:", inputs1["l_max"])

samples1 = np.load(f"{output_dir}/{fileroot1}_samples.npz")
samples2 = np.load(f"{output_dir}/{fileroot2}_samples.npz")
samples3 = np.load(f"{output_dir}/{fileroot3}_samples.npz")

t1 = samples1["time_points"]
t2 = samples2["time_points"]
t3 = samples3["time_points"]

z1 = samples1["expec_z"]
z2 = samples2["expec_z"]
z3 = samples3["expec_z"]

plt.plot(t1, z1.real)
plt.plot(t2, z2.real)
plt.plot(t3, z3.real, "--")

plt.show()
