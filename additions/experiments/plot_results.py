import sys
import os
path = os.path.dirname(os.path.realpath(__file__))  # path to this directory
sys.path.append(os.path.abspath(path + "/../.."))

from misc import utils
import numpy as np
import matplotlib.pyplot as plt
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--show", default=True)
parser.add_argument("--path", default="results/two-room-gw/linear/")
parser.add_argument("--title", default="")
parser.add_argument("--lambda_test", default=False)

to_bool = lambda x : x in [True, "True", "true", "1"]

args = parser.parse_args()
show = to_bool(args.show)
results_path = str(args.path)
title = str(args.title)
lambda_test = to_bool(args.lambda_test)

MARKERS = ["o", "D", "s", "^", "v", "p", "*"]
COLORS = ["#0e5ad3", "#bc2d14", "#22aa16", "#a011a3", "#d1ba0e", "#14ccc2", "#d67413", "#ef24d4"]
LINES = ["solid", "dashed", "dashdot", "dotted", "solid", "dashed", "dashdot", "dotted"]


def plot_curves(x_data, y_mean_data, y_std_data=None, title="", x_label="Episodes", y_label="Performance", names=None,
                file_name=None):
    assert len(x_data) < 16

    plt.style.use('ggplot')

    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = 'Ubuntu'
    plt.rcParams['font.monospace'] = 'Ubuntu Mono'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 10
    # plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['axes.titlesize'] = 15
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['figure.titlesize'] = 20
    
    plt.rcParams['figure.figsize'] = [16,9]

    fig, ax = plt.subplots()

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    X = np.array(x_data)
    plt.xlim([X.min(), X.max()])

    for i in range(len(x_data)):
        
        linestyle = i // len(COLORS)
        linestyle = LINES[linestyle]

        ax.plot(x_data[i], y_mean_data[i], linewidth=3, color=COLORS[i % len(COLORS)], marker=None, markersize=8.0,
                linestyle=linestyle, label=names[i] if names is not None else None)
        if y_std_data is not None:
            ax.fill_between(x_data[i], y_mean_data[i] - y_std_data[i], y_mean_data[i] + y_std_data[i],
                            facecolor=COLORS[i % len(COLORS)], edgecolor=COLORS[i % len(COLORS)],
                            linestyle=linestyle, alpha=0.3)

    if names is not None:
        ax.legend(loc='best', numpoints=1, fancybox=True, frameon=False)

    if file_name is not None:
        plt.savefig(file_name + ".pdf", format='pdf')

    if show == True:
        plt.show()


def learning_rew(iterations, episodes_time, episode_rew, mean_episodes=5):
    """
    :param iterations: list of list of iterations to which compute a sample of learning reward
    :param episodes_time: list of lists of iterations in which an episode finished
    :param episode_rew: list of lists of rewards associated to the episode
    :param mean_episodes: number of episodes to take for the moving average
    :return:
    """
    learning_rew = []
    for run in range(len(episodes_time)):
        t = 0
        rew = []
        for i in range(len(iterations[run])):
            iter = iterations[run][i]
            while t < len(episodes_time[run]) and iter > episodes_time[run][t]:
                t += 1

            r = sum(episode_rew[run][max(0, t-mean_episodes):t])/float(len(episode_rew[run][max(0, t-mean_episodes):t])) if t > 0 else 0.
            rew.append(r)
        learning_rew.append(np.array(rew))

    return np.array(learning_rew)

if not lambda_test:
    experiments = {
        "mgvt_1c": "1-MGVT", 
        "mgvt_3c": "3-MGVT", 
        "t2vt_1c": "1-T2VT", 
        "t2vt_3c": "3-T2VT"
    }
