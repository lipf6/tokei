<p align="center">
  <img src="https://img.shields.io/badge/platform-macOS_13+-black?style=flat-square&logo=apple&logoColor=white" alt="macOS 13+">
  <img src="https://img.shields.io/badge/swift-5.9+-F05138?style=flat-square&logo=swift&logoColor=white" alt="Swift 5.9+">
  <img src="https://img.shields.io/badge/python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License">
  <a href="https://github.com/lipf6/tokei/stargazers"><img src="https://img.shields.io/github/stars/lipf6/tokei?style=flat-square&color=yellow" alt="Stars"></a>
  <a href="https://github.com/lipf6/tokei/releases"><img src="https://img.shields.io/github/v/release/lipf6/tokei?style=flat-square&color=blue" alt="Release"></a>
</p>

<h1 align="center">⏱ Tokei 知度</h1>

<p align="center">
  <strong>macOS 菜单栏 AI 编程用量监控</strong><br>
  <sub>了然于心，掌控全局。</sub><br><br>
  <a href="https://tokei.lanshuagent.com">🌐 原项目官网</a> · <a href="https://github.com/lipf6/tokei/releases/latest">⬇️ 下载 Kimi 版</a> · <a href="#english">English</a>
</p>

---

## 什么是 Tokei？

Tokei 是一款 **macOS 菜单栏应用**，实时追踪你在 **13 款 AI 编程工具** 上的用量、成本和性能。Token 统计以本地日志为主，额度查询使用对应工具已有的本机登录态。

### 支持的工具

| 工具 | 追踪指标 |
|------|----------|
| **Claude Code** | Token（输入/输出/缓存）、成本、配额、模型 |
| **Codex CLI** | Token、成本、配额、会话 |
| **Gemini CLI** | Token、思考量、成本、模型 |
| **Grok Build** | Token（输入/输出/缓存/推理）、会话、上下文、延迟、配额（本地日志；可选实时） |
| **Hermes** | Token、成本、缓存命中率、模型 |
| **OpenClaw** | Token、成本、任务、模型 |
| **Pi Coding Agent CLI** | Token、成本、缓存命中率、模型、项目 |
| **WorkBuddy** | Token、成本、缓存命中率、模型、项目 |
| **OpenCode** | Token、成本、缓存命中率、模型 |
| **Qwen Code** | Token、思考量、成本、模型 |
| **Kimi Code** | Token（输入/输出/缓存）、模型、会话、项目、周/5 小时额度、Extra Usage |
| **Qoder** | Token、调用次数、配额 |
| **QoderWork** | Token、调用次数、配额 |

## 功能一览

### 实时监控
- 30 秒自动刷新，菜单栏直接显示配额/用量
- 菜单栏支持经典白、彩色、刻度、圆点、数字、星轨、椰影 7 种样式
- 双额度、单额度、仅图标 3 档信息量，最窄只占一个状态栏槽位
- 按工具展示卡片，一眼掌握所有 AI 工具状态

### 成本估算
- 基于 API 实际定价估算成本（非订阅费用）
- 317 个模型价格表（来源 OpenRouter），支持一键更新
- 本地价格覆盖（`pricing_overrides.json`），更新不丢失
- 未知模型按家族关键词回退，兜底用 Opus 价格（保守上限）

### 数据面板
- 每日成本折线图
- 每周热力图
- 工具用量占比分析

### 时间维度
- 今天 / 昨天 / 本周 / 上周 / 本月 / 今年
- 随时切换，对比不同时段用量趋势

### 项目追踪
- 按项目维度查看 Claude Code / Pi / WorkBuddy / Grok Build / Kimi Code 用量
- 了解每个项目消耗了多少 Token 和成本

### 多设备同步
- 基于 Git 的跨设备同步（Mac + Linux 服务器）
- Mac 端设置里一键开启
- 远程 Linux 服务器支持 crontab 自动采集和同步
- 也可以让 Claude Code 帮你自动完成全部配置

