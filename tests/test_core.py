"""Fast unit tests for rtcourse (run: pytest tests/)."""
import numpy as np
import pytest

from rtcourse import autoseg, data, dicom_io, metrics
from rtcourse.case import Case
from rtcourse.phantom import make_phantom, write_dicom_rt


@pytest.fixture(scope="module")
def phantom():
    return make_phantom(seed=0, variability=0.0, shape=(32, 96, 96), spacing=(3.0, 4.0, 4.0))


def test_metrics_basic():
    a = np.zeros((10, 20, 20), bool)
    a[3:7, 5:15, 5:15] = True
    assert metrics.dice(a, a) == 1.0
    assert metrics.dice(a, np.zeros_like(a)) == 0.0
    assert metrics.hd95(a, a, (1, 1, 1)) == 0.0
    b = np.roll(a, 2, axis=2)
    assert 0 < metrics.dice(a, b) < 1
    assert metrics.hd95(a, b, (1, 1, 1)) == pytest.approx(2.0)
    assert metrics.surface_dice(a, b, (1, 1, 1), tolerance_mm=2.0) == pytest.approx(1.0)


def test_dvh_metrics():
    dose = np.linspace(0, 10, 1000).reshape(10, 10, 10)
    mask = np.ones_like(dose, bool)
    assert metrics.mean_dose(dose, mask) == pytest.approx(5.0)
    assert metrics.volume_at_dose(dose, mask, 5.0) == pytest.approx(50.0, abs=0.2)
    assert metrics.dose_at_volume(dose, mask, 50) == pytest.approx(5.0, abs=0.02)
    b, v = metrics.dvh(dose, mask)
    assert v[0] == pytest.approx(100.0) and v[-1] == pytest.approx(0.0)


def test_phantom_and_dose(phantom):
    s = phantom.structures
    for n in ["BODY", "Lung_L", "Lung_R", "Heart", "Esophagus", "SpinalCord", "GTV", "PTV"]:
        assert s[n].any(), n
    assert metrics.dose_at_volume(phantom.dose, s["PTV"], 95) == pytest.approx(60.0, abs=0.1)
    assert phantom.dose[~s["BODY"]].max() == 0


def test_dicom_roundtrip(phantom, tmp_path):
    write_dicom_rt(phantom, str(tmp_path))
    c2 = dicom_io.load_case_from_folder(str(tmp_path))
    assert c2.ct.shape == phantom.ct.shape
    assert np.allclose(c2.ct, np.round(phantom.ct))
    for n, m in phantom.structures.items():
        assert metrics.dice(m, c2.structures[n]) > 0.97, n
    body = phantom.structures["BODY"]
    assert np.median(np.abs(c2.dose - phantom.dose)[body]) < 0.5
    assert c2.meta["plan"]["fractions"] == 30


def test_npz_roundtrip(phantom, tmp_path):
    p = tmp_path / "c.npz"
    phantom.save_npz(p)
    c = Case.load_npz(p)
    assert set(c.structures) == set(phantom.structures)
    assert np.array_equal(c.structures["Heart"], phantom.structures["Heart"])


def test_simulated_autoseg(phantom):
    ai = autoseg.simulate_autoseg(phantom)
    t = metrics.compare_masks(phantom.structures, ai, phantom.spacing)
    assert (t["Dice"] < 1).any() and (t["Dice"] > 0.3).all()


def test_synthetic_mode(monkeypatch):
    monkeypatch.setenv("RTCOURSE_MODE", "synthetic")
    assert data.get_course_pack() is None
    c = data.load_case(1, verbose=False)
    assert c.source == "synthetic"


def test_monitoring_detects_drift():
    from rtcourse import monitoring as mon

    pool = mon.make_pool(3, seed=0)
    df = mon.simulate_weeks(12, 3, events={7: "nowy protokół CT (kontrast, cieńsze warstwy)"}, pool=pool, seed=0, organs=("Heart",))
    w = df.groupby("week").Dice.mean()
    m, lcl, _, sd = mon.shewhart_limits(w.loc[:6])
    assert w.loc[7:].mean() < m
    _, alarm = mon.cusum_lower(w.values, m, sd)
    assert alarm is not None and alarm >= 6
    res = mon.evaluate_acceptance(df, {"Heart": {"Dice_median_min": 0.5, "HD95_p90_max": 100}})
    assert (res["wynik"] == "SPEŁNIONE").all()
