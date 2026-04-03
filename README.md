# steganographic file system (sfs)

hide encrypted files inside normal-looking png images

## what it does

sfs combines military-grade encryption with steganography to provide:
- **security**: aes-256-gcm encryption with argon2id key derivation
- **stealth**: lsb steganography hides data in image pixels
- **plausible deniability**: files look like regular photos

## installation

```bash
# install dependencies
pip install -r requirements.txt
```

**dependencies:**
- cryptography >= 41.0.0 (encryption)
- pillow >= 10.0.0 (image processing)
- click >= 8.1.0 (cli interface)
- numpy >= 1.24.0 (array operations)

## quick start

### gui mode (easiest for demos)
```bash
python gui.py
```

graphical interface with buttons for all operations:
- no typing commands
- visual feedback
- progress indicators
- file dialogs

**demo password**: `sfsproject`

### cli mode (advanced)
```bash
python sfs.py init
```
creates `~/.sfs/` directory with encrypted index

**demo password**: `sfsproject`

### 2. store a file
```bash
python sfs.py store myfile.txt
```
encrypts and hides the file in png images

### 3. list stored files
```bash
python sfs.py list
```
shows all files with sizes and metadata

### 4. extract a file
```bash
python sfs.py extract myfile.txt
```
retrieves and decrypts the file

### 5. verify integrity
```bash
python sfs.py verify
```
checks all files for corruption

### 6. delete a file
```bash
python sfs.py delete myfile.txt
```
removes from index (optionally deletes images)

## 📖 documentation

- **[USER_TUTORIAL.md](USER_TUTORIAL.md)** - complete step-by-step guide for using sfs (start here!)
- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** - technical details and architecture
- **[DEMO_GUIDE.md](DEMO_GUIDE.md)** - tips for presenting/demonstrating the system

## usage examples

```bash
# initialize with strong password
python sfs.py init

# store multiple files
python sfs.py store document.pdf
python sfs.py store photo.jpg
python sfs.py store secrets.txt

# see what's stored
python sfs.py list

# extract to different directory
python sfs.py extract document.pdf -o ./extracted/

# verify all files are ok
python sfs.py verify

# delete file and wipe images
python sfs.py delete secrets.txt --wipe-images
```

## how it works

### encryption layer (crypto.py)
1. **key derivation**: argon2id transforms password into 256-bit key
   - memory: 64 mb (gpu-resistant)
   - iterations: 3 (interactive use)
   - parallelism: 4 threads

2. **encryption**: aes-256-gcm encrypts file data
   - confidentiality: data is encrypted
   - authenticity: tampering detected via auth tag
   - overhead: 44 bytes (salt + nonce + tag)

### steganography layer (stg.py)
1. **lsb embedding**: modifies least significant bits in rgb channels
   - 2 bits per channel = 6 bits per pixel
   - capacity: ~1.48 mb per 1920x1080 image
   - minimal visual impact

2. **carrier images**: generates random noise images
   - looks natural
   - provides plausible deniability

### metadata layer (metadata.py)
1. **encrypted index**: tracks all stored files
   - filename, size, checksum
   - chunk locations in images
   - timestamps

2. **chunking**: splits large files across multiple images
   - default: 256 kb chunks
   - automatic image generation

### cli layer (sfs.py)
1. **commands**: init, store, extract, list, delete, verify
2. **password prompts**: secure input (hidden)
3. **progress feedback**: shows operation status

## storage structure

```
~/.sfs/
├── index.enc           # encrypted metadata
└── storage/
    ├── img_0001.png    # carrier image 1
    ├── img_0002.png    # carrier image 2
    └── img_0003.png    # carrier image 3
```

## capacity calculation

with 2 lsb bits per channel:
- **100x100 image**: 7.5 kb
- **1920x1080 image**: 1.48 mb
- **overhead**: ~33% (encryption + steganography)

**example**: 1 mb file needs 1 image (1920x1080)

## security features

### defense in depth
1. **layer 1**: aes-256-gcm encryption (confidentiality + integrity)
2. **layer 2**: lsb steganography (concealment)
3. **layer 3**: encrypted metadata (obscures structure)

### key benefits
- encrypted volumes are suspicious → images look normal
- no metadata leakage → everything encrypted
- tamper detection → gcm authentication
- plausible deniability → can mix with real photos

## testing

```bash
# test crypto module
python crypto.py

# test steganography module
python stg.py

# test complete system
python test_system.py
```

all modules have built-in tests that verify functionality.

## limitations

- **max file size**: 1 gb (configurable)
- **image format**: png only (lossless required)
- **single user**: one password per system
- **local storage**: no cloud sync

## project structure

```
sfs/
├── crypto.py           # encryption/decryption
├── stg.py              # steganography embed/extract
├── metadata.py         # index management
├── sfs.py              # cli application
├── gui.py              # graphical interface (new!)
├── test_system.py      # integration tests
├── requirements.txt    # dependencies
├── README.md           # this file
├── DEMO_GUIDE.md       # demo instructions
└── PROJECT_DOCUMENTATION.md  # full technical docs
```

## technical details

### encryption
- **algorithm**: aes-256-gcm
- **mode**: galois/counter mode (authenticated encryption)
- **key derivation**: argon2id
- **salt**: 16 bytes random
- **nonce**: 12 bytes random per encryption

### steganography
- **method**: lsb (least significant bit)
- **bits**: 2 per rgb channel
- **capacity**: width × height × 6 bits / 8
- **format**: png (lossless)

### metadata format
```json
{
  "version": 1,
  "created_at": "2026-02-11T...",
  "last_modified": "2026-02-11T...",
  "files": {
    "example.txt": {
      "original_size": 1024,
      "encrypted_size": 1068,
      "chunk_count": 1,
      "chunks": [...],
      "checksum": "sha256...",
      "created_at": "2026-02-11T..."
    }
  }
}
```

## demonstration tips

for presentations/demos:
1. **use gui mode**: `python gui.py` (much easier!)
2. use password: `sfsproject`
3. test with small text files first
4. show the images look normal (click "open storage")
5. demonstrate wrong password fails
6. verify checksums match

### gui features:
- visual status indicators
- file selection dialogs
- progress bars for operations
- clear output log
- one-click storage access

## academic context

this project demonstrates:
- **applied cryptography**: aes, argon2, authentication
- **steganography techniques**: lsb embedding
- **file system concepts**: chunking, metadata, allocation
- **security architecture**: defense in depth

ideal for:
- information security courses
- cryptography projects
- computer science capstone
- cybersecurity demonstrations

## troubleshooting

**"index not found" error**
```bash
python sfs.py init  # initialize first
```

**"wrong password" error**
- password is case-sensitive
- use same password for all operations

**"data too large" error**
- file exceeds capacity
- reduce file size or modify config

**"image not found" error**
- don't manually delete images from ~/.sfs/storage/
- use `sfs delete` command instead

## license

educational/academic project - see full documentation for details

## author

semester project - steganographic file system implementation
