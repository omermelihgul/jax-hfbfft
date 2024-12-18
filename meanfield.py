import jax
from jax import numpy as jnp
from functools import partial
from dataclasses import dataclass
from jax.tree_util import register_dataclass
from levels import cdervx00, cdervx02, cdervy00, cdervy02, cdervz00, cdervz02

@partial(register_dataclass,
         data_fields=['upot', 'bmass', 'divaq', 'v_pair', 'aq',
                      'spot', 'wlspot', 'dbmass', 'ecorrp'],
         meta_fields=[])
@dataclass
class Meanfield:
    upot: jax.Array
    bmass: jax.Array
    divaq: jax.Array
    v_pair: jax.Array

    aq: jax.Array
    spot: jax.Array
    wlspot: jax.Array
    dbmass: jax.Array

    ecorrp: float

def init_meanfield(grids) -> Meanfield:
    shape4d = (2, grids.nx, grids.ny, grids.nz)
    shape5d = (2, 3, grids.nx, grids.ny, grids.nz)

    default_kwargs = {
        'upot': jnp.zeros(shape4d, dtype=jnp.float64),
        'bmass': jnp.zeros(shape4d, dtype=jnp.float64),
        'divaq': jnp.zeros(shape4d, dtype=jnp.float64),
        'v_pair': jnp.zeros(shape4d, dtype=jnp.float64),
        'aq': jnp.zeros(shape5d, dtype=jnp.float64),
        'spot': jnp.zeros(shape5d, dtype=jnp.float64),
        'wlspot': jnp.zeros(shape5d, dtype=jnp.float64),
        'dbmass': jnp.zeros(shape5d, dtype=jnp.float64),
        'ecorrp': 0.0
    }
    return Meanfield(**default_kwargs)


def hpsi0fft(grids, meanfield, iq, pinn):
    sigis = jnp.array([0.5, -0.5])

    pout = jnp.multiply(pinn, meanfield.upot[iq,...])

    pout = pout.at[0,...].add(
        jax.lax.complex(meanfield.spot[iq,0,...], - meanfield.spot[iq,1,...]) * \
        pinn[1,...] + meanfield.spot[iq,2,...] * pinn[0,...])

    pout = pout.at[1,...].add(
        jax.lax.complex(meanfield.spot[iq,0,...], meanfield.spot[iq,1,...]) * \
        pinn[0,...] - meanfield.spot[iq,2,...] * pinn[1,...])

    pswk, pswk2 = cdervx02(grids.dx, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -jax.lax.complex(0.0, 0.5 * meanfield.aq[iq,0,...] - sigis[0] * meanfield.wlspot[iq,1,...]) * \
        pswk[0,...] - sigis[0] * meanfield.wlspot[iq,2,...] * pswk[1,...] - pswk2[0,...])

    pout = pout.at[1,...].add(
        -jax.lax.complex(0.0, 0.5 * meanfield.aq[iq,0,...] - sigis[1] * meanfield.wlspot[iq,1,...]) * \
        pswk[1,...] - sigis[1] * meanfield.wlspot[iq,2,...] * pswk[0,...] - pswk2[1,...])

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 0.5j) * (meanfield.aq[iq,0,...] - meanfield.wlspot[iq,1,...]) * \
        pinn[0,...] - 0.5 * meanfield.wlspot[iq,2,...] * pinn[1,...])

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 0.5j) * (meanfield.aq[iq,0,...] + meanfield.wlspot[iq,1,...]) * \
        pinn[1,...] + 0.5 * meanfield.wlspot[iq,2,...] * pinn[0,...])

    pswk = cdervx00(grids.dx, pswk2)

    pout = pout.at[...].add(pswk)

    pswk, pswk2 = cdervy02(grids.dy, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -jax.lax.complex(0.0, 0.5 * meanfield.aq[iq,1,...] + sigis[0] * meanfield.wlspot[iq,0,...]) * \
        pswk[0,...] + jax.lax.complex(0.0, 0.5 * meanfield.wlspot[iq,2,...]) * \
        pswk[1,...] - pswk2[0,...])

    pout = pout.at[1,...].add(
        -jax.lax.complex(0.0, 0.5 * meanfield.aq[iq,1,...] + sigis[1] * meanfield.wlspot[iq,0,...]) * \
        pswk[1,...] + jax.lax.complex(0.0, 0.5 * meanfield.wlspot[iq,2,...]) * \
        pswk[0,...] - pswk2[1,...])

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 0.5j) * (meanfield.aq[iq,1,...] + meanfield.wlspot[iq,0,...]) * \
        pinn[0,...] + (0.0 + 0.5j) * meanfield.wlspot[iq,2,...] * pinn[1,...])

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 0.5j) * (meanfield.aq[iq,1,...] - meanfield.wlspot[iq,0,...]) * \
        pinn[1,...] + (0.0 + 0.5j) * meanfield.wlspot[iq,2,...] * pinn[0,...])

    pswk = cdervy00(grids.dy, pswk2)

    pout = pout.at[...].add(pswk)

    pswk, pswk2 = cdervz02(grids.dz, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -jax.lax.complex(0.0, 0.5 * meanfield.aq[iq,2,...]) * pswk[0,...] + \
        jax.lax.complex(sigis[0] * meanfield.wlspot[iq,0,...], -0.5 * meanfield.wlspot[iq,1,...]) * \
        pswk[1,...] - pswk2[0,...])

    pout = pout.at[1,...].add(
        -jax.lax.complex(0.0, 0.5 * meanfield.aq[iq,2,...]) * pswk[1,...] + \
        jax.lax.complex(sigis[1] * meanfield.wlspot[iq,0,...], -0.5 * meanfield.wlspot[iq,1,...]) * \
        pswk[0,...] - pswk2[1,...])

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 0.5j) * meanfield.aq[iq,2,...] * pinn[0,...] + \
        jax.lax.complex(0.5 * meanfield.wlspot[iq,0,...], -0.5 * meanfield.wlspot[iq,1,...]) * \
        pinn[1,...])

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 0.5j) * meanfield.aq[iq,2,...] * pinn[1,...] + \
        jax.lax.complex(0.5 * meanfield.wlspot[iq,0,...], -0.5 * meanfield.wlspot[iq,1,...]) * \
        pinn[0,...])

    pswk = cdervz00(grids.dz, pswk2)

    pout = pout.at[...].add(pswk)

    return pout

