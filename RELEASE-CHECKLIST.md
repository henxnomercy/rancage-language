# RANCAGE Standalone Release Checklist

Before publishing any Windows standalone release:

- [ ] Source unit/integration tests pass on the declared Python versions.
- [ ] GitHub Actions Windows build succeeds.
- [ ] One-file executable smoke tests pass.
- [ ] One-folder executable smoke tests pass.
- [ ] Source `.cage` check/run pass from the packaged executable.
- [ ] Bytecode `.rcb` build/run pass from the packaged executable.
- [ ] Artifact is downloaded and tested on a clean Windows machine without Python installed.
- [ ] SHA-256 hashes are published and verified.
- [ ] Third-party notices accompany the distribution.
- [ ] Release notes clearly state the build bundles Python and is not a native compiler.
