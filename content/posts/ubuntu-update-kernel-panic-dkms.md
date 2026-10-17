+++
date = '2026-10-16'
draft = false
title = 'Ubuntu 更新後無法開機？一次 Kernel Panic 與 DKMS 驅動衝突的修復紀錄'
tags = ["Ubuntu", "Linux", "DKMS", "Kernel Panic", "Wi-Fi"]
categories = ["技術筆記"]
author = ["Will"]
+++

# Ubuntu 更新後無法開機？一次 Kernel Panic 與 DKMS 驅動衝突的修復紀錄

**環境：** Ubuntu 24.04 LTS  
**問題 Kernel：** 6.8.0-147-generic  
**可正常開機 Kernel：** 6.8.0-146-generic  
**問題類型：** Kernel Panic、DKMS 編譯失敗、第三方 Wi-Fi 驅動不相容  
**修復結果：** 成功，無須重灌系統

## 一、問題發生：Ubuntu 更新後無法開機

某次 Ubuntu 系統更新後，重新啟動電腦時，系統突然無法進入桌面，而是停留在 Kernel Panic 畫面。

主要錯誤訊息如下：

```text
/dev/root: Can't open blockdev

VFS: Cannot open root device "/dev/nvme0n1p2"
or unknown-block(0,0): error -6

Kernel panic - not syncing:
VFS: Unable to mount root fs on unknown-block(0,0)
```

即使嘗試進入 Recovery Mode，仍然發生相同問題。

從錯誤訊息判斷，Linux Kernel 無法找到或掛載根檔案系統（root filesystem）。

這類問題可能由多種原因造成：

- Kernel 更新未完成。
- initramfs 損壞或缺少必要模組。
- GRUB 開機參數錯誤。
- 儲存裝置或檔案系統發生問題。

因此，不能只憑 Kernel Panic 畫面就斷定硬碟損壞。

## 二、第一步：使用舊版 Kernel 開機

Ubuntu 通常會保留至少一個舊版 Kernel，讓使用者在新版 Kernel 出問題時仍有機會進入系統。

重新開機，進入 GRUB 選單：

```text
Advanced options for Ubuntu
```

選擇先前正常運作的 Kernel：

```text
Ubuntu, with Linux 6.8.0-146-generic
```

注意選擇一般開機模式，而不是 Recovery Mode。

這次成功進入 Ubuntu 桌面。

透過 Terminal 確認：

```bash
uname -r
```

結果：

```text
6.8.0-146-generic
```

這是一個重要線索：舊 Kernel 能正常掛載同一個 root filesystem，表示問題較可能與新版 Kernel 或開機環境有關，而不是整個作業系統完全損壞。

**在問題修復之前，請勿刪除這個能正常開機的舊 Kernel。**

## 三、第二步：檢查 APT 套件狀態

先執行：

```bash
sudo apt update
```

本案例首先遇到另一個問題：系統仍保留一個失效的第三方 AMD repository。

錯誤如下：

```text
E: The repository
'https://repo.radeon.com/amdgpu/22.20/ubuntu focal Release'
does not have a Release file.
```

該 repository 對應舊版 Ubuntu 20.04（focal），而目前系統使用 Ubuntu 24.04（noble）。

透過以下指令找到來源：

```bash
grep -R -n 'repo.radeon.com/amdgpu/22.20' \
  /etc/apt/sources.list /etc/apt/sources.list.d/
```

本案例找到兩個啟用中的設定檔：

```text
/etc/apt/sources.list.d/amdgpu.sources
/etc/apt/sources.list.d/amdgpu-proprietary.sources
```

確認它們確實是已不再使用的舊 repository 後，將其停用：

```bash
sudo mv /etc/apt/sources.list.d/amdgpu.sources \
  /etc/apt/sources.list.d/amdgpu.sources.disabled

sudo mv /etc/apt/sources.list.d/amdgpu-proprietary.sources \
  /etc/apt/sources.list.d/amdgpu-proprietary.sources.disabled
```

再次執行：

```bash
sudo apt update
```

APT 更新成功。

需要強調的是，**這個失效的 AMD repository 並非後續確認的 Kernel 安裝失敗主因**，只是排除過程中發現的另一個問題。

