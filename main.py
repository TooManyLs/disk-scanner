import shutil
import os
import sys
from time import perf_counter
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

def format_size(size, pre, precision=2):
    if pre != 10 and pre != 2:
        raise Exception(f"Invalid prefix value: {pre};\nValid prefixes: 2 (mebibyte...), 10 (megabyte...)")
    if pre == 10:
        if size < GB:
            return f"{size/MB:.{precision}f} MB"
        else:
            return f"{size/GB:.{precision}f} GB"
    if pre == 2:
        if size < GiB:
            return f"{size/MiB:.{precision}f} MiB"
        else:
            return f"{size/GiB:.{precision}f} GiB"

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


def run_scan(path, pre=2):
    t1 = perf_counter()
    sizes = {path:get_directory_size(path)}
    t2 = perf_counter() - t1
    print(f"{path} scanned in {t2:.3f} seconds")
    ids, labels, parents, values = create_trace(sizes)
    total, used, free = shutil.disk_usage(path)
    settings = {"ids": ids,
                "labels":labels, 
                "parents": parents,
                "values": values,
                "maxdepth": 4,
                "textfont": {"family": "monospace"},
                "leaf": {"opacity": 0.5},
                "marker": {"line": {"width": 1.5}},
                "insidetextorientation": "horizontal",
                "hovertemplate":"<b>%{label}</b>: %{customdata}<br>%{id}<extra></extra>",
                }
    labels[0] = f"{path}<br>{format_size(values[0], pre, 1)}<br>/{format_size(total, pre, 1)}"
    fig = go.Figure(go.Sunburst( 
        customdata=[format_size(v, pre) for v in values],
        **settings
        )
    )
    conf = {
    "displayModeBar": False,
    }
    fig.update_layout(
        hoverlabel=dict(
            font_size=12,
            font_family="monospace",
        ),       
    )
    fig.update_traces(root={"color":"rgba(42, 42, 42, 1)"}, outsidetextfont={"size":24, "color":"white"})
    fig.write_html(resource_path("html/disk.html"), config=conf)     #comment for linux/mac
    # fig.show(config=conf)       #uncomment for linux/mac
# run_scan("/")       #uncomment for linux/mac