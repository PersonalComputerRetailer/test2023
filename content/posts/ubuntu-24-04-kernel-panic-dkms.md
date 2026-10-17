+++
date = '2026-10-16'
draft = false
title = 'Ubuntu 24.04 Kernel Panic After an Update: Fixing a Failed DKMS Build'
tags = ["Ubuntu", "Linux", "DKMS", "Kernel Panic", "Wi-Fi"]
categories = ["技術筆記"]
author = ["Will"]
+++

# Ubuntu 24.04 Kernel Panic After an Update: How I Fixed a Failed DKMS Build (Realtek 8852au)

**Environment:** Ubuntu 24.04 LTS  
**Affected kernel:** 6.8.0-147-generic  
**Last working kernel:** 6.8.0-146-generic  
**Issue:** Kernel panic, incomplete kernel installation, DKMS driver incompatibility  
**Outcome:** Successfully repaired without reinstalling Ubuntu or losing personal data

## 1. The Problem: Ubuntu Wouldn't Boot After an Update

After a routine Ubuntu system update, my computer suddenly failed to boot. Instead of reaching the desktop, it stopped at a kernel panic.

The main error messages were:

```text
/dev/root: Can't open blockdev

VFS: Cannot open root device "/dev/nvme0n1p2"
or unknown-block(0,0): error -6

Kernel panic - not syncing:
VFS: Unable to mount root fs on unknown-block(0,0)
```

Attempting to boot into recovery mode produced the same result.

At first glance, these messages suggested that the Linux kernel could not locate or mount the root filesystem.

Several possible causes came to mind:

- An incomplete kernel update
- A corrupted or incomplete initramfs
- Incorrect GRUB boot parameters
- Missing storage or filesystem drivers
- A problem with the SSD or filesystem

However, a kernel panic does not necessarily mean the storage device has failed.

Before attempting a reinstall, I decided to investigate the kernel installation itself.

## 2. Booting with an Older Kernel

Fortunately, Ubuntu usually retains previous kernel versions.

I restarted the computer and opened the GRUB menu:

```text
Advanced options for Ubuntu
```

Then I selected the previous kernel:

```text
Ubuntu, with Linux 6.8.0-146-generic
```

I chose the normal boot option rather than recovery mode.

**It worked. Ubuntu booted normally.**

After logging in, I confirmed the running kernel:

```bash
uname -r
```

Output:

```text
6.8.0-146-generic
```

This was an important clue.

The older kernel could successfully access the same root filesystem, making a complete filesystem failure less likely. The problem appeared to be associated with the newer kernel or its boot environment.

I deliberately kept the working kernel installed as a fallback.

## 3. Checking APT and Package Management

My next step was to check the package manager:

```bash
sudo apt update
```

This revealed an unrelated but potentially troublesome issue: an outdated AMD Radeon repository.

The error was:

```text
E: The repository
'https://repo.radeon.com/amdgpu/22.20/ubuntu focal Release'
does not have a Release file.
```

The repository targeted Ubuntu 20.04 (Focal Fossa), while the system was running Ubuntu 24.04 (Noble Numbat).

I located the corresponding configuration files using:

```bash
grep -R -n 'repo.radeon.com/amdgpu/22.20' \
  /etc/apt/sources.list /etc/apt/sources.list.d/
```

Two active source files were identified:

```text
/etc/apt/sources.list.d/amdgpu.sources
/etc/apt/sources.list.d/amdgpu-proprietary.sources
```

After confirming that these obsolete repositories were no longer required, I disabled them by renaming the files:

```bash
sudo mv /etc/apt/sources.list.d/amdgpu.sources \
  /etc/apt/sources.list.d/amdgpu.sources.disabled

sudo mv /etc/apt/sources.list.d/amdgpu-proprietary.sources \
  /etc/apt/sources.list.d/amdgpu-proprietary.sources.disabled
```

I then ran:

```bash
sudo apt update
```

This time, APT completed without repository errors.

Importantly, **the obsolete AMD repository was not established as the cause of the kernel panic**. It was a separate issue discovered during troubleshooting.

## 4. Discovering an Incomplete Kernel Installation

Next, I examined the package installation status:

```bash
sudo dpkg --audit
```

The output identified four packages that had not been fully configured:

```text
linux-generic
linux-headers-generic
linux-headers-6.8.0-147-generic
linux-image-6.8.0-147-generic
```

The kernel image and version-specific headers were in a half-configured state.

This strongly suggested that the previous kernel update had not completed successfully.

Before proceeding, I checked disk space:

```bash
df -h / /boot /boot/efi
```

There was plenty of available space on both the root filesystem and EFI partition.

Therefore, insufficient disk space was unlikely to explain the failed installation.

