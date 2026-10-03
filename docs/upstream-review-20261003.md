# Kwrt 上游对比与清理审查

审查日期：2026-10-03（北京时间）。本文记录的是源码、提交历史和已取得的构建日志检查；固件产物检查及实机测试另行记录。

## 1. 结论

你的改动主要是两台设备选择、网络和 Wi-Fi 默认值、预装插件、Actions 编译与校验，以及必要的兼容修复。整体恢复成上游原样，会丢失这些已确认的需求。

连续失败有三个已经由完整日志证实的原因。上游原有的 Go 更新方式、当前依赖版本、你的插件组合共同影响了结果；统一 Go 后又触发了 Tailscale 的新兼容问题，不能把所有失败都归因于上游，也不能仅凭失败次数认定网络默认值有错。

| 实际失败 | 来源及触发条件 | 当前保留的修复 | 已确认的验证范围 |
| --- | --- | --- | --- |
| geoview 要求 Go ≥ 1.25，实际调用 Go 1.24.13 | 原有脚本只替换一个 Go Makefile，编译器和辅助文件不同源；PassWall2 选入的依赖需要较新 Go | 安装 feeds 前完整同步 kiddin9 的 Go 树到 packages，再重建索引 | 源码及版本一致性检查；后续完整 Actions 日志确认 geoview、v2ray-plugin 通过编译 |
| Tailscale 的 `alias.go` 报 `json.SkipFunc`、`json.DiscardUnknownMembers` 未定义 | 统一后的 Go 1.27 默认 JSON v2，与 Tailscale 1.98.3 固定的 JSON 实验库不兼容；统一 Go 的修复改变了编译环境，继而触发此问题 | 仅向 Tailscale 的包构建变量传入 `GOEXPERIMENT=nojsonv2` | 官方 Go 和 Tailscale 源码复现及 ARM64 完整编译；后续两台 Actions 日志确认 OpenWrt Tailscale 包编译通过 |
| dnsmasq-full 安装失败，三个共享库文件冲突 | 上游 dnsmasq 补丁手动复制共享库；当前固件也选入这些库的独立包，opkg 拒绝重复文件所有权 | 恢复官方 `nftset:nftables-json` 运行依赖，移除手动复制；保留 DNS 初始化修改 | 两台完整日志确认冲突；实际包安装规则配合测试文件验证修复后所有权唯一。完整固件 rootfs 安装仍等待新 Actions 结果 |

**当前没有依据宣布两台固件已经全部正常。** 源码检查已完成，但最新构建、实际产物和实机运行仍需验证。

## 2. 比较基准与历史解释

