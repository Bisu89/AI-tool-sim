# Offline simulator validation record

Environment: Windows, Python 3.11.4, NumPy 2.2.6, OpenCV contrib 4.12.0.88,
PySide6 / Qt 6.12.0, Pydantic 2.7.1 and pytest 8.4.2. No dependencies were
downloaded for this simulator development task, and no administrator access or
physical input executor was used.

## Automated suite

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
py -3.11 -m pytest --basetemp=.pytest-tmp-offline-final
```

Result: **60 passed in 2.27 seconds**. This includes the original tests and new
simulator unit, workflow, persistence, safety, import/network isolation and Qt
interaction tests. Qt interaction is delivered to widgets in-process, not to
the operating-system mouse. Source and test compilation also completed with
`py -3.11 -m compileall -q src tests`.

## Headless experiment

```powershell
py -3.11 -m sim_designer.main --headless --seed 7 --output output
```

Result: fake backend, **CONVERGED**, 32 simulated actions, geometric score
0.9981689467488027 and error 0.0018310532511972705 (tolerance 0.002).
A unique JSON session report was written under the requested output directory.
This score measures synthetic parameter error, not real-person likeness.

## Scope

No The Sims 4 integration tests were run. No real desktop capture was needed.
The previous observer-mode BitBlt limitation does not affect this simulator.
RealCASAdapter remains UNVERIFIED, with no physical drag implementation or exact
game restore. GUI usability across real Windows DPI layouts still needs manual
review; the automated Qt tests use the offscreen platform.
