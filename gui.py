"""sfs gui - graphical interface for steganographic file system"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import os
from pathlib import Path
from PIL import Image, ImageTk
import threading

import crypto
import stg
from metadata import MetadataManager


class SFSGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("steganographic file system")
        self.root.geometry("800x600")
        
        self.meta = MetadataManager()
        self.password = None
        self.is_initialized = os.path.exists(self.meta.index_file)
        
        # create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # configure grid weight
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        self.create_widgets()
        self.update_status()
        
    def create_widgets(self):
        # title
        title = ttk.Label(self.main_frame, text="steganographic file system", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # status frame
        status_frame = ttk.LabelFrame(self.main_frame, text="status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="not initialized")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.password_label = ttk.Label(status_frame, text="password: not set")
        self.password_label.grid(row=0, column=1, sticky=tk.E, padx=20)
        
        # password frame
        pwd_frame = ttk.LabelFrame(self.main_frame, text="authentication", padding="10")
        pwd_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(pwd_frame, text="password:").grid(row=0, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(pwd_frame, show="*", width=30)
        self.password_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(pwd_frame, text="set password", command=self.set_password).grid(
            row=0, column=2, padx=5)
        ttk.Button(pwd_frame, text="initialize system", command=self.initialize_system).grid(
            row=0, column=3, padx=5)
        
        # settings frame
        settings_frame = ttk.LabelFrame(self.main_frame, text="settings", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.auto_delete_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="auto-delete original files after storing", 
                       variable=self.auto_delete_var).grid(row=0, column=0, sticky=tk.W)
        
        # operations frame
        ops_frame = ttk.LabelFrame(self.main_frame, text="operations", padding="10")
        ops_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(ops_frame, text="store file", command=self.store_file, width=15).grid(
            row=0, column=0, padx=5, pady=5)
        ttk.Button(ops_frame, text="store in image", command=self.store_with_carrier, width=15).grid(
            row=0, column=3, padx=5, pady=5)
        ttk.Button(ops_frame, text="extract file", command=self.extract_file, width=15).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Button(ops_frame, text="list files", command=self.list_files, width=15).grid(
            row=0, column=2, padx=5, pady=5)
        ttk.Button(ops_frame, text="search files", command=self.search_files, width=15).grid(
            row=1, column=3, padx=5, pady=5)
        ttk.Button(ops_frame, text="delete file", command=self.delete_file, width=15).grid(
            row=1, column=0, padx=5, pady=5)
        ttk.Button(ops_frame, text="verify integrity", command=self.verify_files, width=15).grid(
            row=1, column=1, padx=5, pady=5)
        ttk.Button(ops_frame, text="open storage", command=self.open_storage, width=15).grid(
            row=1, column=2, padx=5, pady=5)
        
        # file browser and preview frame
        browser_frame = ttk.LabelFrame(self.main_frame, text="file browser & preview", padding="10")
        browser_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        browser_frame.columnconfigure(1, weight=1)
        browser_frame.rowconfigure(0, weight=1)
        
        # left side - file list
        list_container = ttk.Frame(browser_frame)
        list_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        ttk.Label(list_container, text="stored files:").pack()
        
        self.file_listbox = tk.Listbox(list_container, width=30)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        ttk.Button(list_container, text="refresh", command=self.refresh_file_list).pack(pady=5)
        
        # right side - preview area
        preview_container = ttk.Frame(browser_frame)
        preview_container.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_container.columnconfigure(0, weight=1)
        preview_container.rowconfigure(1, weight=1)
        
        self.preview_label = ttk.Label(preview_container, text="select a file to preview")
        self.preview_label.pack()
        
        self.preview_text = scrolledtext.ScrolledText(preview_container, height=10, width=60)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # image preview label (hidden by default)
        self.preview_image_label = ttk.Label(preview_container)
        self.preview_image_label.pack()
        self.preview_image_label.pack_forget()
        
        # output frame
        output_frame = ttk.LabelFrame(self.main_frame, text="output", padding="10")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(5, weight=1)
        self.main_frame.rowconfigure(6, weight=1)
        
        # progress bar
        self.progress = ttk.Progressbar(self.main_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # refresh file list on startup
        self.root.after(100, self.refresh_file_list)
        
    def log(self, message):
        """add message to output"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update()
        
    def clear_log(self):
        """clear output"""
        self.output_text.delete(1.0, tk.END)
        
    def update_status(self):
        """update status labels"""
        if self.is_initialized:
            self.status_label.config(text=f"✓ initialized at {self.meta.storage_dir}")
        else:
            self.status_label.config(text="✗ not initialized")
            
        if self.password:
            self.password_label.config(text="✓ password set")
        else:
            self.password_label.config(text="✗ password not set")
            
    def set_password(self):
        """set the password from entry"""
        pwd = self.password_entry.get()
        if not pwd:
            messagebox.showerror("error", "please enter a password")
            return
            
        self.password = pwd
        self.update_status()
        self.log(f"password set")
        
    def initialize_system(self):
        """initialize new sfs system"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        if self.is_initialized:
            if not messagebox.askyesno("confirm", "system already exists. reinitialize?"):
                return
                
        try:
            self.log("initializing system...")
            self.meta.initialize(self.password)
            self.is_initialized = True
            self.update_status()
            self.log("✓ system initialized successfully")
            messagebox.showinfo("success", "system initialized")
        except Exception as e:
            self.log(f"✗ error: {e}")
            messagebox.showerror("error", str(e))
            
    def store_file(self):
        """store a file"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        if not self.is_initialized:
            messagebox.showerror("error", "system not initialized")
            return
            
        filepath = filedialog.askopenfilename(title="select file to store")
        if not filepath:
            return
            
        def store_thread():
            try:
                self.progress.start()
                self.clear_log()
                
                file_path = Path(filepath)
                file_size = file_path.stat().st_size
                
                self.log(f"storing: {file_path.name}")
                self.log(f"size: {self.format_size(file_size)}")
                
                # read file
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                # calculate checksum
                import hashlib
                checksum = hashlib.sha256(file_data).hexdigest()
                
                # encrypt
                self.log("encrypting...")
                encrypted_data = crypto.encrypt_data(file_data, self.password)
                
                # split into chunks
                chunk_size = 256 * 1024
                chunks_data = []
                offset = 0
                while offset < len(encrypted_data):
                    chunk = encrypted_data[offset:offset + chunk_size]
                    chunks_data.append(chunk)
                    offset += len(chunk)
                
                self.log(f"split into {len(chunks_data)} chunks")
                
                # embed in images
                chunks_meta = []
                for i, chunk_data in enumerate(chunks_data):
                    self.log(f"embedding chunk {i+1}/{len(chunks_data)}...")
                    
                    img = stg.create_carrier_image(len(chunk_data), (1920, 1080))
                    stego_img = stg.embed_data(img, chunk_data)
                    
                    img_name = self.meta.get_next_image_name()
                    img_path = os.path.join(self.meta.images_dir, img_name)
                    stego_img.save(img_path, 'PNG')
                    
                    chunks_meta.append({
                        'chunk_id': i,
                        'image_file': img_name,
                        'offset': 0,
                        'length': len(chunk_data)
                    })
                
                # update index
                self.log("updating index...")
                self.meta.add_file(
                    self.password,
                    file_path.name,
                    file_size,
                    len(encrypted_data),
                    checksum,
                    chunks_meta
                )
                
                self.log(f"✓ stored {file_path.name} successfully")
                
                # refresh file list
                self.root.after(100, self.refresh_file_list)
                
                # auto-delete original if enabled
                if self.auto_delete_var.get():
                    try:
                        os.remove(filepath)
                        self.log(f"✓ deleted original file: {file_path.name}")
                        messagebox.showinfo("success", 
                            f"file stored and original deleted\n\nfile: {file_path.name}")
                    except Exception as e:
                        self.log(f"⚠ warning: could not delete original: {e}")
                        messagebox.showwarning("partial success", 
                            f"file stored successfully but could not delete original:\n{e}")
                else:
                    messagebox.showinfo("success", f"file stored: {file_path.name}")
                
            except Exception as e:
                self.log(f"✗ error: {e}")
                messagebox.showerror("error", str(e))
            finally:
                self.progress.stop()
        
        threading.Thread(target=store_thread, daemon=True).start()
        
    def store_with_carrier(self):
        """store file using existing carrier image"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        if not self.is_initialized:
            messagebox.showerror("error", "system not initialized")
            return
            
        # select carrier image first
        carrier_path = filedialog.askopenfilename(
            title="select carrier image (jpg/png)",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if not carrier_path:
            return
            
        # validate carrier image
        try:
            carrier_img = Image.open(carrier_path)
            capacity = stg.get_image_capacity(carrier_img.width, carrier_img.height)
            carrier_img.close()
        except Exception as e:
            messagebox.showerror("error", f"invalid image: {e}")
            return
            
        # now select file to hide
        filepath = filedialog.askopenfilename(title="select file to hide in image")
        if not filepath:
            return
            
        def store_thread():
            try:
                self.progress.start()
                self.clear_log()
                
                file_path = Path(filepath)
                file_size = file_path.stat().st_size
                
                self.log(f"storing: {file_path.name}")
                self.log(f"size: {self.format_size(file_size)}")
                self.log(f"carrier: {Path(carrier_path).name} ({capacity} bytes capacity)")
                
                # read file
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                # calculate checksum
                import hashlib
                checksum = hashlib.sha256(file_data).hexdigest()
                
                # encrypt
                self.log("encrypting...")
                encrypted_data = crypto.encrypt_data(file_data, self.password)
                encrypted_size = len(encrypted_data)
                
                # check if fits in carrier
                if encrypted_size > capacity:
                    self.log(f"✗ error: encrypted data ({encrypted_size} bytes) too large for carrier ({capacity} bytes)")
                    self.log(f"carrier image size: {carrier_img.width}x{carrier_img.height}")
                    self.log(f"need larger image or smaller file")
                    messagebox.showerror("error", 
                        f"file too large for this carrier image!\n\n"
                        f"encrypted size: {self.format_size(encrypted_size)}\n"
                        f"carrier capacity: {self.format_size(capacity)}\n\n"
                        f"use a larger image or smaller file")
                    return
                
                self.log(f"✓ file fits in carrier")
                
                # split into chunks
                chunk_size = min(capacity, 256 * 1024)
                chunks_data = []
                offset = 0
                while offset < encrypted_size:
                    chunk = encrypted_data[offset:offset + chunk_size]
                    chunks_data.append(chunk)
                    offset += len(chunk)
                
                self.log(f"split into {len(chunks_data)} chunks")
                
                # embed in images
                chunks_meta = []
                for i, chunk_data in enumerate(chunks_data):
                    self.log(f"embedding chunk {i+1}/{len(chunks_data)}...")
                    
                    if i == 0:
                        # use carrier for first chunk
                        img = Image.open(carrier_path)
                        self.log(f"  using your image: {Path(carrier_path).name}")
                    else:
                        # create new for additional chunks
                        img = stg.create_carrier_image(len(chunk_data), (1920, 1080))
                        self.log(f"  created additional carrier")
                    
                    stego_img = stg.embed_data(img, chunk_data)
                    
                    img_name = self.meta.get_next_image_name()
                    img_path = os.path.join(self.meta.images_dir, img_name)
                    stego_img.save(img_path, 'PNG')
                    
                    chunks_meta.append({
                        'chunk_id': i,
                        'image_file': img_name,
                        'offset': 0,
                        'length': len(chunk_data)
                    })
                
                # update index
                self.log("updating index...")
                self.meta.add_file(
                    self.password,
                    file_path.name,
                    file_size,
                    encrypted_size,
                    checksum,
                    chunks_meta
                )
                
                self.log(f"✓ stored {file_path.name} in your image")
                
                # refresh file list
                self.root.after(100, self.refresh_file_list)
                
                # auto-delete original if enabled
                if self.auto_delete_var.get():
                    try:
                        os.remove(filepath)
                        self.log(f"✓ deleted original file: {file_path.name}")
                        messagebox.showinfo("success", 
                            f"file hidden and original deleted!\n\n"
                            f"file: {file_path.name}\n"
                            f"carrier: {Path(carrier_path).name}\n"
                            f"saved as: {chunks_meta[0]['image_file']}")
                    except Exception as e:
                        self.log(f"⚠ warning: could not delete original: {e}")
                        messagebox.showwarning("partial success", 
                            f"file stored but could not delete original:\n{e}")
                else:
                    messagebox.showinfo("success", 
                        f"file hidden in your image!\n\n"
                        f"file: {file_path.name}\n"
                        f"carrier: {Path(carrier_path).name}\n"
                        f"saved as: {chunks_meta[0]['image_file']}")
                
            except Exception as e:
                self.log(f"✗ error: {e}")
                messagebox.showerror("error", str(e))
            finally:
                self.progress.stop()
        
        threading.Thread(target=store_thread, daemon=True).start()
        
    def extract_file(self):
        """extract a file"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        if not self.is_initialized:
            messagebox.showerror("error", "system not initialized")
            return
            
        try:
            files = self.meta.list_files(self.password)
            if not files:
                messagebox.showinfo("info", "no files stored")
                return
                
            # create selection dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("select file to extract")
            dialog.geometry("400x300")
            
            ttk.Label(dialog, text="select file:").pack(pady=10)
            
            listbox = tk.Listbox(dialog)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for filename in files.keys():
                listbox.insert(tk.END, filename)
                
            def extract_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showerror("error", "no file selected")
                    return
                    
                filename = listbox.get(selection[0])
                dialog.destroy()
                
                output_dir = filedialog.askdirectory(title="select output directory")
                if not output_dir:
                    return
                    
                def extract_thread():
                    try:
                        self.progress.start()
                        self.clear_log()
                        
                        file_info = self.meta.get_file(self.password, filename)
                        self.log(f"extracting: {filename}")
                        self.log(f"size: {self.format_size(file_info['original_size'])}")
                        
                        # extract chunks
                        encrypted_data = bytearray()
                        for i, chunk in enumerate(file_info['chunks']):
                            self.log(f"extracting chunk {i+1}/{file_info['chunk_count']}...")
                            
                            img_path = os.path.join(self.meta.images_dir, chunk['image_file'])
                            img = Image.open(img_path)
                            chunk_data = stg.extract_data(img, chunk['length'])
                            encrypted_data.extend(chunk_data)
                        
                        # decrypt
                        self.log("decrypting...")
                        decrypted_data = crypto.decrypt_data(bytes(encrypted_data), self.password)
                        
                        # verify checksum
                        import hashlib
                        checksum = hashlib.sha256(decrypted_data).hexdigest()
                        if checksum != file_info['checksum']:
                            self.log("⚠ warning: checksum mismatch!")
                            if not messagebox.askyesno("warning", "checksum mismatch! save anyway?"):
                                return
                        
                        # write file
                        output_path = os.path.join(output_dir, filename)
                        with open(output_path, 'wb') as f:
                            f.write(decrypted_data)
                        
                        self.log(f"✓ extracted to {output_path}")
                        messagebox.showinfo("success", f"file extracted to:\n{output_path}")
                        
                    except Exception as e:
                        self.log(f"✗ error: {e}")
                        messagebox.showerror("error", str(e))
                    finally:
                        self.progress.stop()
                
                threading.Thread(target=extract_thread, daemon=True).start()
            
            ttk.Button(dialog, text="extract", command=extract_selected).pack(pady=10)
            
        except crypto.DecryptionError:
            messagebox.showerror("error", "wrong password")
        except Exception as e:
            messagebox.showerror("error", str(e))
            
    def list_files(self):
        """list all stored files"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        if not self.is_initialized:
            messagebox.showerror("error", "system not initialized")
            return
            
        try:
            self.clear_log()
            files = self.meta.list_files(self.password)
            
            if not files:
                self.log("no files stored")
                return
                
            self.log(f"{len(files)} file(s) stored:\n")
            
            for filename, info in files.items():
                self.log(f"  {filename}")
                self.log(f"    size: {self.format_size(info['original_size'])}")
                self.log(f"    chunks: {info['chunk_count']}")
                self.log(f"    created: {info['created_at'][:19]}")
                
                # show which images contain this file
                if info['chunks']:
                    imgs = [c['image_file'] for c in info['chunks']]
                    if len(imgs) == 1:
                        self.log(f"    stored in: {imgs[0]}")
                    else:
                        self.log(f"    stored in: {imgs[0]} ... {imgs[-1]} ({len(imgs)} images)")
                
                self.log("")
                
        except crypto.DecryptionError:
            messagebox.showerror("error", "wrong password")
        except Exception as e:
            messagebox.showerror("error", str(e))
            
    def search_files(self):
        """search for files by name"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        if not self.is_initialized:
            messagebox.showerror("error", "system not initialized")
            return
            
        # get search term
        search_term = tk.simpledialog.askstring("search files", "enter search term:")
        if not search_term:
            return
            
        try:
            self.clear_log()
            all_files = self.meta.list_files(self.password)
            
            if not all_files:
                self.log("no files stored")
                return
            
            # filter files
            files = {k: v for k, v in all_files.items() if search_term.lower() in k.lower()}
            
            if not files:
                self.log(f"no files found matching '{search_term}'")
                self.log(f"\ntotal files: {len(all_files)}")
                return
                
            self.log(f"found {len(files)} file(s) matching '{search_term}':\n")
            
            for filename, info in files.items():
                self.log(f"  {filename}")
                self.log(f"    size: {self.format_size(info['original_size'])}")
                self.log(f"    chunks: {info['chunk_count']}")
                self.log(f"    created: {info['created_at'][:19]}")
                
                # show images with details
                if info['chunks']:
                    self.log(f"    stored in:")
                    for chunk in info['chunks']:
                        self.log(f"      - {chunk['image_file']} ({self.format_size(chunk['length'])})")
                
                self.log("")
                
        except crypto.DecryptionError:
            messagebox.showerror("error", "wrong password")
        except Exception as e:
            messagebox.showerror("error", str(e))
            
    def delete_file(self):
        """delete a file"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        if not self.is_initialized:
            messagebox.showerror("error", "system not initialized")
            return
            
        try:
            files = self.meta.list_files(self.password)
            if not files:
                messagebox.showinfo("info", "no files stored")
                return
                
            # create selection dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("select file to delete")
            dialog.geometry("400x300")
            
            ttk.Label(dialog, text="select file:").pack(pady=10)
            
            listbox = tk.Listbox(dialog)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for filename in files.keys():
                listbox.insert(tk.END, filename)
                
            wipe_var = tk.BooleanVar()
            ttk.Checkbutton(dialog, text="also delete images", variable=wipe_var).pack()
                
            def delete_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showerror("error", "no file selected")
                    return
                    
                filename = listbox.get(selection[0])
                
                if not messagebox.askyesno("confirm", f"delete '{filename}'?"):
                    return
                    
                try:
                    self.meta.delete_file(self.password, filename, wipe_var.get())
                    self.log(f"✓ deleted {filename}")
                    messagebox.showinfo("success", f"file deleted: {filename}")
                    dialog.destroy()
                    self.refresh_file_list()
                except Exception as e:
                    messagebox.showerror("error", str(e))
            
            ttk.Button(dialog, text="delete", command=delete_selected).pack(pady=10)
            
        except crypto.DecryptionError:
            messagebox.showerror("error", "wrong password")
        except Exception as e:
            messagebox.showerror("error", str(e))
            
    def verify_files(self):
        """verify file integrity"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        if not self.is_initialized:
            messagebox.showerror("error", "system not initialized")
            return
            
        def verify_thread():
            try:
                self.progress.start()
                self.clear_log()
                
                files = self.meta.list_files(self.password)
                
                if not files:
                    self.log("no files to verify")
                    return
                    
                self.log(f"verifying {len(files)} file(s)...\n")
                
                ok_count = 0
                corrupt_count = 0
                
                for fname, info in files.items():
                    self.log(f"checking {fname}...")
                    
                    try:
                        encrypted_data = bytearray()
                        for chunk in info['chunks']:
                            img_path = os.path.join(self.meta.images_dir, chunk['image_file'])
                            img = Image.open(img_path)
                            chunk_data = stg.extract_data(img, chunk['length'])
                            encrypted_data.extend(chunk_data)
                        
                        decrypted_data = crypto.decrypt_data(bytes(encrypted_data), self.password)
                        
                        import hashlib
                        checksum = hashlib.sha256(decrypted_data).hexdigest()
                        
                        if checksum == info['checksum']:
                            self.log("  ✓ ok")
                            ok_count += 1
                        else:
                            self.log("  ✗ corrupted")
                            corrupt_count += 1
                            
                    except Exception as e:
                        self.log(f"  ✗ error: {e}")
                        corrupt_count += 1
                
                self.log(f"\nresults: {ok_count} ok, {corrupt_count} corrupted")
                messagebox.showinfo("verification complete", 
                                  f"{ok_count} ok\n{corrupt_count} corrupted")
                
            except crypto.DecryptionError:
                messagebox.showerror("error", "wrong password")
            except Exception as e:
                self.log(f"✗ error: {e}")
                messagebox.showerror("error", str(e))
            finally:
                self.progress.stop()
        
        threading.Thread(target=verify_thread, daemon=True).start()
        
    def open_storage(self):
        """open storage directory in explorer"""
        if os.path.exists(self.meta.images_dir):
            os.startfile(self.meta.images_dir)
        else:
            messagebox.showinfo("info", "storage directory does not exist yet")
            
    def refresh_file_list(self):
        """refresh the file list in browser"""
        self.file_listbox.delete(0, tk.END)
        
        if not self.password or not self.is_initialized:
            return
            
        try:
            files = self.meta.list_files(self.password)
            for filename in files.keys():
                self.file_listbox.insert(tk.END, filename)
        except:
            pass
            
    def on_file_select(self, event):
        """handle file selection for preview"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
            
        filename = self.file_listbox.get(selection[0])
        self.preview_file(filename)
        
    def preview_file(self, filename):
        """extract and preview selected file"""
        if not self.password:
            messagebox.showerror("error", "please set password first")
            return
            
        def preview_thread():
            try:
                self.progress.start()
                
                # get file info
                file_info = self.meta.get_file(self.password, filename)
                
                # update preview label
                self.preview_label.config(
                    text=f"{filename} ({self.format_size(file_info['original_size'])})")
                
                # extract chunks
                encrypted_data = bytearray()
                for chunk in file_info['chunks']:
                    img_path = os.path.join(self.meta.images_dir, chunk['image_file'])
                    img = Image.open(img_path)
                    chunk_data = stg.extract_data(img, chunk['length'])
                    encrypted_data.extend(chunk_data)
                
                # decrypt
                decrypted_data = crypto.decrypt_data(bytes(encrypted_data), self.password)
                
                # clear previous preview
                self.preview_text.delete(1.0, tk.END)
                self.preview_image_label.pack_forget()
                
                # determine file type and preview
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ['.txt', '.py', '.md', '.json', '.xml', '.html', '.css', '.js']:
                    # text file preview
                    try:
                        text_content = decrypted_data.decode('utf-8')
                        self.preview_text.insert(1.0, text_content)
                    except:
                        self.preview_text.insert(1.0, "[binary file - cannot display as text]")
                        
                elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                    # image preview
                    try:
                        from io import BytesIO
                        img = Image.open(BytesIO(decrypted_data))
                        
                        # resize if too large
                        max_size = (400, 400)
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        photo = ImageTk.PhotoImage(img)
                        self.preview_image_label.config(image=photo)
                        self.preview_image_label.image = photo
                        self.preview_image_label.pack()
                        
                        self.preview_text.insert(1.0, 
                            f"image dimensions: {img.width}x{img.height}\n"
                            f"format: {img.format}\n"
                            f"mode: {img.mode}")
                    except Exception as e:
                        self.preview_text.insert(1.0, f"[error displaying image: {e}]")
                        
                else:
                    # show file info for other types
                    self.preview_text.insert(1.0, 
                        f"file type: {ext if ext else 'unknown'}\n"
                        f"size: {self.format_size(file_info['original_size'])}\n"
                        f"chunks: {file_info['chunk_count']}\n"
                        f"created: {file_info['created_at'][:19]}\n\n"
                        f"stored in images:\n")
                    
                    for chunk in file_info['chunks']:
                        self.preview_text.insert(tk.END, 
                            f"  - {chunk['image_file']} ({self.format_size(chunk['length'])})\n")
                    
                    # show hex preview for binary
                    self.preview_text.insert(tk.END, "\nhex preview (first 256 bytes):\n")
                    hex_preview = decrypted_data[:256].hex()
                    for i in range(0, len(hex_preview), 32):
                        self.preview_text.insert(tk.END, hex_preview[i:i+32] + "\n")
                
            except crypto.DecryptionError:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, "[decryption failed - wrong password?]")
            except Exception as e:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, f"[error: {e}]")
            finally:
                self.progress.stop()
        
        threading.Thread(target=preview_thread, daemon=True).start()
    
    def format_size(self, bytes_size):
        """human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"


def main():
    root = tk.Tk()
    app = SFSGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
