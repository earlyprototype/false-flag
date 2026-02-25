"""
Image post-processing utilities for pixel art asset generation.
Handles resizing, palette conversion to DB16, and transparency management.
"""

from PIL import Image
import numpy as np
from typing import Tuple

# DB16 Palette (DawnBringer 16)
DB16_PALETTE = [
    (0x14, 0x0c, 0x1c),  # #140c1c - dark purple-black
    (0x44, 0x24, 0x34),  # #442434 - dark purple
    (0x30, 0x34, 0x6d),  # #30346d - dark blue
    (0x4e, 0x4a, 0x4e),  # #4e4a4e - dark grey
    (0x85, 0x4c, 0x30),  # #854c30 - brown
    (0x34, 0x65, 0x24),  # #346524 - dark green
    (0xd0, 0x46, 0x48),  # #d04648 - red
    (0x75, 0x71, 0x61),  # #757161 - grey
    (0x59, 0x7d, 0xce),  # #597dce - blue
    (0xd2, 0x7d, 0x2c),  # #d27d2c - orange
    (0x85, 0x95, 0xa1),  # #8595a1 - light grey-blue
    (0x6d, 0xaa, 0x2c),  # #6daa2c - green
    (0xd2, 0xaa, 0x99),  # #d2aa99 - skin tone
    (0x6d, 0xc2, 0xca),  # #6dc2ca - cyan
    (0xda, 0xd4, 0x5e),  # #dad45e - yellow
    (0xde, 0xee, 0xd6),  # #deeed6 - off-white
]


def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Calculate Euclidean distance between two RGB colors."""
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def find_nearest_db16_color(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Find the closest DB16 palette color to the given RGB color."""
    min_distance = float('inf')
    nearest_color = DB16_PALETTE[0]
    
    for palette_color in DB16_PALETTE:
        distance = color_distance(rgb, palette_color)
        if distance < min_distance:
            min_distance = distance
            nearest_color = palette_color
    
    return nearest_color


def convert_to_db16_palette(image: Image.Image) -> Image.Image:
    """
    Convert image to DB16 palette by mapping each pixel to the nearest DB16 color.
    Preserves alpha channel for transparency.
    """
    # Ensure image is in RGBA mode
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Get image data as numpy array
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # Create output array
    output_array = np.zeros_like(img_array)
    
    # Process each pixel
    for y in range(height):
        for x in range(width):
            r, g, b, a = img_array[y, x]
            
            # Preserve full transparency
            if a == 0:
                output_array[y, x] = [0, 0, 0, 0]
            else:
                # Map RGB to nearest DB16 color
                nearest_color = find_nearest_db16_color((r, g, b))
                output_array[y, x] = [nearest_color[0], nearest_color[1], nearest_color[2], a]
    
    # Convert back to PIL Image
    return Image.fromarray(output_array, 'RGBA')


def resize_to_exact(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """
    Resize image to exact dimensions using nearest-neighbor for pixel art.
    Centers the image and crops/pads as needed.
    """
    # Use NEAREST for pixel-perfect scaling (no anti-aliasing)
    current_width, current_height = image.size
    
    # Calculate scaling to fit within target while maintaining aspect ratio
    scale_x = target_width / current_width
    scale_y = target_height / current_height
    scale = min(scale_x, scale_y)
    
    # Resize with nearest-neighbor
    new_width = int(current_width * scale)
    new_height = int(current_height * scale)
    resized = image.resize((new_width, new_height), Image.NEAREST)
    
    # Create target canvas with transparency
    canvas = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
    
    # Center the resized image on canvas
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    canvas.paste(resized, (paste_x, paste_y), resized if resized.mode == 'RGBA' else None)
    
    return canvas


def process_generated_image(
    image: Image.Image,
    target_width: int,
    target_height: int,
    apply_db16: bool = True
) -> Image.Image:
    """
    Complete post-processing pipeline for generated images.
    
    Args:
        image: Source PIL Image
        target_width: Target width in pixels
        target_height: Target height in pixels
        apply_db16: Whether to apply DB16 palette conversion
    
    Returns:
        Processed PIL Image in RGBA mode
    """
    # Ensure RGBA mode
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Resize to exact dimensions
    image = resize_to_exact(image, target_width, target_height)
    
    # Apply DB16 palette conversion if requested
    if apply_db16:
        image = convert_to_db16_palette(image)
    
    return image


def save_with_transparency(image: Image.Image, output_path: str):
    """Save image as PNG with transparency preserved."""
    image.save(output_path, 'PNG', optimize=True)
    print(f"✓ Saved: {output_path}")