## 四、第三步：發現 Kernel 套件安裝不完整

執行：

```bash
sudo dpkg --audit
```

結果顯示四個套件尚未完成設定：

```text
linux-generic
linux-headers-generic
linux-headers-6.8.0-147-generic
linux-image-6.8.0-147-generic
```

其中兩個套件處於 half-configured 狀態。

接著檢查磁碟空間：

```bash
df -h / /boot /boot/efi
```

結果顯示 root filesystem 尚有超過 100 GB 可用空間，EFI partition 也有充足空間。

因此，本案例沒有明顯的磁碟空間不足問題。

嘗試完成套件設定：

```bash
sudo dpkg --configure -a
```

這次終於出現真正有用的錯誤訊息。

## 五、第四步：找到根本問題——DKMS 編譯失敗

執行 `dpkg --configure -a` 時，系統嘗試為新版 Kernel 重新編譯第三方驅動。

其中一個模組失敗：

```text
dkms autoinstall on 6.8.0-147-generic/x86_64
succeeded for openrazer-driver rtw89

dkms autoinstall on 6.8.0-147-generic/x86_64
failed for 8852au(10)
```

失敗的模組為：

```text
8852au/1.15.0.1
```

`8852au` 是 Realtek RTL8852AU 系列 Wi-Fi 裝置可能使用的第三方驅動。

進一步查看編譯紀錄：

```bash
tail -n 40 \
  /var/lib/dkms/8852au/1.15.0.1/build/make.log
```

發現以下錯誤：

```text
error: initialization of
'int (*)(struct wiphy *, struct net_device *,
struct cfg80211_chan_def *)'

from incompatible pointer type
'int (*)(struct wiphy *, struct cfg80211_chan_def *)'

[-Werror=incompatible-pointer-types]
```

這表示舊驅動程式的函式介面與目前 Kernel headers 所要求的介面不相容。

由於編譯錯誤，DKMS 回傳非零狀態，造成 Kernel 套件的 post-installation script 失敗。

結果是：

1. DKMS 無法完成第三方模組編譯。
2. Kernel headers 設定失敗。
3. Kernel image 套件設定失敗。
4. `linux-generic` 等相依套件無法完成設定。

**至此，可以確認 DKMS 驅動衝突是套件安裝失敗的直接原因。**

至於最初的 root filesystem 掛載失敗，則可能與未完成的 Kernel 安裝或 initramfs 有關；沒有額外證據能將其單獨歸因於 Wi-Fi 驅動。

## 六、第五步：確認舊驅動是否仍然必要

在移除任何 DKMS 驅動之前，應先確認系統是否仍然需要它。

執行：

```bash
dkms status
```

結果：

```text
8852au/1.15.0.1, 6.8.0-146-generic: installed

openrazer-driver/3.12.4, 6.8.0-146-generic: installed
openrazer-driver/3.12.4, 6.8.0-147-generic: installed

rtw89/7.3, 6.8.0-146-generic: installed
rtw89/7.3, 6.8.0-147-generic: installed
```

檢查 USB 裝置：

```bash
lsusb
```

系統偵測到 D-Link 802.11ax USB Wi-Fi Adapter。

再檢查已載入的 Kernel modules：

```bash
lsmod | grep -E '8852au|rtw89'
```

結果顯示：

```text
rtw89_8852au_git
rtw89_usb_git
rtw89_8852a_git
rtw89_core_git
```

這裡有一個重要差異：

- `8852au/1.15.0.1` 是舊的 DKMS 驅動。
- `rtw89/7.3` 是另一套驅動實作。
- `rtw89_8852au_git` 雖然名稱包含 `8852au`，但屬於 `rtw89` 驅動系列。

在本案例中，系統已經載入 `rtw89` 系列模組，且它能成功為新版 Kernel 編譯。

因此，可以考慮移除舊版 `8852au` DKMS 註冊。

注意：不同 Wi-Fi 裝置可能依賴不同驅動。**不要在未確認目前網卡驅動的情況下直接照抄移除指令。**

## 七、第六步：移除不相容的 DKMS 模組

