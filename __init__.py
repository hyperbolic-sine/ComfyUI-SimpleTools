"""ComfyUI-SimpleTools.

A small, dependency-free collection of everyday ComfyUI utilities:

* Resolution Selector        - resolution tier x aspect ratio -> exact INT width/height
* Batch Progress             - live batch progress bar, index and percent
* Simple Counter             - pass-through counter with a stable index output
* Save Image Without Metadata - PNG/JPEG/WebP with zero embedded metadata
"""

from .batch_progress import NODE_CLASS_MAPPINGS as _BATCH_CLASSES
from .batch_progress import NODE_DISPLAY_NAME_MAPPINGS as _BATCH_NAMES
from .resolution_selector import NODE_CLASS_MAPPINGS as _RES_CLASSES
from .resolution_selector import NODE_DISPLAY_NAME_MAPPINGS as _RES_NAMES
from .save_image_clean import NODE_CLASS_MAPPINGS as _SAVE_CLASSES
from .save_image_clean import NODE_DISPLAY_NAME_MAPPINGS as _SAVE_NAMES
from .simple_counter import NODE_CLASS_MAPPINGS as _COUNTER_CLASSES
from .simple_counter import NODE_DISPLAY_NAME_MAPPINGS as _COUNTER_NAMES

NODE_CLASS_MAPPINGS = {
    **_BATCH_CLASSES,
    **_RES_CLASSES,
    **_SAVE_CLASSES,
    **_COUNTER_CLASSES,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **_BATCH_NAMES,
    **_RES_NAMES,
    **_SAVE_NAMES,
    **_COUNTER_NAMES,
}

# Frontend extension directory (served by ComfyUI at /extensions/<module>/).
WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
