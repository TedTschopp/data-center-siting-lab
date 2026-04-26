# Public Report Bundle Deviations

This bundle is a bounded public approximation, not a report-equivalent reproduction.

- The execution grid is `/Users/tedtschopp/Developer/reVeal/tests/data/downscale/inputs/grid_char_weighted_scores.gpkg` rather than a reproduced nationwide report surface.
- The current bundle uses baseline year `2022` while the report narrative frames the scenario around operating data centers in `2025`.
- The current grid priority field is `suitability_score`, not a reproduced Baxtel-trained random-forest output from the published methodology.
- The current feasible-land artifact is a bounded approximation that keeps cells where `developable_capacity_mw > 0` and excludes cells whose staged NLCD water/wetland share across classes `11`, `90`, and `95` is at least `0.5`, rather than a reproduced exclusion stack from the report.
- The current suitability-percentile artifact ranks the pre-existing `suitability_score` field on those bounded feasible cells, rather than a trained nationwide model surface.
- The current workflow validates downscaling mechanics and schema compatibility, not parity of learned weights or parity of nationwide siting predictions.
