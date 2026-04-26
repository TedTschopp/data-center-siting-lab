# Report Reproduction Gaps

Tracked inventory of the remaining report-layer dependencies that still prevent exact
reproduction of the data center opportunity outputs from public repo-local workflows.

## Summary

- Exact reproduction is still blocked by one commercial dependency: `gap_001` Baxtel
  data center locations. The repo now defines a manual procurement path for sample
  or licensed access, but the data is still not publicly downloadable.
- A first-pass public proxy workflow now exists for `gap_002`.
- A first-pass public proxy workflow now exists for `gap_003`.
- A first-pass public assembly workflow now exists for `gap_004`.
- A first-pass public proxy workflow now exists for `gap_005`.
- A first-pass public proxy workflow now exists for `gap_006`.
- A first-pass public proxy workflow now exists for `gap_007`.
- A scripted public webservice workflow now exists for `gap_008` RIBITS.

The table below translates the gap register and open-substitute matrix into a single
execution view for the repo.

| Gap | Presentation feature or dataset | Exact parity blocker | Current public path | Parity posture | Next repo action |
| --- | --- | --- | --- | --- | --- |
| `gap_001` | Existing, under-construction, and planned data center locations | Baxtel is commercial and was the cited presentation source. | OpenStreetMap + Wikidata + operator announcements + permitting records | Public approximation only | The repo now includes a first-pass baseline generator from exported OSM, Wikidata, and manual augmentation payloads, plus a staged Baxtel procurement note for requesting a sample or licensed snapshot. Remaining work is to secure access, stage any delivered CSV locally, and compare the licensed schema against the public baseline. |
| `gap_002` | Distance to substations and transmission lines greater than 135 kV | The presentation does not cite an authoritative national source. | OpenStreetMap power lines and substations + public utility or federal GIS where available | Public approximation only | The repo now includes a first-pass OSM baseline generator with a `>=135 kV` transmission-line filter and a companion public substation layer. Remaining fidelity risk is sparse voltage tagging and the absence of utility or federal supplement layers in the first pass. |
| `gap_003` | Average distance to onshore fiber | The presentation does not cite route geometry, and public broadband availability is not the same as route centerlines. | FCC Broadband Data Collection + OSM telecom layers | Weak public proxy | The repo now includes a first-pass fiber proxy workflow that converts exported OSM telecom linework into a route-proxy layer and FCC availability polygons into a binary availability raster aligned to a template raster. Remaining mismatch: the OSM line layer is only a route proxy, while FCC coverage indicates service availability rather than exact fiber centerlines. |
| `gap_004` | Percent of developable land in natural gas service territory | The presentation does not cite a national gas service-territory layer. | State public service commission territory layers where available | Weak public proxy | The repo now includes a state-by-state assembly workflow that merges manually sourced state territory extracts through a local manifest CSV. Remaining limitation: national completeness depends on which state sources are actually collected and normalized into the manifest. |
| `gap_005` | Land fair market value | The presentation does not cite a national open land-value source or preprocessing method. | County assessor parcel values or public land-value proxies | Public approximation only | The repo now includes a first-pass county workflow that joins a local county proxy CSV to county polygons, computes a within-state `state_land_value_index`, and area-weights both raw and normalized values into the repo's EMM zones. Remaining limitation: county valuation methods differ across jurisdictions, so the normalized index is only directly comparable within a state and should not be treated as a harmonized national market-price surface. |
| `gap_006` | Data center construction cost | The presentation does not cite a public national dollars-per-MW source. | Regional wage and price proxies from public labor data | Public approximation only | The repo now includes a first-pass county workflow that joins a local wage-and-price proxy CSV to county polygons, computes `construction_cost_proxy_score = construction_worker_mean_wage_usd * regional_price_parity_index / 100`, normalizes that score to `construction_cost_relative_index`, and area-weights the resulting signals into the repo's EMM zones. Remaining limitation: this is a relative affordability screen built from public labor and price pressure proxies, not an exact dollars-per-MW construction-cost model. |
| `gap_007` | Water availability | The presentation does not cite the source or transformation used for total water availability. | USGS water-use or water-availability proxies | Public approximation only | The repo now includes a first-pass state-to-zone proxy workflow that apportions USGS-style state freshwater withdrawal values into EMM zones using the repo's existing state-to-zone weighting logic. Remaining mismatch: observed withdrawal values are only a proxy for water-resource availability, not a direct site-level availability measure. |
| `gap_008` | RIBITS mitigation banks and in-lieu fee lands | The portal originally looked like a manual-only browser workflow. | Public ORDS webservices plus EPA-hosted ESRI mirror | Public source, scripted webservice workflow | The repo now includes a scripted snapshot command built around `bank_site_list` and `bank_site_data`. Remaining work is downstream transformation of the staged snapshot into the exact exclusion-layer geometry needed by the broader workflow. |

## Bottom line

The remaining work is no longer "find more datasets" in the abstract.

It is a bounded gap-closure program:

1. One commercial dependency that blocks exact parity, even though the repo now has a defined manual procurement path for it.
2. One implemented public power proxy workflow that is still weaker than an authoritative transmission model.
3. One implemented public fiber proxy workflow that is still weaker than exact route geometry.
4. One implemented public gas service-territory assembly workflow whose completeness is state-source dependent.
5. One implemented public land-value proxy workflow whose normalized index is only directly comparable within a state.
6. One implemented public construction-cost proxy workflow whose score reflects wage and price pressure rather than exact dollars per MW.
7. One implemented public water proxy workflow whose selected source measures withdrawal rather than literal site availability.
8. One public dataset that now has a scripted webservice acquisition path, but still needs downstream transformation work to become a finished exclusion-layer input.