# Release process

Levo.ai's Demo apps are available as a Docker images.

Stable releases are built from git tags in the `main` branch prefixed with `v`, for example, `v1.0`.

The Docker images for the demo apps are tagged as `stable` and `<version>` and available on DockerHub and
GitHub Package Registry.

## How to make a new release

1. Update the package version in `README` and commit it to the repo
2. Tag this commit with the package version prefixed by `v` (for example, `v1.1`)
3. Push the git tag and wait for CI to finish

## Latest releases

Additionally, Docker images for the demo apps are built on every commit to the `main` branch.
They are tagged with the `latest` tag and handled automatically.
