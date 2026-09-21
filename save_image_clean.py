"""Save Image Without Metadata - write images with zero embedded metadata."""

import os

import folder_paths
import numpy as np
from PIL import Image


class SaveImageWithoutMetadata:
    """Save an image with zero embedded metadata.

    No prompt, no workflow, no EXIF, no PNG tEXt chunks - a pure clean file.
    Handy as the counterpart of a metadata-saving node:

    * intermediate / preview images -> SaveImageWithoutMetadata (clean)
    * final high-resolution images  -> your metadata-saving node (full metadata)

    The node returns the images unchanged, so it can be chained.
    """

    FILE_FORMATS = ["png", "jpeg", "webp"]

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "output",
                        "tooltip": (
                            "Output filename prefix. Supports subdirectories, "
                            "e.g. clean/img  ->  saves under output/clean/."
                        ),
                    },
                ),
                "file_format": (cls.FILE_FORMATS, {"default": "png"}),
            },
            "optional": {
                "quality": (
                    "INT",
                    {
                        "default": 100,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Quality for lossy JPEG/WebP (100 = best).",
                    },
                ),
                "lossless_webp": (
                    "BOOLEAN",
                    {"default": True, "tooltip": "Lossless WebP (ignores quality)."},
                ),
                "add_counter_to_filename": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Append an incrementing counter to avoid overwrites.",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "save_images"
    CATEGORY = "SimpleTools"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Save an image with zero metadata - no prompt, no workflow, no EXIF. "
        "Use it for intermediate or preview outputs that must stay clean."
    )

    def save_images(
        self,
        images,
        filename_prefix="output",
        file_format="png",
        quality=100,
        lossless_webp=True,
        add_counter_to_filename=True,
        prompt=None,
        extra_pnginfo=None,
    ):
        # Normalize path separators to OS-native (Windows: \, Linux: /)
        filename_prefix = filename_prefix.replace("/", os.sep)
        full_output_folder, filename, counter, subfolder, _ = (
            folder_paths.get_save_image_path(filename_prefix, self.output_dir)
        )
        # Ensure the output directory exists before writing
        os.makedirs(full_output_folder, exist_ok=True)

        results = list()
        for image in images:
            # BHWC float[0,1] -> uint8 PIL
            arr = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

            # Build filename
            if add_counter_to_filename:
                file = f"{filename}_{counter:05d}.{file_format}"
            else:
                file = f"{filename}.{file_format}"
                out_path = os.path.join(full_output_folder, file)
                base, ext = os.path.splitext(file)
                n = 1
                while os.path.exists(out_path):
                    file = f"{base}_{n}{ext}"
                    out_path = os.path.join(full_output_folder, file)
                    n += 1

            file_path = os.path.join(full_output_folder, file)

            # Save - deliberately pass NO pnginfo / exif / comment
            save_kwargs = {}
            if file_format == "png":
                save_kwargs["compress_level"] = 4
            elif file_format == "jpeg":
                save_kwargs["quality"] = quality
                save_kwargs["optimize"] = True
            elif file_format == "webp":
                if lossless_webp:
                    save_kwargs["lossless"] = True
                else:
                    save_kwargs["quality"] = quality

            img.save(file_path, format=file_format.upper(), **save_kwargs)

            results.append({"filename": file, "subfolder": subfolder, "type": self.type})
            counter += 1

        return {"ui": {"images": results}, "result": (images,)}


NODE_CLASS_MAPPINGS = {
    "SaveImageWithoutMetadata": SaveImageWithoutMetadata,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageWithoutMetadata": "Save Image Without Metadata",
}