hpsi0fft_jit = jax.jit(hpsi0fft)


def hpsi00(grids, meanfield, iq, weight, weightuv, pinn):
    sigis = jnp.array([0.5, -0.5])

    # Step 1: non-derivative parts not involving spin
    pout = jnp.multiply(pinn, meanfield.upot[iq,...])

    # Step 2: the spin-current coupling
    pout = pout.at[0,...].add(
        (meanfield.spot[iq,0,...] - 1j * meanfield.spot[iq,1,...]) * \
        pinn[1,...] + meanfield.spot[iq,2,...] * pinn[0,...]
    )

    pout = pout.at[1,...].add(
        (meanfield.spot[iq,0,...] + 1j * meanfield.spot[iq,1,...]) * \
        pinn[0,...] - meanfield.spot[iq,2,...] * pinn[1,...]
    )

    # Step 3: derivative terms in x
    pswk, pswk2 = cdervx02(grids.dx, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,0,...] - sigis[0] * \
        meanfield.wlspot[iq,1,...])) * pswk[0,...] - sigis[0] * \
        meanfield.wlspot[iq,2,...] * pswk[1,...] - pswk2[0,...]
    )

    pout = pout.at[1,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,0,...] - sigis[1] * \
        meanfield.wlspot[iq,1,...])) * pswk[1,...] - sigis[1] * \
        meanfield.wlspot[iq,2,...] * pswk[0,...] - pswk2[1,...]
    )

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 1j * 0.5) * (meanfield.aq[iq,0,...] - meanfield.wlspot[iq,1,...]) * \
        pinn[0,...] - 0.5 * meanfield.wlspot[iq,2,...] * pinn[1,...]
    )

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 1j * 0.5) * (meanfield.aq[iq,0,...] + meanfield.wlspot[iq,1,...]) * \
        pinn[1,...] + 0.5 * meanfield.wlspot[iq,2,...] * pinn[0,...]
    )

    pswk = cdervx00(grids.dx, pswk2)

    pout = pout.at[...].add(pswk)

    # Step 4: derivative terms in y
    pswk, pswk2 = cdervy02(grids.dy, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,1,...] + sigis[0] * \
        meanfield.wlspot[iq,0,...])) * pswk[0,...] + (0.0 + 1j * (0.5 * \
        meanfield.wlspot[iq,2,...])) * pswk[1,...] - pswk2[0,...]
    )

    pout = pout.at[1,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,1,...] + sigis[1] * \
        meanfield.wlspot[iq,0,...])) * pswk[1,...] + (0.0 + 1j * (0.5 * \
        meanfield.wlspot[iq,2,...])) * pswk[0,...] - pswk2[1,...]
    )

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 1j * 0.5) * (meanfield.aq[iq,1,...] + meanfield.wlspot[iq,0,...]) * \
        pinn[0,...] + (0.0 + 1j * 0.5) * meanfield.wlspot[iq,2,...] * pinn[1,...]
    )

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 1j * 0.5) * (meanfield.aq[iq,1,...] - meanfield.wlspot[iq,0,...]) * \
        pinn[1,...] + (0.0 + 1j * 0.5 * meanfield.wlspot[iq,2,...]) * pinn[0,...]
    )

    pswk = cdervy00(grids.dy, pswk2)

    pout = pout.at[...].add(pswk)

    # Step 5: derivative terms in z
    pswk, pswk2 = cdervz02(grids.dz, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,2,...])) * pswk[0,...] + \
        (sigis[0] * meanfield.wlspot[iq,0,...] - 1j * (0.5 * \
        meanfield.wlspot[iq,1,...])) * pswk[1,...] - pswk2[0,...]
    )

    pout = pout.at[1,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,2,...])) * pswk[1,...] + \
        (sigis[1] * meanfield.wlspot[iq,0,...] - 1j * (0.5 * \
        meanfield.wlspot[iq,1,...])) * pswk[0,...] - pswk2[1,...]
    )

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 1j * 0.5) * meanfield.aq[iq,2,...] * pinn[0,...] + \
        (0.5 * meanfield.wlspot[iq,0,...] - 1j * (0.5 * meanfield.wlspot[iq,1,...])) * pinn[1,...]
    )

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 1j * 0.5) * meanfield.aq[iq,2,...] * pinn[1,...] + \
        (-0.5 * meanfield.wlspot[iq,0,...] - 1j * (0.5 * meanfield.wlspot[iq,1,...])) * pinn[0,...]
    )

    pswk = cdervz00(grids.dz, pswk2)

    pout = pout.at[...].add(pswk)

    # Step 6: multiply weight and single-particle
    # Hamiltonian, then add pairing part to pout
    pout_mf = jnp.copy(pout)

    pout = pout.at[0,...].set(
        weight * pout[0,...] - weightuv * meanfield.v_pair[iq,...] * pinn[0,...]
    )

    pout = pout.at[1,...].set(
        weight * pout[1,...] - weightuv * meanfield.v_pair[iq,...] * pinn[1,...]
    )

    return pout, pout_mf

