# Change control contract

## Any iteration that changes behavior must also update control artifacts

At minimum, behavioral work requires updates to:
- capability matrix
- implementation log
- verification status
- next iteration brief

## Architectural changes also require

- decision log entry
- mapping document update if subsystem boundaries changed
- risk register review if the change affects program shape

## Forbidden pattern

Code-only rounds that change scope or semantics without tracker updates are not valid program progress.