### 年度回顾（Wrapped）
- 回顾你一整年的 AI 编程旅程
- 总用量、总成本、高峰日、工具偏好等统计

### 久坐提醒
- 感知空闲状态，智能提醒休息
- 可自定义间隔时间

### 隐私优先
- Token、成本和项目统计均在本机完成，不向 Tokei 服务上传使用数据
- Codex 额度使用本机 Codex 登录态读取官方接口；重置卡每天最多自动查询一次
- Grok 实时额度默认关闭，可选择只读本地日志
- 其余联网操作仅用于检查/下载更新，以及手动更新模型价格表

## 快速开始

1. 从 [GitHub Releases](https://github.com/lipf6/tokei/releases/latest) 下载最新 DMG
2. 打开 DMG，将 Tokei.app 拖入 Applications 文件夹
3. 首次打开如被 macOS 拦截，在终端运行：`sudo xattr -rd com.apple.quarantine /Applications/Tokei.app`
4. 打开 Tokei 即可

<details>
<summary>从源码构建</summary>

```bash
git clone https://github.com/lipf6/tokei.git
cd tokei/Tokei
bash package.sh
open Tokei.app
```
</details>

## 多设备同步配置

Tokei 支持通过私有 Git 仓库在多台机器间同步用量数据。

**Mac 端：** 打开设置 → 多设备同步 → 开启，选择一个 Git 仓库目录。

**远程 Linux 服务器：**

```bash
git clone <你的私有仓库> ~/.tokei/sync
curl -fsSL https://raw.githubusercontent.com/lipf6/tokei/main/usage.30s.py -o ~/.tokei/usage.30s.py
echo '{"sync_dir":"~/.tokei/sync","device_id":"'$(hostname -s)'","auto_sync":true,"sync_interval":30}' > ~/.tokei/config.json
cat > ~/.tokei/tokei-sync.sh <<'SH'
#!/bin/bash
set -euo pipefail
exec 9>"$HOME/.tokei/sync.lock"
flock -n 9 || exit 0
cd "$HOME/.tokei/sync"
python3 "$HOME/.tokei/usage.30s.py" --json >/dev/null
device_file=$(find . -maxdepth 1 -type f -iname "$(hostname -s).json" -print -quit)
[ -n "$device_file" ] || device_file="./$(hostname -s).json"
for peer_file in ./*.json; do
  [ "$peer_file" = "$device_file" ] && continue
  git restore --staged --worktree -- "$peer_file" 2>/dev/null || true
done
git add -- "$device_file"
git diff --cached --quiet || git commit -qm "chore(sync): update $(hostname -s) usage"
for attempt in 1 2 3; do
  git fetch -q origin main
  if ! git rebase -q origin/main; then
    git rebase --abort 2>/dev/null || true
    exit 1
  fi
  git push -q origin HEAD:main && exit 0
  sleep "$attempt"
done
exit 1
SH
chmod +x ~/.tokei/tokei-sync.sh
# 每 30 分钟自动采集并同步，日志写入 ~/.tokei/sync.log
(crontab -l 2>/dev/null | grep -v 'tokei-sync.sh'; echo '*/30 * * * * ~/.tokei/tokei-sync.sh >> ~/.tokei/sync.log 2>&1') | crontab -
```

## 数据来源

Token、会话和项目统计来自本地日志。Codex、Kimi 等套餐额度会使用对应 CLI 的本地登录态查询官方额度接口，并做短时本地缓存。

| 工具 | 日志路径 |
|------|----------|
| Claude Code | `~/.claude/projects/<proj>/<session>.jsonl` |
| Codex CLI | `~/.codex/sessions/YYYY/MM/DD/*.jsonl` |
| Gemini CLI | `~/.gemini/gemini-cli/conversations/*.json` |
| Grok Build | `${GROK_HOME:-~/.grok}/logs/unified.jsonl`（含真实 token + billing 额度）+ `sessions/*/*/{summary,signals}.json`；可选实时账单接口（设置里默认关闭） |
| Hermes | `~/.hermes/state.db` + `~/.hermes/profiles/*/state.db` |
| OpenClaw | `~/.openclaw/agents/*/sessions/*.jsonl` + `~/.openclaw/state/openclaw.sqlite` |
| Pi Coding Agent CLI | `~/.pi/agent/sessions/<project>/*.jsonl` |
| WorkBuddy | `~/.workbuddy/projects/<project>/*.jsonl` |
| OpenCode | `~/.opencode/sessions/*.json` |
| Qwen Code | `~/.qwen/usage/token-usage-*.jsonl` + `~/.qwen/usage_record.jsonl` |
| Kimi Code | `${KIMI_CODE_HOME:-~/.kimi-code}/sessions/**/agents/*/wire.jsonl`；额度读取 `credentials/kimi-code.json` 并查询官方 `/usages` |
| Qoder | `~/.qodo-ai/sessions/*.jsonl` |
| QoderWork | `~/Library/Application Support/Qoder/SharedClientCache/cache/db/local.db` |

## 对比 CodexBar

| 功能 | Tokei | [CodexBar](https://github.com/steipete/CodexBar) |
|------|:-----:|:---------:|
| 支持工具 | 13 | 40+ |
| Token 级用量分析 | ✅ | — |
| 成本估算（317 模型） | ✅ | 部分 |
| 数据面板（图表 + 热力图） | ✅ | — |
| 多时间维度 | 6 个 | — |
| 项目级追踪 | ✅ | — |
| 多设备同步 | ✅ | — |
| 年度回顾 | ✅ | — |
| 防休眠 / 久坐提醒 | ✅ | — |
| 需要联网 | 仅实时额度 | 是 |
| 需要登录 | 复用对应 CLI 登录态 | 是 |
| 数据来源 | 本地日志 | 远程 API |

> CodexBar 在提供商覆盖和配额可见性上表现出色。Tokei 更深入——Token 级分析、成本趋势、项目维度拆分、跨设备同步——全部无需登录。

## 更新日志

### v1.0.33

- fix: Codex 周额度跟 ChatGPT 官方用量页走。官方剩余 100%、重置 08-31 时，不再用旧日志里的 18%/08-27 盖掉；周期卡把 used=0 的新窗口当作当前周期

### v1.0.32

- fix: Codex 周额度不再被日志里最新一条空的 `now+7d` 窗口盖掉，主卡与周期卡都回落到仍在进行的重置日
- fix: 没用过的工具不再显示「还没有周额度卡片」提示；花不完时去掉与回满倒计时重复的「还能撑 X 天」

### v1.0.31

- fix: Codex 官方 usage 在窗口没翻完时会报 used=0、reset=现在+7 天；主卡不再用这份空读数覆盖日志里仍有效的周额度和重置时间

### v1.0.30

- fix: 周额度节奏预测不再报「还能撑 21 天」这种跨过回满点的天数；花不完写能撑到回满，见底才报预计几天后额度用完

### v1.0.29

- feat: 额度轨迹 Tab 只展示实际有额度或用量的工具，默认落到有数据的项；补齐 Grok 剩余% 采样
- feat: 周额度当前卡增加节奏预测：到回满预计剩余（超支为负）和按当前节奏还能撑几天

### v1.0.28

- fix: Codex 额度过期后不再伪装成「周剩余 100%」，菜单栏同步隐藏失真读数
- fix: Codex 实时额度拉取失败时保留最新缓存，并按账号隔离、失败 5 分钟退避
- fix: Grok 账单周期重置后 protobuf 省略 0% 导致额度卡住
- fix: 多设备同步 push 前排除 Finder `.DS_Store`，避免垃圾文件卡死同步
- feat: 账本改为内存对账、单次落盘，统一 token 口径，回顾页增加巅峰日 Top3（含项目回填）
- feat: 周额度周期改用真实观测锚点，多设备账本合并，轨迹页落盘秒开；Kimi 一并接入

### v1.0.27

- feat: 引入每日高水位账本，日志被 CLI 清理后历史用量不再缩水；Kimi Code 一并接入
- feat: 账本随多设备同步快照备份，本地账本丢失时可自愈恢复
- feat: Grok Build 按 API 价估算成本，并进入卡片、数据面板、年度回顾和项目轨迹
- chore: 附 `scripts/backfill_ledger.py`，可从同步仓 git 历史回填已丢失的每日用量

### v1.0.26

- fix: Codex 日志解析不再依赖 JSON 字段顺序，兼容 `ordinal` 等新增元数据并跳过无时间戳记录
- perf: 扫描缓存迁移到持久目录并每 5 秒保存重扫进度，升级或中断后可继续扫描
- fix: 启动时先展示最近一次有效数据，后台刷新期间同步校验 Kimi 额度是否过期

### v1.0.25

- fix: Kimi 周额度或滚动 5 小时额度到达重置时间后，立即失效旧缓存并重新请求官方额度
- fix: 面板手动刷新跳过 Kimi 额度缓存，直接获取最新额度
- fix: 刷新任务执行期间再次手动刷新时保留强制刷新请求，避免被并发刷新吞掉

### v1.0.24

- feat: Kimi Code 纳入额度历史轨迹，记录周额度和滚动 5 小时额度变化
- feat: 额度历史轨迹记录 Kimi 模型活动，并兼容升级前的历史数据

### v1.0.23

- feat: Kimi Code 显示周额度、滚动 5 小时额度、重置时间和 Extra Usage 钱包
- feat: 按 Kimi Code 官方协议自动续期 OAuth，跨进程加锁并以 `0600` 原子更新凭证
- privacy: Kimi 额度缓存不保存 access token 或 refresh token；可在设置中关闭，也可设置 `TOKEI_KIMI_LIVE_QUOTA=0`

### v1.0.22

- feat: 支持 Kimi Code 本地 Token、缓存 Token、模型、会话和项目统计
- feat: Kimi Code 纳入日报、年度回顾、项目轨迹和多设备汇总
- chore: 更新源和下载入口切换到 `lipf6/tokei`

### v1.0.19

- feat: Codex 卡片显示可用重置卡数量、最近到期时间及完整北京时间列表
- feat: Grok Build 显示周额度、重置时间和分产品用量，菜单栏可选择 Grok 作为额度来源
- feat: 新增最近 7 天额度历史轨迹，每分钟记录一次本地快照
- fix: 补齐 Hermes 0.19 迁移后的历史与辅助用量
- fix: Codex 额度活动基线跨扫描间隙保持稳定，事件缓存拆分后刷新性能更平稳
- privacy: 重置卡仅缓存数量和到期时间；按天或最近一张到期后更新，未登录及接口失败静默降级

#### 社区贡献

- [**CherryLover**](https://github.com/CherryLover)：贡献 [Grok 周额度、重置时间与菜单栏额度来源 #34](https://github.com/cclank/tokei/pull/34)
- [**刘巍峰**](https://github.com/liuweifeng)：修复 [Hermes 0.19 历史与辅助用量 #36](https://github.com/cclank/tokei/pull/36)
- [**AMortalsOdyssey**](https://github.com/AMortalsOdyssey)：贡献 [额度历史轨迹 #37](https://github.com/cclank/tokei/pull/37)

### v1.0.16
- chore: 自动检查更新频率从 24 小时缩短为 6 小时

### v1.0.15

本版本吸收了 **12 个社区 PR** 的贡献，并完成了一轮安全、同步与性能加固。

- feat: 新增 Qwen Code、ZCode、MiMoCode、Oh My Pi 和 Grok Build 真实 Token 数据采集
- feat: Codex 支持按真实模型统计，兼容新版 Gemini CLI、OpenCode SQLite、OpenClaw 任务数据库和 Windows 日志路径
- fix: 修正 Codex 分叉会话重复累计、Claude Code 用量少算和 OpenClaw 任务状态识别异常
- fix: 自动同步调整为每 30 分钟，增强多设备同时提交时的 Git 同步可靠性
- security: 更新包增加域名白名单、SHA-256 校验、随机临时目录和安装失败回滚
- perf: 优化刷新缓存、SQLite 数据读取、数据面板预热及菜单栏紧凑布局

#### 社区贡献

- [**易良**](https://github.com/yiliang114)：贡献 [Qwen Code 支持 #25](https://github.com/cclank/tokei/pull/25)
- [**Orime**](https://github.com/orime)：修复 [Codex 分叉会话重复统计 #24](https://github.com/cclank/tokei/pull/24)
- [**Vuri**](https://github.com/vurihuang)：补充 [Oh My Pi 数据采集 #21](https://github.com/cclank/tokei/pull/21)
- [**刘巍峰**](https://github.com/liuweifeng)：贡献 [Codex 模型明细及 ZCode、MiMoCode #17](https://github.com/cclank/tokei/pull/17)、[Claude Code 去重修复 #18](https://github.com/cclank/tokei/pull/18)、[OpenCode SQLite 支持 #20](https://github.com/cclank/tokei/pull/20)、[多设备同步可靠性优化 #28](https://github.com/cclank/tokei/pull/28)、[Grok Build 真实 Token 采集 #29](https://github.com/cclank/tokei/pull/29)、[设置页与菜单栏布局优化 #30](https://github.com/cclank/tokei/pull/30)、[OpenClaw 统计及面板修复 #31](https://github.com/cclank/tokei/pull/31)
- [**yanglinzhen**](https://github.com/yanglinzhen1022)：修复 [新版 Gemini CLI 统计 #14](https://github.com/cclank/tokei/pull/14)
- [**阿**](https://github.com/proffitteoy)：贡献 [Windows 日志路径发现 #11](https://github.com/cclank/tokei/pull/11)

### v1.0.13
- feat: WorkBuddy 本地 JSONL 用量采集（Token、缓存、模型、成本、项目）
- feat: WorkBuddy 数据接入卡片、Dashboard、回顾、项目足迹和多设备同步
- feat: 各工具 token 按小时追踪（hours/day_hours），扩展作息分析维度
- feat: 菜单栏新增 6 种可即时切换并持久保存的图标样式（含自绘星轨）
- feat: 菜单栏新增双额度、单额度和仅图标模式，兼顾信息量与占用宽度
- feat: 自绘 Tokei 菜单栏标记和额度刻度环，移除重复时钟与通用符号
- fix: WorkBuddy 推理 Token 保持包含在输出中，避免总量重复累计
- fix: 恢复合并中误删的 _recalc_costs（本地价格表重算，防 GLM 等价格回退）

### v1.0.12
- feat: 开机自启动（设置页「登录时启动」开关）
- fix: Codex token 快照去重，避免重复累计
- fix: 同步配置只更新同步字段，保留 qoder_ide_enabled 等其他配置
- fix: 启动时落盘 Qoder IDE 开关状态

### v1.0.11
- fix: Codex 跨 rollout 去重，避免子代理和分叉任务重复累计父任务 Token

### v1.0.10
- fix: Codex 实时配额抓取（plan / 周配额 / 重置时间）
- fix: Codex 按时长检测配额窗口，跳过重复 token 快照
- fix: 多设备同步稳定性

### v1.0.9
- fix: 多设备同步按日期边界对齐，修正跨设备采集时差导致的 range 串台

### v1.0.8
- feat: 点击模型行展开详情（输入/输出/缓存读写/命中率/单价）
- feat: 回顾新增「Loop Engineering !!」「Loop滴神」成就（连续 24/7 活跃）
- fix: GLM 5.2 价格映射修复（不再按 Opus 价计算）
- fix: 同步数据成本自动修正（本地价格表重算对端模型成本）

### v1.0.7
- feat: Qoder 拆分为 CLI 和 IDE 两张独立卡片
- feat: Qoder IDE 数据采集（支持 VS Code / JetBrains 插件用量）
- fix: Qoder 分拆后数据模型和同步适配

### v1.0.6
- perf: 脚本性能优化 10 倍（6.5s→0.6s），CPU 占用从 ~22% 降至 ~1%
- fix: 首次加载失败自动重试 3 次，不再直接显示错误
- fix: Python 路径探测，解决 GUI 应用 PATH 缺失问题

### v1.0.5
- fix: 彻底消除外部 zstd 二进制依赖，根治 Gatekeeper 拦截问题
- fix: Swift 内置 CZstd 解压修复（帧边界精确定位）
- feat: 设置关闭工具卡片后菜单栏同步隐藏对应额度
- feat: 设置页手动检查更新按钮
- fix: 移除过时的 zstd 安装提示

### v1.0.4
- feat: 回顾支持时间周期筛选（今日/本周/本月/今年/全部），模型用量联动
- feat: 新增「永动机」成就（24h 全时段活跃）
- fix: 成就命名优化（俱乐部→先生）
- fix: Claude 额度条缺失时显示 zstd 安装提示

### v1.0.3
- feat: 主页顶部动态升级按钮，有新版本自动显示，一键升级
- feat: 24 小时自动检查更新
- feat: 品牌升级「時計」→「知度」(Token + Insight = Tokei)
- fix: Claude Desktop 配额条不显示（zstd 路径发现 + 二进制打包）
- fix: 下载超时保护（5 分钟）+ 失败自动恢复

### v1.0.2
- feat: 久坐提醒语音播报
- feat: 按模型显示 token 总量 + 缓存命中率
- feat: Hermes 多 profile 支持（`~/.hermes/profiles/*/state.db`）
- feat: 设置页 GitHub 链接按钮
- fix: 菜单栏无配额时兜底显示今日总 token 或品牌图标
- fix: 3 处文件句柄泄漏（Claude/Gemini/Pi 扫描）
- fix: Hermes「上周」数据缺失
- fix: OpenCode 成本纳入每日汇总

### v1.0.1
- fix: Claude Code 按 message ID 去重，修复重复计数问题
- fix: Claude Code 扫描 subagent/workflow 日志（之前遗漏）
- fix: Codex 额度过期后自动归零，解决刷新不及时问题
- feat: 设置页增加「检查更新」按钮 + "已是最新"反馈
- fix: 应用内自动更新支持

## Star History

<p align="center">
  <a href="https://star-history.com/#cclank/tokei&Date">
    <img src="https://api.star-history.com/svg?repos=cclank/tokei&type=Date" width="600" alt="Star History Chart">
  </a>
</p>

---

<a id="english"></a>

## English

Tokei is a **macOS menu bar app** that tracks usage, cost, and performance across **13 AI coding tools** in real-time — all from local log files, with zero network traffic.

**Features:** Real-time monitoring (30s refresh, seven menu bar styles, three density modes) · Cost estimation (317 models, OpenRouter pricing) · Dashboard (daily chart, weekly heatmap) · Time ranges (today/week/month/year) · Project-level tracking · Multi-device sync (Git-based, Mac + Linux) · Annual Wrapped · Keep awake · Sit reminder · Privacy-first (local logs only) · [Compare with CodexBar](https://tokei.lanshuagent.com#compare)

**Supported tools:** Claude Code, Codex CLI, Gemini CLI, Grok Build, Hermes, OpenClaw, Pi Coding Agent CLI, WorkBuddy, OpenCode, Qwen Code, Kimi Code, Qoder, QoderWork

For full documentation, visit [tokei.lanshuagent.com](https://tokei.lanshuagent.com).

## License

MIT