hpsi00_jit = jax.jit(hpsi00)

def hpsi01(grids, meanfield, iq, weight, weightuv, pinn):
    sigis = jnp.array([0.5, -0.5])

    # Step 1: non-derivative parts not involving spin
    pout = jnp.multiply(pinn, meanfield.upot[iq,...])

    # Step 2: the spin-current coupling
    pout = pout.at[0,...].add(
        (meanfield.spot[iq,0,...] - 1j * meanfield.spot[iq,1,...]) * \
        pinn[1,...] + meanfield.spot[iq,2,...] * pinn[0,...]
    )

    pout = pout.at[1,...].add(
        (meanfield.spot[iq,0,...] + 1j * meanfield.spot[iq,1,...]) * \
        pinn[0,...] - meanfield.spot[iq,2,...] * pinn[1,...]
    )

    # Step 3: derivative terms in x
    pswk, pswk2 = cdervx02(grids.dx, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,0,...] - sigis[0] * \
        meanfield.wlspot[iq,1,...])) * pswk[0,...] - sigis[0] * \
        meanfield.wlspot[iq,2,...] * pswk[1,...] - pswk2[0,...]
    )

    pout = pout.at[1,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,0,...] - sigis[1] * \
        meanfield.wlspot[iq,1,...])) * pswk[1,...] - sigis[1] * \
        meanfield.wlspot[iq,2,...] * pswk[0,...] - pswk2[1,...]
    )

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 1j * 0.5) * (meanfield.aq[iq,0,...] - meanfield.wlspot[iq,1,...]) * \
        pinn[0,...] - 0.5 * meanfield.wlspot[iq,2,...] * pinn[1,...]
    )

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 1j * 0.5) * (meanfield.aq[iq,0,...] + meanfield.wlspot[iq,1,...]) * \
        pinn[1,...] + 0.5 * meanfield.wlspot[iq,2,...] * pinn[0,...]
    )

    pswk = cdervx00(grids.dx, pswk2)

    pout = pout.at[...].add(pswk)

    # Step 4: derivative terms in y
    pswk, pswk2 = cdervy02(grids.dy, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,1,...] + sigis[0] * \
        meanfield.wlspot[iq,0,...])) * pswk[0,...] + (0.0 + 1j * (0.5 * \
        meanfield.wlspot[iq,2,...])) * pswk[1,...] - pswk2[0,...]
    )

    pout = pout.at[1,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,1,...] + sigis[1] * \
        meanfield.wlspot[iq,0,...])) * pswk[1,...] + (0.0 + 1j * (0.5 * \
        meanfield.wlspot[iq,2,...])) * pswk[0,...] - pswk2[1,...]
    )

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 1j * 0.5) * (meanfield.aq[iq,1,...] + meanfield.wlspot[iq,0,...]) * \
        pinn[0,...] + (0.0 + 1j * 0.5) * meanfield.wlspot[iq,2,...] * pinn[1,...]
    )

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 1j * 0.5) * (meanfield.aq[iq,1,...] - meanfield.wlspot[iq,0,...]) * \
        pinn[1,...] + (0.0 + 1j * 0.5 * meanfield.wlspot[iq,2,...]) * pinn[0,...]
    )

    pswk = cdervy00(grids.dy, pswk2)

    pout = pout.at[...].add(pswk)

    # Step 5: derivative terms in z
    pswk, pswk2 = cdervz02(grids.dz, pinn, meanfield.bmass[iq,...])

    pout = pout.at[0,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,2,...])) * pswk[0,...] + \
        (sigis[0] * meanfield.wlspot[iq,0,...] - 1j * (0.5 * \
        meanfield.wlspot[iq,1,...])) * pswk[1,...] - pswk2[0,...]
    )

    pout = pout.at[1,...].add(
        -(0.0 + 1j * (0.5 * meanfield.aq[iq,2,...])) * pswk[1,...] + \
        (sigis[1] * meanfield.wlspot[iq,0,...] - 1j * (0.5 * \
        meanfield.wlspot[iq,1,...])) * pswk[0,...] - pswk2[1,...]
    )

    pswk2 = pswk2.at[0,...].set(
        (0.0 - 1j * 0.5) * meanfield.aq[iq,2,...] * pinn[0,...] + \
        (0.5 * meanfield.wlspot[iq,0,...] - 1j * (0.5 * meanfield.wlspot[iq,1,...])) * pinn[1,...]
    )

    pswk2 = pswk2.at[1,...].set(
        (0.0 - 1j * 0.5) * meanfield.aq[iq,2,...] * pinn[1,...] + \
        (-0.5 * meanfield.wlspot[iq,0,...] - 1j * (0.5 * meanfield.wlspot[iq,1,...])) * pinn[0,...]
    )

    pswk = cdervz00(grids.dz, pswk2)

    pout = pout.at[...].add(pswk)

    # Step 6: multiply weight and single-particle
    # Hamiltonian, then add pairing part to pout
    pout_mf = jnp.copy(pout)

    pout_del = jnp.multiply(pinn, meanfield.v_pair[iq,...])

    pout = pout.at[...].set(
        weight * pout - weightuv * pout_del
    )

    return pout, pout_mf, pout_del


