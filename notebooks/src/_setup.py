# %% [markdown]
# ## 0. Przygotowanie środowiska
# Uruchom tę komórkę jako pierwszą (**Shift+Enter**). W Google Colab trwa to ok. 30–60 s.
# Nic nie musisz instalować na swoim komputerze.
#
# `MODE` decyduje o źródle danych:
# - `"auto"` – pakiet danych kursu (prawdziwe CT z TCIA), a jeśli go nie ma → syntetyczny fantom,
# - `"real"` – tylko dane rzeczywiste (błąd, jeśli ich brak),
# - `"synthetic"` – **tryb awaryjny**: zawsze syntetyczny fantom (działa bez internetu i bez GPU).

# %%
# --- Komórka instalacyjna: Colab / Kaggle / komputer lokalny ---
import os, sys, subprocess, pathlib, zipfile

MODE = os.environ.get("RTCOURSE_MODE", "auto")  # zmień na "synthetic", jeśli coś nie działa
REPO_URL = "https://github.com/bartektomasik/ai-rt-course.git"
IN_COLAB = "google.colab" in sys.modules
IN_KAGGLE = "KAGGLE_KERNEL_RUN_TYPE" in os.environ


def _find_code():
    here = pathlib.Path.cwd()
    for p in [here, *here.parents, here / "ai-rt-course", here / "course_pack", pathlib.Path("/content/course_pack")]:
        if (p / "rtcourse" / "__init__.py").exists():
            return p
    return None


code_dir = _find_code()
if code_dir is None:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pydicom>=2.4", "scikit-image", "ipywidgets"], check=False)
    if pathlib.Path("rtcourse.zip").exists():  # plik od prowadzącego (gdy repozytorium jest prywatne)
        zipfile.ZipFile("rtcourse.zip").extractall(".")
    else:
        subprocess.run(["git", "clone", "-q", "--depth", "1", REPO_URL], check=False)
    code_dir = _find_code()
if code_dir is None:
    raise RuntimeError("Nie udało się pobrać kodu kursu. Poproś prowadzącego o plik rtcourse.zip "
                       "i wgraj go do Colab (ikona folderu po lewej), potem uruchom komórkę ponownie.")
sys.path.insert(0, str(code_dir))
try:
    import pydicom  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pydicom>=2.4"], check=False)

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import rtcourse
from rtcourse import data, metrics, viz

pd.set_option("display.width", 140)
print(f"Kod kursu: {code_dir} | rtcourse {rtcourse.__version__} | MODE = {data.get_mode(MODE)}")
