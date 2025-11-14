# Transistor sweep visualisation - redistributable interactive 2D & 3D I-V Plots

This repository provides Python utilities for importing and interactively visualising **transistor sweep data** (e.g. *Ids–Vgs–Vds* measurements) in **2D and 3D** using Plotly.

Figures are exported as standalone **HTML files** — fully interactive and viewable in any modern web browser, with no dependencies or Python environment required on the viewer's machine.

---

## 
![Demo](demo.gif)

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

## 🧰 Installation

```bash
pip install pandas numpy plotly
```

Clone or download this repository:

```bash
git clone https://github.com/event-driven-robotics/ivplot.git
cd ivplot
```

---

## 🧠 Quick Example

```python
from ivplot import plot
import numpy as np

# Example synthetic data
vgs = np.linspace(0, 2, 20)
vds = np.linspace(0, 10, 30)
ids = 1e-6 * np.outer(np.exp(vgs), (vds / 10))

# Create the 6-panel interactive figure
fig = plot(vgs, vds, ids, label="Measured")

# Overlay a model
ids_model = ids * 0.9
plot(vgs, vds, ids_model, fig=fig, label="Modelled")
```

This produces `transistor_plot.html` and opens it in your default browser.

---

## 📦 Output Layout

```text
+---------------------+---------------------+---------------------+
| Ids–Vgs (log)       | 3D log(Ids)         | Ids–Vds (log)       |
| color = Vds         |                     | color = Vgs         |
+---------------------+---------------------+---------------------+
| Ids–Vgs (linear)    | 3D Ids              | Ids–Vds (linear)    |
| color = Vds         |                     | color = Vgs         |
+---------------------+---------------------+---------------------+
```

---

## 🎯 Why Interactive 3D?

Papers often show Ids-Vds and Ids-Vgs plots, although these are just slices through a fundamentally 3D landscape. A 3D visualisation can be more useful for understanding and comparing these spaces, but only if you are able to roll them around interactively, otherwise they are often unreadable. Such visualisations are already available within certain existing software, but by exporting these visualisations to a self-contained `.html` file, you can distribute the *full interactive 3D figure* to anyone.
  
With browser-based 3D views you can freely rotate and explore:

- saturation transition
- subthreshold curvature  
- contact and mobility effects  
- multi-dimensional relationships otherwise invisible in 2D plots  

---

## 📜 License

MIT License.  
Use freely in research or commercial settings.  
If appropriate, please cite the repository.

---

## 🧠 Citation

If used in scientific work:

> **Bamford, S. (2025). Transistor Sweep Visualisation – Interactive 2D and 3D Plotly Plotter. GitHub repository.**
