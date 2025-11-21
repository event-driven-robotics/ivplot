# plot_plotly.py — 6-panel Plotly transistor plotter
import numpy as np
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path

# Force browser renderer for Spyder / scripts
pio.renderers.default = "browser"

try:
    from matplotlib.tri import Triangulation as _Triangulation
except Exception:
    _Triangulation = None

# -------------------- marker symbol mapping (mpl -> plotly) --------------------
def _to_plotly_symbol(m):
    m = (m or "circle")
    table = {
        "o": "circle", ".": "circle", ",": "circle",
        "x": "x", "+": "cross",
        "s": "square", "D": "diamond", "d": "diamond",
        "^": "triangle-up", "v": "triangle-down",
        "<": "triangle-left", ">": "triangle-right",
        "p": "pentagon", "*": "star",
    }
    return table.get(m, m)

# ---------------------- cmap name -> plotly colorscale -------------------------
def _to_plotly_colorscale(name):
    if not name:
        return "Viridis"
    n = str(name).lower()
    lut = {
        "viridis": "Viridis",
        "plasma": "Plasma",
        "cividis": "Cividis",
        "magma": "Magma",
        "inferno": "Inferno",
        "turbo": "Turbo",
        "hot": "Hot",
        "jet": "Jet",
    }
    return lut.get(n, name)  # pass through if already a valid Plotly scale or list

# ------------------------------ helpers ---------------------------------------

def _downsample(samples, max_samples=np.inf, rng_seed=0):
    N = samples.shape[0]
    if not np.isfinite(max_samples) or max_samples >= N:
        return samples
    k = int(max(1, np.floor(max_samples)))
    rng = np.random.default_rng(rng_seed)
    idx = rng.choice(N, size=k, replace=False)
    return samples.iloc[idx]

def _log_ids(ids, eps=1e-12):
    mask = ids > 0
    ids_log = np.log10(ids[mask] + eps)
    return mask, ids_log

def adaptive_alpha(n):
    """Return alpha between 0.8 (for n<=100) and 0.1 (for n>=1000)."""
    n = max(1, n)
    if n <= 100:
        return 0.8
    elif n >= 1000:
        return 0.1
    else:
        # linear interpolation between 100 → 0.8 and 1000 → 0.1
        return 0.8 - (n - 100) * (0.7 / 900)
    
# keep one figure across calls unless user provides a new one
_current_fig = None

def _ensure_fig(fig, colorscale, name, view='all'):
    """Create a fresh 2x3 layout unless an explicit fig is provided."""
    if fig is not None:
        return fig

    if view == '3d':
        fig = make_subplots(
            rows=2, cols=1,
            specs=[
                [{'type': 'scene'}],
                [{'type': 'scene'}],
            ],
            horizontal_spacing=0.08,
            vertical_spacing=0.12,
            subplot_titles=("Ids(Vgs,Vds) [log]",
                            "Ids(Vgs,Vds) [lin]"),
        )

    else:
        fig = make_subplots(
            rows=2, cols=3,
            specs=[
                [{'type': 'xy'}, {'type': 'scene'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'scene'}, {'type': 'xy'}],
            ],
            horizontal_spacing=0.08,
            vertical_spacing=0.12,
            subplot_titles=("Ids vs Vgs [log]", "3D: Ids(Vgs,Vds) [log]", "Ids vs Vds [log]",
                            "Ids vs Vgs [lin]", "3D: Ids(Vgs,Vds) [lin]", "Ids vs Vds [lin]"),
        )

    if view != '3d':
        # 2D axis titles
        fig.update_xaxes(title_text="Vgs (V)", row=1, col=1)
        fig.update_yaxes(title_text="Ids (A, log10)", row=1, col=1)
        fig.update_xaxes(title_text="Vds (V)", row=1, col=3)
        fig.update_yaxes(title_text="Ids (A, log10)", row=1, col=3)
        fig.update_xaxes(title_text="Vgs (V)", row=2, col=1)
        fig.update_yaxes(title_text="Ids (A)", row=2, col=1)
        fig.update_xaxes(title_text="Vds (V)", row=2, col=3)
        fig.update_yaxes(title_text="Ids (A)", row=2, col=3)

    # 3D scenes + legend + colorbars
    fig.update_layout(
                
        scene=dict(
            xaxis_title="Vgs (V)", yaxis_title="Vds (V)", zaxis_title="Ids (A, log10)",
            aspectmode="cube", dragmode="turntable",
            camera=dict(
                up=dict(x=0, y=0, z=1),           # ← keep Z as “up”
                eye=dict(x=1.6, y=1.6, z=1.0)     # ← optional: Matplotlib-like start
            ),
        ),
        scene2=dict(
            xaxis_title="Vgs (V)", yaxis_title="Vds (V)", zaxis_title="Ids (A)",
            aspectmode="cube", dragmode="turntable",
            camera=dict(
                up=dict(x=0, y=0, z=1),           # ← keep Z as “up”
                eye=dict(x=1.6, y=1.6, z=1.0)     # ← optional: Matplotlib-like start
            ),
        ),
        title=name,
        margin=dict(l=40, r=40, t=60, b=40),
        # Legend beside the middle column (top, center-right)
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.66),
        uirevision="keep",
        # SAME colorscale on both sides; independent ranges; bars at far left/right
        coloraxis=dict(colorscale=colorscale,
                       colorbar=dict(title="Vds (V)", x=-0.08, xanchor="left")),
        coloraxis2=dict(colorscale=colorscale,
                        colorbar=dict(title="Vgs (V)", x=1.06, xanchor="left")),
    )

    # track ranges for the shared 2D coloraxes
    fig._ivgs_vds_range = [np.inf, -np.inf]   # left column encodes Vds
    fig._ivds_vgs_range = [np.inf, -np.inf]   # right column encodes Vgs
    return fig


