---
id: X1tG4eLPTQw
title: managing multiple git identities
description: dealing with multiple identities for work/personal accounts
author: Darius
visibility: public
created: 2026-04-20T11:29:01+00:00
---


If like myself, you find yourself using different accounts across multiple platforms (GitHub for work/personal, Codeberg, etc.), you need to manage multiple Git identities on one machine.

Here I documented my setup, mostly to have a quick reference I can pull up to share with friends or if I need to set up another machine.

## Setup

General setup: main `.gitconfig` is just includes based on different folders:

```ini
[includeIf "gitdir:~/Projects/work/"]
    path = "~/Projects/work/.gitconfig-work"
[includeIf "gitdir:~/Projects/personal/"]
    path = "~/Projects/work/.gitconfig-personal"
``` 

Inside each gitconfig, I define basic identity stuff and a few defaults:

```ini
[user]
    email = <REDACTED>
    name = Darius
    signingkey = <REDACTED> # GPG signing key id
[push]
    default = current
[alias]
    tree = log --graph --pretty=oneline --abbrev-commit
[core]
    editor = code
    sshCommand = "ssh -i ~/.ssh/dit-gh/some_ssh_key"
[commit]
    gpgsign = true
[init]
    defaultBranch = main
```

## Extra: Adding a GPG key & using it on GitHub/GitLab

To generate a new GPG key:

```bash
gpg --full-generate-key
```

Fill out all the info, add a password and it's ready to export and use for signing commits. Make sure the email matches one of the verified emails on your GitHub/GitLab/etc. account if you want to have verified commits on that site.

To export the key, first grab the long form of the GPG key id:

```bash
gpg --list-secret-keys --keyid-format=long
```

For the relevant key, it should be the string that comes after `ed25519/...` or `4096R/...` etc.

Then you can use the ID to export the public key:

```bash
gpg --armor --export SOMEGPGKEYID
```

The output can be pasted somewhere in your account settings, and you're ready to go.

## Extra: Managing SSH keys

To manage SSH keys, you can define multiple hosts in your `.ssh/config` file:

```sshconfig
# work account
Host github.com-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/work-gh/id_ed25519

# personal account
Host github.com-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/personal-gh/id_ed25519

Host codeberg.org
    HostName codeberg.org
    User git
    IdentityFile ~/.ssh/codeberg_key
```

If you have multiple accounts on GitHub (same `HostName`), make sure to give unique names for the `Host` (e.g. `github.com-work`).

When cloning repos, make sure to then use SSH and specify the different host (so instead of just `github.com`, you need to use `github.com-personal` when cloning).

## Better cloning for same host

Since the above mentioned unique hostname can be quite of a hassle sometimes, I have created a zsh function and added it to my `.zshrc`:

```zsh
pclone() {
    git clone git@github.com-personal:"$@".git
}
```

Like that, I can just use `pclone username/somerepo.git` and know for sure that the correct SSH key will be used.

Another option would be to include a custom SSH command in your config, see [this comment on lobsters](https://lobste.rs/s/ggqd2g/how_i_configure_my_git_identities#c_rchsxp) for more info.
