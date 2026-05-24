# Python usage

`pyidfm` can also be used directly as a Python library. The main entry point
is the {class}`pyidfm.idfm.IDFMApi` class.

## Listing stops on a line

```python
from pyidfm.idfm import IDFMApi

api = IDFMApi(apikey="your-key-here")

stops = api.get_stops("C01742")
for s in stops:
    print(s.name, s.stop_id)
```

## Next departures at a stop

```python
departures = api.get_traffic("STIF:StopArea:SP:43135:")
for d in departures:
    print(d.schedule, d.destination_name, d.direction)
```

Optional filters mirror the CLI:

```python
departures = api.get_traffic(
    stop_id="STIF:StopArea:SP:43135:",
    line_id="STIF:Line::C01742:",
    destination_name="Gare de Lyon",
)
```

## Disruption reports

```python
reports = api.get_line_reports("C01742")
for r in reports:
    print(r.name, r.severity, r.effect)
```

## Working with the local dataset directly

The static IDFM datasets are exposed through the
{class}`pyidfm.dataset.Dataset` class. It is lazily instantiated by
{class}`~pyidfm.idfm.IDFMApi` through the `data` property, but you can also
use it standalone:

```python
from pyidfm.dataset import Dataset

dataset = Dataset()

# All metro lines, keyed by display name.
for name, line_id in dataset.lines["metro"].items():
    print(name, line_id)
```

To refresh the cached datasets:

```python
dataset.update_data()
```

## Exception handling

The API surfaces two exceptions:

- {exc}`pyidfm.idfm.UnknownIdentifierException` — raised when a
  `MonitoringRef` / `LineRef` couple is rejected by the PRIM endpoint.
- {exc}`pyidfm.idfm.ParameterException` — raised when incompatible
  parameters are passed (e.g. both `line_id` and `stop_id` to
  {meth}`~pyidfm.idfm.IDFMApi.get_messages`).
