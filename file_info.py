"""utility to show detailed file info"""
import sys
from metadata import MetadataManager
import crypto
from pathlib import Path


def show_file_info(filename, password):
    """show detailed information about a stored file"""
    meta = MetadataManager()
    
    try:
        file_info = meta.get_file(password, filename)
        if not file_info:
            print(f"error: file '{filename}' not found")
            return
        
        print(f"\n{'='*60}")
        print(f"FILE: {filename}")
        print(f"{'='*60}\n")
        
        print(f"original size:    {file_info['original_size']:,} bytes")
        print(f"encrypted size:   {file_info['encrypted_size']:,} bytes")
        print(f"overhead:         {file_info['encrypted_size'] - file_info['original_size']} bytes")
        print(f"checksum:         {file_info['checksum'][:32]}...")
        print(f"chunks:           {file_info['chunk_count']}")
        print(f"created:          {file_info['created_at']}")
        print(f"modified:         {file_info['modified_at']}")
        
        print(f"\n{'='*60}")
        print(f"STORAGE DETAILS")
        print(f"{'='*60}\n")
        
        storage_dir = meta.images_dir
        total_storage = 0
        
        for i, chunk in enumerate(file_info['chunks'], 1):
            img_path = Path(storage_dir) / chunk['image_file']
            if img_path.exists():
                img_size = img_path.stat().st_size
                total_storage += img_size
                status = "✓ exists"
            else:
                img_size = 0
                status = "✗ missing"
            
            print(f"chunk {i}:")
            print(f"  image:     {chunk['image_file']}")
            print(f"  data size: {chunk['length']:,} bytes")
            print(f"  image size: {img_size:,} bytes")
            print(f"  status:    {status}")
            print()
        
        print(f"{'='*60}")
        print(f"total storage used: {total_storage:,} bytes")
        print(f"efficiency: {(file_info['original_size'] / total_storage * 100):.1f}%")
        print(f"{'='*60}\n")
        
    except crypto.DecryptionError:
        print("error: wrong password")
    except Exception as e:
        print(f"error: {e}")


def show_all_mappings(password):
    """show file-to-image mappings for all files"""
    meta = MetadataManager()
    
    try:
        files = meta.list_files(password)
        
        if not files:
            print("no files stored")
            return
        
        print(f"\n{'='*60}")
        print(f"FILE TO IMAGE MAPPING")
        print(f"{'='*60}\n")
        print(f"total files: {len(files)}\n")
        
        # create reverse mapping: image -> files
        image_map = {}
        for filename, info in files.items():
            for chunk in info['chunks']:
                img = chunk['image_file']
                if img not in image_map:
                    image_map[img] = []
                image_map[img].append(filename)
        
        # show file -> images
        print("files -> images:")
        print("-" * 60)
        for filename, info in sorted(files.items()):
            images = [c['image_file'] for c in info['chunks']]
            if len(images) == 1:
                print(f"  {filename}")
                print(f"    → {images[0]}")
            else:
                print(f"  {filename}")
                for img in images:
                    print(f"    → {img}")
            print()
        
        # show images -> files
        print("\nimages -> files:")
        print("-" * 60)
        for img, filenames in sorted(image_map.items()):
            print(f"  {img}")
            for fname in filenames:
                print(f"    ← {fname}")
            print()
        
        print(f"{'='*60}\n")
        
    except crypto.DecryptionError:
        print("error: wrong password")
    except Exception as e:
        print(f"error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage:")
        print("  python file_info.py <filename>        # show detailed file info")
        print("  python file_info.py --all             # show all mappings")
        print()
        print("you will be prompted for password")
        sys.exit(1)
    
    import getpass
    password = getpass.getpass("enter password: ")
    
    if sys.argv[1] == "--all":
        show_all_mappings(password)
    else:
        show_file_info(sys.argv[1], password)
