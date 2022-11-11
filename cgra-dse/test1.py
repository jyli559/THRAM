import numpy as np
import torch
import pandas as pd
import matplotlib.pyplot as plt
from pymoo.factory import get_problem
from pymoo.util.plotting import plot
from pymoo.util.dominator import Dominator


problem = get_problem("zdt1", n_var = 5)


dim = problem.n_var
num_obj = problem.n_obj
print(num_obj)
num_constr = problem.n_constr
print(num_constr)

def obj(param : pd.DataFrame) -> np.ndarray:
    names = ['x' + str(i) for i in range(problem.n_var)]
    x   = param[names].values
    print(param)
    #print(x)
    #print(x.shape[0])
    out = {}
    problem._evaluate(x,out)
    o = out['F'].reshape(x.shape[0], num_obj)
    #print(o)
    print("!!!!!!!!!!!")
    if num_constr > 0:
        c = out['G'].reshape(x.shape[0], num_constr)
    else:
        c = np.zeros((x.shape[0],0))
    #print(c)
    return np.hstack([o,c])

def extract_pf(points : np.ndarray) -> np.ndarray:
    dom_matrix = Dominator().calc_domination_matrix(points,None)
    is_optimal = (dom_matrix >= 0).all(axis = 1)
    return points[is_optimal]

from hebo.design_space.design_space import DesignSpace

lb,ub  = problem.bounds()
params = [{'name' : 'x' + str(i), 'type' : 'num', 'lb' : lb[i], 'ub' : ub[i]} for i in range(dim)]
space  = DesignSpace().parse(params)

from hebo.optimizers.general import GeneralBO
conf = {}
conf['num_hiddens'] = 64
conf['num_layers'] = 2
conf['output_noise'] = False
conf['rand_prior'] = True
conf['verbose'] = False
conf['l1'] = 3e-3
conf['lr'] = 3e-2
conf['num_epochs'] = 100
opt = GeneralBO(space, num_obj, num_constr, model_conf = conf)
for i in range(50):
    rec = opt.suggest(n_suggestions=4)
    #print(rec)
    opt.observe(rec, obj(rec))

feasible_y = extract_pf(opt.y)
rand_y     = extract_pf(obj(space.sample(opt.y.shape[0])))
plt.plot(feasible_y[:,0], feasible_y[:,1], 'x', color = 'r', label = 'BO')
plt.plot(rand_y[:,0], rand_y[:,1], 'x', color = 'b', label = 'Rand')
plt.title('Number of Pareto optimal points from BO: %d' % feasible_y.shape[0])
plt.legend()