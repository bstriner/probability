# Copyright 2018 The TensorFlow Probability Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Tests for ShapeUtil."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports
import numpy as np
import tensorflow as tf

from tensorflow_probability.python.bijectors.shape import _DistributionShape
from tensorflow.python.framework import tensor_util

_empty_shape = np.array([], dtype=np.int32)


def _constant(x):
  if hasattr(x, "__iter__"):
    return [tensor_util.constant_value(x) for x in x]
  return tensor_util.constant_value(x)


class MakeBatchReadyTest(tf.test.TestCase):

  def setUp(self):
    self._rng = np.random.RandomState(42)

  def _random_sample(self, sample_shape, dtype=np.float32):
    return self._rng.random_sample(sample_shape).astype(dtype)

  def _get_expected(self, x, batch_ndims, event_ndims, expand_batch_dim):
    # Cast as int32 array explicitly, since an empty x.shape defaults
    # to float64, and we can't index as float64 in numpy 1.12+.
    x_shape = np.array(x.shape, dtype=np.int32)
    n = x.ndim - batch_ndims - event_ndims
    sample_shape = x_shape[:n]
    y = np.reshape(x, np.concatenate([[-1], x_shape[n:]], 0))
    y = np.transpose(y, np.roll(np.arange(y.ndim), -1))
    if event_ndims == 0:
      y = y[..., np.newaxis, :]
    if batch_ndims == 0 and expand_batch_dim:
      y = y[np.newaxis, ...]
    return y, sample_shape

  def _build_graph(self, x, batch_ndims, event_ndims, expand_batch_dim):
    shaper = _DistributionShape(batch_ndims=batch_ndims,
                                event_ndims=event_ndims,
                                validate_args=True)
    y, sample_shape = shaper.make_batch_of_event_sample_matrices(
        x, expand_batch_dim=expand_batch_dim)
    should_be_x_value = shaper.undo_make_batch_of_event_sample_matrices(
        y, sample_shape, expand_batch_dim=expand_batch_dim)
    return y, sample_shape, should_be_x_value

  def _test_dynamic(self, x, batch_ndims, event_ndims, expand_batch_dim=True):
    x_pl = tf.placeholder_with_default(x, shape=None)
    batch_ndims_pl = tf.placeholder_with_default(batch_ndims, shape=None)
    event_ndims_pl = tf.placeholder_with_default(event_ndims, shape=None)
    [y_, sample_shape_, should_be_x_value_] = self.evaluate(
        self._build_graph(
            x_pl, batch_ndims_pl, event_ndims_pl, expand_batch_dim))
    expected_y, expected_sample_shape = self._get_expected(
        x, batch_ndims, event_ndims, expand_batch_dim)
    self.assertAllEqual(expected_sample_shape, sample_shape_)
    self.assertAllEqual(expected_y, y_)
    self.assertAllEqual(x, should_be_x_value_)

  def _test_static(self, x, batch_ndims, event_ndims, expand_batch_dim):
    [y_, sample_shape_, should_be_x_value_] = self.evaluate(
        self._build_graph(x, batch_ndims, event_ndims, expand_batch_dim))
    expected_y, expected_sample_shape = self._get_expected(
        x, batch_ndims, event_ndims, expand_batch_dim)
    self.assertAllEqual(expected_sample_shape, sample_shape_)
    self.assertAllEqual(expected_y, y_)
    self.assertAllEqual(x, should_be_x_value_)

  # Group 1a: Static scalar input.

  def testStaticScalarNdims00ExpandNo(self):
    self._test_static(x=self._random_sample([]),
                      batch_ndims=0,
                      event_ndims=0,
                      expand_batch_dim=False)

  def testStaticScalarNdims00ExpandYes(self):
    self._test_static(x=self._random_sample([]),
                      batch_ndims=0,
                      event_ndims=0,
                      expand_batch_dim=True)

  def testStaticScalarNdims01ExpandNo(self):
    with self.assertRaises(ValueError):
      self._test_static(x=self._random_sample([]),
                        batch_ndims=0,
                        event_ndims=1,
                        expand_batch_dim=False)

  def testStaticScalarNdims01ExpandYes(self):
    with self.assertRaises(ValueError):
      self._test_static(x=self._random_sample([]),
                        batch_ndims=0,
                        event_ndims=1,
                        expand_batch_dim=True)

  def testStaticScalarNdims10ExpandNo(self):
    with self.assertRaises(ValueError):
      self._test_static(x=self._random_sample([]),
                        batch_ndims=1,
                        event_ndims=0,
                        expand_batch_dim=False)

  def testStaticScalarNdims10ExpandYes(self):
    with self.assertRaises(ValueError):
      self._test_static(x=self._random_sample([]),
                        batch_ndims=1,
                        event_ndims=0,
                        expand_batch_dim=True)

  def testStaticScalarNdims11ExpandNo(self):
    with self.assertRaises(ValueError):
      self._test_static(x=self._random_sample([]),
                        batch_ndims=1,
                        event_ndims=1,
                        expand_batch_dim=False)

  def testStaticScalarNdims11ExpandYes(self):
    with self.assertRaises(ValueError):
      self._test_static(x=self._random_sample([]),
                        batch_ndims=1,
                        event_ndims=1,
                        expand_batch_dim=True)

  # Group 1b: Dynamic scalar input.
  def testDynamicScalar3Ndims00ExpandNo(self):
    self._test_dynamic(x=self._random_sample([]),
                       batch_ndims=0,
                       event_ndims=0,
                       expand_batch_dim=False)

  def testDynamicScalar3Ndims00ExpandYes(self):
    self._test_dynamic(x=self._random_sample([]),
                       batch_ndims=0,
                       event_ndims=0,
                       expand_batch_dim=True)

  def testDynamicScalarNdims01ExpandNo(self):
    with self.assertRaisesOpError(""):
      self._test_dynamic(x=self._random_sample([]),
                         batch_ndims=0,
                         event_ndims=1,
                         expand_batch_dim=False)

  def testDynamicScalarNdims01ExpandYes(self):
    with self.assertRaisesOpError(""):
      self._test_dynamic(x=self._random_sample([]),
                         batch_ndims=0,
                         event_ndims=1,
                         expand_batch_dim=True)

  def testDynamicScalarNdims10ExpandNo(self):
    with self.assertRaisesOpError(""):
      self._test_dynamic(x=self._random_sample([]),
                         batch_ndims=1,
                         event_ndims=0,
                         expand_batch_dim=False)

  def testDynamicScalarNdims10ExpandYes(self):
    with self.assertRaisesOpError(""):
      self._test_dynamic(x=self._random_sample([]),
                         batch_ndims=1,
                         event_ndims=0,
                         expand_batch_dim=True)

  def testDynamicScalarNdims11ExpandNo(self):
    with self.assertRaisesOpError(""):
      self._test_dynamic(x=self._random_sample([]),
                         batch_ndims=1,
                         event_ndims=1,
                         expand_batch_dim=False)

  def testDynamicScalarNdims11ExpandYes(self):
    with self.assertRaisesOpError(""):
      self._test_dynamic(x=self._random_sample([]),
                         batch_ndims=1,
                         event_ndims=1,
                         expand_batch_dim=True)

  # Group 2a: Static vector input.

  def testStaticVectorNdims00ExpandNo(self):
    self._test_static(x=self._random_sample([3]),
                      batch_ndims=0,
                      event_ndims=0,
                      expand_batch_dim=False)

  def testStaticVectorNdims00ExpandYes(self):
    self._test_static(x=self._random_sample([3]),
                      batch_ndims=0,
                      event_ndims=0,
                      expand_batch_dim=True)

  def testStaticVectorNdims01ExpandNo(self):
    self._test_static(x=self._random_sample([3]),
                      batch_ndims=0,
                      event_ndims=1,
                      expand_batch_dim=False)

  def testStaticVectorNdims01ExpandYes(self):
    self._test_static(x=self._random_sample([3]),
                      batch_ndims=0,
                      event_ndims=1,
                      expand_batch_dim=True)

  def testStaticVectorNdims10ExpandNo(self):
    self._test_static(x=self._random_sample([3]),
                      batch_ndims=1,
                      event_ndims=0,
                      expand_batch_dim=False)

  def testStaticVectorNdims10ExpandYes(self):
    self._test_static(x=self._random_sample([3]),
                      batch_ndims=1,
                      event_ndims=0,
                      expand_batch_dim=True)

  def testStaticVectorNdims11ExpandNo(self):
    with self.assertRaises(ValueError):
      self._test_static(x=self._random_sample([3]),
                        batch_ndims=1,
                        event_ndims=1,
                        expand_batch_dim=False)

  def testStaticVectorNdims11ExpandYes(self):
    with self.assertRaises(ValueError):
      self._test_static(x=self._random_sample([3]),
                        batch_ndims=1,
                        event_ndims=1,
                        expand_batch_dim=True)

  # Group 2b: Dynamic vector input.

  def testDynamicVectorNdims00ExpandNo(self):
    self._test_dynamic(x=self._random_sample([3]),
                       batch_ndims=0,
                       event_ndims=0,
                       expand_batch_dim=False)

  def testDynamicVectorNdims00ExpandYes(self):
    self._test_dynamic(x=self._random_sample([3]),
                       batch_ndims=0,
                       event_ndims=0,
                       expand_batch_dim=True)

  def testDynamicVectorNdims01ExpandNo(self):
    self._test_dynamic(x=self._random_sample([3]),
                       batch_ndims=0,
                       event_ndims=1,
                       expand_batch_dim=False)

  def testDynamicVectorNdims01ExpandYes(self):
    self._test_dynamic(x=self._random_sample([3]),
                       batch_ndims=0,
                       event_ndims=1,
                       expand_batch_dim=True)

  def testDynamicVectorNdims10ExpandNo(self):
    self._test_dynamic(x=self._random_sample([3]),
                       batch_ndims=1,
                       event_ndims=0,
                       expand_batch_dim=False)

  def testDynamicVectorNdims10ExpandYes(self):
    self._test_dynamic(x=self._random_sample([3]),
                       batch_ndims=1,
                       event_ndims=0,
                       expand_batch_dim=True)

  def testDynamicVectorNdims11ExpandNo(self):
    with self.assertRaisesOpError(""):
      self._test_dynamic(x=self._random_sample([3]),
                         batch_ndims=1,
                         event_ndims=1,
                         expand_batch_dim=False)

  def testDynamicVectorNdims11ExpandYes(self):
    with self.assertRaisesOpError(""):
      self._test_dynamic(x=self._random_sample([3]),
                         batch_ndims=1,
                         event_ndims=1,
                         expand_batch_dim=True)

  # Group 3a: Static matrix input.

  def testStaticMatrixNdims00ExpandNo(self):
    self._test_static(x=self._random_sample([2, 3]),
                      batch_ndims=0,
                      event_ndims=0,
                      expand_batch_dim=False)

  def testStaticMatrixNdims00ExpandYes(self):
    self._test_static(x=self._random_sample([2, 3]),
                      batch_ndims=0,
                      event_ndims=0,
                      expand_batch_dim=True)

  def testStaticMatrixNdims01ExpandNo(self):
    self._test_static(x=self._random_sample([2, 3]),
                      batch_ndims=0,
                      event_ndims=1,
                      expand_batch_dim=False)

  def testStaticMatrixNdims01ExpandYes(self):
    self._test_static(x=self._random_sample([2, 3]),
                      batch_ndims=0,
                      event_ndims=1,
                      expand_batch_dim=True)

  def testStaticMatrixNdims10ExpandNo(self):
    self._test_static(x=self._random_sample([2, 3]),
                      batch_ndims=1,
                      event_ndims=0,
                      expand_batch_dim=False)

  def testStaticMatrixNdims10ExpandYes(self):
    self._test_static(x=self._random_sample([2, 3]),
                      batch_ndims=1,
                      event_ndims=0,
                      expand_batch_dim=True)

  def testStaticMatrixNdims11ExpandNo(self):
    self._test_static(x=self._random_sample([2, 3]),
                      batch_ndims=1,
                      event_ndims=1,
                      expand_batch_dim=False)

  def testStaticMatrixNdims11ExpandYes(self):
    self._test_static(x=self._random_sample([2, 3]),
                      batch_ndims=1,
                      event_ndims=1,
                      expand_batch_dim=True)

  # Group 3b: Dynamic matrix input.

  def testDynamicMatrixNdims00ExpandNo(self):
    self._test_dynamic(x=self._random_sample([2, 3]),
                       batch_ndims=0,
                       event_ndims=0,
                       expand_batch_dim=False)

  def testDynamicMatrixNdims00ExpandYes(self):
    self._test_dynamic(x=self._random_sample([2, 3]),
                       batch_ndims=0,
                       event_ndims=0,
                       expand_batch_dim=True)

  def testDynamicMatrixNdims01ExpandNo(self):
    self._test_dynamic(x=self._random_sample([2, 3]),
                       batch_ndims=0,
                       event_ndims=1,
                       expand_batch_dim=False)

  def testDynamicMatrixNdims01ExpandYes(self):
    self._test_dynamic(x=self._random_sample([2, 3]),
                       batch_ndims=0,
                       event_ndims=1,
                       expand_batch_dim=True)

  def testDynamicMatrixNdims10ExpandNo(self):
    self._test_dynamic(x=self._random_sample([2, 3]),
                       batch_ndims=1,
                       event_ndims=0,
                       expand_batch_dim=False)

  def testDynamicMatrixNdims10ExpandYes(self):
    self._test_dynamic(x=self._random_sample([2, 3]),
                       batch_ndims=1,
                       event_ndims=0,
                       expand_batch_dim=True)

  def testDynamicMatrixNdims11ExpandNo(self):
    self._test_dynamic(x=self._random_sample([2, 3]),
                       batch_ndims=1,
                       event_ndims=1,
                       expand_batch_dim=False)

  def testDynamicMatrixNdims11ExpandYes(self):
    self._test_dynamic(x=self._random_sample([2, 3]),
                       batch_ndims=1,
                       event_ndims=1,
                       expand_batch_dim=True)

  # Group 4a: Static tensor input.

  def testStaticTensorNdims00ExpandNo(self):
    self._test_static(x=self._random_sample([4, 1, 2, 3]),
                      batch_ndims=0,
                      event_ndims=0,
                      expand_batch_dim=False)

  def testStaticTensorNdims00ExpandYes(self):
    self._test_static(x=self._random_sample([4, 1, 2, 3]),
                      batch_ndims=0,
                      event_ndims=0,
                      expand_batch_dim=True)

  def testStaticTensorNdims01ExpandNo(self):
    self._test_static(x=self._random_sample([4, 1, 2, 3]),
                      batch_ndims=0,
                      event_ndims=1,
                      expand_batch_dim=False)

  def testStaticTensorNdims01ExpandYes(self):
    self._test_static(x=self._random_sample([4, 1, 2, 3]),
                      batch_ndims=0,
                      event_ndims=1,
                      expand_batch_dim=True)

  def testStaticTensorNdims10ExpandNo(self):
    self._test_static(x=self._random_sample([4, 1, 2, 3]),
                      batch_ndims=1,
                      event_ndims=0,
                      expand_batch_dim=False)

  def testStaticTensorNdims10ExpandYes(self):
    self._test_static(x=self._random_sample([4, 1, 2, 3]),
                      batch_ndims=1,
                      event_ndims=0,
                      expand_batch_dim=True)

  def testStaticTensorNdims11ExpandNo(self):
    self._test_static(x=self._random_sample([4, 1, 2, 3]),
                      batch_ndims=1,
                      event_ndims=1,
                      expand_batch_dim=False)

  def testStaticTensorNdims11ExpandYes(self):
    self._test_static(x=self._random_sample([4, 1, 2, 3]),
                      batch_ndims=1,
                      event_ndims=1,
                      expand_batch_dim=True)

  # Group 4b: Dynamic tensor input.

  def testDynamicTensorNdims00ExpandNo(self):
    self._test_dynamic(x=self._random_sample([4, 1, 2, 3]),
                       batch_ndims=0,
                       event_ndims=0,
                       expand_batch_dim=False)

  def testDynamicTensorNdims00ExpandYes(self):
    self._test_dynamic(x=self._random_sample([4, 1, 2, 3]),
                       batch_ndims=0,
                       event_ndims=0,
                       expand_batch_dim=True)

  def testDynamicTensorNdims01ExpandNo(self):
    self._test_dynamic(x=self._random_sample([4, 1, 2, 3]),
                       batch_ndims=0,
                       event_ndims=1,
                       expand_batch_dim=False)

  def testDynamicTensorNdims01ExpandYes(self):
    self._test_dynamic(x=self._random_sample([4, 1, 2, 3]),
                       batch_ndims=0,
                       event_ndims=1,
                       expand_batch_dim=True)

  def testDynamicTensorNdims10ExpandNo(self):
    self._test_dynamic(x=self._random_sample([4, 1, 2, 3]),
                       batch_ndims=1,
                       event_ndims=0,
                       expand_batch_dim=False)

  def testDynamicTensorNdims10ExpandYes(self):
    self._test_dynamic(x=self._random_sample([4, 1, 2, 3]),
                       batch_ndims=1,
                       event_ndims=0,
                       expand_batch_dim=True)

  def testDynamicTensorNdims11ExpandNo(self):
    self._test_dynamic(x=self._random_sample([4, 1, 2, 3]),
                       batch_ndims=1,
                       event_ndims=1,
                       expand_batch_dim=False)

  def testDynamicTensorNdims11ExpandYes(self):
    self._test_dynamic(x=self._random_sample([4, 1, 2, 3]),
                       batch_ndims=1,
                       event_ndims=1,
                       expand_batch_dim=True)


