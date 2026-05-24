# API reference

The `pyidfm` package is organised in a few small modules:

| Module                                | Purpose                                         |
| ------------------------------------- | ----------------------------------------------- |
| [`pyidfm.idfm`](idfm.md)              | Live PRIM API client ({class}`IDFMApi`).        |
| [`pyidfm.dataset`](dataset.md)        | Local static dataset loader and updater.        |
| [`pyidfm.models`](models.md)          | Dataclasses for lines, stops, reports, traffic. |
| [`pyidfm.utils`](utils.md)            | Small helpers (HTML stripping, ID conversion).  |
| [`pyidfm.types`](types.md)            | Type aliases for line / stop identifiers.       |

```{toctree}
:hidden:

idfm
dataset
models
utils
types
```
