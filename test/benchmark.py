import time
import numpy as np
import pandas as pd
import neworder as no

from math import sqrt

no.verbose()

# define some global variables describing where the starting population and the parameters of the dynamics come from
INITIAL_POPULATION = "./ssm_hh_E09000001_OA11_2011.csv"

t = np.array([
  [0.9,  0.05, 0.05, 0.,   0.,   0.  ],
  [0.05, 0.9,  0.04, 0.01, 0.,   0.  ],
  [0.,   0.05, 0.9,  0.05, 0.,   0.  ],
  [0.,   0.,   0.05, 0.9,  0.05, 0.  ],
  [0.1,  0.1,  0.1,  0.1,  0.5,  0.1 ],
  [0.,   0.,   0.,   0.,   0.2,  0.8 ]])

c = [-1, 1, 2, 3, 4, 5]

def get_data():
  hh = pd.read_csv(INITIAL_POPULATION)#, nrows=100)
  for i in range(8):
    hh = hh.append(hh, ignore_index=True)
  return hh


def interp(cumprob, x):
  lbound = 0
  while lbound < len(cumprob) - 1:
    if cumprob[lbound] > x:
      break
    lbound += 1
  return lbound

def sample(u, tc, c):
  return c[interp(tc, u)]

def transition(model, c, t, df, colname):
  #u = m.mc.ustream(len(df))
  tc = np.cumsum(t, axis=1)

  # reverse mapping of category label to index
  lookup = { c[i]: i for i in range(len(c)) }

  # for i in range(len(df)):
  #   current = df.loc[i, colname]
  #   df.loc[i, colname] = sample(u[i], tc[lookup[current]], c)

  df[colname] = df[colname].apply(lambda current: sample(m.mc.ustream(1), tc[lookup[current]], c))

def python_impl(m, df):

  start = time.time()
  transition(m, c, t, df, "LC4408_C_AHTHUK11")
  return len(df), time.time() - start, df.LC4408_C_AHTHUK11.values

def cpp_impl(m, df):

  start = time.time()
  no.df.transition(m, c, t, df, "LC4408_C_AHTHUK11")
  return len(df), time.time() - start, df.LC4408_C_AHTHUK11.values


#def f(m):

  # n = 1000

  # c = [1,2,3]
  # df = pd.DataFrame({"n": [1]*n})

  # # no transitions
  # t = np.identity(3)

  # no.df.transition(m, c, t, df, "n")
  # no.log(df.n.value_counts()[1] == 1000)

  # # all 1 -> 2
  # t[0,0] = 0.0
  # t[1,0] = 1.0
  # no.df.transition(m, c, t, df, "n")
  # no.log(df.n.value_counts()[2] == 1000)

  # # all 2 -> 1 or 3
  # t = np.array([
  #   [1.0, 0.5, 0.0],
  #   [0.0, 0.0, 0.0],
  #   [0.0, 0.5, 1.0],
  # ])

  # no.df.transition(m, c, t, df, "n")
  # no.log(2 not in df.n.value_counts())#[2] == 1000)
  # no.log(df.n.value_counts())

  # t = np.ones((3,3)) / 3
  # no.df.transition(m, c, t, df, "n")
  # no.log(df.n.value_counts())
  # for i in c:
  #   no.log(df.n.value_counts()[i] > n/3 - sqrt(n) and df.n.value_counts()[i] < n/3 + sqrt(n))

  # t = np.array([
  #   [1.0, 1.0, 1.0],
  #   [0.0, 0.0, 0.0],
  #   [0.0, 0.0, 0.0],
  # ])
  # no.df.transition(m, c, t, df, "n")
  # no.log(df.n.value_counts())

if __name__ == "__main__":
  m = no.Model(no.NoTimeline(), no.MonteCarlo.deterministic_identical_stream)

  rows, tc, colcpp = cpp_impl(m, get_data())
  no.log("C++ %d: %f" % (rows, tc))

  m.mc.reset()
  rows, tp, colpy = python_impl(m, get_data())
  no.log("py  %d: %f" % (rows, tp))

  #no.log(colcpp-colpy)

  assert np.array_equal(colcpp, colpy)

  no.log("speedup factor = %f" % (tp / tc))

#  f(m)