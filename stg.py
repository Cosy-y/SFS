"""steganography module - hide data in images"""
from PIL import Image
import numpy as np
from typing import Tuple

# config
LSB_BITS_PER_CHANNEL = 2
CHANNELS_TO_USE = 3


def get_image_capacity(width: int, height: int) -> int:
    """calculate how many bytes can be stored in image"""
    total_pixels = width * height
    bits_per_pixel = LSB_BITS_PER_CHANNEL * CHANNELS_TO_USE
    total_bits = total_pixels * bits_per_pixel
    return total_bits // 8


def modify_lsb(channel_value: int, new_bits: int, num_bits: int = 2) -> int:
    """replace last num_bits of channel with new data"""
    mask = 255 << num_bits
    cleared = channel_value & mask
    return cleared | new_bits


def extract_lsb(channel_value: int, num_bits: int = 2) -> int:
    """extract last num_bits from channel"""
    mask = (1 << num_bits) - 1
    return channel_value & mask


def embed_data(image: Image.Image, data: bytes) -> Image.Image:
    """hide data in image using lsb steganography"""
    image = image.convert('RGB')
    width, height = image.size
    pixels = image.load()
    
    capacity = get_image_capacity(width, height)
    if len(data) > capacity:
        raise ValueError(f"data too large: {len(data)} bytes, capacity: {capacity} bytes")
    
    bit_string = ''.join(format(byte, '08b') for byte in data)
    total_bits = len(bit_string)
    bit_index = 0
    for y in range(height):
        for x in range(width):
            if bit_index >= total_bits:
                break
            
            r, g, b = pixels[x, y]
            
            if bit_index < total_bits:
                bits_to_embed = int(bit_string[bit_index:bit_index + 2], 2)
                r = modify_lsb(r, bits_to_embed, 2)
                bit_index += 2
            
            if bit_index < total_bits:
                bits_to_embed = int(bit_string[bit_index:bit_index + 2], 2)
                g = modify_lsb(g, bits_to_embed, 2)
                bit_index += 2
            
            if bit_index < total_bits:
                bits_to_embed = int(bit_string[bit_index:bit_index + 2], 2)
                b = modify_lsb(b, bits_to_embed, 2)
                bit_index += 2
            
            pixels[x, y] = (r, g, b)
        
        if bit_index >= total_bits:
            break
    
    return image


def extract_data(image: Image.Image, data_length: int) -> bytes:
    """extract hidden data from image"""
    image = image.convert('RGB')
    width, height = image.size
    pixels = image.load()
    
    total_bits = data_length * 8
    bit_string = ""
    bit_index = 0
    for y in range(height):
        for x in range(width):
            if bit_index >= total_bits:
                break
            
            r, g, b = pixels[x, y]
            
            if bit_index < total_bits:
                extracted = extract_lsb(r, 2)
                bit_string += format(extracted, '02b')
                bit_index += 2
            
            if bit_index < total_bits:
                extracted = extract_lsb(g, 2)
                bit_string += format(extracted, '02b')
                bit_index += 2
            
            if bit_index < total_bits:
                extracted = extract_lsb(b, 2)
                bit_string += format(extracted, '02b')
                bit_index += 2
        
        if bit_index >= total_bits:
            break
    data = bytearray()
    for i in range(0, len(bit_string), 8):
        byte_string = bit_string[i:i+8]
        if len(byte_string) == 8:
            byte_value = int(byte_string, 2)
            data.append(byte_value)
    
    return bytes(data)


def create_carrier_image(min_capacity_bytes: int, dimensions: Tuple[int, int] = None) -> Image.Image:
    """create blank image with random noise for hiding data"""
    if dimensions:
        width, height = dimensions
    else:
        total_pixels_needed = (min_capacity_bytes * 8 + 5) // 6
        import math
        size = int(math.ceil(math.sqrt(total_pixels_needed)))
        width, height = size, size
    
    noise_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    image = Image.fromarray(noise_array, 'RGB')
    return image


def validate_image(image: Image.Image, min_width: int = 100, min_height: int = 100) -> Tuple[bool, str]:
    """check if image is suitable for steganography"""
    width, height = image.size
    
    if width < min_width or height < min_height:
        return False, f"image too small: {width}x{height}, minimum {min_width}x{min_height}"
    
    if image.mode not in ['RGB', 'RGBA', 'L']:
        return False, f"unsupported image mode: {image.mode}"
    
    return True, "image is suitable"


def test_steganography():
    """test steganography functions"""
    print("=== steganography module test ===")
    print()
    
    print("test 1: capacity calculation")
    capacity = get_image_capacity(100, 100)
    print(f"  100x100 image capacity: {capacity} bytes")
    assert capacity == 7500
    print("  ✓ passed\n")
    
    print("test 2: bit manipulation")
    modified = modify_lsb(214, 3, 2)
    print(f"  modify_lsb(214, 3) = {modified}")
    assert modified == 215
    
    extracted = extract_lsb(215, 2)
    print(f"  extract_lsb(215) = {extracted}")
    assert extracted == 3
    print("  ✓ passed\n")
    
    print("test 3: embed and extract data")
    test_data = b"hello, steganography!"
    print(f"  original: {test_data}")
    print(f"  size: {len(test_data)} bytes")
    
    image = create_carrier_image(len(test_data))
    print(f"  created carrier: {image.size[0]}x{image.size[1]}")
    
    stego_image = embed_data(image, test_data)
    print(f"  data embedded")
    
    extracted_data = extract_data(stego_image, len(test_data))
    print(f"  extracted: {extracted_data}")
    
    assert extracted_data == test_data
    print("  ✓ passed\n")
    
    print("test 4: large binary data")
    large_data = bytes(range(256)) * 10
    print(f"  testing {len(large_data)} bytes")
    
    image = create_carrier_image(len(large_data))
    stego_image = embed_data(image, large_data)
    extracted = extract_data(stego_image, len(large_data))
    
    assert extracted == large_data
    print("  ✓ passed\n")
    
    print("="*40)
    print("all tests passed ✓")
    print("="*40)
if __name__ == "__main__":
    test_steganography()