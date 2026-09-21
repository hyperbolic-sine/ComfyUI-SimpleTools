"""Shared helpers for ComfyUI-SimpleTools."""


def is_vhs_requeue(prompt) -> bool:
    """Return True when the current run is a VideoHelperSuite auto-requeue.

    ``VHS_BatchManager`` re-queues the whole prompt with ``requeue`` incremented
    once per batch. Counter-style nodes must keep counting across those
    re-queues and only reset when the user queues a new prompt manually.

    Returns False when VideoHelperSuite is not installed or not in use.
    """
    if not prompt:
        return False

    for node in prompt.values():
        if not isinstance(node, dict):
            continue
        if node.get("class_type") != "VHS_BatchManager":
            continue
        inputs = node.get("inputs") or {}
        try:
            if int(inputs.get("requeue", 0) or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False
