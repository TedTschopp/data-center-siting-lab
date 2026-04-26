# Public Report Limitations

This bundle carries forward the known limitations and candidate refinements named in the LinkedIn Part I and Part II descriptions.
These items are not fully implemented in the current bounded public report surface and should be read as active fidelity limits.

| Limitation | Status | Current posture | Output implication |
| --- | --- | --- | --- |
| Local transmission hosting capacity | bounded proxy | The current bundle stages a regional NERC reserve-margin headroom overlay as a coarse hosting-capacity proxy, but it still does not model local transmission hosting-capacity headroom. | The hosting overlay supports coarse regional screening only; it does not confirm local deliverability or interconnection feasibility. |
| Demand queue times | not implemented | The current bundle does not model interconnection queue wait times or developer queue backlog. | Report outputs do not imply deployment-ready timing or queue-adjusted build schedules. |
| Zoning information | bounded proxy | The current bundle stages an NLCD developed-land context overlay as a coarse zoning proxy, but it still does not model parcel-level zoning or allowed land uses. | The zoning overlay supports coarse developed-context screening only; it does not confirm parcel-level zoning approval or data-center entitlement. |
| Permitting and ordinance information | not implemented | The current bundle does not model local permitting pathways or ordinance restrictions. | Report outputs do not imply permit readiness or ordinance compatibility. |
| More representative capacity scaling by market trends | bounded approximation | The current bundle uses public EER scenario inputs and smoke-config site-addition limits rather than market-specific capacity scaling. | Cumulative buildout outputs are screening artifacts, not market-calibrated deployment forecasts. |
| Social acceptance | not implemented | The current bundle does not model community acceptance, local opposition, or related siting friction. | Ranked outputs do not account for local acceptance risk. |
