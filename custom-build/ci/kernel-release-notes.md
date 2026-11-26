适用于联想 Y700 第五代 / Legion Tab Gen 5（TB323FU）。

## 版本要点

$changes

## 验证与已知限制

- CI 已通过补丁审计、Helper 测试、initramfs 打包回归、ARM64 内核构建和产物校验。
- $device_validation
$known_issues

## 构建与源码

| 项目 | 版本 |
| --- | --- |
| san-flavored | `v$version` |
| 上游基线 | [kernel-$upstream_kernel]($upstream_release) · [`$upstream_commit_short`]($upstream_commit_url) |
| Linux 与补丁 | `$linux_version` · $upstream_patch_count 个上游补丁 · $custom_patch_count 个定制补丁 |
| 内核版本 | `$kernel_release` |
| libcamera 自动对焦 | `$libcamera_version` |

[CI 构建记录]($ci_url) · [源码提交 `$source_short`]($source_url)$compare_link
