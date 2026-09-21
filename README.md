# ComfyUI-SimpleTools

Four small, dependency-free utility nodes for ComfyUI. No model downloads, no
extra pip packages — clone the folder into `custom_nodes/` and restart.

| Node | Category | What it does |
| --- | --- | --- |
| **Resolution Selector** | `SimpleTools` | Pick a resolution tier + aspect ratio → exact INT `width` / `height`, with a live `W×H` readout under the node. |
| **Save Image Without Metadata** | `SimpleTools` | Save PNG / JPEG / WebP with **zero** embedded metadata — no prompt, no workflow, no EXIF. |
| **Batch Progress** | `SimpleTools` | A progress bar for batched sampling loops, plus `index` and `percent` outputs. |
| **Simple Counter** | `SimpleTools` | Pass any value through and emit an incrementing index. |

Developed and tested on ComfyUI 0.3.x with the 1.5x frontend. Python 3.9+.

---

## Installation

### ComfyUI Manager

Search for **Simple Tools** in ComfyUI Manager → Install → restart ComfyUI.
(Once the package is published to the ComfyUI Registry.)

### Manual

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hyperbolic-sine/ComfyUI-SimpleTools
# restart ComfyUI
```

Update later with `git pull` inside the folder.

---

## Resolution Selector

`SimpleTools → Resolution Selector`

Two dropdowns, two INT outputs:

| Input | Values |
| --- | --- |
| `resolution` | `480P` `720P` `1080P` `2K` `4K` |
| `aspect_ratio` | `16:9` `9:16` `4:3` `3:4` `1:1` `21:9` |

| Output | Type | Meaning |
| --- | --- | --- |
| `width` | `INT` | Frame width in pixels |
| `height` | `INT` | Frame height in pixels |

The node body shows the current output size (`1920×1080`) and updates the moment
you change either dropdown. Wire `width` / `height` into *Empty Latent Image* (or
any other size input) and the numbers are already exact integers.

### Full size table

| Tier | 16:9 | 9:16 | 4:3 | 3:4 | 1:1 | 21:9 |
| --- | --- | --- | --- | --- | --- | --- |
| **480P** | 854 × 480 | 480 × 854 | 640 × 480 | 480 × 640 | 480 × 480 | 1120 × 480 |
| **720P** | 1280 × 720 | 720 × 1280 | 960 × 720 | 720 × 960 | 720 × 720 | 1680 × 720 |
| **1080P** | 1920 × 1080 | 1080 × 1920 | 1440 × 1080 | 1080 × 1440 | 1080 × 1080 | 2520 × 1080 |
| **2K** | 2560 × 1440 | 1440 × 2560 | 1920 × 1440 | 1440 × 1920 | 1440 × 1440 | 3360 × 1440 |
| **4K** | 3840 × 2160 | 2160 × 3840 | 2880 × 2160 | 2160 × 2880 | 2160 × 2160 | 5040 × 2160 |

### How the numbers are chosen

* **Short-side alignment.** The tier fixes the *short* side of the frame
  (480 / 720 / 1080 / 1440 / 2160 px) and the other side is derived from the
  ratio. The short side is what the "P" of a tier refers to, so 1080P is
  1920×1080 in 16:9 and 1440×1080 in 4:3 — both are still 1080P.
* **Precomputed.** All 30 combinations are built once at import time. The
  readout in the UI and the value the graph executes come from the same
  dictionary, so they can never drift apart.
* **`2K` = 1440 and `4K` = 2160** on the short side (QHD / UHD).
* **480P 16:9 / 9:16 use 854 px** on the long side, the common convention;
  480 × 16 / 9 = 853.33 would otherwise truncate to 853.

### Caveat: multiples of 8

Latent-based pipelines divide dimensions by 8, i.e. the real output is
`width // 8 * 8`. **854 is the only value in the table that is not a multiple of
8**, so on such a pipeline 480P 16:9 comes out as **848×480** and 480P 9:16 as
**480×848**, while the node reports 854. Every other combination is already a
multiple of 8.

### Notes

* Workflows saved with the pre-release node key `ResolutionSelectorJWB` keep
  loading: that key is still registered (shown as *Resolution Selector (Legacy)*
  in the node menu). New graphs should use **Resolution Selector**.
* The readout is a frontend convenience only. The size table is served by the
  backend at `GET /simpletools/resolution_selector/options`; if that endpoint is
  unavailable the node still works, only the readout stays empty.

---

## Save Image Without Metadata

`SimpleTools → Save Image Without Metadata`

Writes images with no prompt, no workflow and no EXIF embedded — useful for
intermediate results, previews or files you want to share as-is. Pair it with a
metadata-saving node: clean copies from this one, full metadata on the final
render.

