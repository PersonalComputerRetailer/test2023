+++
date = '2026-11-05'
draft = false
title = "Sober “Gameplay Unavailable” on Linux: Installing a Newer Flathub Build When Flatpak Says “Nothing to do”"
tags = ["Linux", "Flatpak", "Sober", "Roblox"]
categories = ["技術筆記"]
author = ["Will"]
+++

Sober reported “Gameplay Unavailable” while Flatpak found no updates. This post documents how I compared Flathub builds and commits, installed a newer signed package, and restored the normal update path.
...<!--more-->
<div style="clear:both;"></div>

# Sober “Gameplay Unavailable” on Linux: Installing a Newer Flathub Build When Flatpak Says “Nothing to do”

*November 5, 2026 · Technical Notes · Linux / Flatpak / Sober / Roblox*

Sober suddenly stopped launching Roblox on a Linux computer. The window reported **“Gameplay Unavailable”**, but the usual Flatpak update command said **“Nothing to do.”** I eventually found that a newer Sober build had already been produced by Flathub, although the stable repository was still serving the older build. Manually installing that signed build restored normal operation.

This post documents the troubleshooting process, the evidence behind the diagnosis, and the commands I used. **I did not compile Sober from source or modify its executable.** I installed an existing Flathub build that had not yet reached the normal stable update channel.

**Environment:** Linux desktop, Flatpak system installation  
**Application:** `org.vinegarhq.Sober`  
**Displayed version:** 1.8.0 (both before and after the fix)  
**Issue:** “Gameplay Unavailable”; standard Flatpak update found no updates  
**Outcome:** Sober launched successfully after manually installing a newer signed Flathub build

> **Time-sensitive workaround:** The build repository and commit in this article document a specific incident on November 5, 2026. A numbered Flathub build repository is not a permanent release channel. Try the regular stable update first, and prefer the latest stable version when it is available. Installing a build before stable publication is not an officially endorsed release procedure.

## 1. The Problem: Sober Would Not Start Roblox

The problem was straightforward from the user's perspective: Roblox had stopped working through Sober.

My first attempt was the normal Flatpak update:

```bash
flatpak update --system -y org.vinegarhq.Sober
```

The result was:

```text
Looking for updates…

Nothing to do.
```

That usually means the installed application already matches the version offered by the configured repository. But in this case, Sober still refused to start.

I checked the installed package and the version offered by Flathub:

```bash
flatpak info --system org.vinegarhq.Sober
flatpak remote-info --system flathub org.vinegarhq.Sober
```

Both still pointed to the older October build.

I also refreshed the AppStream metadata and tried again:

```bash
flatpak update --system --appstream flathub
flatpak update --system -y org.vinegarhq.Sober
```

Nothing changed.

This was an important distinction. **A working build might exist somewhere, but Flatpak would not automatically install it unless the configured update repository offered it.** Refreshing AppStream metadata does not publish a new application commit to the stable repository.

## 2. Inspecting the Startup Logs

Instead of repeatedly reinstalling the same version, I launched Sober from the terminal:

```bash
flatpak run org.vinegarhq.Sober
```

Sober's application logs were also available at:

```text
~/.var/app/org.vinegarhq.Sober/data/sober/sober_logs/
```

The relevant log lines were:

```text
info: app: app tag: s0126-3212-x86_64-gnu
info: state: using manifest object: {"app_settings":{"FFlagUIGpuGradient11":false},"r1":1,"startup_message_treatment":"fatal_v1__update_pending","u":1}
info: UIServicesConduit: will execute ui service binary
```

The most useful clue was:

```text
"startup_message_treatment":"fatal_v1__update_pending"
```

The same app tag appeared in Sober's [public runtime manifest](https://raw.githubusercontent.com/vinegarhq/sober/refs/heads/gh-pages/app). The manifest selected an update-pending startup treatment for the installed build. This was consistent with the “Gameplay Unavailable” dialog.

The logs showed that startup stopped before normal Roblox engine initialization. They did **not** establish exactly which Roblox compatibility change required the update, so I did not assume a specific underlying cause.

## 3. Finding the Newer Build

The next question was whether a newer Sober package already existed.

