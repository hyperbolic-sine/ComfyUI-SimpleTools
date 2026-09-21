"""Batch Progress - a live progress bar for batched sampling loops."""

from .utils import is_vhs_requeue


class BatchProgress:
    """Show batch progress and forward an incrementing index and percent.

    Plug it anywhere on a wire (it passes ``input`` through untouched) and read
    the progress bar in the node body plus the ``index`` / ``percent`` outputs.
    Each node instance keeps its own counter, so several progress nodes can be
    used in one workflow.
    """

    _counters = {}
    _total_batch = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("*",),
                "batch_size": (
                    "INT",
                    {
                        "default": 16,
                        "min": 1,
                        "step": 1,
                        "tooltip": "Frames per batch (e.g. the VideoHelperSuite batch_size).",
                    },
                ),
                "total_frames": (
                    "INT",
                    {
                        "default": 60,
                        "min": 1,
                        "step": 1,
                        "tooltip": "Total frames to cover; the batch count is ceil(total_frames / batch_size).",
                    },
                ),
            },
            "optional": {
                "start": (
                    "INT",
                    {
                        "default": 1,
                        "min": 0,
                        "step": 1,
                        "tooltip": "Index reported for the first batch.",
                    },
                ),
                "showMode": (
                    ["singleLine", "multiline"],
                    {
                        "default": "singleLine",
                        "tooltip": "singleLine: one line. multiline: counters and bar on two lines.",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # A progress node must run on every iteration.
        return float("NaN")

    RETURN_TYPES = ("*", "INT", "FLOAT")
    RETURN_NAMES = ("output", "index", "percent")
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "SimpleTools"
    DESCRIPTION = (
        "Passes its input through while displaying batch progress and emitting "
        "the current batch index and percentage. Counters survive "
        "VideoHelperSuite auto-requeues and reset on a manual queue."
    )

    def run(self, input, batch_size, total_frames, start=1, showMode="singleLine",
            prompt=None, unique_id=None):
        if not is_vhs_requeue(prompt):
            self._counters.clear()
            self._total_batch.clear()

        key = str(unique_id) if unique_id is not None else "bp_global"
        if key not in self._counters:
            self._counters[key] = start - 1
            self._total_batch[key] = max(1, int(total_frames + batch_size - 1) // batch_size)

        total_batches = self._total_batch[key]
        self._counters[key] += 1
        current = self._counters[key]
        percent = min(current / total_batches * 100, 100.0)

        bar_len = 18
        raw = bar_len * percent / 100
        filled = int(raw)
        if raw > 0 and filled == 0:
            filled = 1
        if current >= total_batches:
            filled = bar_len
        bar = "█" * filled + "░" * (bar_len - filled)

        if showMode == "multiline":
            text = f"Batch {current}/{total_batches}  {percent:.2f}%\n[{bar}]"
        else:
            text = f"Batch {current}/{total_batches} [{bar}] {percent:.2f}%"

        return {
            "ui": {"text": [text]},
            "result": (input, current, round(percent, 2)),
        }


NODE_CLASS_MAPPINGS = {
    "BatchProgress": BatchProgress,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchProgress": "Batch Progress",
}
