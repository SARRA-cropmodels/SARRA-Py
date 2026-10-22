# SARRA-Py documentation

These Markdown files are the maintained documentation for the current code.
They can be read directly in the repository without building or deploying a
website.

## Start here

| If you want to... | Read... |
|---|---|
| Run a prepared dataset from Python or the command line | [Python API and command line](usage_api_cli.md) |
| Follow a complete, commented workflow | [Example notebooks](notebook_examples.md) |
| Understand parameter groups and overrides | [Parameter files](parameter_files.md) |
| Understand the daily calculation and its scientific status | [Model formalisms](model_formalisms.md) |
| Understand grid choice, coordinates and spatial outputs | [Spatialization strategy](spatialization_strategy.md) |
| Understand software layers and execution engines | [Software architecture](architecture.md) |
| See unresolved scientific questions | [Scientific validation questions](scientific_validation_questions.md) |
| Review release changes | [Changelog](../CHANGELOG.md) |

The [project README](../README.md) covers installation and a first run.
Scientific equations and units belong in *Model formalisms*; unresolved choices
belong in *Scientific validation questions*.

## Maintaining the documentation

Edit the relevant Markdown file alongside changes to model behaviour, input
requirements or the public API. Distinguish behaviour observed in the active
code from equations validated against a scientific source. Link new guides from
this index.
