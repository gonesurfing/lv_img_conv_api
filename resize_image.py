#!/usr/bin/env python3
"""
Image Resizing Module

This module provides a simple way to resize JPG and PNG images using PIL/Pillow.
It preserves aspect ratio by default and supports multiple resampling methods.
"""

import os
import argparse
from pathlib import Path
from typing import Tuple, Optional, Union
import logging

from PIL import Image

logger = logging.getLogger(__name__)

def resize_image(
    input_path: str,
    output_path: Optional[str] = None,
    target_size: Union[Tuple[int, int], int] = None,
    keep_aspect_ratio: bool = True,
    resampling_method: int = Image.Resampling.LANCZOS,
    crop: Optional[dict] = None
) -> str:
    """
    Resize an image to the specified dimensions.
    
    Args:
        input_path: Path to the input image file (JPG or PNG)
        output_path: Path for the resized image. If None, creates a file with '_resized' suffix
        target_size: Target size as (width, height) tuple or single dimension (same aspect ratio)
        keep_aspect_ratio: If True, maintains aspect ratio when resizing
        resampling_method: PIL resampling filter (default: LANCZOS for high quality)
        crop: Optional dict with keys 'left','top','right','bottom' specifying pixels to crop before resizing
     
    Returns:
        Path to the resized image file
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If input file is not JPG or PNG
        ValueError: If target_size is invalid
    """
    # Validate input file
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Check file extension
    file_ext = Path(input_path).suffix.lower()
    if file_ext not in ['.jpg', '.jpeg', '.png']:
        raise ValueError(f"Unsupported file format: {file_ext}. Only JPG and PNG are supported")

    # Default output path if not provided
    if output_path is None:
        input_base = Path(input_path).stem
        output_path = str(Path(input_path).parent / f"{input_base}_resized{file_ext}")

    # Open image and apply cropping if requested
    img = Image.open(input_path)
    if crop:
        orig_w, orig_h = img.size
        left = crop.get('left', 0)
        top = crop.get('top', 0)
        right_crop = crop.get('right', 0)
        bottom_crop = crop.get('bottom', 0)
        right = orig_w - right_crop
        bottom = orig_h - bottom_crop
        # Ensure coordinates are within image bounds
        left = max(0, min(left, orig_w))
        top = max(0, min(top, orig_h))
        right = max(left, min(right, orig_w))
        bottom = max(top, min(bottom, orig_h))
        img = img.crop((left, top, right, bottom))
        logger.info("Cropped image to: %d, %d, %d, %d", left, top, right, bottom)
    # Determine dimensions
    orig_width, orig_height = img.size
    # If no target size provided, only cropping is applied
    if target_size is None:
        # Ensure output path
        if output_path is None:
            input_base = Path(input_path).stem
            file_ext = Path(input_path).suffix
            output_path = str(Path(input_path).parent / f"{input_base}_resized{file_ext}")
        # Save cropped image
        img.save(output_path, quality=95 if Path(input_path).suffix.lower() in ['.jpg', '.jpeg'] else None)
        return output_path

    # Calculate target dimensions
    if target_size is None:
        raise ValueError("Target size must be specified")

    if isinstance(target_size, int):
        # Single dimension provided, calculate other based on aspect ratio
        if target_size <= 0:
            raise ValueError("Target size must be positive")

        # Use the provided dimension as the width
        target_width = target_size
        target_height = int(orig_height * (target_width / orig_width))

    elif isinstance(target_size, tuple) and len(target_size) == 2:
        target_width, target_height = target_size

        if target_width <= 0 or target_height <= 0:
            raise ValueError("Width and height must be positive")

        if keep_aspect_ratio:
            # Calculate dimensions while preserving aspect ratio
            width_ratio = target_width / orig_width
            height_ratio = target_height / orig_height

            # Use the smaller ratio to ensure the image fits within the target size
            if width_ratio < height_ratio:
                target_height = int(orig_height * width_ratio)
            else:
                target_width = int(orig_width * height_ratio)
    else:
        raise ValueError("Target size must be a single integer or a (width, height) tuple")

    # Perform the resize operation
    logger.info("Resizing image to: %d, %d", target_width, target_height)
    resized_img = img.resize((target_width, target_height), resampling_method)

    # Save the resized image
    resized_img.save(output_path, quality=95 if file_ext in ['.jpg', '.jpeg'] else None)

    return output_path


def main():
    """Command-line interface for the resize function"""
    parser = argparse.ArgumentParser(description="Resize JPG or PNG images")

    parser.add_argument("input_path", help="Path to the input image file (JPG or PNG)")
    parser.add_argument("-o", "--output", help="Path for the output resized image")

    # Two ways to specify dimensions
    size_group = parser.add_mutually_exclusive_group(required=True)

    size_group.add_argument(
        "-s",
        "--size",
        type=int,
        help="Target width (height will be calculated to maintain aspect ratio)"
    )

    size_group.add_argument(
        "-d",
        "--dimensions",
        nargs=2,
        type=int,
        metavar=("WIDTH", "HEIGHT"),
        help="Target dimensions as WIDTH HEIGHT"
    )

    parser.add_argument(
        "--no-aspect-ratio",
        action="store_true",
        help="Don't preserve aspect ratio when using --dimensions"
    )

    parser.add_argument(
        "--resampling",
        choices=["nearest", "box", "bilinear", "bicubic", "lanczos"],
        default="lanczos",
        help="Resampling method to use"
    )

    parser.add_argument(
        "--crop",
        type=int,
        nargs=4,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="Crop the image before resizing (pixels from each side)"
    )

    args = parser.parse_args()

    # Map resampling method names to PIL constants
    resampling_methods = {
        "nearest": Image.Resampling.NEAREST,
        "box": Image.Resampling.BOX,
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "lanczos": Image.Resampling.LANCZOS
    }

    try:
        crop = None
        if args.crop:
            crop = {
                'left': args.crop[0],
                'top': args.crop[1],
                'right': args.crop[2],
                'bottom': args.crop[3]
            }

        if args.size:
            target_size = args.size
        else:
            target_size = tuple(args.dimensions)

        output_path = resize_image(
            args.input_path,
            args.output,
            target_size,
            not args.no_aspect_ratio,
            resampling_methods[args.resampling],
            crop
        )

        logger.info("Image resized successfully: %s", output_path)
        logger.info("New dimensions: %s", Image.open(output_path).size)

    except Exception as e:
        logger.error("Error: %s", e)
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
