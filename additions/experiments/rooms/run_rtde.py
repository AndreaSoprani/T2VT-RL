import sys
import os
path = os.path.dirname(os.path.realpath(__file__))  # path to this directory
sys.path.append(os.path.abspath(path + "/../../.."))

import numpy as np
from envs.two_room_gw import TwoRoomGridworld
from envs.three_room_gw import ThreeRoomGridworld
from features.agrbf import build_features_gw_state
from additions.approximators.mlp_torch import MLPQFunction
from operators.mellow_torch import MellowBellmanOperator
from additions.algorithms.mgvt_torch import learn
from misc import utils
import argparse
from joblib import Parallel, delayed
import datetime
from additions.temporal_kernel import temporal_kernel

# Global parameters
render = False
verbose = False

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--kappa", default=100.)
parser.add_argument("--xi", default=0.5)
parser.add_argument("--tau", default=0.0)
parser.add_argument("--batch_size", default=50)
parser.add_argument("--max_iter", default=10000)
parser.add_argument("--buffer_size", default=50000)
parser.add_argument("--random_episodes", default=0)
parser.add_argument("--train_freq", default=1)
parser.add_argument("--eval_freq", default=50)
parser.add_argument("--mean_episodes", default=50)
parser.add_argument("--alpha_adam", default=0.001)
parser.add_argument("--alpha_sgd", default=0.1)
parser.add_argument("--lambda_", default=0.000001)
parser.add_argument("--time_coherent", default=False)
parser.add_argument("--n_weights", default=10)
parser.add_argument("--timesteps", default=10)
parser.add_argument("--env", default="two-room-gw")
parser.add_argument("--gw_size", default=10)
parser.add_argument("--cholesky_clip", default=0.0001)
# Door at -1 means random positions over all runs
parser.add_argument("--n_basis", default=11)
parser.add_argument("--n_jobs", default=1)
parser.add_argument("--n_runs", default=20)
parser.add_argument("--source_file", default=path + "/sources")
parser.add_argument("--tasks_file", default=path + "/tasks")
parser.add_argument("--eta", default=1e-6)  # learning rate for
parser.add_argument("--eps", default=0.001)  # precision for the initial posterior approximation and upperbound tighting
parser.add_argument("--bandwidth", default=.00001)  # Bandwidth for the Kernel Estimator
parser.add_argument("--post_components", default=1)  # number of components of the posterior family
parser.add_argument("--max_iter_ukl", default=60)
# rtde arguments
parser.add_argument("--temporal_bandwidth", default=0.3333)
parser.add_argument("--kernel", default="epanechnikov")
parser.add_argument("--experiment_type", default="linear")

# Read arguments
args = parser.parse_args()
kappa = float(args.kappa)
xi = float(args.xi)
tau = float(args.tau)
batch_size = int(args.batch_size)
max_iter = int(args.max_iter)
buffer_size = int(args.buffer_size)
random_episodes = int(args.random_episodes)
train_freq = int(args.train_freq)
eval_freq = int(args.eval_freq)
mean_episodes = int(args.mean_episodes)
alpha_adam = float(args.alpha_adam)
alpha_sgd = float(args.alpha_sgd)
lambda_ = float(args.lambda_)
time_coherent = bool(int(args.time_coherent))
n_weights = int(args.n_weights)
timesteps = int(args.timesteps)
cholesky_clip = float(args.cholesky_clip)
env = str(args.env)
experiment_type = str(args.experiment_type)
gw_size = int(args.gw_size)
n_basis = int(args.n_basis)
n_jobs = int(args.n_jobs)
n_runs = int(args.n_runs)
source_file = str(args.source_file)
tasks_file = str(args.tasks_file)
eps = float(args.eps)
eta = float(args.eta)
post_components = int(args.post_components)
bandwidth = float(args.bandwidth)
max_iter_ukl = int(args.max_iter_ukl)
temporal_bandwidth = float(args.temporal_bandwidth)
kernel = str(args.kernel)

file_name = "results/" + env + "/" + experiment_type+ "/" + "rtde_" + str(post_components) + "c_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

source_file += "-" + experiment_type
source_file += "-2r" if env == "two-room-gw" else ("-3r" if env == "three-room-gw" else "")
tasks_file += "-" + experiment_type
tasks_file += "-2r" if env == "two-room-gw" else ("-3r" if env == "three-room-gw" else "")

# Seed to get reproducible results
seed = 1
np.random.seed(seed)

# Generate tasks
mdps = utils.load_object(tasks_file)

eval_states = [np.array([0., 0.]) for _ in range(10)]

state_dim = mdps[0].state_dim
action_dim = 1
n_actions = mdps[0].action_space.n
K = n_basis ** 2

# Create BellmanOperator
operator = MellowBellmanOperator(kappa, tau, xi, mdps[0].gamma, K, action_dim)
# Create Q Function
Q = MLPQFunction(K, n_actions, layers=None)
# Create RBFs
rbf = build_features_gw_state(gw_size, n_basis, state_dim)

prior_weights = temporal_kernel(timesteps, temporal_bandwidth, kernel)

def run(mdp, seed=None):
    return learn(mdp,
                 Q,
                 operator,
                 max_iter=max_iter,
                 buffer_size=buffer_size,
                 batch_size=batch_size,
                 alpha_adam=alpha_adam,
                 alpha_sgd=alpha_sgd,
                 lambda_=lambda_,
                 n_weights=n_weights,
                 train_freq=train_freq,
                 eval_freq=eval_freq,
                 random_episodes=random_episodes,
                 eval_states=eval_states,
                 mean_episodes=mean_episodes,
                 preprocess=rbf,
                 cholesky_clip=cholesky_clip,
                 bandwidth=bandwidth,
                 post_components=post_components,
                 prior_weights=prior_weights,
                 max_iter_ukl=max_iter_ukl,
                 eps=eps,
                 eta=eta,
                 time_coherent=time_coherent,
                 source_file=source_file,
                 seed=seed,
                 render=render,
                 verbose=verbose)


seeds = [9, 44, 404, 240, 259, 141, 371, 794, 41, 507, 819, 959, 829, 558, 638, 127, 672, 4, 635, 687]
seeds = seeds[:n_runs]

# On each run use a random mdp from the ones created
mdps = np.random.choice(mdps, len(seeds))

if n_jobs == 1:
    results = [run(mdp,seed) for (mdp,seed) in zip(mdps,seeds)]
elif n_jobs > 1:
    results = Parallel(n_jobs=n_jobs)(delayed(run)(mdp,seed) for (mdp,seed) in zip(mdps,seeds))

utils.save_object(results, file_name)