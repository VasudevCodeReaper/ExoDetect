from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import numpy as np
import pandas as pd
from astropy.timeseries import BoxLeastSquares
from scipy.ndimage import median_filter


@dataclass
class Candidate:
    period_days: float
    duration_hours: float
    depth_ppm: float
    epoch: float
    snr: float
    fap: float
    odd_even_sigma: float
    secondary_snr: float
    n_in_transit: int
    class_probabilities: dict[str, float]
    predicted_class: str
    confidence: float
    quality_flags: list[str]


def load_lightcurve(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"time", "flux"}
    if not required.issubset(frame.columns):
        raise ValueError("Input CSV needs columns: time, flux (optional: flux_err)")
    out = frame[[c for c in ["time", "flux", "flux_err"] if c in frame]].copy()
    out = out.replace([np.inf, -np.inf], np.nan).dropna(subset=["time", "flux"]).sort_values("time")
    if len(out) < 100: raise ValueError("At least 100 finite observations are required")
    return out.reset_index(drop=True)


def preprocess(lc: pd.DataFrame, window_days: float = 1.0, clip_sigma: float = 6.0) -> pd.DataFrame:
    """Normalize and median-detrend without masking prospective transits."""
    x, y = lc.time.to_numpy(float), lc.flux.to_numpy(float)
    cadence = np.nanmedian(np.diff(x)); width = max(11, int(window_days / cadence) | 1)
    base = median_filter(y, size=width, mode="nearest")
    flux = y / np.where(base == 0, np.nanmedian(base), base)
    resid = flux - np.nanmedian(flux); mad = 1.4826 * np.nanmedian(np.abs(resid - np.nanmedian(resid)))
    keep = np.abs(resid) < clip_sigma * max(mad, 1e-8)
    out = lc.loc[keep].copy(); out["flux_clean"] = flux[keep]
    out["flux_err_clean"] = out.get("flux_err", pd.Series(np.full(len(out), mad), index=out.index)).to_numpy() / np.abs(base[keep])
    return out.reset_index(drop=True)


def _estimate_odd_even(time, flux, period, epoch, duration):
    phase_cycle = ((time - epoch) / period) % 1
    event = np.floor((time - epoch) / period).astype(int)
    in_event = np.minimum(phase_cycle, 1 - phase_cycle) < duration / (2 * period)
    depths = []
    for parity in (0, 1):
        sel = in_event & ((event % 2) == parity)
        depths.append(1 - np.nanmedian(flux[sel]) if sel.sum() > 3 else np.nan)
    scatter = 1.4826 * np.nanmedian(np.abs(flux - np.nanmedian(flux)))
    return float(abs(depths[0] - depths[1]) / max(scatter / np.sqrt(max(in_event.sum() / 2, 1)), 1e-8))


def search_periodic_dips(lc: pd.DataFrame, min_period=0.5, max_period=15.0) -> dict:
    time, flux = lc.time.to_numpy(), lc.flux_clean.to_numpy()
    baseline = time.max() - time.min(); max_period = min(max_period, baseline * 0.8)
    if max_period <= min_period: raise ValueError("Light curve baseline is too short for requested search range")
    durations = np.linspace(0.5, 10, 12) / 24
    bls = BoxLeastSquares(time, flux)
    period_grid = np.exp(np.linspace(np.log(min_period), np.log(max_period), 6000))
    result = bls.power(period_grid, durations)
    k = int(np.nanargmax(result.power)); period, duration, epoch = map(float, (result.period[k], result.duration[k], result.transit_time[k]))
    # Astropy's BLS model derives the fitted depth from the BLS instance.
    # Passing depth was accepted by older examples but fails on current Astropy.
    model = bls.model(time, period, duration, epoch)
    in_transit = model < 1 - abs(result.depth[k]) / 2
    scatter = 1.4826 * np.nanmedian(np.abs(flux - np.nanmedian(flux)))
    snr = float(abs(result.depth[k]) * np.sqrt(in_transit.sum()) / max(scatter, 1e-8))
    phase = ((time - epoch + .5 * period) % period) - .5 * period
    secondary = np.abs(phase - .5 * period) < duration / 2
    secondary_snr = float(abs(1 - np.nanmedian(flux[secondary])) * np.sqrt(secondary.sum()) / max(scatter, 1e-8)) if secondary.sum() else 0.0
    return dict(period=period, duration=duration, epoch=epoch, depth=float(abs(result.depth[k])), snr=snr,
                fap=float(np.exp(-max(float(result.power[k]), 0))), odd_even=_estimate_odd_even(time, flux, period, epoch, duration),
                secondary_snr=secondary_snr, n_in=int(in_transit.sum()), power=float(result.power[k]))


