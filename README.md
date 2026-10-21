# ROS2neuro documentation

Source of the documentation site of **ROS2neuro**, a modular ROS 2 framework for neurophysiological signal
acquisition, processing, decoding and closed-loop BCI. The site is built with
[MkDocs](https://www.mkdocs.org) and the [Material](https://squidfunk.github.io/mkdocs-material/) theme.

## Content

```text
docs/
├── index.md             home
├── assets/              figures (architecture.svg)
├── concepts/            architecture, messages and data types, topics, plugins, protocols
├── packages/            one page per package and per plugin
└── tutorials/           one folder per tutorial: the page (index.md) and its ROS 2 package (tutorial_*/)
```

- **Concepts** explains how ROS2neuro is organised.
- **Packages** documents every package of the workspace. A base package (for example
  `acquisition`) explains the node and tells which plugin to select, and links to one page per plugin.
- **Tutorials** are step-by-step guides. The code of each one is a real ROS 2 package in the same folder as its
  page, and the page includes the code from the files, so text and code cannot drift apart.

## Build the site locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdocs serve            # http://127.0.0.1:8000, reloads on every change
mkdocs build --strict   # builds into site/, fails on broken links and missing files
```

## Before the first push

The package pages link to the repository of each package (`https://github.com/ros2neuro/<package>`). Then set
`repo_url` (and `site_url`, if you publish the site) in `mkdocs.yml`.

## Publish the site

The site is plain static HTML: `mkdocs build` writes it to `site/`. Two ways to publish it:

- **GitHub Pages.** In **Settings → Pages** set the source to **GitHub Actions**. The workflow
  `.github/workflows/docs.yml` builds the site and deploys it on every push to `main`.
  Without Pages enabled the deploy step fails, while the build step still checks the documentation.
  Mind that a GitHub Pages site is **public on the internet**, even when the repository is private, unless the
  organization has GitHub Enterprise Cloud (which can restrict it to its members).
- **Any other web server**, for example a university one: copy the content of `site/`.

If the documentation must stay visible only to the members of the organization, do not enable Pages: read the
Markdown files in the repository, or run `mkdocs serve`.

## Tutorial packages

The packages `docs/tutorials/*/tutorial_*/` are ordinary ROS 2 packages, shown and explained in the
tutorial pages. They depend on `ros2neuro_msgs`, `ros2neuro_filters` and `ros2neuro_integrator`. To build one by
hand, from your ROS2neuro workspace:

```bash
colcon build --paths path/to/docs/docs/tutorials/filter-plugin/tutorial_filter_plugin
colcon test  --packages-select tutorial_filter_plugin
```

## Writing documentation

- Package pages follow the same order: what it is, node and topics, parameters, a minimal example, pitfalls and
  the plugins available.
- Take names, topics and parameters from the code and the package READMEs of the workspace, and check them on a
  running system with `ros2 node info`, `ros2 topic list -t` and `ros2 param list`.
- In a tutorial, build and test the code first, run it, and only then write the page around the real output.
- Names of packages and plugin classes written in inline code (`ros2neuro_recorder`, `ros2neuro::acquisition::XDFDevice`) must
  lead to their page. After writing or editing pages, run `python3 tools/link_names.py` to see which names are not yet links,
  and `python3 tools/link_names.py --apply` to make them links. When you add a package or a plugin page, add its name to the
  tables at the top of the script.
- Use `--8<-- "<tutorial>/<package>/<file>"` to include a code file in a page (paths are relative to
  `docs/tutorials`).
