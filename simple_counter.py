"""Simple Counter - pass a value through while emitting an incrementing index."""

from .utils import is_vhs_requeue


class SimpleCounter:
    """Pass ``input`` through unchanged and count how many times it ran.

    Lighter than ``Batch Progress``: no progress bar, just a stable index that
    can drive filenames, seeds or prompt lists. The index is reset whenever the
    user queues a new prompt and continues across VideoHelperSuite requeues.
    """

    _counters = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("*",),
                "start": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "step": 1,
                        "tooltip": "Index reported for the first run.",
                    },
                ),
            },
            "optional": {
                "key": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "tooltip": "Counter key. Leave empty for one counter per node; "
                                   "set different keys to share or separate counters.",
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
        # A counter must run on every iteration.
        return float("NaN")

    RETURN_TYPES = ("*", "INT")
    RETURN_NAMES = ("output", "index")
    FUNCTION = "run"
    CATEGORY = "SimpleTools"
    DESCRIPTION = (
        "Passes its input through while emitting an incrementing index, useful "
        "for numbered outputs, batch filenames or cycling seeds."
    )

    def run(self, input, start, key="", prompt=None, unique_id=None):
        if not is_vhs_requeue(prompt):
            self._counters.clear()

        counter_key = key or f"sc_{unique_id if unique_id is not None else 'global'}"
        if counter_key not in self._counters:
            self._counters[counter_key] = start - 1

        self._counters[counter_key] += 1
        return (input, self._counters[counter_key])


NODE_CLASS_MAPPINGS = {
    "SimpleCounter": SimpleCounter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleCounter": "Simple Counter",
}