I attempted to complete the interrupted package configuration:

```bash
sudo dpkg --configure -a
```

This produced the error messages that ultimately revealed the underlying package installation problem.

## 5. Finding the Culprit: A Failed DKMS Build

During kernel configuration, Ubuntu attempted to rebuild third-party kernel modules using DKMS (Dynamic Kernel Module Support).

Most modules compiled successfully, but one failed:

```text
dkms autoinstall on 6.8.0-147-generic/x86_64
succeeded for openrazer-driver rtw89

dkms autoinstall on 6.8.0-147-generic/x86_64
failed for 8852au(10)
```

The failing module was:

```text
8852au/1.15.0.1
```

This was a third-party driver for Realtek RTL8852AU-series wireless adapters.

To investigate further, I inspected its compilation log:

```bash
tail -n 40 \
  /var/lib/dkms/8852au/1.15.0.1/build/make.log
```

The critical error was:

```text
error: initialization of
'int (*)(struct wiphy *, struct net_device *,
struct cfg80211_chan_def *)'

from incompatible pointer type
'int (*)(struct wiphy *, struct cfg80211_chan_def *)'

[-Werror=incompatible-pointer-types]
```

The error occurred while compiling the driver's `ioctl_cfg80211.c` file.

Essentially, the driver provided a function pointer with a signature that did not match the interface expected by the kernel headers.

Because incompatible pointer types were treated as errors, compilation stopped.

The failed DKMS build then caused the kernel package configuration scripts to fail.

The sequence was:

1. Ubuntu attempted to configure kernel 6.8.0-147.
2. DKMS attempted to rebuild the third-party `8852au` driver.
3. The driver failed to compile against the new kernel headers.
4. DKMS returned an error.
5. The kernel image and headers remained incompletely configured.
6. The kernel installation process could not finish normally.

**The DKMS failure was the confirmed cause of the incomplete kernel package installation.**

The original root filesystem mount failure was likely related to the incomplete kernel installation or boot environment, although the available logs did not establish the exact intermediate mechanism.

## 6. Checking Whether the Failing Driver Was Still Needed

Before removing a kernel module, it is important to verify whether the hardware still depends on it.

I checked the DKMS status:

```bash
dkms status
```

The output included:

```text
8852au/1.15.0.1, 6.8.0-146-generic: installed

openrazer-driver/3.12.4, 6.8.0-146-generic: installed
openrazer-driver/3.12.4, 6.8.0-147-generic: installed

rtw89/7.3, 6.8.0-146-generic: installed
rtw89/7.3, 6.8.0-147-generic: installed
```

Interestingly, the system had two different Realtek wireless driver implementations installed:

- `8852au/1.15.0.1`
- `rtw89/7.3`

I checked the USB devices:

```bash
lsusb
```

A D-Link 802.11ax USB wireless adapter was detected.

Next, I examined the currently loaded kernel modules:

```bash
lsmod | grep -E '8852au|rtw89'
```

The output showed:

```text
rtw89_8852au_git
rtw89_usb_git
rtw89_8852a_git
rtw89_core_git
```

This was an important discovery.

Although the module name `rtw89_8852au_git` contains the string `8852au`, it belongs to the `rtw89` driver family, not the older standalone `8852au` DKMS package.

The system was already using the `rtw89` driver family, and its DKMS build had succeeded for the new kernel.

This suggested that the older `8852au` DKMS installation was redundant.

**Warning:** Do not blindly remove a DKMS module simply because its compilation fails. If your network adapter depends on that module, removing it may disable Wi-Fi connectivity. Verify the active driver and hardware compatibility first.

## 7. Removing the Incompatible DKMS Module

After confirming that the system was using the alternative `rtw89` driver, I removed the obsolete `8852au` DKMS registration:

```bash
sudo dkms remove 8852au/1.15.0.1 --all
```

The command reported:

```text
Deleting module 8852au-1.15.0.1
completely from the DKMS tree.
```

This removed the old DKMS module registration and its installed kernel modules.

It did not remove the working `rtw89` driver.

The previously working kernel was also retained.

## 8. Completing the Kernel Installation

With the incompatible module removed, I retried the package configuration:

```bash
sudo dpkg --configure -a
```

This time, the operation completed successfully.

The output included:

```text
Setting up linux-image-6.8.0-147-generic
Setting up linux-headers-6.8.0-147-generic

dkms: autoinstall for kernel 6.8.0-147-generic
...done.

Setting up linux-headers-generic
Setting up linux-generic
```

Ubuntu then regenerated the initramfs:

```text
update-initramfs: Generating
/boot/initrd.img-6.8.0-147-generic
```

GRUB was also updated automatically:

