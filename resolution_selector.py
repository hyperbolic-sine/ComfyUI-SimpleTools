"""Resolution Selector - pick a tier and a ratio, get exact INT width/height.

Design
------
* **Short-side alignment.** The chosen tier fixes the *short* side of the frame
  (480/720/1080/1440/2160 px) and the other side is derived from the ratio. The
  short side is the one that defines the "P" of a tier, so 1080P is 1920x1080 in
  16:9 and 1440x1080 in 4:3 - both are still 1080P.
* **One precomputed table.** Every tier x ratio combination is built once into
  ``RESOLUTIONS`` at import time, so ``get_size`` is a plain dictionary lookup.
  The size the frontend shows is therefore byte-for-byte the size the graph
  executes - no rounding can drift between the two.
* **480P 16:9 / 9:16 use 854** px on the long side (the common convention).
  480 * 16 / 9 = 853.33 would otherwise truncate to 853.
* ``OPTIONS_ROUTE`` exposes the same table to ``js/resolution_selector.js``,
  which renders the live "W x H" readout under the node.

See README.md for the full 30-combination table and the multiple-of-8 caveat.
"""

try:  # pragma: no cover - only importable inside a running ComfyUI
    from aiohttp import web
    from server import PromptServer
except Exception:  # pragma: no cover - plain Python / unit tests
    web = None
    PromptServer = None

OPTIONS_ROUTE = "/simpletools/resolution_selector/options"

# Resolution tier -> short-side pixel count.
TIER_SHORT_SIDES = {
    "480P": 480,
    "720P": 720,
    "1080P": 1080,
    "2K": 1440,
    "4K": 2160,
}

# Aspect ratios (width:height), in menu order.
ASPECT_RATIOS = ["16:9", "9:16", "4:3", "3:4", "1:1", "21:9"]

# Explicit overrides that are not derivable from the short side alone.
_OVERRIDES = {
    ("480P", "16:9"): (854, 480),
    ("480P", "9:16"): (480, 854),
}


def _build_resolutions():
    """Precompute {tier: {ratio: (width, height)}} using short-side alignment."""
    table = {}
    for tier, short in TIER_SHORT_SIDES.items():
        table[tier] = {}
        for ratio in ASPECT_RATIOS:
            if (tier, ratio) in _OVERRIDES:
                table[tier][ratio] = _OVERRIDES[(tier, ratio)]
                continue

            a, b = (int(part) for part in ratio.split(":"))
            if a == b:
                width = height = short
            elif a > b:  # landscape: height is the short side
                width, height = short * a // b, short
            else:  # portrait: width is the short side
                width, height = short, short * b // a
            table[tier][ratio] = (width, height)
    return table


RESOLUTIONS = _build_resolutions()


def register_options_route() -> None:
    """Serve RESOLUTIONS to the bundled frontend extension (best effort)."""
    if PromptServer is None or web is None:
        return
    try:
        @PromptServer.instance.routes.get(OPTIONS_ROUTE)
        async def _resolution_options(request):  # pragma: no cover - HTTP only
            return web.json_response(RESOLUTIONS)
    except Exception as exc:  # pragma: no cover - never break node loading
        print(f"[SimpleTools] resolution options route not registered: {exc}")


register_options_route()


class SimpleResolutionSelector:
    """Resolution tier x aspect ratio -> exact INT width/height."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "resolution": (
                    list(TIER_SHORT_SIDES.keys()),
                    {
                        "default": "1080P",
                        "tooltip": "Target tier. It fixes the SHORT side of the frame.",
                    },
                ),
                "aspect_ratio": (
                    ASPECT_RATIOS,
                    {
                        "default": "16:9",
                        "tooltip": "Frame ratio. The resulting size is shown under the node.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_size"
    CATEGORY = "SimpleTools"
    DESCRIPTION = (
        "Pick a resolution tier (480P/720P/1080P/2K/4K) and an aspect ratio "
        "(16:9/9:16/4:3/3:4/1:1/21:9) to get an exact INT width and height. "
        "Sizes use short-side alignment and are precomputed, so what the node "
        "shows is exactly what the sampler receives."
    )

    def get_size(self, resolution, aspect_ratio):
        """Return the precomputed (width, height) for this combination."""
        try:
            return RESOLUTIONS[resolution][aspect_ratio]
        except KeyError:
            return 1024, 1024


NODE_CLASS_MAPPINGS = {
    "SimpleResolutionSelector": SimpleResolutionSelector,
    # Legacy key kept so workflows saved before the first public release keep
    # loading. It is the same class, only the registry key differs.
    "ResolutionSelectorJWB": SimpleResolutionSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleResolutionSelector": "Resolution Selector",
    "ResolutionSelectorJWB": "Resolution Selector (Legacy)",
}
