"""metadata manager - handles file index operations"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import crypto


class MetadataManager:
    """manages encrypted file index"""
    
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            storage_dir = os.path.join(Path.home(), '.sfs')
        
        self.storage_dir = storage_dir
        self.index_file = os.path.join(storage_dir, 'index.enc')
        self.images_dir = os.path.join(storage_dir, 'storage')
        
    def initialize(self, password: str):
        """create new empty index"""
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        empty_index = {
            'version': 1,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'files': {}
        }
        
        self._save_index(empty_index, password)
        
    def _save_index(self, index: Dict, password: str):
        """encrypt and save index to disk"""
        json_data = json.dumps(index, indent=2)
        encrypted = crypto.encrypt_data(json_data.encode('utf-8'), password)
        
        with open(self.index_file, 'wb') as f:
            f.write(encrypted)
            
    def _load_index(self, password: str) -> Dict:
        """load and decrypt index from disk"""
        if not os.path.exists(self.index_file):
            raise FileNotFoundError("index not found, run 'sfs init' first")
        
        with open(self.index_file, 'rb') as f:
            encrypted = f.read()
        
        decrypted = crypto.decrypt_data(encrypted, password)
        return json.loads(decrypted.decode('utf-8'))
        
    def add_file(self, password: str, filename: str, original_size: int, 
                 encrypted_size: int, checksum: str, chunks: List[Dict]):
        """add file entry to index"""
        index = self._load_index(password)
        
        if filename in index['files']:
            raise ValueError(f"file '{filename}' already exists")
        
        index['files'][filename] = {
            'original_size': original_size,
            'encrypted_size': encrypted_size,
            'chunk_count': len(chunks),
            'chunks': chunks,
            'checksum': checksum,
            'created_at': datetime.now().isoformat(),
            'modified_at': datetime.now().isoformat()
        }
        
        index['last_modified'] = datetime.now().isoformat()
        self._save_index(index, password)
        
    def get_file(self, password: str, filename: str) -> Optional[Dict]:
        """get file entry from index"""
        index = self._load_index(password)
        return index['files'].get(filename)
        
    def list_files(self, password: str) -> Dict:
        """list all files in index"""
        index = self._load_index(password)
        return index['files']
        
    def delete_file(self, password: str, filename: str, delete_images: bool = False):
        """remove file entry from index"""
        index = self._load_index(password)
        
        if filename not in index['files']:
            raise ValueError(f"file '{filename}' not found")
        
        file_info = index['files'][filename]
        
        # optionally delete image files
        if delete_images:
            for chunk in file_info['chunks']:
                img_path = os.path.join(self.images_dir, chunk['image_file'])
                if os.path.exists(img_path):
                    os.remove(img_path)
        
        del index['files'][filename]
        index['last_modified'] = datetime.now().isoformat()
        self._save_index(index, password)
        
    def get_next_image_name(self) -> str:
        """generate next available image filename"""
        existing = os.listdir(self.images_dir) if os.path.exists(self.images_dir) else []
        img_numbers = []
        
        for fname in existing:
            if fname.startswith('img_') and fname.endswith('.png'):
                try:
                    num = int(fname[4:-4])
                    img_numbers.append(num)
                except:
                    pass
        
        next_num = max(img_numbers) + 1 if img_numbers else 1
        return f"img_{next_num:04d}.png"
