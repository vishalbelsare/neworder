"""
Spatial structures for positioning and moving entities and computing distances
"""

import numpy as np
from scipy import signal


def _bounce(point, min, max):
  for d in range(len(point)):
    if point[d] < min[d]:
      point[d] = min[d] - point[d]
    if point[d] > max[d]:
      point[d] = max[d] - point[d]
  return point


class Domain:
  """
  Base class for spatial domains.
  """

  """
  Edge behaviour
  """
  UNBOUNDED = 0
  WRAP = 1
  CONSTRAIN = 2
  BOUNCE = 3

  def __init__(self, dim, edge, continuous):
    self.__dim = dim
    self.__edge = edge
    self.__continuous = continuous

  @property
  def dim(self):
    """ The dimension of the spatial domain """
    return self.__dim

  @property
  def edge(self):
    """ The tyoe of edge constraint """

    return self.__edge

  @property
  def continuous(self):
    """ Whether space is continuous or discrete """
    return self.__continuous


class Space(Domain):
  """
  Continuous rectangular n-dimensional finite or infinite domain.
  If finite, positioning and/or movement near the domain boundary is
  dictated by the `wrap` attribute.
  """

  @staticmethod
  def unbounded(dim):
    """ Construct an unbounded Space """
    assert dim
    return Space(np.full(dim, -np.inf), np.full(dim, +np.inf), edge=Domain.UNBOUNDED)

  def __init__(self, min, max, edge=Domain.CONSTRAIN):
    assert len(min) and len(min) == len(max)
    super().__init__(len(min), edge, True)

    # Space supports all edge behaviours
    assert edge in [Domain.UNBOUNDED, Domain.WRAP, Domain.CONSTRAIN, Domain.BOUNCE]

    assert np.all(max > min)

    self.min = min
    self.max = max

  @property
  def extent(self):
    """ The extent of the space in terms of two opposing points """
    return self.min, self.max

  def move(self, positions, velocities, delta_t, ungroup=False):
    """ Returns translated positions AND velocities """
    # group tuples into a single array if necessary
    if type(positions) == tuple:
      positions = np.column_stack(positions)
    if type(velocities) == tuple:
      velocities = np.column_stack(velocities)

    assert positions.dtype == float
    assert velocities.dtype == float
    assert positions.shape[-1] == self.dim and velocities.shape[-1] == self.dim
    if self.edge == Domain.UNBOUNDED:
      p = positions + velocities * delta_t
      v = velocities
    elif self.edge == Domain.CONSTRAIN:
      p = positions + velocities * delta_t
      v = velocities
      hitmin = np.where(p < self.min, 1, 0)
      p = np.where(hitmin, self.min, p)
      v = np.where(hitmin, 0, v)
      hitmax = np.where(p > self.max, 1, 0)
      p = np.where(hitmax, self.max, p)
      v = np.where(hitmax, 0, v)
    elif self.edge == Domain.BOUNCE:
      p = positions + velocities * delta_t
      v = velocities
      hitmin = np.where(p < self.min, 1, 0)
      p = np.where(hitmin, 2 * self.min - p, p)
      v = np.where(hitmin, -v, v)
      hitmax = np.where(p > self.max, 1, 0)
      p = np.where(hitmax, 2 * self.max - p, p)
      v = np.where(hitmax, -v, v)
    else:
      p = self.min + np.mod(positions + velocities * delta_t - self.min, self.max - self.min)
      v = velocities

    if ungroup:
      p = np.split(p, self.dim, axis=1)
      v = np.split(v, self.dim, axis=1)
    return p, v

  def dists2(self, positions, to_points=None):
    """ The squared distance between points and separations along each axis """
    # group tuples into a single array if necessary
    if type(positions) == tuple:
      positions = np.column_stack(positions)
    if type(to_points) == tuple:
      to_points = np.column_stack(to_points)
    # distances w.r.t. self if to_points not explicitly specified
    if to_points is None:
      to_points = positions
    assert positions.dtype == float
    assert to_points.dtype == float
    n = positions.shape[0]
    m = to_points.shape[0]
    d = positions.shape[1]
    d2 = np.zeros((m, n))
    separations = ()
    if self.edge != Domain.WRAP:
      for i in range(d):
        delta = np.tile(positions[:, i], m).reshape((m, n)) - np.repeat(to_points[:, i], n).reshape(m, n)
        separations += (delta,)
        d2 += delta * delta
    else: # wrapped domains need special treatment - distance across an edge may be less than naive distance
      for i in range(d):
        delta = np.tile(positions[:, i], m).reshape((m, n)) - np.repeat(to_points[:, i], n).reshape(m, n)
        r = self.max[i] - self.min[i]
        delta = np.where(delta > r / 2, delta - r, delta)
        delta = np.where(delta < -r / 2, delta + r, delta)
        separations += (delta,)
        d2 += delta * delta

    return d2, separations

  def dists(self, positions, to_points=None):
    """ Returns distances between the points"""
    return np.sqrt(self.dists2(positions, to_points)[0])

  def in_range(self, distance, positions, count=False): # to_points=None,
    """ Returns either indices or counts of points within the specified distance from each point """
    ind = np.where(self.dists2(positions)[0] < distance * distance, 1, 0)
    # fill diagonal so as not to include self - TODO how does this work if to_points!=positions
    np.fill_diagonal(ind, 0)
    return ind if not count else np.sum(ind, axis=1)

  def __repr__(self):
    return "%s dim=%d min=%s max=%s edge=%s" % (self.__class__.__name__, self.dim, self.min, self.max, self.edge)


class StateGrid(Domain):
  """
  Discrete rectangular n-dimensional finite grid domain with each cell having an integer state.
  Allows for counting of neighbours according to the supported edge behaviours:
    CONSTRAIN (no neighburs over edge), WRAP (toroidal), BOUNCE (reflect)
  """

  __mode_lookup = {
    Domain.CONSTRAIN: "constant",
    Domain.WRAP: "wrap",
    Domain.BOUNCE: "reflect"
  }

  def __init__(self, initial_values, edge=Domain.CONSTRAIN):
    super().__init__(initial_values.ndim, edge, False)

    # StateGrid supports two edge behaviours
    if edge not in [Domain.WRAP, Domain.CONSTRAIN]:
      raise ValueError("edge policy must be one of Domain.WRAP, Domain.CONSTRAIN")

    if initial_values.ndim < 1:
      raise ValueError("state array must have dimension of 1 or above")
    if initial_values.size < 1:
      raise ValueError("state array must have size of 1 or above in every dimension")

    self.state = initial_values

    # int neighbour kernel (not including self)
    self.kernel = np.ones([3] * self.dim)
    self.kernel[(1,) * self.dim] = 0

  @property
  def extent(self):
    """ The extent of the space in terms of two opposing points """
    return self.state.shape

  def count_neighbours(self, indicator=lambda x: x == 1):
    """ Counts neighbouring cells with a state indicated by supplied indicator function """

    ind = np.array([indicator(x) for x in self.state]).astype(int)  # automagically preserves shape
    # pad with boundary according to edge policy
    bounded = np.pad(ind, pad_width=1, mode=self.__mode_lookup[self.edge])

    # count neighbours, drop padding, covert to int
    count = signal.convolve(bounded, self.kernel, mode="same", method="direct")[(slice(1, -1),) * self.dim].astype(int)

    return count
