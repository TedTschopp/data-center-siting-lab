**********************
data-center-siting-lab
**********************

|License| |Ruff| |Pixi|

.. |Ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff

.. |License| image:: https://img.shields.io/badge/License-BSD_3--Clause-orange.svg
    :target: https://opensource.org/licenses/BSD-3-Clause

.. |Pixi| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json
    :target: https://pixi.sh

.. inclusion-intro


``data-center-siting-lab`` is a bounded public data center siting and large-load
analysis repository built on the upstream ``reVeal`` package from
``NatLabRockies/reVeal``. It adds public-data staging, proxy workflows,
report-bundle generation, executive review artifacts, and explicit assumption
contracts for data center siting analysis.

The underlying Python package and CLI command still use the upstream ``reVeal``
module name. That is intentional: this repository is a derivative lab and report
workflow, not a wholesale rewrite of the original modeling engine.


Installing data-center-siting-lab
=================================
If you would like to install and run the lab from source, we recommend using
`pixi <https://pixi.sh/latest/>`_:

.. code-block:: bash

    git clone git@github.com:TedTschopp/data-center-siting-lab.git
    cd data-center-siting-lab
    pixi run reVeal

For detailed instructions, see the `installation documentation <https://tedtschopp.github.io/data-center-siting-lab/misc/installation.html>`_.


Quickstart
==========
.. To run a quick reVeal demo, use:

.. .. code-block:: shell

..     pixi run demo

.. This will generate sample map outputs using example reV geothermal supply curve outputs.

For more information on running the lab workflows, see
`Usage <https://github.com/TedTschopp/data-center-siting-lab/blob/main/usage.md>`_.


Data Center Public Report Bundle
================================
This repository includes a bounded public approximation of the data center siting
report workflow. It adds repo-local dataset manifests, public-source substitutes,
explicit gap documentation, report-bundle generation, and an Executive Siting and
Buildout View HTML report for coworker review.

Start here if you are trying to understand what is in the solution, what is still
missing, and how the current work differs from the original upstream package and
source report workflow:

* `Data Center Report Bundle Guide <docs/source/misc/data_center_report_bundle.rst>`_
* `Usage Guide <usage.md>`_
* `Report Reproduction Gaps <external-data/provenance/report-reproduction-gaps.md>`_
* `Data Center Bundle Deviations <external-data/provenance/data-center-bundle-deviations.md>`_
* `Publishing Checklist <PUBLISHING.md>`_

The report bundle is intentionally framed as a bounded public approximation, not a
claim of exact report parity. Generated HTML, GeoPackage, JSON, CSV, Markdown, and
cache payloads under ``external-data/derived/report-bundle`` are local deliverables
and are not intended to be committed.


Development
===========
Please see the `Development Guidelines <https://tedtschopp.github.io/data-center-siting-lab/dev/index.html>`_
if you wish to contribute code to this repository.