確認舊驅動不再需要後，執行：

```bash
sudo dkms remove 8852au/1.15.0.1 --all
```

系統回報：

```text
Deleting module 8852au-1.15.0.1
completely from the DKMS tree.
```

這個操作移除了舊版 DKMS 模組的註冊與已安裝模組，但保留另一套 `rtw89` 驅動。

需要注意，這也會移除舊 Kernel 上的 `8852au` 模組。如果你的網路連線仍依賴它，可能造成 Wi-Fi 無法使用。

## 八、第七步：重新完成 Kernel 安裝

移除有問題的 DKMS 模組後，再次執行：

```bash
sudo dpkg --configure -a
```

這次成功！

主要輸出：

```text
Setting up linux-image-6.8.0-147-generic
Setting up linux-headers-6.8.0-147-generic

dkms: autoinstall for kernel 6.8.0-147-generic
...done.

Setting up linux-headers-generic
Setting up linux-generic
```

接著系統自動重新產生 initramfs：

```text
update-initramfs: Generating
/boot/initrd.img-6.8.0-147-generic
```

並更新 GRUB：

```text
Found linux image: /boot/vmlinuz-6.8.0-147-generic
Found initrd image: /boot/initrd.img-6.8.0-147-generic

Found linux image: /boot/vmlinuz-6.8.0-146-generic
Found initrd image: /boot/initrd.img-6.8.0-146-generic

done
```

新版與舊版 Kernel 都保留在 GRUB 選單中。

## 九、第八步：最後驗證

執行：

```bash
sudo dpkg --audit
```

沒有任何輸出，代表 dpkg 沒有回報未完成設定的套件。

檢查 DKMS：

```bash
dkms status
```

確認 `openrazer-driver` 與 `rtw89` 都已經安裝在新版 Kernel。

檢查 initramfs：

```bash
ls -lh /boot/initrd.img-6.8.0-147-generic
```

結果顯示新版 initramfs 已成功產生，大小約 72 MB。

最後重新開機：

```bash
sudo reboot
```

**結果：Ubuntu 成功使用新版 Kernel 開機，問題解決。**

整個過程不需要重灌系統，也不需要格式化磁碟。

## 十、經驗總結

這次故障最重要的教訓是：**Kernel Panic 不一定代表硬碟損壞，也不一定是 Kernel 本身有 Bug。**

第三方驅動、DKMS 編譯失敗，以及未完成的套件安裝，都可能間接造成開機問題。

遇到類似情況，可以按照以下順序排查：

| 順序 | 檢查項目 | 指令或方法 |
|---|---|---|
| 1 | 嘗試舊 Kernel | GRUB → Advanced options |
| 2 | 確認目前 Kernel | `uname -r` |
| 3 | 檢查套件狀態 | `sudo dpkg --audit` |
| 4 | 檢查磁碟空間 | `df -h / /boot /boot/efi` |
| 5 | 完成套件設定 | `sudo dpkg --configure -a` |
| 6 | 檢查 DKMS | `dkms status` |
| 7 | 檢查編譯錯誤 | `/var/lib/dkms/.../build/make.log` |
| 8 | 處理不相容驅動 | 依實際模組與設備判斷 |
| 9 | 重建開機環境 | `update-initramfs`、`update-grub` |
| 10 | 驗證新版 Kernel | 重新開機後執行 `uname -r` |

另外，建議保留至少一個已知能正常開機的舊版 Kernel，不要在系統不穩定時貿然執行 `apt autoremove`。

### 結語

Linux 的開機機制雖然複雜，但保留舊 Kernel 的設計提供了非常重要的復原途徑。

本案例真正解決問題的關鍵，不是反覆重灌或修改 GRUB，而是找到 Kernel 安裝程序中失敗的第三方 DKMS 模組。

**先讓系統恢復可操作，再從錯誤紀錄追查原因，通常比直接重灌更有效。**

---

*本文根據一次真實的 Ubuntu 24.04 故障排除過程整理。已移除個人識別資訊，並保留必要的技術細節。不同硬體、Kernel 版本及第三方驅動可能需要不同處理方式，請勿未經確認直接移除驅動。*