- 实际上游：[kiddin9/Kwrt 的 25.12 分支](https://github.com/kiddin9/Kwrt/tree/25.12)。用户提到的 `kiddin/Kwrt` 按实际 fork 来源解析为这个仓库。
- 本次获取的上游最新提交：[3bf5f80371f76c706594ba00ebe4b502f86f29fd](https://github.com/kiddin9/Kwrt/commit/3bf5f80371f76c706594ba00ebe4b502f86f29fd)，提交时间 2026-10-02 21:34:53 +08:00。
- 审查开始时你的提交：[23192180c25e78247524c6e3b228bdeb89c1cbab](https://github.com/leo-lcy/Kwrt/commit/23192180c25e78247524c6e3b228bdeb89c1cbab)。
- 你的仓库此前已合并上游 `802a3f78`。本次 fetch 显示上游分支被改写到 `3bf5f803`，共同祖先变为 `5e95c8a2`。
- 合并前 Git 的历史统计为“上游有 1 条我方没有的提交，我方有 41 条最新上游历史没有的提交”。其中 **12 条是此前上游提交、29 条是个人定制及修复（含合并提交）**。这不是 41 个待删除功能，也不是 41 个错误。
- 按你的选择保留历史：用普通合并和清理提交更新，不 reset、不 force push、不改写原有提交号。GitHub 的 ahead 数量因此不会自动归零。

### 上游最新提交是否已经有编译验证

审查时按 `head_sha=3bf5f803…` 查询上游公开 Actions，返回 0 条运行。此前最近公开成功记录对应 2026-09-25 的 `fa314ac1`，例如[这次上游运行](https://github.com/kiddin9/Kwrt/actions/runs/36142307798)。这不能证明最新 `3bf5f803` 配合现在的 feeds 和你的插件组合已经通过编译。

仓库在构建时继续拉取 OpenWrt 和插件源；同一 Kwrt 提交不同日期编译，依赖也可能发生变化。因此需要依据具体运行的日志和产物判断，不能只看 Kwrt 主仓库提交号。

## 3. 最新上游新增内容

比较此前已合并的 `802a3f78` 与最新 `3bf5f803`，实际文件变化只有三处：

| 文件 | 上游新变化 | 本次处理 |
| --- | --- | --- |
| `assets/p1.png` | 更新介绍截图 | 同步最新上游 |
| `assets/p5.png` | 更新介绍截图 | 同步最新上游 |
| `devices/common/patches/base-files.patch` | 安装 rpcd ACL 后重载 rpcd；区分首次安装服务和升级时已启用的服务 | 同步最新上游，验证关闭的服务在升级时不会被启动 |

上游最新 dnsmasq 补丁仍包含手动打包共享库的 Makefile 修改；Go 更新仍只下载一个 Makefile。因此这两项不能用上游文件覆盖掉本 fork 的修复。

本次普通合并提交为 `139ffb68e0d2cf1fd394eebee6b1e6a1abe9053a`，只有上述三个文件变化。两台 profile、默认脚本和兼容修复保持完整。

## 4. 审查开始时全部有效文件差异

以下是 `23192180` 相对最新上游的全部 28 个差异文件，不把旧历史中的每一次改动重复算成当前功能。

| 文件 | 相对上游的作用 | 处理结果 |
| --- | --- | --- |
| `.github/workflows/Openwrt-AutoBuild.yml` | 选择 AX6000/Cudy、分开缓存和产物、注入 Secrets、详细重试日志、校验固件、上传配置/校验值/profile 元数据 | 保留；移除未执行的旧 Secrets 调试注释 |
| `.github/workflows/repo-dispatcher.yml` | Dispatcher 按所选机型触发，用结构化 JSON 传参，避免取消其他机型 | 保留 |
| `.gitignore` | 本地维护文档不提交 | 保留 |
| `README.md` | 两台设备的编译和使用说明 | 保留并补充同步与兼容修复说明，标明后半部分是上游介绍 |
| `assets/p1.png` | 与上游截图版本不同 | 同步后此差异消除 |
| `assets/p5.png` | 与上游截图版本不同 | 同步后此差异消除 |
| `devices/common/.config` | Argon、PassWall2、Tailscale、Turbo ACC、HTTPS；不选覆盖自用配置的 my-default-settings | 保留 |
| `devices/common/diy.sh` | 默认 LAN10、插件列表、Wi-Fi 默认开启、Go 同源处理及旧插件临时修补 | 保留有效部分；移除 Xray 和 PassWall2 两处过时处理 |
| `devices/common/diy/package/base-files/files/etc/banner` | 个人终端欢迎文字 | 保留 |
| `devices/common/diy/package/base-files/files/etc/rc.local` | AX6000 首次生成 Wi-Fi、Nginx Tailscale 访问许可、最终 Turbo ACC 值 | 保留；执行末尾自行删除，不是在每次启动重置设置 |
| `devices/common/diy/package/base-files/files/etc/uci-defaults/99-router-settings` | AX6000 LAN、PPPoE、光猫访问、SSH、NTP 等默认值 | 保留 |
| `devices/common/diy/package/base-files/files/etc/uci-defaults/zz-router-tailscale` | 两台 Tailscale 网络/防火墙预设，默认关闭服务 | 保留 |
| `devices/common/patches/base-files.patch` | 原本缺少上游最新 ACL/服务安装处理 | 同步后此差异消除 |
| `devices/common/patches/dnsmasq.patch` | 去掉导致共享库冲突的 Makefile 修改，保留上游 DNS 初始化定制 | 保留修复 |
| `devices/common/patches/tailscale-jsonv2.patch` | Tailscale 使用兼容的 JSON 构建开关 | 保留修复 |
| `devices/common/prepare-golang.sh` | 统一 Go 编译器和辅助文件，重建 feeds 索引，缺文件时提前失败 | 保留修复 |
| `devices/cudy_tr3000/.config` | 独立选择 cudy_tr3000-mod，内置 USB 网络/存储驱动 | 保留 |
| `devices/cudy_tr3000/diy/package/base-files/files/etc/hotplug.d/net/90-f50-wan` | USB 网络设备出现时绑定 F50 WAN | 保留 |
| `devices/cudy_tr3000/diy/package/base-files/files/etc/rc.local` | Cudy 按频段配置 Wi-Fi、Nginx、Turbo ACC、首次连接 F50 | 保留；执行末尾自行删除 |
| `devices/cudy_tr3000/diy/package/base-files/files/etc/uci-defaults/99-cudy-settings` | LAN20、USB DHCP 优先、有线 WAN 备用、F50 防火墙等 | 保留 |
| `devices/cudy_tr3000/diy/package/base-files/files/usr/sbin/f50-wan` | 按 RNDIS/CDC 驱动识别 USB 网卡；变更才 reload，再 ifup | 保留 |
| `devices/mediatek_filogic/.config` | 关闭全部 profile，默认选择 AX6000 | 保留；Cudy 叠加配置覆盖设备选择 |
| `devices/mediatek_filogic/patches/25-platform.patch` | 使原有分区/升级补丁匹配当前 OpenWrt 的 platform.sh | 保留；直接恢复旧补丁会重新造成应用失败或不正确的 stock 分支处理 |
| `scripts/check-firmware.py` | 检查实际机型、manifest、必需插件/USB 包、SHA256；兼容单机型共享 rootfs manifest | 保留 |
| `scripts/inject-ax6000-secrets.py` | 将 AX6000 密码和 PPPoE 参数作为 shell 字面量安全注入 | 保留 |
| `scripts/inject-cudy-secrets.py` | 注入 Cudy ROOT/Wi-Fi Secrets | 保留 |
| `scripts/prepare-tailscale-service.py` | 修正 LuCI 辅助服务，让关闭开关在启动/reload 时有效 | 保留 |
| `scripts/tests/test_tailscale_defaults.py` | 覆盖新装、旧配置、匿名区域和辅助服务启用开关 | 保留 |

同步消除三个文件差异后，原有有效差异为 25 个文件。本审查文档新增一个文件，最终相对上游为 26 个文件；这不表示需要删除上游通用设备目录。通用源码和未选入的其他 profile 仍沿用上游。

## 5. 个人历史提交逐项整理

以下 29 条提交保留原有提交号。标注“已被后续替代”指其旧实现已不在当前版本使用，不是要求删除历史或回滚当前功能。

### 原有个人提交（19 条，含一次上游合并）

| 提交 | 当时修改 | 现在是否仍有作用 |
| --- | --- | --- |
| `04cd596a` | 自用 AX6000 构建与默认配置 | 有效；设备、插件及默认值保留，后续修正了部分实现 |
| `8e156a17` | 双频 Home SSID | 有效，现由首次启动 rc.local 配置 |
| `0b915e0a` | Tailscale 防火墙和 Nginx 访问 | 有效，基础网络现由共享 Tailscale 默认脚本补齐 |
| `6faf2617` | SSH 端口 30001 | 有效，两台一致 |
| `02e99e60` | Wi-Fi/Nginx 设置移到 rc.local | 有效，避免 wireless/Nginx 尚未生成 |
| `513a4a8f` | 关闭 rebind 保护和 miniupnpd | 现有使用偏好保留；不是本次构建失败原因 |
| `ff32c995` | 手动构建 nocache 选项 | 有效 |
| `13acace4` | 关闭自动发布 Release | 有效，使用 Actions Artifacts |
| `b2dcfa4f` | Turbo ACC 默认值 | 配置意图有效；早期位置已由 `3480e88c` 替代 |
| `51217616` | LAN 端口去重和国内 NTP | NTP 有效；手动 LAN 端口覆盖已由 `421d044f` 改为沿用 board.d |
| `52e86f46` | Wi-Fi 6/149 信道 | 已被 `b70e5a0f` 的 11/157 替代，旧值不保留到 AX6000 当前脚本 |
| `8911d28d` | 修正 openwrt-* 产物匹配 | 有效，后续补充 manifest/config/SHA/profile 上传 |
| `10257fc6` | Wi-Fi 默认开启、修正 Nginx Tailscale 许可 | 有效 |
| `3480e88c` | Turbo ACC 移到启动末尾，避免包默认脚本覆盖 | 有效；一次性 rc.local 保留 |
| `6eb73b5f` | 本地维护文档不再跟踪 | 有效 |
| `b7e74920` | 欢迎文字署名 | 有效 |
| `b70e5a0f` | AX6000 信道 11/157 | 有效；Cudy 仍使用自身按频段的 auto/149 |
| `b6e412dd` | 合并当时上游 25.12 | 有效历史；不会为减少 ahead 数量删除 |
| `8cf815a0` | 更新旧 platform.sh 补丁 | 早期版本已由 `dbe7b803` 的再次刷新替代 |

### 本次会话的合并、新设备与修复提交（10 条）

| 提交 | 修改 | 现在处理 |
| --- | --- | --- |
| `dbe7b803` | 合并此前上游，刷新 AX6000 平台补丁 | 保留，继续与最新上游合并 |
| `9e6d759a` | 增加 Cudy TR3000 112M 和 F50 USB WAN | 保留 |
| `a9f478cc` | Cudy 主机名与 AX6000 对齐 | 保留；当前值 Router |
| `421d044f` | F50 DHCP/IPv6、manifest、Secrets 引用、LAN 端口、ToModem 五项修复 | 保留 |
| `50abd31c` | Tailscale 基础预设，默认不启动 | 保留 |
| `5a969d01` | LuCI 辅助服务也遵守启用开关 | 保留，不能只关闭主 daemon 而遗漏辅助脚本 |
| `accd8dc2` | Cudy LAN20，刷新 router 别名 | 保留；防止两家 Tailscale 子网重叠 |
| `526d0499` | Go 编译器与辅助文件统一 | 保留，已有实际包编译通过记录 |
| `2606f9ff` | Tailscale 单包 nojsonv2 | 保留，已有实际 OpenWrt 编译通过记录 |
| `23192180` | dnsmasq 恢复运行依赖、取消重复库打包 | 保留，当前构建验证中 |

### 最新上游历史中消失的 12 条旧上游提交

`6af151ab`、`7d5e6c17`、`cd7c4585`、`44affe06`、`e762abcb`、`51fc23a8`、`e03e5d72`、`77463456`、`4d143f1e`、`593edda5`、`fa314ac1`、`802a3f78`。

它们原作者都是 kiddin9，不是你的个人新增功能。上游改写分支历史后，这些提交仍由你保留的旧合并历史引用；源码差异已逐文件审查，不能对这些提交逐个机械 revert。

## 6. 本次真正删掉的内容

1. `diy.sh` 中删除旧 Xray `AllowInsecure.patch` 的处理。核对最新 `kiddin9/op-packages`：该包树只有 Makefile，没有这个补丁。
2. `diy.sh` 中把 PassWall 资源路径替换成 PassWall2 的两次 sed。最新插件页面已经使用 `/luci-static/passwall2/` 和 `[[passwall2]]`，这两次替换不再有效。删除后也避免最后一个文件存在性判断成为脚本退出状态。
3. Actions 中一段未执行的旧 Secrets 调试注释。移除注释不改变运行步骤或 Secrets 注入行为。
4. 上游最新截图和 base-files 补丁已同步，消除了没有必要的版本差异。

没有为了减少行数而删除插件、USB 驱动、固件校验、默认关闭 Tailscale 的逻辑或上述有失败证据的构建修复。也没有新增未经确认的 AX6000 按 band 改 Wi-Fi、F50 断网自动恢复或 SQM。

## 7. 两台默认值复核

| 项目 | AX6000 | Cudy TR3000 112M |
| --- | --- | --- |
| profile | xiaomi_redmi-router-ax6000 | cudy_tr3000-mod |
| LAN / 后台 | 192.168.10.0/24 / 192.168.10.1 | 192.168.20.0/24 / 192.168.20.1 |
| 主机名 / 本地管理域名 | Router / router.lan | Router / router.lan |
| Wi-Fi | Home 2.4G、Home 5G；11/157 | Home 2.4G、Home 5G；auto/149，按 band 匹配 |
| 密码来源 | Actions ROOT/WIFI Secrets；PPPoE 单独 Secrets | 同一 ROOT/WIFI Secrets |
| SSH | 30001 | 30001 |
| 上网方式 | 原有 PPPoE，保留 ToModem | wan_f50 USB DHCP 优先，有线 WAN 备用 |
| Tailscale | 基础接口/防火墙预设，服务默认关闭 | 同左，并增加到 F50 区域转发 |
| 手动恢复 | PPPoE/插件细项、Tailscale 登录及子网授权等 | F50 USB 共享开关、Tailscale 登录及子网授权等 |

本地 `router.lan` 使用对应家庭路由器的 DNS。远程通过 Tailscale 管理两台时应使用各自独立的 Tailscale 地址或名称；共享主机名 Router 不保证远程 MagicDNS 名称相同。子网发布仍手动，分别发布 LAN10 和 LAN20。

## 8. 本次验证与仍待验证的部分

已通过：

- 普通合并只引入三个明确的上游文件变化，原有配置与修复逐字节保留。
- 新 base-files 的 functions.sh 修改应用到官方源码，shell 语法检查通过。
- 隔离执行实际 postinstall 函数：首次安装 enable/start；已关闭服务升级不启动；已启用服务升级启动；安装 ACL 重载 rpcd；构建 rootfs 时不启动服务或重载 rpcd。
- 两个 Actions workflow 的 actionlint 检查；清理后结构化 YAML 与清理前运行内容一致。
- Tailscale 的 5 项现有测试：新装两台、恢复匿名区域、旧插件、辅助服务启动/reload 的启用开关。
- 实际 workflow 文件叠加检查：AX6000/Cudy 选择互斥，Cudy 不带 AX6000 PPPoE 默认脚本。
- AX6000 参数使用 shell 字面量，测试字符串中的引号、美元符和反斜线不会执行命令；LAN 端口沿用 board.d；WAN 区域按名称匹配。
- Cudy LAN20/hosts 更新、与官方 WAN 对照的 DHCP/IPv6 防火墙规则、RNDIS/ECM/NCM 识别与重复连接。
- 固件校验器的正常/损坏测试文件、共享 rootfs manifest 允许条件、错误 profile 及缺少 USB 包的拒绝逻辑。
- 补丁正文的上下文空格单独按 patch 格式处理；普通源码 diff 检查通过。

测试文件不是实际固件；模拟 UCI 和 USB 网卡不等于接机验证。尚待核验：两台完整 rootfs 安装和构建成功、实际 sysupgrade/profile/manifest/build 与 kernel config、必需插件和 USB 驱动、SHA256、大小、实际版本、非敏感 Tailscale 默认脚本及二进制构建信息。实机启动、Wi-Fi、USB 供电和 F50 联网稳定性需要刷机后测试。

## 9. 构建跟进与维护方式

审查时正在运行 dnsmasq 修复提交 `23192180` 的两次构建：

- [AX6000 37106662339](https://github.com/leo-lcy/Kwrt/actions/runs/37106662339)
- [Cudy 37106665564](https://github.com/leo-lcy/Kwrt/actions/runs/37106665564)

它们使用审查开始前的源码，尚不包含这次新同步的 ACL 处理及清理文档。先让当前构建完成并核验；整理后的最终提交随后单独做编译验证，不取消另一台正常构建。后续实际提交号和最终运行链接以监控交付记录为准。

今后同步时：先 fetch 并比较源码树；保留两台 profile/defaults；核对 Go、Tailscale JSON、dnsmasq 的修复是否被上游真正解决；普通合并处理冲突；再按机型编译并核验产物。只有确认上游已解决相应问题，才删除具体兼容修复，不根据 ahead 数量删除历史。
