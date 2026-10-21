#!/usr/bin/env python3
"""Make the names of packages and pluginlib classes clickable.

Every name written in inline code that has a page in the documentation, for example `ros2neuro_recorder` or
`ros2neuro::acquisition::XDFDevice`, becomes a link to that page.

Rules
  * in a table every occurrence is linked; in the text only the first occurrence of a name per paragraph or list item;
  * never in fenced code (also mermaid), headings, include lines, existing links, URLs, HTML tags;
  * never a link from a page to itself (the page of a package does not link its own name);
  * only names listed below (a placeholder such as `ros2neuro_filters_myfilter` or a wildcard is left alone).
The script is idempotent: a name that is already a link is skipped, so it can be run again after adding pages.

Usage
  python3 tools/link_names.py            # dry run: list the changes
  python3 tools/link_names.py --apply    # write them
When you add a package or a plugin page, add its name to the tables below.
"""
import os
import re
import sys
from collections import Counter
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
P = "packages"

# --------------------------------------------------------------------------- name -> page (relative to docs/)
MAP = {}


def package(name, page, anchor=""):
    MAP[name] = (f"{page}", anchor)


def family(base, folder, plugins, plugin_pages=None):
    """ros2neuro_<base> -> <folder>/index.md, ros2neuro_<base>_<x> -> <folder>/<x>.md (or the given page)."""
    package(f"ros2neuro_{base}", f"{P}/{folder}/index.md")
    for x in plugins:
        page = (plugin_pages or {}).get(x, f"{x}.md")
        package(f"ros2neuro_{base}_{x}", f"{P}/{folder}/{page}")
        package(f"{base}_{x}", f"{P}/{folder}/{page}")          # the short name used in the plugin tables


family("acquisition", "acquisition", ["dummy", "lsl", "eegdev", "antneuro", "gusbamp", "xdf"])
family("filters", "filters", ["dc", "butterworth", "car", "laplacian", "hann", "hamming", "blackman", "flattop"])
family("decoder", "decoder", ["lda", "qda", "svm", "gaussian", "py", "converters"], {"py": "python.md"})
family("integrator", "integrator", ["exponential", "buffer"])
family("recorder", "recorder", ["xdf"])
family("manager", "manager", ["synchronous", "asynchronous"])
family("feedback", "feedback", ["wheel", "bar"])
package("ros2neuro_processing_spectral", f"{P}/processing/spectral.md")
package("ros2neuro_processing_buffer", f"{P}/processing/buffer.md")
package("neurodraw", f"{P}/feedback/neurodraw.md")
package("ros2neuro_visualizer", f"{P}/visualizer.md")
package("ros2neuro_devel_test", f"{P}/devel-test.md")
package("ros2neuro_msgs", f"{P}/msgs-data.md", "ros2neuro_msgs")
package("ros2neuro_data", f"{P}/msgs-data.md", "ros2neuro_data")

# pluginlib classes: the concrete plugin -> its page, the base class -> the page of the base package
for cls, x in [("DummyDevice", "dummy"), ("LSLDevice", "lsl"), ("EGDDevice", "eegdev"), ("EEGODevice", "antneuro"),
               ("GUSBampDevice", "gusbamp"), ("XDFDevice", "xdf")]:
    package(f"ros2neuro::acquisition::{cls}", f"{P}/acquisition/{x}.md")
package("ros2neuro::acquisition::NeuroDevice", f"{P}/acquisition/index.md")
for x, cls in [("dc", "Dc"), ("butterworth", "Butterworth"), ("car", "Car"), ("laplacian", "Laplacian"),
               ("hann", "Hann"), ("hamming", "Hamming"), ("blackman", "Blackman"), ("flattop", "Flattop")]:
    package(f"ros2neuro_filters_{x}/{cls}Float", f"{P}/filters/{x}.md")
package("ros2neuro::filters::Filter<float>", f"{P}/filters/index.md")
for cls in ["LDA", "QDA", "SVM", "Gaussian"]:
    package(f"ros2neuro::decoder::{cls}", f"{P}/decoder/{cls.lower()}.md")
