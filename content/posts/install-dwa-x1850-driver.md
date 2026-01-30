+++
date = '2026-01-28'
draft = false
title = '在 Ubuntu 24.04 安裝 D-Link DWA-X1850 無線網卡驅動'
tags = ["Linux"]
categories = ["技術筆記"]
author = ["Will"]
+++

這篇文章紀錄了如何解決 D-Link DWA-X1850 (Realtek 8852au) 在 Linux 上無法辨識的問題，包含編譯驅動、手動修正硬體 ID 以及解除 RF-kill 鎖定的完整流程。

1. 安裝環境資訊
- OS: Ubuntu 24.04 LTS (Kernel 6.8.0-71-generic)
- Hardware: D-Link DWA-X1850 (USB ID: 2001:332c)
- Compiler: gcc-13
...<!--more-->
<div style="clear:both;"></div>

2. 安裝必要套件

```
sudo apt update

sudo apt install git build-essential linux-headers-$(uname -r) bc dkms usb_modeswitch
```

若有 Conda 環境，請先執行 `conda deactivate`


3. 下載並編譯驅動

```
git clone -b dwa-x1850 https://github.com/lwfinger/rtl8852au.git

cd rtl8852au


make

sudo make install
```

3. 硬體識別檢查
```
# 檢查裝置是否被系統偵測到 (應看到 2001:332c)
lsusb
```
以我們的 case ID 是 2001:332c
```
Bus 001 Device 002: ID 2001:332c D-Link Corp. 802.11ax WLAN Adapter
```


4. 載入驅動模組
```
sudo modprobe 8852au

# 檢查驅動模組是否已成功載入核心
lsmod | grep 8852au
```
輸出
```
8852au              14282752  0
cfg80211             1355776  1 8852au
```

5. 強制驅動程式識別你的硬體 ID
```
echo "2001 332c" | sudo tee /sys/bus/usb/drivers/rtl8852au/new_id
```



6. 啟用網卡介面 (介面名稱可透過 ip link 查詢，例如 wlxa42a9573b3e7)

```
sudo ip link set wlxa42a9573b3e7 up
```

7. 解除 RF-kill 軟體鎖定 (Optional)

若出現 `RTNETLINK answers: Operation not possible due to RF-kill`：

```
sudo rfkill unblock all
sudo ip link set wlxa42a9573b3e7 up
```

8. 設定永久生效 (防止重啟失效)

建立 udev 規則檔案： `sudo nano /etc/udev/rules.d/99-dwa-x1850.rules` 寫入以下內容： `ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="2001", ATTR{idProduct}=="332c", RUN+="/sbin/modprobe 8852au", RUN+="/bin/sh -c 'echo 2001 332c > /sys/bus/usb/drivers/rtl8852au/new_id'"`

9. 後續維護

若更新系統核心 (Kernel) 後 Wi-Fi 消失，需回到資料夾重新執行： 

```
cd rtl8852au
git pull
make clean
make
sudo make install
sudo modprobe 8852au
echo "2001 332c" | sudo tee /sys/bus/usb/drivers/rtl8852au/new_id
sudo rfkill unblock all
# ip link 可以查界面名稱。這邊以 wlxa42a9573b3e7 為例
sudo ip link set wlxa42a9573b3e7 up
```

## 進階：使用 DKMS 防止核心更新後失效
每次 Ubuntu 更新 Kernel，自行編譯的驅動就會消失。我們可以使用 DKMS (Dynamic Kernel Module Support) 來自動維護。

### 查詢驅動版本
在執行 DKMS 之前，我們需要確認驅動版本：
```
modinfo 8852au | grep ^version
# 或查看標頭檔
cd rtl8852au
cat include/rtw_version.h
```

設定 DKMS
假設版本號為 1.15.0.1，執行以下步驟：

```
# 將原始碼複製到系統目錄
sudo cp -r . /usr/src/8852au-1.15.0.1

# 註冊並安裝
sudo dkms add -m 8852au -v 1.15.0.1
sudo dkms build -m 8852au -v 1.15.0.1
sudo dkms install -m 8852au -v 1.15.0.1
```
完成後，可透過 dkms status 確認狀態。

結語：配置好 DKMS 與 udev 後，即使更新系統核心或重新拔插網卡，Wi-Fi 也能穩定運作！

### FAQ
Q: 執行 dkms status 出現 "Diff between built and installed module" 警告怎麼辦？ 

A: 這是因為手動安裝 (make install) 與 DKMS 安裝衝突。建議先卸載模組後，使用 dkms install 重新覆蓋即可解決。
```
# 先卸載模組
sudo modprobe -r 8852au

# 讓 DKMS 重新安裝一次，覆蓋手動安裝的版本
sudo dkms remove 8852au/1.15.0.1 --all
sudo dkms install 8852au/1.15.0.1 --force

# 重新載入
sudo modprobe 8852au
echo "2001 332c" | sudo tee /sys/bus/usb/drivers/rtl8852au/new_id
sudo rfkill unblock all
# ip link 可以查界面名稱。這邊以 wlxa42a9573b3e7 為例
sudo ip link set wlxa42a9573b3e7 up
```
執行 dkms status，如果警告消失，只剩下 installed，那就代表 DKMS 已經完美接管，未來的核心更新也會更穩定。