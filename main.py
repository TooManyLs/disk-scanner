import shutil
import os
import plotly.graph_objects as go

MiB = 1024**2
GiB = 1024**3
GB = 1000**3
MB = 1000**2

def get_size(path):
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_size(entry.path)
    except PermissionError:
        print(f"Skipped {path} due to PermissionError")
    except FileNotFoundError:
        print(f"{path} not found")
    return total

def get_directory_size(path):
    tree = {"total_size": get_size(path)}
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_dir(follow_symlinks=False):
                    dir_size = get_size(entry.path)
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
        new_path = path + '\\' + name if path else name
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



def run_scan(path):
    sizes = {path:get_directory_size(path)}
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
    curr = os.path.dirname(os.path.abspath(__file__))
    fig.write_html(os.path.join(curr, 'html\\disk.html'))