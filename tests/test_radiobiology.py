import numpy as np
import pytest

from rtcourse import radiobiology as rb


def test_textbook_values():
    assert rb.eqd2(60, 30, 3) == pytest.approx(60.0)            # 2 Gy fractions -> EQD2 = physical
    assert rb.bed(60, 30, 10) == pytest.approx(72.0)
    assert rb.eqd2(25, 5, 10) == pytest.approx(31.25)           # 5 x 5 Gy, a/b 10
    assert rb.eqd2(26, 5, 3) == pytest.approx(26 * (5.2 + 3) / 5)


def test_inverse_and_arrays():
    for n in (1, 5, 20):
        d = rb.total_dose_for_eqd2(50, n, 2)
        assert rb.eqd2(d, n, 2) == pytest.approx(50)
    arr = rb.dose_to_eqd2(np.array([0.0, 30.0, 60.0]), 30, 3)
    assert arr.shape == (3,) and arr[0] == 0


def test_maps_and_sum():
    s = {"PTV": np.array([True, False, False]), "Cord": np.array([False, False, True])}
    ab = rb.alpha_beta_map(s, (3,), default=3, overrides={"PTV": 10, "Cord": 2})
    assert ab.tolist() == [10, 3, 2]
    d = np.array([60.0, 20.0, 40.0])
    tot = rb.sum_eqd2([(d, 30), (d / 2, 10)], ab, recovery_factors=[0.5, 1.0])
    assert tot[0] == pytest.approx(0.5 * rb.eqd2(60, 30, 10) + rb.eqd2(30, 10, 10))
    with pytest.raises(ValueError):
        rb.sum_eqd2([(d, 30), (np.zeros(4), 5)], 3)


def test_time_correction():
    assert rb.bed_with_time(70, 35, 10, 46) == pytest.approx(84 - 0.9 * 18)
    assert rb.bed_with_time(70, 35, 10, 20) == pytest.approx(84)
