import pytest
import numpy as np

import warnings
warnings.filterwarnings(action='ignore', category=RuntimeWarning, message=r't=')
#no.verbose()
import neworder as no


def test_basics():

  # just check you can read the attrs/call the functions
  assert hasattr(no, "verbose")
  assert hasattr(no, "checked")
  assert hasattr(no, "__version__")
  no.log("testing")
  no.log(1)
  no.log(no)
  no.log([1,2,3])
  no.log((1,2,3))
  no.log({1:2,3:4})

def test_submodules():
  assert(hasattr(no, "mpi"))
  assert(hasattr(no, "stats"))
  assert(hasattr(no, "df"))

def test_dummy_model():
  class DummyModel(no.Model):
    def __init__(self):
      super().__init__(no.NoTimeline(), no.MonteCarlo.deterministic_identical_stream)
    def step(self):
      pass
    def finalise(self):
      pass

  assert no.run(DummyModel())

@pytest.mark.filterwarnings("ignore:check()")
def test_check_flag():
  class FailingModel(no.Model):
    def __init__(self):
      super().__init__(no.NoTimeline(), no.MonteCarlo.deterministic_identical_stream)
    def step(self):
      pass
    def check(self):
      return False

  # fails
  assert not no.run(FailingModel())

  no.checked(False)
  # succeeds
  assert no.run(FailingModel())

def test_mpi():
  # if no mpi4py, assume serial like module does
  try:
    import mpi4py.MPI as mpi
    rank = mpi.COMM_WORLD.Get_rank()
    size = mpi.COMM_WORLD.Get_size()
  except Exception:
    rank = 0
    size = 1
  assert no.mpi.rank() == rank
  assert no.mpi.size() == size


