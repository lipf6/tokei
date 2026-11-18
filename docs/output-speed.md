# 平均输出速度的统计口径

卡片按所选时间范围和模型汇总有效请求。平均输出速度使用「输出 Token 合计 ÷ 这些请求的计时合计」，跨天、跨会话和跨设备合并后重新相除。终端显示的最后一次请求速率，与整个时间范围的平均值可能不同。

旧版跨设备快照若缺少 Token／耗时累加值或 TTFT 直方图，兼容合并只能使用请求数加权等近似方式，无法恢复精确的整体速率或中位数。当前采集器会输出这些累加值和直方图，完整快照按它们重新计算。

所有 Agent 的速率都使用首字后的生成耗时。客户端提供直接解码耗时、首个内容块到完成的时间，或请求总耗时及首字等待时，才计入速度。只有请求总耗时或落盘时间的记录继续计入用量。整个时间范围都缺少有效计时时，卡片仅展示可用指标。

Codex 使用本机 rollout 的请求起点、首段思考或回复的开始时间和用量记录时间。WorkBuddy 按请求 ID 匹配首字及流式完成耗时。Pi 兼容客户端使用毫秒单位的 `duration` 和 `ttft`。MiniMax 将用量与同一调用的回复配对，优先使用 `decode_duration_ms`，有效的请求总耗时可用于计算首字延迟。工具执行后的持久化时间不作为生成耗时。

例如一次请求输出 600 个 token，总耗时 12 秒，首字等待 2 秒，则平均输出速度为 600 ÷ (12 − 2) = 60 tok/s。

有效样本需要至少 20 个输出 Token，计时超过 0.2 秒且不超过 30 分钟；超过 3000 tok/s 的样本会被排除。TTFT 超过 120 秒时不进入首字延迟的直方图，生成速率仍可使用有效的生成耗时。TTFT 展示直方图近似中位数；偶数样本取两项中间观测值的平均，分处不同桶时也分别估计后取平均。分桶保留约 5% 的范围，数值精度受分桶影响。

参考：[Pi 消息字段](https://github.com/earendil-works/pi/blob/main/packages/ai/src/types.ts)、[Pi 会话格式](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/session-format.md)、[oh-my-pi 毫秒计时字段](https://github.com/can1357/oh-my-pi/blob/main/packages/ai/src/types.ts)。

回归检查：`tests/test_pi_rate_accuracy.py` 验证 Pi 计时优先级、单位、等待时间筛选、平均值、异常字段与缓存／账本升级；`tests/test_minimax_rate_accuracy.py` 验证 MiniMax 逐次匹配、工具间隔、首字等待筛选、重复／异常记录与缓存／账本升级；`tests/test_perf.py` 覆盖其他采集器与跨设备合并；`tests/test_metric_grid_refresh.py` 验证 Mac 原生网格动态更新；Windows 在 Vite 中打开 `/tests/metric-grid.html`，检查全部生产卡片的动态更新结果与新建视图是否一致。
