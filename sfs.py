"""sfs - steganographic file system cli"""
import os
import sys
import hashlib
from pathlib import Path
from PIL import Image
import click

import crypto
import stg
from metadata import MetadataManager


# config
DEFAULT_CHUNK_SIZE = 256 * 1024  # 256kb chunks
DEFAULT_IMAGE_SIZE = (1920, 1080)
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1gb max


def get_password(prompt="enter password: "):
    """get password from user"""
    return click.prompt(prompt, hide_input=True, confirmation_prompt=False)


def calculate_checksum(data: bytes) -> str:
    """calculate sha256 hash"""
    return hashlib.sha256(data).hexdigest()


def format_size(bytes_size: int) -> str:
    """human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


@click.group()
def cli():
    """steganographic file system - hide files in images"""
    pass


@cli.command()
def init():
    """initialize new sfs system"""
    meta = MetadataManager()
    
    if os.path.exists(meta.index_file):
        if not click.confirm("system already exists. reinitialize?", default=False):
            click.echo("cancelled")
            return
    
    password = get_password("create master password: ")
    confirm = get_password("confirm password: ")
    
    if password != confirm:
        click.echo("error: passwords don't match", err=True)
        return
    
    is_valid, msg = crypto.verify_password_strength(password)
    if not is_valid:
        click.echo(f"error: {msg}", err=True)
        return
    
    if len(password) < 12:
        click.echo(f"warning: {msg}")
        if not click.confirm("continue anyway?", default=False):
            return
    
    try:
        meta.initialize(password)
        click.echo(f"✓ system initialized at {meta.storage_dir}")
    except Exception as e:
        click.echo(f"error: {e}", err=True)


@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--carrier', '-c', type=click.Path(exists=True), help='use existing image as carrier')
@click.option('--delete-original', '-d', is_flag=True, help='delete original file after storing')
def store(filename, carrier, delete_original):
    """store a file in the system"""
    meta = MetadataManager()
    password = get_password()
    
    # read file
    file_path = Path(filename)
    file_size = file_path.stat().st_size
    
    if file_size > MAX_FILE_SIZE:
        click.echo(f"error: file too large (max {format_size(MAX_FILE_SIZE)})", err=True)
        return
    
    if file_size == 0:
        click.echo("error: file is empty", err=True)
        return
    
    click.echo(f"reading {file_path.name} ({format_size(file_size)})...")
    
    with open(filename, 'rb') as f:
        file_data = f.read()
    
    # calculate checksum
    checksum = calculate_checksum(file_data)
    
    # encrypt data
    click.echo("encrypting...")
    encrypted_data = crypto.encrypt_data(file_data, password)
    encrypted_size = len(encrypted_data)
    
    # split into chunks
    click.echo("splitting into chunks...")
    chunks_data = []
    offset = 0
    while offset < encrypted_size:
        chunk = encrypted_data[offset:offset + DEFAULT_CHUNK_SIZE]
        chunks_data.append(chunk)
        offset += len(chunk)
    
    click.echo(f"created {len(chunks_data)} chunks")
    
    # embed in images
    chunks_meta = []
    for i, chunk_data in enumerate(chunks_data):
        click.echo(f"embedding chunk {i+1}/{len(chunks_data)}...", nl=False)
        
        # use existing carrier or create new one
        if carrier and i == 0:
            # use provided carrier image for first chunk
            img = Image.open(carrier)
            capacity = stg.get_image_capacity(img.width, img.height)
            if len(chunk_data) > capacity:
                click.echo(f"\nerror: carrier image too small. need {len(chunk_data)} bytes, capacity is {capacity} bytes", err=True)
                click.echo(f"try a larger image (current: {img.width}x{img.height})", err=True)
                return
            click.echo(f" using {carrier}...", nl=False)
        else:
            # create new random carrier
            img = stg.create_carrier_image(len(chunk_data), DEFAULT_IMAGE_SIZE)
        
        # embed data
        stego_img = stg.embed_data(img, chunk_data)
        
        # save image
        img_name = meta.get_next_image_name()
        img_path = os.path.join(meta.images_dir, img_name)
        stego_img.save(img_path, 'PNG')
        
        chunks_meta.append({
            'chunk_id': i,
            'image_file': img_name,
            'offset': 0,
            'length': len(chunk_data)
        })
        
        click.echo(" done")
    
    # update index
    click.echo("updating index...")
    try:
        meta.add_file(
            password,
            file_path.name,
            file_size,
            encrypted_size,
            checksum,
            chunks_meta
        )
        click.echo(f"✓ stored {file_path.name}")
            
            # auto-delete original if requested
            if delete_original:
                try:
                    os.remove(filepath)
                    click.echo(f"✓ deleted original file: {filepath}")
                except Exception as e:
                    click.echo(f"warning: could not delete original: {e}", err=True)
                    

@cli.command()
@click.argument('filename')
@click.option('--output', '-o', default='.', help='output directory')
def extract(filename, output):
    """extract a file from the system"""
    meta = MetadataManager()
    password = get_password()
    
    try:
        # get file info
        file_info = meta.get_file(password, filename)
        if file_info is None:
            click.echo(f"error: file '{filename}' not found", err=True)
            return
        
        click.echo(f"extracting {filename} ({format_size(file_info['original_size'])})...")
        
        # extract chunks
        encrypted_data = bytearray()
        for i, chunk in enumerate(file_info['chunks']):
            click.echo(f"extracting chunk {i+1}/{file_info['chunk_count']}...", nl=False)
            
            img_path = os.path.join(meta.images_dir, chunk['image_file'])
            if not os.path.exists(img_path):
                click.echo(f"\nerror: image {chunk['image_file']} not found", err=True)
                return
            
            img = Image.open(img_path)
            chunk_data = stg.extract_data(img, chunk['length'])
            encrypted_data.extend(chunk_data)
            
            click.echo(" done")
        
        # decrypt
        click.echo("decrypting...")
        decrypted_data = crypto.decrypt_data(bytes(encrypted_data), password)
        
        # verify checksum
        checksum = calculate_checksum(decrypted_data)
        if checksum != file_info['checksum']:
            click.echo("warning: checksum mismatch! file may be corrupted")
            if not click.confirm("save anyway?", default=False):
                return
        
        # write file
        output_path = os.path.join(output, filename)
        if os.path.exists(output_path):
            if not click.confirm(f"{filename} exists. overwrite?", default=False):
                return
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        click.echo(f"✓ extracted to {output_path}")
        
    except crypto.DecryptionError:
        click.echo("error: wrong password or corrupted data", err=True)
    except Exception as e:
        click.echo(f"error: {e}", err=True)


@cli.command(name='list')
@click.option('--search', '-s', help='search for files by name')
@click.option('--verbose', '-v', is_flag=True, help='show detailed info including images')
def list_files(search, verbose):
    """list all stored files"""
    meta = MetadataManager()
    password = get_password()
    
    try:
        files = meta.list_files(password)
        
        if not files:
            click.echo("no files stored")
            return
        
        # filter by search if provided
        if search:
            files = {k: v for k, v in files.items() if search.lower() in k.lower()}
            if not files:
                click.echo(f"no files found matching '{search}'")
                return
        
        click.echo(f"\n{len(files)} file(s) stored:\n")
        
        for filename, info in files.items():
            click.echo(f"  {filename}")
            click.echo(f"    size: {format_size(info['original_size'])}")
            click.echo(f"    chunks: {info['chunk_count']}")
            click.echo(f"    created: {info['created_at'][:19]}")
            
            # show images if verbose
            if verbose:
                click.echo(f"    stored in:")
                for chunk in info['chunks']:
                    click.echo(f"      - {chunk['image_file']} ({format_size(chunk['length'])})")
            else:
                # show first image only
                if info['chunks']:
                    imgs = [c['image_file'] for c in info['chunks']]
                    if len(imgs) == 1:
                        click.echo(f"    image: {imgs[0]}")
                    else:
                        click.echo(f"    images: {imgs[0]} ... {imgs[-1]} ({len(imgs)} total)")
            
            click.echo()
            
    except crypto.DecryptionError:
        click.echo("error: wrong password", err=True)
    except Exception as e:
        click.echo(f"error: {e}", err=True)


@cli.command()
@click.argument('filename')
@click.option('--wipe-images', is_flag=True, help='also delete image files')
def delete(filename, wipe_images):
    """delete a file from the system"""
    meta = MetadataManager()
    password = get_password()
    
    try:
        file_info = meta.get_file(password, filename)
        if file_info is None:
            click.echo(f"error: file '{filename}' not found", err=True)
            return
        
        click.echo(f"file: {filename}")
        click.echo(f"size: {format_size(file_info['original_size'])}")
        click.echo(f"chunks: {file_info['chunk_count']}")
        
        if not click.confirm("\ndelete this file?", default=False):
            click.echo("cancelled")
            return
        
        meta.delete_file(password, filename, wipe_images)
        
        if wipe_images:
            click.echo(f"✓ deleted {filename} and {file_info['chunk_count']} image(s)")
        else:
            click.echo(f"✓ deleted {filename} (images kept for plausibility)")
            
    except crypto.DecryptionError:
        click.echo("error: wrong password", err=True)
    except Exception as e:
        click.echo(f"error: {e}", err=True)


@cli.command()
@click.argument('filename', required=False)
def verify(filename):
    """verify file integrity"""
    meta = MetadataManager()
    password = get_password()
    
    try:
        files = meta.list_files(password)
        
        if not files:
            click.echo("no files to verify")
            return
        
        # filter to single file if specified
        if filename:
            if filename not in files:
                click.echo(f"error: file '{filename}' not found", err=True)
                return
            files = {filename: files[filename]}
        
        click.echo(f"\nverifying {len(files)} file(s)...\n")
        
        ok_count = 0
        corrupt_count = 0
        
        for fname, info in files.items():
            click.echo(f"checking {fname}...", nl=False)
            
            try:
                # extract and verify
                encrypted_data = bytearray()
                for chunk in info['chunks']:
                    img_path = os.path.join(meta.images_dir, chunk['image_file'])
                    if not os.path.exists(img_path):
                        click.echo(f" error: missing image {chunk['image_file']}")
                        corrupt_count += 1
                        continue
                    
                    img = Image.open(img_path)
                    chunk_data = stg.extract_data(img, chunk['length'])
                    encrypted_data.extend(chunk_data)
                
                decrypted_data = crypto.decrypt_data(bytes(encrypted_data), password)
                checksum = calculate_checksum(decrypted_data)
                
                if checksum == info['checksum']:
                    click.echo(" ✓ ok")
                    ok_count += 1
                else:
                    click.echo(" ✗ corrupted")
                    corrupt_count += 1
                    
            except Exception as e:
                click.echo(f" ✗ error: {e}")
                corrupt_count += 1
        
        click.echo(f"\nresults: {ok_count} ok, {corrupt_count} corrupted")
        
    except crypto.DecryptionError:
        click.echo("error: wrong password", err=True)
    except Exception as e:
        click.echo(f"error: {e}", err=True)


if __name__ == '__main__':
    cli()
