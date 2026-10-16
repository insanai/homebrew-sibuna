# Sibuna Homebrew tap

The upstream tap for [Sibuna](https://github.com/insanai/sibuna), web protection with
browser proof of work and an optional console. This repository publishes a CLI
**formula** for macOS and Linux, on Apple Silicon, ARM64 and x86-64. Packaging source and
the release checks live in the
[Sibuna repository](https://github.com/insanai/sibuna/tree/main/distribution/homebrew).

The formula installs the release archives: the same executables that Sibuna's release
workflow built and started on each platform before publication. Homebrew downloads the
archive for your system and checks it against the SHA-256 in the formula.

## Installation

```sh
brew tap insanai/sibuna
brew install insanai/sibuna/sibuna
sibuna --version
```

The current formula follows the newest published release, which is a beta at present.
No service starts automatically.

Before running Sibuna, create a private admission seed of 64 hexadecimal digits and a
persistent private data directory, and point Sibuna at an IP-literal origin:

```sh
(umask 077; od -An -tx1 -N32 /dev/urandom | tr -d ' \n' > admission.seed)
sibuna --host 127.0.0.1 --port 8080 --upstream-port 3000 \
  --secret-file ./admission.seed --data-dir ./data
```

The console is opt-in. See the
[operations guide](https://insanai.github.io/sibuna/book/operations.html) for
configuration, origin protection, upgrades and backups.

Stop your running Sibuna process before upgrading:

```sh
brew update
brew upgrade insanai/sibuna/sibuna
```

To remove the executable after stopping it:

```sh
brew uninstall insanai/sibuna/sibuna
```

Seeds, configuration and state live outside Homebrew's installation and are kept
during upgrade and removal. Back up the data directory before an upgrade.

## Release updates

The daily **Update Sibuna formula** workflow imports the formula attached to the newest
published release. Before it commits the formula, it checks the formula's own checksum,
and every archive URL and SHA-256 in it, against the release's `SHA256SUMS` and GitHub's
asset digests. Maintainers can also run the workflow for a given release tag. It uses
this tap's own `GITHUB_TOKEN`; no cross-repository secret is needed.

Homebrew core inclusion requires a separate community audit and human review.

## License and security

Sibuna is free software under **LGPL-3.0-or-later**, and so are this tap's recipes,
tooling and documentation. See [LICENSE](LICENSE), [LICENSES](LICENSES) and
[NOTICE](NOTICE) for the complete terms and third-party notices.

Please report security issues privately through
[Sibuna's security reporting page](https://github.com/insanai/sibuna/security/advisories/new).
See [SECURITY.md](SECURITY.md) for the policy. Public issues are for non-sensitive
packaging defects; do not include credentials, private seeds or vulnerability details.
