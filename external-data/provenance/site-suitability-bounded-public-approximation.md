# Site Suitability Bounded Public Approximation

This note defines the current repo policy for site suitability until the report's
training and weighting methodology is fully reproduced.

## Why This Policy Exists

The data center siting report and LinkedIn notes describe a suitability workflow
that depends on:

- existing data center training labels, with Baxtel as the cited source
- a positive-unlabeled learning framing
- random-forest-derived feature importance
- a scored and ranked nationwide suitability surface built from the trained model

The current repo does not yet implement that full training-and-weighting path.

## What The Repo Already Has

- feature-generation workflows for several public or proxy inputs under
  `reVeal.public_data`
- normalization primitives in `reVeal/normalization.py`
- downscale configs that consume a pre-existing `suitability_score` field from
  `tests/data/downscale/inputs/grid_char_weighted_scores.gpkg`
- public EER projection generation and smoke-test execution for the downscaling
  mechanics

Those pieces are enough to exercise the downscaling workflow, but they do not, by
themselves, reproduce the report's learned national suitability surface.

## Current Policy

Until the report-aligned training workflow is implemented, any report-oriented use
of a suitability surface in this repo must be treated as a bounded public
approximation.

That means the repo may currently support:

- workflow validation for characterization, normalization, and downscaling mechanics
- public proxy experiments that show how alternative features affect a suitability
  surface
- report-like demonstrations of downstream mechanics when explicitly labeled as
  approximations

That also means the repo must not currently claim:

- reproduction of the Baxtel-trained suitability surface
- reproduction of the report's learned feature-importance weights
- reproduction of the report's nationwide scored and ranked surface from the
  original training data

## Execution Boundary

The current execution boundary is:

- allowed: use the existing `suitability_score` field and related public proxy
  surfaces to validate mechanics and bounded approximations
- not allowed: describe those runs as report-equivalent ML outputs unless the
  training labels, feature set, weighting logic, and validation path are reproduced

## Conditions To Reopen Exact-Method Work

Move beyond this bounded public approximation only when the repo has all of the
following:

- a defined training-label source policy, including Baxtel or a documented public
  alternative
- implemented workflows for the missing favorability features or documented
  replacements
- a reproducible training pipeline for the site suitability model
- a tracked method for generating the nationwide scored and ranked surface
- validation artifacts that show how the reproduced or approximated surface differs
  from the report claim