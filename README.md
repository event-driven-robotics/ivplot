# Transistor sweep visualisation - redistributable interactive 2D & 3D I-V Plots

We often use Ids-Vds and Ids-Vgs plots to explore transistor characteristics, although these are just slices through a fundamentally 3D landscape: Ids–Vgs–Vds. A 3D visualisation can be more useful for understanding and comparing these spaces, but only if we  are able to roll them around interactively, otherwise they are often unreadable. Such visualisations are already available within certain existing software, but by exporting these visualisations to self-contained **HTML files**, we can distribute the *full interactive 3D figures* to anyone, to be viewed in any browser, with no dependencies or Python environment required on the viewer's machine.

---

## Animation

![Demo](demo.gif)

## Screenshot

![Screenshot](screenshot.png)


## Features

- **Six-panel layout**  
  - Top row: log(Ids)  
  - Bottom row: linear Ids  
  - Columns: Ids–Vgs, 3D Ids(Vgs,Vds), Ids–Vds  
  Shared colorbars encode the “hidden” axis (either Vgs or Vds).

- **Interactive 3D visualisation**  
  Rotate, zoom, and inspect the Ids(Vgs,Vds) surface.  
  Both 3D panels share a linked camera to maintain consistent orientation.

- **Overlay multiple datasets**  
  Call `plot(...)` again with `fig=existing_fig` to add more data (e.g. measured vs modelled, or older versus newer sweeps etc).  Legends and colorbars are handled automatically.

- **Adaptive alpha transparency**  
  Transparency automatically decreases for larger datasets to reduce clutter.

- **Portable output**  
  Each plot writes to a single `.html` file suitable for publication supplements, email attachments, or long-term archival.

---

## Usage

requirements:

```bash
pip install pandas numpy plotly
```

Optionally, use https://github.com/event-driven-robotics/ofet_import to import
example data:

```python
os.environ['PATH_TO_TRANSISTOR_SWEEPS'] = r"path/to/data"
from iit_cnr_2025 import transistors
```

Whatever the data source, format it into a list of sweeps, where each sweep is a dict in this form:

```
{
    'data': df       # DataFrame with columns ['vgs', 'vds', 'ids']
    'type': str,     # 'g' for Vg sweep 'd' for Vd sweep, or 'both' (default if 'type' not present) for mixed data.
}
```

This following code produces one html file per transistor in a folder of your choice and opens each in your default browser.

```python
from ivplot import ivplot

for transistor_name, transistor in transistors.items():
    fig = ivplot(
        transistor['sweeps'], 
        label=transistor_name,
        html_path'=r'path/to/outputs/{transistor_name}.html')
```

This code takes 2 sweep-sets and overlays them in the same graphs - they become different colours in the 3D plots, and use different markers in the 2D graphs.

```python
kwargs = {
    'surf': False, 
    'markersize': 6, 
    'html_path': 'combined_plot.html',
    'name': 'Two characteristics overlaid',
    }
fig = None
for transistor_name, marker in zip(['TR-F1', 'TR-F4'], ['x', 'o']):
    fig = plot(transistors[transistor_name]['sweeps'], marker=marker, fig=fig, label=transistor_name, **kwargs)

```

Generate a gallery of individual 6-plot panels, one for each transistor (in this case, to redistribute the gallery, share the entire folder).
    
```python

from ivplot_gallery import ivplot_gallery

ivplot_gallery(transistors, r'path/to/outputs')
```

## Documentation

ivplot arguments and defaults are as follows:

```python
ivplot(
    sweeps, fig=None,
    linlog="both",        # "both" | "lin" | "log"
    view="all",           # "all" or list of ["ivgs","3d","ivds"]
    surf=False,           # True = 3D surface (triangulated), False = scatter3d
    link_3d=True,         # match camera between log + lin 3D panels
    cmap="viridis",       # colormap for 2D colour axes
    alpha=None,           # point transparency (default auto-adaptive)
    marker="circle",      # Plotly marker symbol (e.g. "circle","x","square")
    markersize=6,         # size of scatter markers
    color=None,           # fixed per-dataset colour (3D only)
    label=None,           # legend label for dataset overlays
    max_samples=inf,      # downsample to at most this many points
    rng_seed=0,           # reproducible sampling when downsampling
    html_path="transistor_plot.html",  # output HTML file
    auto_open=True,       # open in browser after writing
    name="Transistor Curves"           # title in plot + HTML
)
```

* Passing fig=<existing> overlays a new dataset onto an existing plot.
* 2D colour encodes the hidden axis (Vds on left column, Vgs on right).
* 3D colours are constant per dataset unless color is overridden.
* max_samples protects browser/WebGL performance for large sweeps.


ivplot_gallery function params are as follows:

```
ivplot_gallery(
    transistors,              # dict: name -> {"sweeps": ..., other metadata...}
    output_dir,               # directory for all HTML output
    auto_open=True,           # open gallery index.html in browser
    use_thumbnails=True,      # generate 3D-log PNG thumbnails (skip if False)
    **ivplot_kwargs           # all extra keyword arguments forwarded to ivplot()
)
```

## 📜 License

MIT License.  
Use freely in research or commercial settings.  
If appropriate, please cite the repository.


## 🧠 Citation

If used in scientific work:

> **Bamford, S. (2025). Transistor Sweep Visualisation – Interactive 2D and 3D Plotly Plotter. GitHub repository.**
