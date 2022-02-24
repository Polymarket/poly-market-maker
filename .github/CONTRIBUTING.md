## DCLOB Monorepo Contribution Guide

All contributions to the dclob are welcome and greatly appreciated! This document serves to outline the process for contributions and help you get set up.

### Steps to get started

1. Fork 'Polymarket/dclob'
2. Clone your fork
3. Follow the [installation instructions](./README.md) in the monorepo's top level README.
4. Open pull requests with the `[WIP]` flag against the `master` branch and include a description of the intended change in the PR description.

Before removing the `[WIP]` tag and submitting a PR for review, make sure that:

- it passes our linter checks
- the test suite passes for all packages
- it passes our continuous integration tests
- your fork is up to date with `master`

### Branch structure & naming

Our main branch, `master`, represents the current development state of the codebase. All pull requests should be opened against `master`.

Name your branch with the format `{fix | feature | refactor }/{ description }`

- A `fix` addresses a bug or other issue
- A `feature` adds new functionality/interface surface area
- A `refactor` changes no business logic or interfaces, but improves implementation

### Additional Details

If you have any questions, please feel free to reach out to [Liam Kovatch](mailto:liam@polymarket.com) (GitHub [@l-kov](https://github.com/l-kov)), or message us on any of our communication channels. We are always happy to help! If you have feedback, bugs, or feature requests, please shoot them our way.
