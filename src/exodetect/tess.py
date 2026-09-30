"""Lightkurve / MAST access used by both the CLI and the web app."""
from pathlib import Path
import pandas as pd

def fetch_tess_lightcurve(target: str, sector: int | None = None, all_sectors: bool = False) -> pd.DataFrame:
    """Retrieve one SPOC sector by default; all sectors require explicit opt-in.

    This is intentional for the interactive app: some TICs have 40+ sectors
    and downloading every product can look like a frozen browser session.
    """
    try:
        import lightkurve as lk
    except ImportError as exc:
        raise RuntimeError("Install project dependencies, including lightkurve, before fetching TESS data.") from exc
    query = lk.search_lightcurve(target, mission="TESS", sector=sector, author="SPOC")
    if len(query) == 0:
        raise ValueError(f"No SPOC TESS light curve found for {target!r}. Try another TIC ID or sector.")
    if all_sectors:
        collection = query.download_all()
        lightcurve = collection.stitch().remove_nans()
    else:
        lightcurve = query.download().remove_nans()
    frame = lightcurve.to_pandas().reset_index()
    cols = [c for c in ["time", "flux", "flux_err"] if c in frame]
    return frame[cols].dropna(subset=["time", "flux"])

def save_tess_lightcurve(target: str, sector: int | None, outdir: str | Path) -> Path:
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    safe = target.replace(" ", "_")
    file = out / f"{safe}_tess.csv"; fetch_tess_lightcurve(target, sector).to_csv(file, index=False)
    return file