```text
Found linux image: /boot/vmlinuz-6.8.0-147-generic
Found initrd image: /boot/initrd.img-6.8.0-147-generic

Found linux image: /boot/vmlinuz-6.8.0-146-generic
Found initrd image: /boot/initrd.img-6.8.0-146-generic

done
```

Both the new and previous kernels remained available in GRUB.

There was no need to manually reinstall the operating system.

## 9. Verifying the Repair

Before rebooting, I performed several checks.

First:

```bash
sudo dpkg --audit
```

There was no output, indicating that dpkg no longer reported incomplete package configurations.

Next:

```bash
dkms status
```

Both `openrazer-driver` and `rtw89` were installed for kernels 6.8.0-146 and 6.8.0-147.

Finally, I checked the newly generated initramfs:

```bash
ls -lh /boot/initrd.img-6.8.0-147-generic
```

The file existed and was approximately 72 MB.

With package configuration completed and the new initramfs generated, I rebooted:

```bash
sudo reboot
```

**Ubuntu successfully booted with the updated kernel.**

The problem was resolved without reinstalling Ubuntu, formatting any partitions, or losing personal files.

## 10. Lessons Learned

This incident highlighted several useful lessons about troubleshooting Linux systems.

### A kernel panic does not automatically mean hardware failure

An inability to mount the root filesystem may look like a storage problem, but the underlying issue can be elsewhere in the boot process.

In this case, the SSD was accessible using the previous kernel.

### Keep at least one known-working kernel

The ability to boot kernel 6.8.0-146 was essential.

Without that fallback, troubleshooting would likely have required a Live USB environment.

Avoid removing your last known-working kernel while diagnosing boot problems.

### DKMS can interrupt kernel updates

DKMS is useful because it automatically rebuilds third-party kernel modules when a new kernel is installed.

However, an incompatible driver can cause its build to fail and prevent kernel packages from completing their configuration.

This is especially relevant for systems using out-of-tree drivers for Wi-Fi adapters, GPUs, or other hardware.

### Read the compilation logs

The most useful diagnostic information did not come from the original kernel panic.

It came from:

```bash
sudo dpkg --configure -a
```

and the DKMS build log:

```text
/var/lib/dkms/8852au/1.15.0.1/build/make.log
```

The compiler error identified the specific incompatible module.

### Do not remove drivers without checking dependencies

The failing `8852au` driver could be removed in this particular case because the system was already using another compatible driver implementation.

That conclusion should not be generalized to every Realtek wireless adapter.

## 11. Quick Troubleshooting Checklist

If Ubuntu fails to boot after a kernel update, the following sequence may help:

| Step | Action | Command |
|---|---|---|
| 1 | Boot an older kernel | GRUB → Advanced options |
| 2 | Check the running kernel | `uname -r` |
| 3 | Inspect package status | `sudo dpkg --audit` |
| 4 | Check disk space | `df -h / /boot /boot/efi` |
| 5 | Retry package configuration | `sudo dpkg --configure -a` |
| 6 | Inspect DKMS modules | `dkms status` |
| 7 | Examine failed builds | `/var/lib/dkms/.../build/make.log` |
| 8 | Identify active hardware drivers | `lsmod`, `lsusb`, `lspci -k` |
| 9 | Address incompatible modules | Depends on the specific driver |
| 10 | Verify and reboot | `sudo dpkg --audit`, `uname -r` |

If necessary, rebuild the initramfs and update GRUB:

```bash
sudo update-initramfs -u -k <kernel-version>
sudo update-grub
```

Replace `<kernel-version>` with the actual installed kernel version.

Do not run `apt autoremove` or remove older kernels until the repaired system has been tested successfully.

## Conclusion

A failed Ubuntu kernel update can be intimidating, especially when the system stops at a kernel panic and reports that it cannot mount the root filesystem.

However, the problem may be recoverable without reinstalling the operating system.

In this case, a third-party Realtek `8852au` DKMS driver failed to compile against kernel 6.8.0-147, leaving several kernel packages incompletely configured.

By booting the previous kernel, inspecting the package manager and DKMS logs, removing an obsolete driver registration, and completing the interrupted kernel configuration, I was able to restore normal boot functionality.

The most valuable lesson was simple:

**Before reinstalling Linux, try booting an older kernel and investigate why the update failed.**

Sometimes the difference between a seemingly broken operating system and a working computer is a single incompatible third-party kernel module.

---

*This article is based on a real troubleshooting session involving Ubuntu 24.04 LTS. Personal identifiers and unrelated system information have been removed. The commands and diagnostic messages are preserved for educational purposes. Hardware configurations and driver requirements vary, so verify compatibility before removing kernel modules.*
