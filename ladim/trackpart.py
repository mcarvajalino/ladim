# ------------------------------------
# trackpart.py
# Part of the LADIM Model
#
# Bjørn Ådllandsvik, <bjorn@imr.no>
# Institute of Marine Research
#
# Licenced under the MIT license
# ------------------------------------

import numpy as np


class TrackPart:
    """The physical particle tracking kernel"""

    def __init__(self, config):
        self.dt = config.dt
        if config.advection:
            self.advect = getattr(self, config.advection)
        else:
            self.advect = None
        # Read from config:
        self.diffusion = config.diffusion
        if self.diffusion:
            self.D = config.diffusion_coefficient  # [m2.s-1]

    def move_particles(self, grid, forcing, state):
        """Move the particles"""

        X, Y = state.X, state.Y
        self.pm, self.pn = grid.sample_metric(X, Y)
        print("type pm: ", self.pm.dtype)
        dt = self.dt
        print("type dt: ", type(dt))
        self.num_particles = len(X)

        U = np.zeros(self.num_particles, dtype=np.float32)
        V = np.zeros(self.num_particles, dtype=np.float32)

        # --- Advection ---
        if self.advect:
            Uadv, Vadv = self.advect(grid, forcing, state)
            U += Uadv
            V += Vadv
        print("type U, Uadv:", U.dtype, Uadv.dtype)

        # --- Diffusion ---
        if self.diffusion:
            Udiff, Vdiff = self.diffuse()
            U += Udiff
            V += Vdiff
        print("type U, Udiff:", U.dtype, Udiff.dtype)

        # --- Move the particles

        # New position, if OK
        X1 = X + U * self.pm * dt
        Y1 = Y + V * self.pn * dt

        # Land, boundary treatment. Do not move the particles
        # Consider a sequence of different actions
        # I = (grid.ingrid(X1, Y1)) & (grid.atsea(X1, Y1))
        I = grid.atsea(X1, Y1)
        # I = True
        X[I] = X1[I]
        Y[I] = Y1[I]

        state.X = X
        state.Y = Y
        print("**** X", state.X.dtype)
        print("**** X", X.dtype)
        print("**** X", state.X.dtype)
        1/0


    def EF(self, grid, forcing, state):
        """Euler-Forward advection"""

        X, Y, Z = state['X'], state['Y'], state['Z']
        # dt = self.dt
        # pm, pn = grid.sample_metric(X, Y)

        U, V = forcing.sample_velocity(X, Y, Z)

        return U, V

    def RK2(self, grid, forcing, state):
        """Runge-Kutta second order = Heun scheme"""

        X, Y, Z = state['X'], state['Y'], state['Z']
        dt = self.dt
        pm, pn = grid.sample_metric(X, Y)

        print("RK2: X", X.dtype)

        U, V = forcing.sample_velocity(X, Y, Z)
        X1 = X + 0.5 * U * pm * dt
        Y1 = Y + 0.5 * V * pn * dt

        print("RK2: X1", X1.dtype)


        U, V = forcing.sample_velocity(X1, Y1, Z, tstep=0.5)

        print("RK2: U", U.dtype)

        return U, V

    def RK4(self, grid, forcing, state):
        """Runge-Kutta fourth order advection"""

        X, Y, Z = state['X'], state['Y'], state['Z']
        dt = self.dt
        pm, pn = grid.sample_metric(X, Y)

        U1, V1 = forcing.sample_velocity(X, Y, Z, tstep=0.0)
        X1 = X + 0.5 * U1 * pm * dt
        Y1 = Y + 0.5 * V1 * pn * dt

        U2, V2 = forcing.sample_velocity(X1, Y1, Z, tstep=0.5)
        X2 = X + 0.5 * U2 * pm * dt
        Y2 = Y + 0.5 * V2 * pn * dt

        U3, V3 = forcing.sample_velocity(X2, Y2, Z, tstep=0.5)
        X3 = X + U3 * pm * dt
        Y3 = Y + V3 * pn * dt

        U4, V4 = forcing.sample_velocity(X3, Y3, Z, tstep=1.0)

        U = (U1 + 2*U2 + 2*U3 + U4) / 6.0
        V = (V1 + 2*V2 + 2*V3 + V4) / 6.0

        return U, V

    def diffuse(self):
        """Random walk diffusion"""

        # Diffusive velocity
        stddev = (2*self.D/self.dt)**0.5
        U = stddev * np.random.normal(size=self.num_particles).astype(np.float32)
        V = stddev * np.random.normal(size=self.num_particles).astype(np.float32)

        return U, V