I checked the [Flathub packaging repository](https://github.com/flathub/org.vinegarhq.Sober) and found an [official packaging commit](https://github.com/flathub/org.vinegarhq.Sober/commit/01a28a7acd44f9f973bfab2079436105ecfed62c) referencing a November 5 build artifact:

```text
2026-11-05_c107424
```

The [Flathub build job](https://hub.flathub.org/status/653046) pointed to build repository **337540**.

I compared the installed build with that new artifact:

| Detail | Installed build | New Flathub build |
| --- | --- | --- |
| Displayed application version | `1.8.0` | `1.8.0` |
| Artifact ID | `2026-10-05_23f45dd` | `2026-11-05_c107424` |
| Runtime app tag | `s0126-3212-x86_64-gnu` | `s0128-20136-x86_64-gnu` |
| Flatpak commit prefix | `7b6430c703e8` | `0fe4cd04b5ad` |
| Update-pending startup treatment | Present | Absent |

The surprising part was that **both builds identified themselves as version 1.8.0**. Looking only at the version number would have hidden the difference. The artifact date, runtime tag, and Flatpak commit were much more informative.

At the time of troubleshooting, the normal stable Flathub repository still served the October build, while the numbered build repository already contained the November package.

That explained the apparent contradiction: **the new build existed, but `flatpak update` had no new stable commit to install.** I could not determine why stable publication was delayed.

## 4. Installing the Existing Signed Flathub Build

I decided to install that build manually. This did **not** mean compiling the application locally or patching a binary. I was installing a package already produced by Flathub's build infrastructure.

The first approach, installing the `.flatpakref` directly with `--reinstall`, returned an “already installed” result on the Flatpak version I tested. Explicitly adding the build repository as a remote worked.

Before changing the installation, I closed Sober.

### Obtain the build repository's signing key

I retrieved the GPG key embedded in Flathub's own `.flatpakref` file. The script also checks that the reference names the expected application and repository:

```bash
mkdir -p /tmp/sober-update

python3 - <<'PY'
import base64
import configparser
import pathlib
import urllib.request

url = (
    'https://dl.flathub.org/build-repo/337540/'
    'org.vinegarhq.Sober.flatpakref'
)
with urllib.request.urlopen(url, timeout=30) as response:
    text = response.read().decode('utf-8')

config = configparser.ConfigParser()
config.read_string(text)
ref = config['Flatpak Ref']
assert ref['Name'] == 'org.vinegarhq.Sober'
assert ref['Url'].rstrip('/') == 'https://dl.flathub.org/build-repo/337540'

pathlib.Path('/tmp/sober-update/flathub-build.gpg').write_bytes(
    base64.b64decode(ref['GPGKey'])
)
PY
```

### Add the build repository and reinstall

I added the numbered repository, keeping GPG signature verification enabled:

```bash
flatpak remote-add --system --if-not-exists --no-enumerate \
  --gpg-import=/tmp/sober-update/flathub-build.gpg \
  sober-nov5-build https://dl.flathub.org/build-repo/337540
```

Then installed the existing application from that remote:

```bash
flatpak install --system -y --reinstall \
  sober-nov5-build org.vinegarhq.Sober
```

`--no-enumerate` prevents the extra remote from appearing as a general application catalog. The reinstall replaced the application package without requesting deletion of its existing application data.

I did not disable GPG verification, change Sober's runtime manifest, patch its executable, or alter kernel security settings.

## 5. Verifying That the Fix Worked

After installation, I checked the package and commit:

```bash
flatpak info --system org.vinegarhq.Sober
flatpak info --system --show-commit org.vinegarhq.Sober
```

The expected commit for the November build was:

```text
0fe4cd04b5ad9b71273fe9ccd3d8e28be6d43cfbd302bae6bc2f04243f0df4d3
```

Then I launched the application:

```bash
flatpak run org.vinegarhq.Sober
```

The log now reported a different app tag and manifest:

```text
info: app: app tag: s0128-20136-x86_64-gnu
info: state: using manifest object: {"app_settings":{"FFlagUIGpuGradient12":false},"r1":1,"u":1}
```

The earlier `fatal_v1__update_pending` treatment was absent. Sober proceeded to download the required Roblox packages and initialize the Roblox engine.

Most importantly, the person using the computer confirmed that Roblox worked again.

## 6. Restoring Normal Update Behavior

There was one more issue to address. A numbered Flathub build repository is a snapshot, not the normal long-term update channel. I did not want the installation to depend on that temporary build URL for future updates.

After confirming that Sober worked, I changed the additional remote's URL to the ordinary Flathub stable repository:

```bash
flatpak remote-modify --system \
  --url=https://dl.flathub.org/repo/ \
  --collection-id=org.flathub.Stable \
  --title='Flathub (Sober updates)' \
  sober-nov5-build
```

The remote retained the local name `sober-nov5-build`, but future update checks used the stable repository URL.

During verification, Flatpak reported:

```text
Update is older than current version
```

This made sense: the locally installed November build was newer than the package still advertised by stable. Flatpak preserved the installed build instead of replacing it with the older one.

Once the standard Flathub remote offers the same or a newer build, I can return the installation to its ordinary remote. First, check what stable offers:

```bash
flatpak remote-info --system flathub org.vinegarhq.Sober
```

**Do not proceed until stable shows this build or a newer one.** Then reinstall from the normal remote:

```bash
flatpak install --system -y --reinstall flathub org.vinegarhq.Sober
```

After `flatpak info` confirms that `flathub` is the installation origin, the temporary named remote can be removed:

```bash
flatpak remote-delete --system sober-nov5-build
```

## 7. A Debugging Trap: Tracing Changed the Error

One misleading result appeared during the investigation. Launching Sober under `strace -f` produced a separate message involving initialization of core functionality and `ptrace`.

That was different from the failure observed during a normal launch. External tracing interfered with startup behavior, making it a poor basis for diagnosing the original update-pending message.

I therefore relied on normal startup logs, the public manifest, and Flathub's build records for the final diagnosis. No kernel security changes were needed.

## 8. Lessons Learned

### “Nothing to do” only describes the configured update source

The Flatpak client was not necessarily broken. It was correctly reporting that the configured stable repository had no newer application commit to offer.

### Version numbers are not always enough

Both packages reported `1.8.0`. Comparing their artifact identifiers, runtime app tags, and Flatpak commit hashes revealed the actual difference.

### A completed build is not the same as a stable release

Flathub's build infrastructure already hosted the new signed package, but the usual stable update path had not yet exposed it. A publicly accessible build artifact should not be mistaken for a recommended stable release.

### Preserve the update path after a temporary workaround

Installing from a numbered build repository can solve an immediate problem, but that repository is not intended to be a permanent update source. It is important to understand and verify where future updates will come from.

### Keep the troubleshooting evidence proportional to the problem

In this case, normal logs, a public manifest, and repository metadata were enough to support the diagnosis. There was no need to modify Sober or bypass a startup check.

## 9. Quick Troubleshooting Checklist

| Step | Action | Command or source |
| --- | --- | --- |
| 1 | Try the normal update | `flatpak update --system org.vinegarhq.Sober` |
| 2 | Check installed build | `flatpak info --system org.vinegarhq.Sober` |
| 3 | Check stable repository | `flatpak remote-info --system flathub org.vinegarhq.Sober` |
| 4 | Review normal startup logs | `flatpak run org.vinegarhq.Sober` |
| 5 | Inspect application logs | `~/.var/app/org.vinegarhq.Sober/data/sober/sober_logs/` |
| 6 | Compare public build records | [Flathub packaging repository](https://github.com/flathub/org.vinegarhq.Sober) |
| 7 | If necessary, evaluate an official signed build | Verify the specific build and its GPG-enabled remote |
| 8 | Verify the running application | `flatpak info`, `flatpak run` |
| 9 | Restore ordinary updates | Confirm stable has caught up before returning to `flathub` |

For a per-user Flatpak installation, use `--user` instead of `--system` where appropriate. The commands above document the **system-wide installation** tested in this case.

## Conclusion

Sober's “Gameplay Unavailable” message initially looked like a broken application that would require waiting for a future release. But the startup log showed an update-pending treatment, and the public Flathub build records revealed that a newer signed build already existed.

The normal stable repository had not yet published that build, so `flatpak update` correctly reported “Nothing to do.” By manually installing the existing build, verifying its commit, and restoring the normal update URL, I got Sober working again without compiling or modifying the software.

The main lesson is simple:

**When a Flatpak application requires an update but the client finds none, compare the installed commit with the project's published build artifacts—not just the version number.**

---

*This article is based on a real troubleshooting session on November 5, 2026. Personal identifiers and unrelated system details have been omitted. The recorded commands, build identifiers, and diagnostic messages are preserved for educational purposes. Build repositories may expire, and a build not yet published to stable may carry compatibility risks. Always prefer the normal stable update when available.*