hpsi01_jit = jax.jit(hpsi01)


















'''
def skyrme(
    meanfield,
    densities,
    forces,
    params,
    coulomb
    grids
):
    epsilon = 1.0e-25

    for iq in range(2):
        ic = 3 - iq
        meanfield.upot = meanfield.upot.at[iq,...].set(

        )


    # iq = 0
'''





'''
    meanfield.upot = meanfield.upot.at[0,...].set(
        (densities.rho[0,...] + densities.rho[1,...]) ** forces.power *
        (
            (forces.b3 * (forces.power + 2.0) / 3.0 - 2.0 * forces.b3p / 3.0) *
            densities.rho[0,...] + forces.b3 * (forces.power + 2.0) / 3.0 *
            densities.rho[1,...] - (forces.b3p * forces./power / 3.0) *
            (densities.rho[0,...] ** 2 + densities.rho[1,...] ** 2) /
            (densities.rho[0,...] + densities.rho[1,...] + epsilon)
         )
    )

    # iq = 1
    meanfield.upot = meanfield.upot.at[1,...].set(
        (densities.rho[0,...] + densities.rho[1,...]) ** forces.power *
        (
            (forces.b3 * (forces.power + 2.0) / 3.0 - 2.0 * forces.b3p / 3.0) *
            densities.rho[1,...] + forces.b3 * (forces.power + 2.0) / 3.0 *
            densities.rho[0,...] - (forces.b3p * forces.power / 3.0) *
            (densities.rho[0,...] ** 2 + densities.rho[1,...] ** 2) /
            (densities.rho[0,...] + densities.rho[1,...] + epsilon)
         )
    )

    # Step 2: add divergence of spin-orbit current to upot

    # CALL rmulx
    # CALL rmuly
    # CALL rmulz

    # iq = 0
    meanfield.upot = meanfield.upot.at[0,...].add(
        -(forces.b4 + forces.b4p) * workden[0,...] - forces.b4 * workden[1,...]
    )

    # iq = 1
    meanfield.upot = meanfield.upot.at[1,...].add(
        -(forces.b4 + forces.b4p) * workden[1,...] - forces.b4 * workden[0,...]
    )

    # Step 3: Coulomb potential
    if params.tcoul:
        # CALL poisson !!!
        meanfield.upot = meanfield.upot.at[1,...].add(coulomb.wcoul)
        if forces.ex != 0:
            meanfield.upot = meanfield.upot.at[1,...].add(
                -forces.slate * densities.rho[1,...] ** (1.0/3.0)
            )

    # Step 4: remaining terms of upot
    workvec = jnp.array((2, 3, grids.nx, grids.ny, grids.nz), dtype=jnp.float64)

    # DO iq=1,2
        # rmul (x, y ,z)
    # END DO

    # iq, ic = 0, 1
    meanfield.upot = meanfield.upot.at[0,...].add(
        (forces.b0 - forces.b0p) * meanfield.rho[0,...] + forces.b0 * meanfield.rho[1,...] +
        (forces.b1 - forces.b1p) * densities.tau[0,...] + forces.b1 * densities.tau[1,...] -
        (forces.b2 - forces.b2p) * workden[0,...] - forces.b2 * workden[1,...]
    )

    # Step 5.0: effective mass
    meanfield.bmass = meanfield.bmass.at[0,...].set(
        forces.h2m[0] + (forces.b1 - forces.b1p) * densities.rho[0,...] + forces.b1 * densities.rho[1,...]
    )

    # Step 6.0: calculate grad(rho) and wlspot
    # CALL rmuly
    # CALL rmuly
    # CALL rmulz

    # iq, ic = 1, 0
    meanfield.upot = meanfield.upot.at[1,...].add(
        (forces.b0 - forces.b0p) * meanfield.rho[1,...] + forces.b0 * meanfield.rho[0,...] +
        (forces.b1 - forces.b1p) * densities.tau[1,...] + forces.b1 * densities.tau[0,...] -
        (forces.b2 - forces.b2p) * workden[1,...] - forces.b2 * workden[0,...]
    )

    # Step 5.5: effective mass
    meanfield.bmass = meanfield.bmass.at[1,...].set(
        forces.h2m[1] + (forces.b1 - forces.b1p) * densities.rho[1,...] + forces.b1 * densities.rho[0,...]
    )

    # Step 6.5: calculate grad(rho) and wlspot
    # CALL rmulx
    # CALL rmuly
    # CALL rmulz

    # iq, ic = 0, 1


    pass
'''
