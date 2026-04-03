"""test script to demo sfs system"""
import os
import shutil
from pathlib import Path
from metadata import MetadataManager
from PIL import Image
import crypto
import stg

# config
PASSWORD = "sfsproject"
TEST_FILE = "test.txt"


def cleanup():
    """remove existing sfs system"""
    home = Path.home()
    sfs_dir = home / '.sfs'
    if sfs_dir.exists():
        shutil.rmtree(sfs_dir)
        print("cleaned up old system")


def test_init():
    """test system initialization"""
    print("\n=== testing init ===")
    meta = MetadataManager()
    meta.initialize(PASSWORD)
    print(f"✓ initialized at {meta.storage_dir}")
    print(f"✓ index file: {meta.index_file}")
    print(f"✓ storage dir: {meta.images_dir}")


def test_store():
    """test storing a file"""
    print("\n=== testing store ===")
    
    # create test file
    with open(TEST_FILE, 'w') as f:
        f.write("this is a test file for sfs demo\n")
        f.write("steganography + encryption = hidden security\n")
        f.write("password: sfsproject\n")
    
    file_size = os.path.getsize(TEST_FILE)
    print(f"test file: {TEST_FILE} ({file_size} bytes)")
    
    # read file
    with open(TEST_FILE, 'rb') as f:
        file_data = f.read()
    
    # encrypt
    encrypted = crypto.encrypt_data(file_data, PASSWORD)
    print(f"encrypted size: {len(encrypted)} bytes")
    
    # embed in image
    img = stg.create_carrier_image(len(encrypted), (1920, 1080))
    stego_img = stg.embed_data(img, encrypted)
    
    # save
    meta = MetadataManager()
    img_name = meta.get_next_image_name()
    img_path = os.path.join(meta.images_dir, img_name)
    stego_img.save(img_path, 'PNG')
    print(f"✓ saved to {img_name}")
    
    # update metadata
    import hashlib
    checksum = hashlib.sha256(file_data).hexdigest()
    
    meta.add_file(
        PASSWORD,
        TEST_FILE,
        file_size,
        len(encrypted),
        checksum,
        [{
            'chunk_id': 0,
            'image_file': img_name,
            'offset': 0,
            'length': len(encrypted)
        }]
    )
    print(f"✓ added to index")


def test_list():
    """test listing files"""
    print("\n=== testing list ===")
    meta = MetadataManager()
    files = meta.list_files(PASSWORD)
    
    print(f"stored files: {len(files)}")
    for name, info in files.items():
        print(f"  - {name}")
        print(f"    size: {info['original_size']} bytes")
        print(f"    chunks: {info['chunk_count']}")


def test_extract():
    """test extracting a file"""
    print("\n=== testing extract ===")
    meta = MetadataManager()
    
    file_info = meta.get_file(PASSWORD, TEST_FILE)
    if not file_info:
        print("error: file not found")
        return
    
    # extract from image
    chunk = file_info['chunks'][0]
    img_path = os.path.join(meta.images_dir, chunk['image_file'])
    
    img = Image.open(img_path)
    encrypted_data = stg.extract_data(img, chunk['length'])
    print(f"✓ extracted from {chunk['image_file']}")
    
    # decrypt
    decrypted = crypto.decrypt_data(encrypted_data, PASSWORD)
    print(f"✓ decrypted {len(decrypted)} bytes")
    
    # verify checksum
    import hashlib
    checksum = hashlib.sha256(decrypted).hexdigest()
    if checksum == file_info['checksum']:
        print("✓ checksum verified")
    else:
        print("✗ checksum mismatch!")
    
    # save extracted file
    output = "extracted_test.txt"
    with open(output, 'wb') as f:
        f.write(decrypted)
    print(f"✓ saved to {output}")
    
    # show content
    print("\nfile content:")
    print(decrypted.decode('utf-8'))


def test_verify():
    """test integrity verification"""
    print("\n=== testing verify ===")
    meta = MetadataManager()
    files = meta.list_files(PASSWORD)
    
    for fname, info in files.items():
        print(f"verifying {fname}...", end="")
        
        # extract and check
        encrypted_data = bytearray()
        for chunk in info['chunks']:
            img_path = os.path.join(meta.images_dir, chunk['image_file'])
            img = Image.open(img_path)
            chunk_data = stg.extract_data(img, chunk['length'])
            encrypted_data.extend(chunk_data)
        
        decrypted = crypto.decrypt_data(bytes(encrypted_data), PASSWORD)
        
        import hashlib
        checksum = hashlib.sha256(decrypted).hexdigest()
        
        if checksum == info['checksum']:
            print(" ✓ ok")
        else:
            print(" ✗ corrupted")


def test_delete():
    """test deleting a file"""
    print("\n=== testing delete ===")
    meta = MetadataManager()
    
    file_info = meta.get_file(PASSWORD, TEST_FILE)
    if file_info:
        img_name = file_info['chunks'][0]['image_file']
        print(f"deleting {TEST_FILE}")
        print(f"  image: {img_name}")
        
        meta.delete_file(PASSWORD, TEST_FILE, delete_images=False)
        print("✓ deleted (image kept)")
        
        # verify it's gone
        files = meta.list_files(PASSWORD)
        if TEST_FILE not in files:
            print("✓ confirmed removed from index")


def main():
    """run all tests"""
    print("=" * 50)
    print("SFS SYSTEM TEST")
    print("=" * 50)
    print(f"password: {PASSWORD}")
    
    try:
        cleanup()
        test_init()
        test_store()
        test_list()
        test_extract()
        test_verify()
        test_delete()
        
        print("\n" + "=" * 50)
        print("ALL TESTS COMPLETED ✓")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nerror: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