class DistributionShapeTest(tf.test.TestCase):

  def setUp(self):
    self._rng = np.random.RandomState(42)

  def _random_sample(self, sample_shape, dtype=np.float32):
    return self._rng.random_sample(sample_shape).astype(dtype)

  def _assertNdArrayEqual(self, expected, actual):
    """Helper which properly compares two np.ndarray-like objects.

    This function checks for exact equality so is probably only suitable for
    integers or powers of 2.

    Args:
      expected: np.ndarray. Ground-truth value.
      actual: np.ndarray.  Observed value.
    """
    expected = np.asarray(expected)
    actual = np.asarray(actual)
    self.assertEqual(expected.shape, actual.shape,
                     "Shape mismatch: expected %s, got %s." %
                     (expected.shape, actual.shape))
    actual_item = actual.flat
    for expected_item in expected.flat:
      self.assertAllEqual(expected_item, next(actual_item))

  def testDistributionShapeGetNdimsStatic(self):
    shaper = _DistributionShape(batch_ndims=0, event_ndims=0)
    x = 1
    self.assertEqual(0, self.evaluate(shaper.get_sample_ndims(x)))
    self.assertEqual(0, self.evaluate(shaper.batch_ndims))
    self.assertEqual(0, self.evaluate(shaper.event_ndims))

    shaper = _DistributionShape(batch_ndims=1, event_ndims=1)
    x = self._random_sample((1, 2, 3))
    self.assertAllEqual(3, self.evaluate(shaper.get_ndims(x)))
    self.assertEqual(1, self.evaluate(shaper.get_sample_ndims(x)))
    self.assertEqual(1, self.evaluate(shaper.batch_ndims))
    self.assertEqual(1, self.evaluate(shaper.event_ndims))

    x += self._random_sample((1, 2, 3))
    self.assertAllEqual(3, self.evaluate(shaper.get_ndims(x)))
    self.assertEqual(1, self.evaluate(shaper.get_sample_ndims(x)))
    self.assertEqual(1, self.evaluate(shaper.batch_ndims))
    self.assertEqual(1, self.evaluate(shaper.event_ndims))

    # There is no such thing as unfed Tensor in Eager, so exit early.
    if tf.executing_eagerly():
      return

    # Test ndims functions work, even despite unfed Tensors.
    y = tf.placeholder(tf.float32, shape=(1024, None, 1024))
    self.assertEqual(3, self.evaluate(shaper.get_ndims(y)))
    self.assertEqual(1, self.evaluate(shaper.get_sample_ndims(y)))
    self.assertEqual(1, self.evaluate(shaper.batch_ndims))
    self.assertEqual(1, self.evaluate(shaper.event_ndims))

  def testDistributionShapeGetNdimsDynamic(self):
    batch_ndims = tf.placeholder_with_default(1, shape=None)
    event_ndims = tf.placeholder_with_default(1, shape=None)
    shaper = _DistributionShape(
        batch_ndims=batch_ndims, event_ndims=event_ndims)
    y = tf.placeholder_with_default(
        np.ones((4, 2), dtype=np.float32), shape=None)
    self.assertEqual(2, self.evaluate(shaper.get_ndims(y)))

  def testDistributionShapeGetDimsStatic(self):
    shaper = _DistributionShape(batch_ndims=0, event_ndims=0)
    x = 1
    self.assertAllEqual((_empty_shape, _empty_shape, _empty_shape),
                        _constant(shaper.get_dims(x)))
    shaper = _DistributionShape(batch_ndims=1, event_ndims=2)
    x += self._random_sample((1, 1, 2, 2))
    self._assertNdArrayEqual(([0], [1], [2, 3]),
                             _constant(shaper.get_dims(x)))
    x += x
    self._assertNdArrayEqual(([0], [1], [2, 3]),
                             _constant(shaper.get_dims(x)))

  def testDistributionShapeGetDimsDynamic(self):
    # Works for deferred {batch,event}_ndims.
    batch_ndims = tf.placeholder_with_default(1, shape=None)
    event_ndims = tf.placeholder_with_default(2, shape=None)
    shaper = _DistributionShape(
        batch_ndims=batch_ndims, event_ndims=event_ndims)
    y = tf.placeholder_with_default(
        self._random_sample((10, 3, 5, 5), dtype=np.float32), shape=None)
    self._assertNdArrayEqual(
        ([0], [1], [2, 3]), self.evaluate(shaper.get_dims(y)))

    # In eager mode, there is no such thing as unfed input, so exit early.
    if tf.executing_eagerly():
      return

    # Works for static {batch,event}_ndims despite unfed input.
    shaper = _DistributionShape(batch_ndims=1, event_ndims=2)
    y = tf.placeholder(tf.float32, shape=(10, None, 5, 5))
    self._assertNdArrayEqual(
        [[0], [1], [2, 3]], self.evaluate(shaper.get_dims(y)))

  def testDistributionShapeGetShapeStatic(self):
    shaper = _DistributionShape(batch_ndims=0, event_ndims=0)
    self.assertAllEqual((_empty_shape, _empty_shape, _empty_shape),
                        _constant(shaper.get_shape(1.)))
    self._assertNdArrayEqual(([1], _empty_shape, _empty_shape),
                             _constant(shaper.get_shape(np.ones(1))))
    self._assertNdArrayEqual(([2, 2], _empty_shape, _empty_shape),
                             _constant(shaper.get_shape(np.ones((2, 2)))))
    self._assertNdArrayEqual(([3, 2, 1], _empty_shape, _empty_shape),
                             _constant(shaper.get_shape(np.ones((3, 2, 1)))))

    shaper = _DistributionShape(batch_ndims=0, event_ndims=1)
    with self.assertRaisesRegexp(ValueError, "expected .* <= ndims"):
      shaper.get_shape(1.)
    self._assertNdArrayEqual((_empty_shape, _empty_shape, [1]),
                             _constant(shaper.get_shape(np.ones(1))))
    self._assertNdArrayEqual(([2], _empty_shape, [2]),
                             _constant(shaper.get_shape(np.ones((2, 2)))))
    self._assertNdArrayEqual(([3, 2], _empty_shape, [1]),
                             _constant(shaper.get_shape(np.ones((3, 2, 1)))))

    shaper = _DistributionShape(batch_ndims=1, event_ndims=0)
    with self.assertRaisesRegexp(ValueError, "expected .* <= ndims"):
      shaper.get_shape(1.)
    self._assertNdArrayEqual((_empty_shape, [1], _empty_shape),
                             _constant(shaper.get_shape(np.ones(1))))
    self._assertNdArrayEqual(([2], [2], _empty_shape),
                             _constant(shaper.get_shape(np.ones((2, 2)))))
    self._assertNdArrayEqual(([3, 2], [1], _empty_shape),
                             _constant(shaper.get_shape(np.ones((3, 2, 1)))))

    shaper = _DistributionShape(batch_ndims=1, event_ndims=1)
    with self.assertRaisesRegexp(ValueError, "expected .* <= ndims"):
      shaper.get_shape(1.)
    with self.assertRaisesRegexp(ValueError, "expected .* <= ndims"):
      shaper.get_shape(np.ones(1))
    self._assertNdArrayEqual((_empty_shape, [2], [2]),
                             _constant(shaper.get_shape(np.ones((2, 2)))))
    self._assertNdArrayEqual(([3], [2], [1]),
                             _constant(shaper.get_shape(np.ones((3, 2, 1)))))

  def testDistributionShapeGetShapeDynamic(self):
    # Works for static ndims despite unknown static shape.
    shaper = _DistributionShape(batch_ndims=1, event_ndims=1)
    y = tf.placeholder_with_default(
        self._random_sample((3, 4, 2), dtype=np.float32), shape=None)
    self._assertNdArrayEqual(
        ([3], [4], [2]),
        self.evaluate(shaper.get_shape(y)))

    shaper = _DistributionShape(batch_ndims=0, event_ndims=1)
    y = tf.placeholder_with_default(
        np.ones((3, 2), dtype=np.int32), shape=(None, None))
    self._assertNdArrayEqual(
        ([3], _empty_shape, [2]),
        self.evaluate(shaper.get_shape(y)))

    # Works for deferred {batch,event}_ndims.
    batch_ndims = tf.placeholder_with_default(1, shape=None)
    event_ndims = tf.placeholder_with_default(1, shape=None)
    shaper = _DistributionShape(
        batch_ndims=batch_ndims, event_ndims=event_ndims)
    y = tf.placeholder_with_default(
        np.ones((3, 4, 2), dtype=np.int32), shape=[None, None, 2])
    self._assertNdArrayEqual(
        ([3], [4], [2]), self.evaluate(shaper.get_shape(y)))

    y = tf.placeholder_with_default(
        np.ones((3, 2), dtype=np.int32), shape=None)
    batch_ndims = tf.placeholder_with_default(0, shape=None)
    event_ndims = tf.placeholder_with_default(1, shape=None)
    shaper = _DistributionShape(
        batch_ndims=batch_ndims, event_ndims=event_ndims)
    self._assertNdArrayEqual(
        ([3], _empty_shape, [2]), self.evaluate(shaper.get_shape(y)))


if __name__ == "__main__":
  tf.test.main()
