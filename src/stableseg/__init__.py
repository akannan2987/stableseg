"""StableSeg: a measurement-system audit for imaging biomarkers.

The package is organised as layers that only ever call downward:

    cli  ->  api  ->  (config, storage, io, phantom, ...)

`cli` is the command-line front door, `api` is the set of plain Python
functions any other program (a web app, a service, a tool server) can call,
and the modules below `api` do the actual work and know nothing about who
called them. Keeping that direction strict is what lets the core be reused
without rewriting it.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
