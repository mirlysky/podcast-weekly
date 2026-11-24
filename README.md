# 耳边档案

[打开每周播客推荐](https://mirlysky.github.io/podcast-weekly/)

每期推荐五档中文播客和各一集入坑单集。页面从 `weeks-index.json` 读取期数目录，切换时加载对应的 `week-YYYY-MM-DD.json`。小宇宙栏目展示原有推荐和累计收听统计。

## 运动统计

按 Asia/Tokyo 的周一至周日归档，以每次运动的开始时间归周。历史从 2026-01-01 开始，所以第一周只统计周四至周日。顶部汇总三类已确认运动的次数、时长与已记录的活动消耗（kcal）。

力量训练对应 `functionalStrengthTraining`，花样滑冰栏目对应 Apple 的 `skatingSports`（该类型也可包含其他滑冰运动）。户外步行只计明确的 `outdoorWalking`。Apple 原生导出用 `walking` 搭配明确的 `HKIndoorWorkout=false`（或 `0`）表示户外，导入时归入 `outdoorWalking`。缺少户外标记的步行不计入合计，页面会提示该周覆盖不完整。

`workouts.json` 只保存周度聚合数据，发布后任何人均可读取。Apple Health 导出文件、轨迹和授权凭证须保留在仓库之外。

### 本地更新

GitHub 托管的 Actions 无法直接访问个人设备中的 Apple Health。每周一可在 iPhone 的「健康」App 中点击头像，再选择「导出所有健康数据」。将导出文件解压在仓库之外，在 Mac 上用 Python 3.9 或更高版本生成聚合。将下面的日期替换为导出覆盖的最后一天（东京时间）。

```sh
python3 scripts/import-workouts.py /path/to/apple_health_export/export.xml --through 2026-11-23
git diff -- workouts.json
git add -- workouts.json
git commit -m "Update weekly workout aggregates"
git push origin main
```

每次用完整导出重算历史。如果已有可信的自动导出来源，也可在自己的 Mac 上用 `launchd` 于每周一运行聚合命令，输入留在本机，发布前检查输出。GitHub Pages 随 `main` 更新。