| Input | Default | Notes |
| --- | --- | --- |
| `images` | — | `IMAGE` batch |
| `filename_prefix` | `output` | Supports subfolders: `clean/img` → `output/clean/` |
| `file_format` | `png` | `png` / `jpeg` / `webp` |
| `quality` | `100` | JPEG / lossy WebP only |
| `lossless_webp` | `true` | Ignored unless `file_format = webp` |
| `add_counter_to_filename` | `true` | Off → `_1`, `_2`, … suffixes are used to avoid overwrites |

Output: `images` (passed through, so the node can be chained).

---

## Batch Progress

`SimpleTools → Batch Progress`

Drop it on any wire (the `input` is passed straight through) and watch the batch
loop:

```
Batch 3/4 [█████████████░░░░░] 75.00%
```

| Input | Default | Notes |
| --- | --- | --- |
| `input` | — | Any type, passed through |
| `batch_size` | `16` | Frames per batch |
| `total_frames` | `60` | Batch count = `ceil(total_frames / batch_size)` |
| `start` | `1` | Index of the first batch |
| `showMode` | `singleLine` | or `multiline` |

Outputs: `output` (pass-through), `index` (`INT`), `percent` (`FLOAT`).

Each node instance keeps its own counter, so several progress nodes can live in
one workflow.

**When it counts.** The counter is designed for loops that re-run the graph many
times: it resets when you queue a prompt manually and keeps counting across
[VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)
`VHS_BatchManager` auto-requeues (frame batches, video loops). ComfyUI's own
*Queue* batch count starts a new prompt every time, which counts as a manual
queue — so without an auto-requeue node in the graph the bar stays on the first
batch. Pair it with a `VHS_BatchManager` loop for progress across batches.

---

## Simple Counter

`SimpleTools → Simple Counter`

A lighter version of the above when you only need a number: pass a value
through, get an incrementing `index` out. Handy for numbered filenames, cycling
seeds or picking the n-th prompt from a list.

The counting rules are the same as *Batch Progress*: the index resets on a
manual queue and increments across auto-requeues, so it needs an auto-requeue
driver such as VideoHelperSuite's `VHS_BatchManager` to actually walk up. On its
own (one execution per queue) it reports `start` every time.

| Input | Default | Notes |
| --- | --- | --- |
| `input` | — | Any type, passed through |
| `start` | `0` | Index of the first run |
| `key` | `""` | Optional. Empty → one counter per node; identical keys share a counter |

Outputs: `output` (pass-through), `index` (`INT`).

---

## Development

```bash
python -m unittest discover -s tests -v
```

The tests cover the whole size matrix, the frontend/backend route contract and
the node-mapping contract. They need no ComfyUI installation — plain Python is
enough. CI runs them on every push.

```
ComfyUI-SimpleTools/
├── __init__.py              # node registration, WEB_DIRECTORY
├── resolution_selector.py   # Resolution Selector (+ options HTTP route)
├── save_image_clean.py      # Save Image Without Metadata
├── batch_progress.py        # Batch Progress
├── simple_counter.py        # Simple Counter
├── utils.py                 # shared VideoHelperSuite requeue detection
├── js/                      # frontend extensions (live readout, progress bar)
└── tests/                   # unit tests
```

---

## 中文说明

四个零依赖的 ComfyUI 小工具节点，克隆到 `custom_nodes/` 重启即可用。

* **Resolution Selector（分辨率选择器）**：档位（480P/720P/1080P/2K/4K）×
  比例（16:9、9:16、4:3、3:4、1:1、21:9）→ 输出精确的 INT `width` / `height`，
  节点下方实时显示 `宽×高`。采用**短边对齐**：档位决定画面短边，长边按比例精确计算，
  30 种组合全部预计算成静态表，显示值与实际执行值完全一致。
  注意 480P 16:9 用行业标准 854（不是 853），而 **854 不是 8 的倍数**，
  走 latent 流程时实际输出会是 848×480，其余组合均为 8 的倍数。
* **Save Image Without Metadata**：保存**不带任何元数据**的图片（无 prompt、无工作流、
  无 EXIF），支持 png / jpeg / webp，适合中间图、预览图或需要干净交付的文件。
* **Batch Progress**：批处理进度条节点，顺带输出 `index` 与 `percent`。
* **Simple Counter**：轻量计数器，原样透传输入并输出 `index`。

  ⚠️ 这两个计数类节点按「手动 Queue 重置、自动重入续计」设计：**需要搭配
  VideoHelperSuite 的 `VHS_BatchManager` 之类的自动重入循环**才会逐批递增；
  ComfyUI 自带的 Queue 批量次数每次都算一次新 prompt，因此单独使用时
  `index` 会一直停在 `start`（进度条停在第一批）。

旧键名 `ResolutionSelectorJWB` 仍然注册（菜单显示为 *Resolution Selector
(Legacy)*），老工作流不会失效。

---

## License

[MIT](LICENSE)
