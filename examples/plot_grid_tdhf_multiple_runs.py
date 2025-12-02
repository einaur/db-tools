"""
example:    a minimal example for plotting grid-tdhf expec_z for a
            single output located in the 'output/' directory

"""

from db_tools.backends import DBGridTDHF

import matplotlib.pyplot as plt

# set up DBTools instance

dbtools = (
    DBGridTDHF()
    .with_prefix("output")  # only needed if the prefix is not "output"
    .with_base_filters(
        tag="example_runs",
        E0=0.01,
        dt=0.1,
        omega=0.2,
    )
)

results1 = dbtools.search(r_max=32, N=48).load()
results2 = dbtools.search(r_max=36, N=54).load()
results3 = dbtools.search(r_max=40, N=60).load()

t1 = results1.samples.time_points
t2 = results2.samples.time_points
t3 = results3.samples.time_points

z1 = results1.samples.expec_z
z2 = results2.samples.expec_z
z3 = results3.samples.expec_z

plt.plot(t1, z1.real)
plt.plot(t2, z2.real)
plt.plot(t3, z3.real, "--")

plt.show()

# access inputs dict
print("r_max1:", results1.info.inputs["r_max"])
print("r_max2:", results2.info.inputs["r_max"])
