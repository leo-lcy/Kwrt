## 本 fork 的自用固件

在 **Actions → Build OpenWrt → Run workflow** 选择 `device`：

| device | 设备与上网方式 | 后台地址 |
| --- | --- | --- |
| `ax6000`（默认） | Redmi AX6000，现有 PPPoE 配置 | `192.168.10.1` |
| `cudy_tr3000` | Cudy TR3000 v1 112M，F50 USB 共享网络 | `192.168.10.1` |

首次编译新机型或需要刷新 feeds 时勾选 `nocache`。两个机型分别使用缓存和 Artifacts，下载名称包含所选机型。
Repo Dispatcher 也支持同样的机型选择，可通过 `param` 传入 `ssh`、`nocache` 等参数，每次只触发所选设备。

Cudy 复用本仓库的 `cudy_tr3000-mod` 112M 分区布局，不适用于原厂 64M 可用布局或 OpenWrt 官方 U-Boot layout。
设备配置在 `devices/cudy_tr3000/`，共享 mediatek/filogic 补丁与插件源。

- F50 接 USB 数据线后，`wan_f50` 接口自动绑定 RNDIS/CDC Ethernet/NCM 网卡，通过 DHCP 上网；原有线 WAN 保留，USB 路由优先。
- 内置 USB 网络驱动、USB Storage、FAT/exFAT 支持和 `usbutils`。USB Storage 只在 F50 将存储暴露为 USB 磁盘时可用，不会自动格式化或挂载存储卡。
- Cudy 沿用 Argon、PassWall2、Tailscale、Turbo ACC、双频 `Home 2.4G` / `Home 5G` Wi-Fi、HTTPS 后台和 SSH 端口 `30001`，不写入 AX6000 的 PPPoE、光猫访问或 LAN 端口设置。
- Cudy 使用仓库的 `ROOT_PASSWD`、`WIFI_PASSWD` Actions Secrets；AX6000 继续使用现有 Secrets。Cudy 密码以 shell 引号转义，支持特殊字符。
- 编译后检查所选机型、插件与 USB 驱动清单以及固件 SHA256，再上传 Artifacts。实机 USB 供电、启动和网络稳定性仍需接机验证。

---

#### 固件下载与在线定制: [openwrt.ai](https://openwrt.ai)

### openwrt 软路由固件

#### 基于官方openwrt-25.12最新稳定分支, 并基于国内使用喜欢做大量优化

#### 原生极致纯净, 固件默认只包含基础上网功能, 后台在线选装插件, 或在线定制包含指定插件的固件

#### 自建在线插件仓库 [dl.openwrt.ai](https://dl.openwrt.ai), 额外收录三方插件1000+, 插件库日更

##### TG群: [Kwrt交流群](https://t.me/opkwrt)

<img src="assets/p1.png" alt="" width="800">

<img src="assets/p2.png" alt="" width="800">

<img src="assets/p3.png" alt="" width="800">

<img src="assets/p4.png" alt="" width="800">

<img src="assets/p5.png" alt="" width="800">

<img src="assets/p6.png" alt="" width="800">

## Acknowledgments

- [OpenWrt](https://github.com/openwrt/openwrt)
- [Lean's OpenWrt](https://github.com/coolsnowwolf/lede)
- [ImmortalWrt](https://github.com/immortalwrt/immortalwrt)
- [iStoreOS](https://github.com/istoreos)
- [unifreq](https://github.com/unifreq/openwrt_packit)
- [ophub](https://github.com/ophub/amlogic-s9xxx-openwrt)
- [hanwckf](https://github.com/hanwckf/immortalwrt-mt798x)
- [aparcar](https://github.com/openwrt/asu)
- [GitHub](https://github.com)
- [GitHub Actions](https://github.com/features/actions)