def _update_coloraxis_range(fig, which, values):
    vmin, vmax = float(np.nanmin(values)), float(np.nanmax(values))
    if which == 1:  # left column encodes Vds
        lo, hi = fig._ivgs_vds_range
        lo = min(lo, vmin); hi = max(hi, vmax)
        fig._ivgs_vds_range = [lo, hi]
        fig.update_layout(coloraxis=dict(cmin=lo, cmax=hi))
    else:          # right column encodes Vgs
        lo, hi = fig._ivds_vgs_range
        lo = min(lo, vmin); hi = max(hi, vmax)
        fig._ivds_vgs_range = [lo, hi]
        fig.update_layout(coloraxis2=dict(cmin=lo, cmax=hi))

# ------------------------------ public API ------------------------------------
def ivplot(sweeps, fig=None,
         linlog="both", view="all", surf=False,
         link_3d=True, cmap="viridis", alpha=None,
         marker="circle", markersize=6, color=None, label=None,
         max_samples=np.inf, rng_seed=0,
         html_path="transistor_plot.html", auto_open=True,
         name='Transistor Curves'):
    """
    Build/overlay a 6-panel Plotly figure.
    Returns fig.
    """
    # normalize colorscale name (same used by both 2D columns)
    colorscale = _to_plotly_colorscale(cmap)

    '''
    sweeps is a list of dicts, where each dict contains:
        data, which is a df with cols vgs, vds, and ids, 
        and a value 'type' which is 'd' for vds sweep, 'g' for vgs sweep, 
            or 'both' if it is mixed data, i.e. with a loaded draiun rather than a fixed drain voltage.
    '''
    
    fig = _ensure_fig(fig, colorscale, name, view)

    # -------------- LEFT column: Ids vs Vgs (colour encodes Vds) --------------
    if view in ['vgs', 'all']:
        samples = [sweep['data'] for sweep in sweeps if sweep.get('type', 'both') in ['g', 'both']]
        if samples:
            samples = pd.concat(samples, ignore_index=True, sort=False)
            samples = _downsample(samples, max_samples=max_samples, rng_seed=rng_seed)
            ids_lin = samples['ids']
            mask, ids_log = _log_ids(ids_lin)
            vgs = samples['vgs']
            vds = samples['vds']
            alpha_effective = alpha or adaptive_alpha(len(mask))
            
            _update_coloraxis_range(fig, which=1, values=vds) 
            # LOG row
            if np.any(mask):
                fig.add_trace(
                    go.Scatter(
                        x=vgs[mask], y=ids_log,
                        mode="markers",
                        marker=dict(
                            symbol=_to_plotly_symbol(marker),
                            size=markersize,
                            opacity=alpha_effective,
                            color=vds[mask],
                            coloraxis="coloraxis"
                        ),
                        name=label or "dataset",
                        legendgroup=label or "dataset",
                        showlegend=False,  # keep legend for 3D only
                        hovertemplate=(
                            f"Vgs=%{{x:.3g}} V<br>"
                            f"log10(Ids)=%{{y:.3g}}<br>"
                            f"Vds=%{{marker.color:.3g}} V"
                            f"<extra>{label or ''}</extra>"
                        ),
                    ),
                    row=1, col=1
                )
        
            # LIN row
            fig.add_trace(
                go.Scatter(
                    x=vgs, y=ids_lin,
                    mode="markers",
                    marker=dict(
                        symbol=_to_plotly_symbol(marker),
                        size=markersize,
                        opacity=alpha_effective,
                        color=vds,
                        coloraxis="coloraxis"
                    ),
                    name=label or "dataset",
                    legendgroup=label or "dataset",
                    showlegend=False,
                    hovertemplate=(
                        f"Vgs=%{{x:.3g}} V<br>"
                        f"Ids=%{{y:.3e}} A<br>"
                        f"Vds=%{{marker.color:.3g}} V"
                        f"<extra>{label or ''}</extra>"
                    ),
                ),
                row=2, col=1
            )

    # -------------- RIGHT column: Ids vs Vds (colour encodes Vgs) -------------
    if view in ['vds', 'all']:
        samples = [sweep['data'] for sweep in sweeps if sweep.get('type', 'both') in ['d', 'both']]
        if samples:
            samples = pd.concat(samples, ignore_index=True, sort=False)
            samples = _downsample(samples, max_samples=max_samples, rng_seed=rng_seed)
            ids_lin = samples['ids']
            mask, ids_log = _log_ids(ids_lin)
            vgs = samples['vgs']
            vds = samples['vds']
            alpha_effective = alpha or adaptive_alpha(len(mask))
            
            _update_coloraxis_range(fig, which=2, values=vgs)
    
            # LOG row
            if np.any(mask):
                fig.add_trace(
                    go.Scatter(
                        x=vds[mask], y=ids_log,
                        mode="markers",
                        marker=dict(
                            symbol=_to_plotly_symbol(marker),
                            size=markersize,
                            opacity=alpha_effective,
                            color=vgs[mask],
                            coloraxis="coloraxis2"
                        ),
                        name=label or "dataset",
                        legendgroup=label or "dataset",
                        showlegend=False,
                        hovertemplate=(
                            f"Vds=%{{x:.3g}} V<br>"
                            f"log10(Ids)=%{{y:.3g}}<br>"
                            f"Vgs=%{{marker.color:.3g}} V"
                            f"<extra>{label or ''}</extra>"
                        ),
                    ),
                    row=1, col=3
                )
        
            # LIN row
            fig.add_trace(
                go.Scatter(
                    x=vds, y=ids_lin,
                    mode="markers",
                    marker=dict(
                        symbol=_to_plotly_symbol(marker),
                        size=markersize,
                        opacity=alpha_effective,
                        color=vgs,
                        coloraxis="coloraxis2"
                    ),
                    name=label or "dataset",
                    legendgroup=label or "dataset",
                    showlegend=False,
                    hovertemplate=(
                        f"Vds=%{{x:.3g}} V<br>"
                        f"Ids=%{{y:.3e}} A<br>"
                        f"Vgs=%{{marker.color:.3g}} V"
                        f"<extra>{label or ''}</extra>"
                    ),
                ),
                row=2, col=3
            )

    if view in ['3d', 'all']:
        # --------------------------- MIDDLE: 3D scenes ----------------------------

        samples = [sweep['data'] for sweep in sweeps]
        samples = pd.concat(samples, ignore_index=True, sort=False)
        samples = _downsample(samples, max_samples=max_samples, rng_seed=rng_seed)
        ids_lin = samples['ids']
        mask, ids_log = _log_ids(ids_lin)
        vgs = samples['vgs']
        vds = samples['vds']
        alpha_effective = alpha or adaptive_alpha(len(mask))
            
        # ensure consistent color for each label across both 3D plots
        if not hasattr(fig, "_label_colors"):
            fig._label_colors = {}
        _palette = [
            "crimson", "royalblue", "darkorange", "seagreen", "purple",
            "deeppink", "dodgerblue", "chocolate", "limegreen"
        ]
        if label:
            if label not in fig._label_colors:
                fig._label_colors[label] = _palette[len(fig._label_colors) % len(_palette)]
            this_color = fig._label_colors[label]
        else:
            this_color = color or "gray"
    
        
        def _add_3d(row, x, y, z):
            if surf and _Triangulation is not None and z.size >= 3:
                tri = _Triangulation(x, y)
                fig.add_trace(
                    go.Mesh3d(
                        x=x, y=y, z=z,
                        i=tri.triangles[:, 0], j=tri.triangles[:, 1], k=tri.triangles[:, 2],
                        color=color or None, opacity=alpha_effective,
                        name=(label or "dataset"),
                        legendgroup=(label or "dataset"),
                        showlegend=True if (label and row == 1) else False,  # legend only on top 3D
                        showscale=False
                    ),
                    row=row, col=2
                )
            else:
                scale = 0.3 if marker in ('x', '+', 'cross') else 1 # Fix cross being bigger
                fig.add_trace(
                    go.Scatter3d(
                        x=x, y=y, z=z,
                        mode="markers",
                        marker=dict(
                            symbol=_to_plotly_symbol(marker),
                            size=markersize * scale,
                            opacity=alpha_effective,
                            color=(this_color)
                        ),
                        name=(label or "dataset"),
                        legendgroup=(label or "dataset"),
                        showlegend=True if (label and row == 1) else False,  # legend only on top 3D
                    ),
                    row=row, col=2
                )
    
    
        # LOG scene (row 1)
        if np.any(mask):
            _add_3d(1, vgs[mask], vds[mask], ids_log)
        # LIN scene (row 2)
        _add_3d(2, vgs, vds, ids_lin)
    
        # Update title for overlay context
        if label and (fig.layout.title and "Transistor Curves" in fig.layout.title.text):
            fig.update_layout(title=f"Transistor Curves — last added: {label}")
    
        # -------------------- camera linking in exported HTML ---------------------
        # Works for the saved HTML; links both scenes during drag (relayouting) and on release (relayout)
       # -------------------- camera linking in exported HTML ---------------------
        # Lightweight, throttled, no recursion; works during and after drag.
    # -------------------- camera linking in exported HTML (debounced, no jitter) ---
        post_js = r"""
        (function(){
          // Figure <div> is just before this <script>
          var gd = document.currentScript.previousElementSibling;
          if(!gd) return;
        
          // Debounced mirror on release, with source tracking to avoid echo loops
          function linkScenes(g){
            if(g._linkedOnce) return;
            g._linkedOnce = true;
        
            let syncing = false;
            let lastSource = null;
            let timer = null;
        
            function isObj(x){ return x && typeof x === 'object'; }
        
            g.on('plotly_relayout', function(e){
              if(syncing || !isObj(e)) return;
        
              // Which scene emitted the camera?
              const cam1 = e['scene.camera'];
              const cam2 = e['scene2.camera'];
              let src = null, dstKey = null, cam = null;
        
              if (cam1) { src = 'scene';  dstKey = 'scene2.camera'; cam = cam1; }
              else if (cam2) { src = 'scene2'; dstKey = 'scene.camera';  cam = cam2; }
              else { return; } // not a camera change
        
              // Debounce: wait a moment after release so Plotly finishes its own updates
              if (timer) { clearTimeout(timer); timer = null; }
              timer = setTimeout(function(){
                // Avoid bouncing back into the source: set a guard while mirroring
                syncing = true;
                try {
                  // Only mirror when source actually changed since our last mirror
                  if (lastSource !== src) {
                    lastSource = src;
                  }
                  Plotly.relayout(g, { [dstKey]: cam });
                } finally {
                  // Small timeout before allowing another mirror to avoid race with Plotly internals
                  setTimeout(function(){ syncing = false; }, 30);
                }
              }, 60);
            });
          }
          linkScenes(gd);
        })();
        """
    
    html = pio.to_html(fig, include_plotlyjs="cdn", full_html=True, post_script=post_js)
    
    Path(html_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    if auto_open:
        import webbrowser, os
        webbrowser.open("file://" + os.path.abspath(html_path))
    
    return fig