package("ros2neuro::decoder::Decoder", f"{P}/decoder/index.md")
for cls in ["Exponential", "Buffer"]:
    package(f"ros2neuro::integrator::{cls}", f"{P}/integrator/{cls.lower()}.md")
package("ros2neuro::integrator::Integrator", f"{P}/integrator/index.md")
package("ros2neuro::recorder::XDFRecorder", f"{P}/recorder/xdf.md")
package("ros2neuro::recorder::NeuroRecorder", f"{P}/recorder/index.md")
package("ros2neuro::manager::Training", f"{P}/manager/synchronous.md")
package("ros2neuro::manager::Control", f"{P}/manager/asynchronous.md")
package("ros2neuro::manager::ManagerPlugin", f"{P}/manager/index.md")
package("ros2neuro::feedback::Wheel", f"{P}/feedback/wheel.md")
package("ros2neuro::feedback::Bar", f"{P}/feedback/bar.md")
package("ros2neuro::feedback::FeedbackPlugin", f"{P}/feedback/index.md")

# --------------------------------------------------------------------------- scanning
LINK = r"\[[^\]]*\]\([^)]*\)"
HTML = r"<[^>\n]+>"
URL = r"https?://[^\s)>\"']+"
TOKEN = re.compile(rf"({LINK})|({HTML})|({URL})|(`[^`\n]+`)")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s")


def link_for(name, current: Path):
    page, anchor = MAP[name]
    target = DOCS / page
    if target.resolve() == current.resolve():
        return None                                           # no link from a page to itself
    rel = os.path.relpath(target, current.parent).replace(os.sep, "/")
    return f"[`{name}`]({rel}{'#' + anchor if anchor else ''})"


def process_line(line, current, seen, in_table):
    out, last, changed = [], 0, 0
    for m in TOKEN.finditer(line):
        if m.group(1):                                        # an existing link: its names count as already linked
            for inner in re.findall(r"`([^`\n]+)`", m.group(1)):
                if inner in MAP:
                    seen.add(inner)
            continue
        code = m.group(4)
        if not code:
            continue
        name = code[1:-1]
        if name not in MAP:
            continue
        if not in_table and name in seen:
            continue
        new = link_for(name, current)
        if new is None:
            continue
        out.append(line[last:m.start()])
        out.append(new)
        last = m.end()
        changed += 1
        seen.add(name)
    out.append(line[last:])
    return "".join(out), changed


def process_file(path: Path):
    lines = path.read_text().split("\n")
    new_lines, changes, in_fence, seen = [], [], False, set()
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            new_lines.append(line)
            continue
        if in_fence or stripped.startswith("#") or stripped.startswith("--8<--"):
            new_lines.append(line)
            continue
        if not stripped or LIST_ITEM.match(line):
            seen = set()                                      # a new paragraph or list item
        in_table = stripped.startswith("|")
        new, n = process_line(line, path, seen, in_table)
        if n:
            changes.append((i, line, new, n))
        new_lines.append(new)
    return "\n".join(new_lines), changes


def main():
    apply = "--apply" in sys.argv
    verbose = "--diff" in sys.argv
    total, per_file = 0, Counter()
    for path in sorted(DOCS.rglob("*.md")):
        text, changes = process_file(path)
        if not changes:
            continue
        n = sum(c[3] for c in changes)
        total += n
        per_file[str(path.relative_to(DOCS))] = n
        if verbose and not apply:
            for i, old, new, _ in changes:
                print(f"{path.relative_to(DOCS)}:{i}\n  - {old.strip()[:150]}\n  + {new.strip()[:190]}")
        if apply:
            path.write_text(text)
    print(("linked" if apply else "would link"), total, "names in", len(per_file), "files")
    if not apply:
        for f, n in per_file.most_common(12):
            print(f"  {n:3d}  {f}")


if __name__ == "__main__":
    main()
