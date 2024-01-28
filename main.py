from functools import cache
import shutil
import os
import time
import matplotlib.pyplot as plt
import numpy as np
from ctypes import windll
from string import ascii_uppercase
import plotly.graph_objects as go

os.chdir("E:/")
total, used, free = shutil.disk_usage("/")
x = "."
MiB = 1024**2
GiB = 1024**3
GB = 1000**3
MB = 1000**2
categories = {
    "music": [
        ".wav", ".mp3", "aac", ".flac", ".ogg", ".m4a", ".wma", ".dts",
        ".ac3", ".aiff", ".alac", ".amr", ".ape", ".au", ".awb", ".dct",
        ".gsm", ".iklax", ".ivs", ".mka", ".mlp", ".mpc", ".msv", ".ra",
        ".rm", ".tta", ".vqf",
        ],
    "image": [
        ".jpg", ".jpeg", ".jpe", ".jif", ".jfif", ".jfi", ".png", ".tiff",
        ".gif", ".webp", ".ai", ".pdf", ".psd", ".svg", ".eps", ".bmp", 
        ".tif", "indd", ".ico",
        ],
    "video": [
        ".mp4", ".mkv", ".flv", ".3gp", ".webm", ".vob", ".ogv", "drc", 
        ".mng", ".avi", ".mov", ".qt", ".wmv", ".yuv", ".rmvb", ".f4b", 
        ".asf", ".amv", ".m4p", ".m4v", ".mpg", ".mp2", ".mpeg", ".mpe", 
        ".mpv", ".svi", ".3g2", ".mxf", ".roq", ".nsv", ".f4v", ".f4p", 
        ".f4a",
        ],
    "app": [
        ".exe", ".msi", ".appx", ".gadget", ".bat", ".sh", ".ps1", ".vb",
        ".reg", ".wsf", ".dll", ".mr", ".assets", ".ress", ".pkg", ".tiger",
        ".rpf", ".pak", ".nefs", ".dat", ".bundle", ".resource", ".wad",
        ".upk", ".hipfb", ".cubin", ".fatbin", ".ptx", ".pdb", ".ucas",
        ".utoc", ".blk", ".pck", ".usm", ".block", ".bsp",
        ],
    "ai": [".safetensors", ".pth", ".ckpt", ".pt",],
    "archive": [
        ".a", ".ar", ".cpio", ".shar", ".LBR", ".iso", ".lbr", ".mar",
        ".sbx", ".tar", ".br", ".bz2", ".F", ".?XF", ".zip", ".rar",
        ".7z", ".tar.gz", ".tar.bz2", ".gz" 
    ]
}
sizes = {
    "apps": 0,
    "videos": 0,
    "images": 0,
    "music": 0,
    "ai_models": 0,
    "archives": 0,
    "other": 0,
    "free": 0
}

def get_tree_size(path):
    total: int = 0
    for entry in os.scandir(path):
        try:
            if entry.is_dir(follow_symlinks=False):
                total += get_tree_size(entry.path)
            else:         
                size = entry.stat(follow_symlinks=False).st_size
                total += size
                _, ext = os.path.splitext(entry)
                if ext in categories["image"]:
                    sizes["images"] += size
                elif ext in categories["music"]:
                    sizes["music"] += size
                elif ext in categories["video"]:
                    sizes["videos"] += size
                elif ext in categories["app"]:
                    sizes["apps"] += size
                elif ext in categories["ai"]:
                    sizes["ai_models"] += size
                elif ext in categories["archive"]:
                    sizes["archives"] += size
                else:
                    sizes["other"] += size
        except PermissionError:
            print(f"Skipping {entry.path} due to PermissionError")
        except OSError as error:
            print(f"Skipping {entry.path} due to OSError: {error}")
    return total
sz = {
        "apps": [],
        "videos": [],
        "images": [],
        "music": [],
        "ai_models": [],
        "archives": [],
        "other": [],
        "free": []
    }
drives = []
bitmask = windll.kernel32.GetLogicalDrives()
for letter in ascii_uppercase:
    if bitmask & 1:
        drives.append(f"{letter}:/")
    bitmask >>= 1
drives = drives[:-1]        #disabled the check of last drive because I don't need it

if __name__ != "__main__":
    for dr in drives:
        os.chdir(dr)
        total, used, free = shutil.disk_usage('/')
        sizes = {
            "apps": 0,
            "videos": 0,
            "images": 0,
            "music": 0,
            "ai_models": 0,
            "archives": 0,
            "other": 0,
            "free": free
        }
        ts = time.perf_counter()
        get_tree_size(x)
        td = time.perf_counter() - ts
        sizesGiB = {k: v/GiB for k, v in sizes.items()}
        sizesGB = {k: v/GB for k, v in sizes.items()}
        sizesPercent = {k: v/total * 100 for k, v in sizes.items()}
        for k in sz.keys():
            sz[k].append(sizesPercent[k])
        print(f"{dr}{sizesGB= }\n{td:.3f} seconds")
    width = 0.5
    fig, ax = plt.subplots()
    bottom = np.zeros(3)
    for type, size in sz.items():
        p = ax.bar(drives, size, width, label=type, bottom=bottom)
        bottom += size
        ax.bar_label(p, label_type="center")
    ax.legend()
    plt.show()

@cache
def get_size(path):
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_size(entry.path)
    except PermissionError:
        print(f"Skipped {path} due to PermissionError")
    return total

def get_directory_size(path):
    tree = {'total_size': get_size(path)}
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_dir():
                    tree[entry.name] = get_directory_size(entry.path)
    except PermissionError:
        print(f"Skipped {path} due to PermissionError")
    return tree

path = "D:/"
folders = [os.path.join(path, name) for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]

sizes = {}
for f in folders:
    sizes[f] = get_directory_size(f)

def format_size(size):
    if size < GB:
        return f"{size/MB:.2f} MB"
    else:
        return f"{size/GB:.2f} GB"

def create_trace(tree, path='', depth=0):
    ids = []
    labels = []
    parents = []
    values = []

    if depth <= 100:  # Only proceed if depth is less than or equal to 4
        for name, subtree in tree.items():
            if name == 'total_size':
                continue
            new_path = path + '/' + name if path else name
            ids.append(new_path)
            labels.append(name)
            parents.append(path)
            values.append(subtree['total_size'])
            if isinstance(subtree, dict):
                sub_ids, sub_labels, sub_parents, sub_values = create_trace(subtree, new_path, depth+1)
                ids.extend(sub_ids)
                labels.extend(sub_labels)
                parents.extend(sub_parents)
                values.extend(sub_values)

    return ids, labels, parents, values

ids, labels, parents, values = create_trace(sizes)

fig = go.Figure(go.Sunburst(
    ids=ids,
    labels=labels,
    parents=parents,
    values=values,
    hovertemplate='<b>%{label}</b>: %{customdata}<extra></extra>',
    customdata=[format_size(v) for v in values],
    maxdepth=4,
))

fig.show()