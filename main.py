import shutil
import os
import sys
import time
import plotly.graph_objects as go

MiB = 1024**2
GiB = 1024**3
GB = 1000**3
MB = 1000**2

def get_size(path, sizes, checked_dirs):
    if path in checked_dirs:
        return sizes.get(path, 0)
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if os.name == "posix" and ("/dev" in entry.path or "/proc" in entry.path or "/sys" in entry.path):
                    continue        #skip directories with pseudo-files on unix-based systems.
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_size(entry.path, sizes, checked_dirs)
    except PermissionError:
        print(f"Skipped {path} due to PermissionError")
    except FileNotFoundError:
        print(f"{path} not found")
    sizes[path] = total
    checked_dirs.add(path)
    return total

def get_directory_size(path):
    sizes = {}
    checked_dirs = set()
    tree = {"total_size": get_size(path, sizes, checked_dirs)}
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_dir(follow_symlinks=False):
                    dir_size = sizes.get(entry.path, get_size(entry.path, sizes, checked_dirs))
                    if dir_size >= MB:
                        tree[entry.name] = get_directory_size(entry.path)
    except PermissionError:
        pass
    except FileNotFoundError:
        pass
    return tree

def format_size(size):
    if size < GB:
        return f"{size/MB:.2f} MB"
    else:
        return f"{size/GB:.2f} GB"  

def create_trace(tree, path=""):
    ids = []
    labels = []
    parents = []
    values = []

    for name, subtree in tree.items():
        if name == "total_size":
            continue
        new_path = path + '/' + name if path else name
        ids.append(new_path)
        labels.append(name)
        parents.append(path)
        values.append(subtree["total_size"])
        if isinstance(subtree, dict):
            sub_ids, sub_labels, sub_parents, sub_values = create_trace(subtree, new_path)
            ids.extend(sub_ids)
            labels.extend(sub_labels)
            parents.extend(sub_parents)
            values.extend(sub_values)
    return ids, labels, parents, values


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def run_scan(path):
    t1 = time.perf_counter()
    sizes = {path:get_directory_size(path)}
    t2 = time.perf_counter() - t1
    print(f"{path} scanned in {t2:.3f} seconds")
    ids, labels, parents, values = create_trace(sizes)
    total, used, free = shutil.disk_usage(path)
    labels[0] = f"{path}<br>{values[0]/GB:.1f}GB<br>/{total/GB:.1f}GB"
    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        hovertemplate="<b>%{label}</b>: %{customdata}<br>%{id}<extra></extra>",
        customdata=[format_size(v) for v in values],
        maxdepth=4,
        textfont={"family": "monospace"},
        leaf={"opacity": 0.5},
        marker={"line": {"width": 0.5}},
        insidetextorientation="horizontal",
    ))
    fig.update_traces(root={"color":"rgba(42, 42, 42, 1)"}, outsidetextfont={"size":24, "color":"white"})
    fig.write_html(resource_path("html/disk.html"))     #comment for linux/mac
    # fig.show()        #uncomment for linux/mac
# run_scan("/")       #uncomment for linux/mac