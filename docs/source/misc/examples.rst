.. _examples:

Examples
========

The repo includes runnable public-data example bundles for the generated proxy
workflows. These examples are intentionally staged under ``external-data/examples``
so they can be rebuilt locally without committing generated inputs and outputs.

Stage a single example bundle from the repository root:

.. code-block:: bash

   python -m reVeal.public_data stage-example-bundle public_data_center_baseline --repo-root .

Available bundle IDs are:

* ``public_data_center_baseline``
* ``public_power_infrastructure_baseline``
* ``public_fiber_proxy_baseline``
* ``public_gas_service_territory_baseline``
* ``public_land_value_proxy``
* ``public_construction_cost_proxy``
* ``public_water_availability_proxy``

Each staged bundle writes ``external-data/examples/<bundle_id>/README.md`` with
the exact command and expected outputs for that workflow.

To stage and run the validated public example workflows with checkpointed
stop/resume behavior, use:

.. code-block:: bash

   python -m reVeal.public_data run-public-example-workflows \
     --status-path external-data/derived/public_example_workflows_status.json

Use ``--resume`` to continue an interrupted run, ``--force`` to restart from a
clean status file, and ``--force-stage`` to rebuild the staged example bundles
before running them.

These examples cover the public approximation surface only. They do not recover
commercial or uncited report inputs, and they do not make the generated proxy
layers equivalent to report-grade siting evidence.
