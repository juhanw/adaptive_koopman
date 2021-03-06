import numpy as np
# change init in test!
class Koopman:
    def __init__(self, Xub, Xlb, Uub, Ulb, num_lift=2, weighting=0.96, Mub=None, Mlb=None):
        """
        potential improvements:
        1. delay
        2. sparse regression to denoise
        """
        self.n = np.size(Xub)
        self.m = np.size(Uub)
        self.weighting = weighting
        self.Xub = Xub.reshape(1,self.n)
        self.Xlb = Xlb.reshape(1,self.n)
        self.Uub = Uub.reshape(1,self.m)
        self.Ulb = Ulb.reshape(1,self.m)

        # set scale center and range
        Xub_scale = self.Xub + 0.3*(self.Xub-self.Xlb)
        Xlb_scale = self.Xlb - 0.3*(self.Xub-self.Xlb)
        Uub_scale = self.Uub + 0.3*(self.Uub-self.Ulb)
        Ulb_scale = self.Ulb - 0.3*(self.Uub-self.Ulb)
        self.state_range = (Xub_scale - Xlb_scale) / 2
        self.state_center = (Xub_scale + Xlb_scale) / 2
        self.action_range = (Uub_scale - Ulb_scale) / 2
        self.action_center = (Uub_scale + Ulb_scale) / 2
        if Mub is None:
            self.metric_range = self.state_range
            self.metric_center = self.state_center
            self.ncost = 0
        else:
            self.metric_range = (Mub - Mlb) / 2
            self.metric_center = (Mub + Mlb) / 2
            self.ncost = np.size(Mub)
        self.nk = num_lift + self.n + self.ncost
        print('Set up scale ranges and centers successfully!')

    def initialization(self, states, actions, costs=None):
        """
        scale data to [-1,1]
        data = Nt x N
        construct Koopman matrices A, B, C
        initialize recursive update matrices G, beta
        z = A*x + B*u
        x = C*z
        Koopman library functions: RFF
        psi = [x; cost; liftx]
        """
        # set rff:
        rff_sigma_gaussian = np.std(states)
        num_features = int((self.nk - self.n- self.ncost)/2)
        # np.random.get_state()[1][0]
        np.random.seed(878528420)  # 1536292545 1536292545
        self.rff_z = np.random.randn(self.n, num_features)/rff_sigma_gaussian
        print('Set up Random Fourier Features successfully!')

        states_scaled = self.scale(states)
        actions_scaled = self.scale(actions,state_scale=False)
        X_scaled = states_scaled[:-1,:]
        Y_scaled = states_scaled[1:,:]
        U_scaled = actions_scaled
        Nt = np.size(X_scaled,0)
        Weights = np.sqrt(self.weighting)**range(Nt-1,-1,-1)
        # Weights = Weights.reshape(Nt,1)
        self.X = Weights*X_scaled.T
        self.Y = Weights*Y_scaled.T
        self.U = Weights*U_scaled.T
        if costs is None:
            self.PsiX = self.lift(self.X.T)
            self.PsiY = self.lift(self.Y.T)
        else:
            costs_scaled = self.scale_lift(costs)
            CX_scaled = costs_scaled[:-1,:]
            CY_scaled = costs_scaled[1:,:]
            self.CX = Weights*CX_scaled.T
            self.CY = Weights*CY_scaled.T
            self.PsiX = self.lift(self.X.T,self.CX.T)
            self.PsiY = self.lift(self.Y.T,self.CY.T)
        self.Zeta = np.vstack((self.PsiX,self.U))
        self.non_singular = 0.05
        self.Q = np.matmul(self.PsiY,self.Zeta.T)
        self.G = np.linalg.inv(np.matmul(self.Zeta,self.Zeta.T) + self.non_singular*np.eye(len(self.Zeta)))
        # self.G = np.linalg.inv(np.matmul(self.Zeta,self.Zeta.T))
        self.AB = np.matmul(self.Q,self.G)
        self.A = self.AB[:,:self.nk]
        self.B = self.AB[:,self.nk:]
        self.C = np.hstack((np.eye(self.n),np.zeros((self.n,self.nk-self.n))))
        self.G = self.G /self.weighting
        self.G = (self.G + self.G.T)/2
        # Evaluate regression accuracy:
        error = self.Y - np.matmul(self.C,np.matmul(self.AB,self.Zeta))
        NRMSE_Koopman = 100*np.sqrt(sum(np.linalg.norm(error,axis=0)**2)) / np.sqrt(sum(np.linalg.norm(self.Y,axis=0)**2))
        print(NRMSE_Koopman,"%")

        return self.A, self.B, self.C

    def scale_lift(self,data, scale_down=True,metric_scale=True):
        '''
        This scaling would only be used when there have non-convex tracking or constraints,
        where those metrics are appended into the lifted states and will be tackled in MPC. 
        '''
        if metric_scale:
            if scale_down:
                scaled = (data - self.metric_center)/self.metric_range
                # scaled = 2/(1+np.exp(-data)) - 1
            else:
                scaled = data*self.metric_range + self.metric_center
                # scaled = -np.log(2/(data+1)-1)
        else:
            scaled = data
        return scaled

    def scale(self, data, scale_down=True, state_scale=True):
        """
        data is a Nt x N matrix
        scale down to [-1,1], scale up to stored scaling range
        initialize scaling range with first initialization data set
        """ 
        if np.shape(data) == (self.m,1) or np.shape(data) == (self.n,1):
            data = data.T
        if state_scale:
            if scale_down:
                scaled = (data - self.state_center) / self.state_range
                # scaled = 2/(1+np.exp(-data)) - 1
            else:
                scaled = data*self.state_range + self.state_center
                # scaled = -np.log(2/(data+1)-1)
        else:
            if scale_down:
                scaled = (data - self.action_center) / self.action_range
                # scaled = 2/(1+np.exp(-data)) - 1
            else:
                scaled = data*self.action_range + self.action_center
                # scaled = -np.log(2/(data+1)-1)
        
        return scaled

    def lift(self, data, cost=None):
        """
        data is a Nt x N matrix
        cost is a Nt x N matrix
        return lifted states Nk x Nt matrix (s.t A*Psi)
        lift the state space to a Koopman subspace
        lifted = [states; (actions?); lift(states)]
        RFF sampling rff_z ~ N(0, sigma^2*I_n)
        """
        # # Quadratic regression (50% NRMSE)
        # Psi = np.ones([np.size(data,0),self.nk])
        # for k in range(self.nk):
        #     for i in range(np.size(data,1)):
        #         for j in range(i,np.size(data,1)):
        #             Psi[:,k] = np.matmul(data[:,i].T,data[:,j])
        if cost is not None:
            if np.size(cost) == self.ncost:
                cost = cost.reshape(1, np.size(cost))
                data = data.reshape(1, np.size(data))
        Q = np.matmul(data,self.rff_z)
        Fcos = np.cos(Q)
        Fsin = np.sin(Q)
        F = np.hstack((Fcos, Fsin))/ np.sqrt(np.size(self.rff_z,1))
        if cost is None:
            Psi = np.hstack((data,F))
        else:
            if np.size(cost) == 1:
                Psi = np.hstack((np.append(data,cost).reshape(1,self.n+self.ncost),F))
            else:
                Psi = np.hstack((data,cost,F))
        Psi = Psi.T

        return Psi

    def update(self, states_x, states_y, actions, costs_x=None, costs_y= None):
        """
        recursive update AB, G 
        states is 1 x n
        actions is 1 x m
        scale_down -> update
        """
        statesx_scaled = self.scale(states_x.reshape(1,self.n))
        statesy_scaled = self.scale(states_y.reshape(1,self.n))
        actions_scaled = self.scale(actions.reshape(1,self.m),state_scale=False)
        x_new = statesx_scaled.reshape(self.n,1)
        y_new = statesy_scaled.reshape(self.n,1)
        u_new = actions_scaled.reshape(self.m,1)
        if costs_x is None:
            delta = np.vstack((self.lift(x_new.reshape(1,self.n)),u_new))
        else:
            costsx_scaled = self.scale_lift(costs_x)
            costsy_scaled = self.scale_lift(costs_y)
            delta = np.vstack((self.lift(x_new.reshape(1,self.n),costsx_scaled),u_new))
        calc_easy = np.matmul(self.G,delta)
        beta = 1/(1 + np.matmul(delta.T,calc_easy))
        if costs_x is None:
            innovation = self.lift(y_new.reshape(1,self.n)) - np.matmul(self.AB,delta)
        else:
            innovation = self.lift(y_new.reshape(1,self.n),costsy_scaled) - np.matmul(self.AB,delta)
        self.AB += beta*np.matmul(innovation,calc_easy.T)
        self.A = self.AB[:,:self.nk]
        if np.max(self.A) > 1000:
            print("SOmething wrong") # G has become negative definite det = -5e136 <-- calc_easy exp grow
        self.B = self.AB[:,self.nk:]
        self.G = (self.G - beta*np.matmul(calc_easy,calc_easy.T))/self.weighting
        self.G = (self.G + self.G.T)/2
        # print(np.linalg.det(self.G))
        if np.linalg.det(self.G) < 0:
            temp = beta*np.matmul(calc_easy,calc_easy.T)
            rank = np.linalg.eigvals(temp)
            print(min(rank))
            GG = np.linalg.inv(np.matmul(self.Zeta,self.Zeta.T) + self.non_singular*np.eye(len(self.Zeta)))
            GG = GG /self.weighting
            GG = (GG + GG.T)/2
            self.G = GG
        
        self.X = np.hstack((self.X,x_new))
        self.Y = np.hstack((self.Y,y_new))
        self.U= np.hstack((self.U,u_new))
        self.Zeta = np.hstack((self.Zeta,delta))
        return self.A, self.B, self.C

    def predict(self, states, actions, costs=None):
        """
        scale_down -> Koopman_predict -> scale_up
        """
        states = states.reshape(1,self.n)
        actions = actions.reshape(1,self.m)
        states_scaled = self.scale(states)
        actions_scaled = self.scale(actions,state_scale=False)
        if costs is None:
            delta_new = np.vstack([self.lift(states_scaled),actions_scaled.reshape(self.m,1)])
        else:
            costs_scaled = self.scale_lift(costs)
            delta_new = np.vstack([self.lift(states_scaled,costs_scaled),actions_scaled.reshape(self.m,1)])
        lift_predicted = np.matmul(self.AB,delta_new)
        predicts_scaled = np.matmul(self.C, lift_predicted)
        predicted = self.scale(predicts_scaled.reshape(1,self.n),scale_down=False)

        return predicted