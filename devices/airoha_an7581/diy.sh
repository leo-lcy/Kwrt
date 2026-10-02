#!/bin/bash

shopt -s extglob

curl -sL https://patch-diff.githubusercontent.com/raw/openwrt/openwrt/pull/24883.patch | git apply -v

rm -rf package/boot

git_clone_path main https://github.com/openwrt/openwrt package/boot

wget -N https://github.com/openwrt/openwrt/raw/refs/heads/main/target/linux/airoha/dts/an7581-nokia_xg-040g-md-common.dtsi -P target/linux/airoha/dts/
wget -N https://github.com/openwrt/openwrt/raw/refs/heads/main/target/linux/airoha/dts/an7581-nokia_xg-040g-md-ubi.dts -P target/linux/airoha/dts/
wget -N https://github.com/openwrt/openwrt/raw/refs/heads/main/target/linux/airoha/dts/an7581-nokia_xg-040g-md.dts -P target/linux/airoha/dts/
wget -N https://github.com/openwrt/openwrt/raw/refs/heads/main/target/linux/airoha/dts/an758x-nokia_xg-040g-common.dtsi -P target/linux/airoha/dts/
wget -N https://github.com/openwrt/openwrt/raw/refs/heads/main/target/linux/airoha/dts/an758x-nokia_xg-040g-stock-parts.dtsi -P target/linux/airoha/dts/
wget -N https://github.com/openwrt/openwrt/raw/refs/heads/main/target/linux/airoha/dts/an758x-nokia_xg-040g-ubi-parts.dtsi -P target/linux/airoha/dts/
