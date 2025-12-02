"""
example:    a minimal example for plotting grid-tdhf expec_z for a
            single output located in the 'output/' directory

"""

from db_tools.backends import DBGridTDHF

import matplotlib.pyplot as plt

# set up DBTools instance

results = (
    DBGridTDHF()
    .search(
        tag="example_runs",
        E0=0.01,
        dt=0.1,
        omega=0.2,
        r_max=40,
        N=60,
    )
    .load()
)

t = results.samples.time_points
z = results.samples.expec_z

plt.plot(t, z.real)

plt.show()
