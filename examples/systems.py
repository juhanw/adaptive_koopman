import numpy as np
import pystorms

class system:
    def __init__(self, system="pystorm Delta"):
        """
        Define bounds for states, inputs, and extra observables
        Define 
        """
        if system == "pystorm Delta":
            self.systemName = "Delta"
            self.statesUpper = np.asarray([5.7, 9.5, 5.92, 6.59, 11.99]) # [BC, BS, N1, N2, N3]
            self.statesLower = np.asarray([2.21, 0, 2.11, 4.04, 5.28])
            self.inputUpper = np.ones((1,5))
            self.inputLower = 0*np.ones((1,5))
            self.simulator = pystorms.scenarios.delta() # states = [BC, BS, N1, N2, N3, N4]

        if system == "pystorm Theta":
            self.systemName = "Theta"
            self.statesUpper = np.asarray([0.5, 0.5])
            self.statesLower = np.asarray([-0.1, -0.1])
            self.inputUpper = np.ones((1,5))
            self.inputLower = 0*np.ones((1,5))
            self.simulator = pystorms.scenarios.theta() # states = [P1, P2]
            self.metricUpper = 0.5
            self.metricLower = 0

    def stateBounds(self):
        return self.statesUpper, self.statesLower

    def inputBounds(self):
        return self.inputUpper, self.inputLower

    def metricBounds(self):
        return self.metricUpper, self.metricLower
    
    def simulate(self,actions):
        done = self.simulator.step(actions)
        states = self.simulator.state()
        if self.systemName == "Delta":
            return done, states
        elif self.systemName == "Theta":
            metrics = self.simulator.data_log["flow"]["8"]
            return done, states, metrics