else:
    experiments = {
        "t2vt_1c_l=likelihood": "1-T2VT - l = max log-likelihood",
        "t2vt_1c_l=0.1": "1-T2VT - l = 0.1",
        "t2vt_1c_l=0.2": "1-T2VT - l = 0.2",
        "t2vt_1c_l=0.3": "1-T2VT - l = 0.3",
        "t2vt_1c_l=0.4": "1-T2VT - l = 0.4",
        "t2vt_1c_l=0.5": "1-T2VT - l = 0.5",
        "t2vt_1c_l=0.6": "1-T2VT - l = 0.6",
        "t2vt_1c_l=0.7": "1-T2VT - l = 0.7",
        "t2vt_1c_l=0.8": "1-T2VT - l = 0.8",
        "t2vt_1c_l=0.9": "1-T2VT - l = 0.9",
        "t2vt_1c_l=1.0": "1-T2VT - l = 1.0",
        "t2vt_3c_l=likelihood": "3-T2VT - l = max log-likelihood",
        "t2vt_3c_l=0.1": "3-T2VT - l = 0.1",
        "t2vt_3c_l=0.2": "3-T2VT - l = 0.2",
        "t2vt_3c_l=0.3": "3-T2VT - l = 0.3",
        "t2vt_3c_l=0.4": "3-T2VT - l = 0.4",
        "t2vt_3c_l=0.5": "3-T2VT - l = 0.5",
        "t2vt_3c_l=0.6": "3-T2VT - l = 0.6",
        "t2vt_3c_l=0.7": "3-T2VT - l = 0.7",
        "t2vt_3c_l=0.8": "3-T2VT - l = 0.8",
        "t2vt_3c_l=0.9": "3-T2VT - l = 0.9",
        "t2vt_3c_l=1.0": "3-T2VT - l = 1.0"
    }

files = []
names = []

for exp, name in experiments.items():
    fs = glob.glob(results_path + exp + "*.pkl")
    if len(fs) == 0:
        continue
    files.append(fs[0][:-4])
    names.append(name)

x = []
y_mean = []
y_std = []
y2_mean = []
y2_std = []
y3_mean = []
y3_std = []
y4_mean = []
y4_std = []

for file in files:
    results = [r[2] for r in utils.load_object(file)]
    iterations = []
    episodes = []
    n_samples = []
    lear_rew = []
    eval_rew = []
    l_2 = []
    l_inf = []
    for result in results:
        iterations.append(result[0])
        episodes.append(result[1])
        n_samples.append(result[2])
        lear_rew.append(result[3])
        eval_rew.append(result[4])
        l_2.append(result[5])
        l_inf.append(result[6])
    iterations = np.array(iterations)
    x.append(np.mean(iterations,axis=0))
    n_samples = np.array(n_samples)
    lear_rew = np.array(lear_rew)
    y_mean.append(np.mean(lear_rew, axis=0))
    y_std.append(2 * np.std(lear_rew, axis=0) / np.sqrt(lear_rew.shape[0]))
    eval_rew = np.array(eval_rew)
    y2_mean.append(np.mean(eval_rew, axis=0))
    y2_std.append(2 * np.std(eval_rew, axis=0) / np.sqrt(eval_rew.shape[0]))
    l_2 = np.array(l_2)
    y3_mean.append(np.mean(l_2, axis=0))
    y3_std.append(2 * np.std(l_2, axis=0) / np.sqrt(l_2.shape[0]))
    l_inf = np.array(l_inf)
    y4_mean.append(np.mean(l_inf, axis=0))
    y4_std.append(2 * np.std(l_inf, axis=0) / np.sqrt(l_inf.shape[0]))

plot_curves([a[1:] for a in x], [a[1:] for a in y_mean], [a[1:] for a in y_std], title=title, x_label="Iterations", y_label="Learning Reward", names=names, file_name=results_path + "lrev")
plot_curves(x, y2_mean, y2_std, title=title, x_label="Iterations", y_label="Evaluation Reward", names=names, file_name=results_path + "erew")
plot_curves(x, y3_mean, y3_std, title=title, x_label="Iterations", y_label="L_2", names=names, file_name=results_path + "l2")
plot_curves(x, y4_mean, y4_std, title=title, x_label="Iterations", y_label="L_INF", names=names, file_name=results_path + "linf")