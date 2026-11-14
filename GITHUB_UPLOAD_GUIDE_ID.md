# RANCAGE Repository Maintenance Guide (Windows)

Main repository:

`https://github.com/henxnomercy/rancage-language`

Do not reinitialize an existing local repository with `git init`. Preserve its
`.git` directory and existing history.

## Verify the local repository

```powershell
git remote -v
git branch --show-current
git status
```

Expected `origin` URL:

`https://github.com/henxnomercy/rancage-language.git`

## Synchronize the main branch

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git status
```

Only switch branches when the working tree is clean or all local changes have
been safely committed/stashed. Work on feature branches and use pull requests
for code changes.

## Validate before pushing

```powershell
git diff --check
git status --short
.\run-tests.cmd
.\cage.cmd --version
.\cage.cmd check .\examples\hello.cage
.\cage.cmd run .\examples\hello.cage
```

To update the remote after a repository rename:

```powershell
git remote set-url origin https://github.com/henxnomercy/rancage-language.git
git remote -v
git fetch origin
```

Do not use `git init`, `git push --force`, `git reset --hard`, or `git clean -fd`
as routine troubleshooting. Never commit `.env` files, tokens, API keys,
passwords, Android keystores, private keys, or local build artifacts.

## Publication and security settings

Before changing visibility, review the license files, current working-tree
diff, complete commit history, tags, workflow permissions, and commit author
metadata. Assume branches, tags, commit metadata, and Actions logs may become
publicly inspectable.

GitHub provides private vulnerability reporting for eligible public
repositories, but it must be enabled separately for this repository.
After making this repository public, open Settings > Security and quality >
Advanced Security > Private vulnerability reporting and enable it.

Then verify that the Report a vulnerability action is available in the
repository's Advisories area. Do not claim this feature is enabled until
the setting has actually been activated.
