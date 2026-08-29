# 1. 前置条件核对表

交付开始前逐项核对，全部满足才进入安装。任一项不满足先解决再继续。

## 云资源与系统

- [ ] server 主机 1 台（可无 GPU）：系统盘 ≥40G，余量 ≥15G，可访问公网（拉 ACR 镜像）
- [ ] worker 主机 1+ 台（GPU）：系统盘 ≥100G（镜像 60G+ 模型），余量 ≥25G+模型体积
- [ ] 两机网络互通：worker 能访问 server 443/8080；**server 能访问 worker 10150**（安全组对 server IP 放行，v2.2.x 硬性要求）
- [ ] SSH 可达两机（维护通道）

## GPU 环境（worker）

- [ ] NVIDIA 驱动 ≥ **570**（`nvidia-smi` 正常，对应 CUDA 12.8）
- [ ] nvidia-container-toolkit 已安装且 `docker run --rm --runtime nvidia e2eteam/busybox nvidia-smi` 类容器测试可用
- [ ] docker daemon 正常，docker compose v2 可用

## 镜像与网络

- [ ] 客户网络可访问 `registry.cn-chengdu.aliyuncs.com`（阿里云 ACR，公开仓库零凭证）
- [ ] 无需 docker hub / quay.io（全部镜像已自持于 `lmzjai` 命名空间，见 `../acr-image-mirror.md`）

## 应用层约定（已确认的交付形态）

- [ ] 入口：server **8080 直连**（客户如需 443/TLS 由客户自有网关负责）
- [ ] 认证：本地账号（管理员首次初始化密码），不接 SSO
- [ ] 模型文件：落盘 worker 本地目录（约定 `/home/ubuntu/models`），以 LOCAL_PATH 方式部署

## 信息收集（安装时填写）

| 项 | 值 |
|---|---|
| server 内网/公网 IP | |
| worker 内网/公网 IP | |
| server 对外地址（域名或 IP:8080） | |
| 模型目录 | |
| 交付镜像 SHA（40 位，见 2-server-install） | |