def classify(features: dict) -> tuple[str, dict[str, float]]:
    """Auditable baseline scoring; replace with a trained calibrated model when available."""
    snr, depth = features["snr"], features["depth"] * 1e6
    odd, secondary = features["odd_even"], features["secondary_snr"]
    raw = {
        "transit": max(0.01, 1.7 * (snr - 4) / 10 + 1.2 - .16 * odd - .09 * secondary - .000025 * max(depth - 25000, 0)),
        "eclipsing_binary": max(0.01, .13 * secondary + .20 * odd + .00004 * depth),
        "blend_or_variability": max(0.01, .08 * max(5 - snr, 0) + .000015 * depth + .07 * odd),
        "noise": max(0.01, (5 - snr) / 3),
    }
    total = sum(raw.values()); probs = {k: round(v / total, 4) for k, v in raw.items()}
    return max(probs, key=probs.get), probs


def analyse(lc: pd.DataFrame, model_path: str | None = None) -> tuple[pd.DataFrame, Candidate]:
    clean = preprocess(lc); f = search_periodic_dips(clean); label, probs = classify(f)
    if model_path:
        import joblib
        saved = joblib.load(model_path); names = saved["features"]
        values = {"period_days": f["period"], "duration_hours": f["duration"] * 24, "depth_ppm": f["depth"] * 1e6,
                  "snr": f["snr"], "fap": f["fap"], "odd_even_sigma": f["odd_even"], "secondary_snr": f["secondary_snr"], "n_in_transit": f["n_in"]}
        p = saved["model"].predict_proba(pd.DataFrame([[values[n] for n in names]], columns=names))[0]
        classes = list(saved["classes"])
        # Dataset-builder models are binary (0 = FP/FA, 1 = CP/KP); keep the
        # user-facing web contract descriptive instead of exposing 0/1 labels.
        if set(classes) == {0, 1}:
            positive = float(p[classes.index(1)])
            probs = {"exoplanet_like": round(positive, 4), "non_exoplanet": round(1 - positive, 4)}
            label = "exoplanet_like" if positive >= 0.5 else "non_exoplanet"
        else:
            probs = {str(name): round(float(prob), 4) for name, prob in zip(classes, p)}; label = max(probs, key=probs.get)
    flags = []
    if f["snr"] < 7: flags.append("low_detection_snr")
    if f["odd_even"] > 3: flags.append("odd_even_depth_difference")
    if f["secondary_snr"] > 4: flags.append("secondary_eclipse_like_feature")
    if f["n_in"] < 20: flags.append("few_in_transit_samples")
    return clean, Candidate(f["period"], f["duration"] * 24, f["depth"] * 1e6, f["epoch"], f["snr"], f["fap"], f["odd_even"], f["secondary_snr"], f["n_in"], probs, label, probs[label], flags)


def save_result(candidate: Candidate, outdir: str | Path) -> None:
    p = Path(outdir); p.mkdir(parents=True, exist_ok=True)
    with (p / "result.json").open("w") as f: json.dump(asdict(candidate), f, indent=2)
