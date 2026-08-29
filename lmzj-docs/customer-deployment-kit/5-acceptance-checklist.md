# 5. 验收清单（逐项勾选，全绿 = 交付完成）

交付 Issue：`<编号>`　交付 SHA：`<40位>`　验收日期：`<日期>`　验收人：`<签名>`

## A. 平台健康

- [ ] `curl http://<server>:8080/healthz` → 200
- [ ] `curl http://<server>:8080/readyz` → 200
- [ ] `docker exec gpustack-server gpustack version` → version/git_commit 均为交付 SHA
- [ ] UI 登录正常（admin 已改密）

## B. 节点与资源

- [ ] UI 节点页：所有节点 READY，无 unreachable
- [ ] GPU 页：每台节点 GPU 型号/数量/显存正确
- [ ] server 日志无 worker 探活失败刷屏

## C. 模型推理（每个交付模型一行）

| 模型 | 实例状态 | Playground 对话 | 业务路由调用 |
|---|---|---|---|
| | [ ] RUNNING | [ ] 通过 | [ ] 通过（如配置） |

- [ ] 路由页目标稳定显示（无闪现），可用数正确

## D. 运维能力交底（向客户演示）

- [ ] 升级方式：新 SHA 重跑 deploy 命令（数据不丢）
- [ ] 回滚方式：上一交付 Issue 中的 SHA 重跑
- [ ] 加节点方式：3-worker-join 模板
- [ ] 日志位置：server `docker logs gpustack-server`；实例日志 worker
      `/var/lib/gpustack/log/serve/`

## E. 收尾

- [ ] 交付 Issue 回填：SHA、各清单结果、客户签字/确认记录
- [ ] 首月观察点约定：worker 心跳、磁盘余量（<20% 告警）、实例重启次数
