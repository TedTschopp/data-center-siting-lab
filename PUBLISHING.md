# Publishing Checklist

## Bottom Line

This repository can be published for coworker review once the documentation,
validation checks, and metadata decisions below are complete. Keep the distinction
clear: source code, tests, manifests, provenance, and documentation are versioned;
large downloads and generated report-bundle payloads are not.

## Source Vs Generated Policy

Commit these files and directories:

- `reVeal/` source code.
- `tests/` regression tests and fixtures.
- `README.rst`, `usage.md`, `PUBLISHING.md`, and `docs/source/`.
- `external-data/manifest/` source inventory, gap register, and substitute matrix.
- `external-data/provenance/` human-readable provenance and deviation notes.
- Small reproducible derived configuration files and README policy files under
  `external-data/derived/`.

Do not commit these local/generated surfaces:

- `external-data/raw/` downloaded source archives and files.
- `external-data/unpacked/` extracted working copies.
- `external-data/examples/` runnable local example bundles.
- Generated report-bundle HTML, GeoPackage, JSON, CSV, Markdown, and cache payloads
  under `external-data/derived/report-bundle/`.

The tracked exception under the report-bundle directory is
`external-data/derived/report-bundle/README.md`, which documents the regeneration
policy.

## Report-Bundle Snapshot Policy

The report bundle is a regenerated local deliverable. Treat it like a build
artifact, not source code.

- Recreate it with `python -m reVeal.public_data run-public-report-bundle`.
- Review the generated HTML and contract artifacts locally.
- If a reviewed snapshot needs to be shared, attach the generated bundle to a GitHub
  release, internal file share, or other controlled artifact store.
- Do not make the ignored generated payloads part of normal git history.

## Validation Commands

Run these before publishing or handing the repo to coworkers:

```bash
micromamba run -p /Users/tedtschopp/micromamba/envs/reVeal make -C /Users/tedtschopp/Developer/reVeal/docs html
micromamba run -p /Users/tedtschopp/micromamba/envs/reVeal python -m pytest tests/test_public_data.py::test_run_public_report_bundle_writes_manifest_and_deviation_note -q
uvx ruff check ./reVeal && git diff --check
```

For a full confidence pass:

```bash
micromamba run -p /Users/tedtschopp/micromamba/envs/reVeal python -m pytest -q
```

## Metadata Review Before Publishing Under TedTschopp

The current repository metadata still points to upstream `NatLabRockies/reVeal` and
the `NLR-reVeal` package identity. That is deliberate until the publishing model is
explicit.

Before publishing under `TedTschopp`, decide whether this is:

- A fork that preserves upstream package identity and attribution.
- A renamed derivative package.
- An internal/private analysis repository that is not intended for package release.

Review these files in one deliberate metadata change:

- `pyproject.toml`: project URLs, package name, author/maintainer posture, and PyPI
  implications.
- `README.rst`: clone links, documentation links, badges, Codecov target, and usage
  links.
- `CITATION.cff`: `repository-code`, release metadata, and citation expectations.
- `docs/source/conf.py`: GitHub context owner/repo/version settings.
- Git remotes and branch protection rules.
- Any GitHub release, documentation-hosting, or issue-template links introduced
  outside this checklist.

Do not rewrite upstream attribution casually. If the repository is a fork, preserve
the original license, citation metadata, and upstream authorship while making the
fork ownership and additions clear.

## Attribution To Preserve

- License: BSD-3-Clause.
- Upstream project: `NatLabRockies/reVeal`.
- Package identity unless intentionally renamed: `NLR-reVeal`.
- Citation metadata in `CITATION.cff` unless a new derivative citation is created
  with clear provenance.
- Existing author and maintainer records unless the project governance changes.

## Coworker Handoff Checklist

- [ ] Run the validation commands above.
- [ ] Confirm `git diff --check` is clean.
- [ ] Confirm generated report-bundle payloads are not staged.
- [ ] Regenerate the report bundle locally if a fresh HTML view is needed.
- [ ] Open `external-data/derived/report-bundle/public_report_suitability_map.html`
      and review suitability, buildout, theme, and display-mode controls.
- [ ] Read `docs/source/misc/data_center_report_bundle.rst`.
- [ ] Read `external-data/provenance/data-center-bundle-deviations.md`.
- [ ] Review `external-data/provenance/report-reproduction-gaps.md` for remaining
      source-data blockers.
- [ ] Decide whether the repo is being published as a fork, a derivative package, or
      an internal analysis repository.
- [ ] Update publishing metadata only after that decision is explicit.
