from pathlib import Path
import html

try:
    # Package import
    from .ivplot import ivplot
except ImportError:
    # Fallback: standalone script
    from ivplot import ivplot

# For thumbnails (static image export)
try:
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False


def ivplot_gallery(transistors, output_dir, auto_open=True, **ivplot_kwargs):
    """
    For each transistor, call ivplot() to generate an individual HTML file,
    then build a gallery HTML combining all plots into one scrollable page.

    Any extra kwargs passed to ivplot_gallery(...) are forwarded to ivplot(),
    except for the ones that must be overridden:
      - html_path: per-transistor HTML filename
      - name:      transistor name
      - auto_open: always False (only the gallery is auto-opened)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    html_files = {}
    meta_by_name = {}
    thumb_files = {}

    # ----------------------------------------------------------------------
    # 1. Generate individual IV plot HTML files (and thumbnails if possible)
    # ----------------------------------------------------------------------
    for name, transistor in transistors.items():
        out_file = output_dir / f"{name}.html"

        # Merge user kwargs with forced overrides
        kwargs = dict(ivplot_kwargs)
        kwargs.update({
            "html_path": str(out_file),
            "name": name,
            "auto_open": False,
        })

        print(f"Generating IV plot for {name}")
        fig = ivplot(transistor["sweeps"], **kwargs)
        html_files[name] = out_file.name  # relative filename

        # Collect metadata (anything except 'sweeps')
        meta_items = {k: v for k, v in transistor.items() if k != "sweeps"}
        meta_by_name[name] = meta_items

        # Try to build a thumbnail (3D log scene only) using plotly's static export
        if _HAS_PLOTLY and fig is not None:
            # Select traces in the log 3D scene (usually 'scene')
            log3d_traces = [
                tr for tr in fig.data
                if getattr(tr, "type", "").startswith("scatter3d")
                and getattr(tr, "scene", "scene") == "scene"
            ]
            if log3d_traces:
                thumb_fig = go.Figure(data=log3d_traces, layout=fig.layout)
                thumb_fig.update_layout(
                    showlegend=False,
                    margin=dict(l=0, r=0, t=0, b=0),
                    width=500,
                    height=350,
                )
                thumb_path = output_dir / f"{name}_thumb.png"
                thumb_fig.write_image(str(thumb_path))
                thumb_files[name] = thumb_path.name

    # ----------------------------------------------------------------------
    # 2. Build gallery HTML with lazy-loading iframes, thumbnails, and UI
    # ----------------------------------------------------------------------
    gallery_file = output_dir / "index.html"
    lines = []

    lines.append("<!DOCTYPE html>")
    lines.append("<html>")
    lines.append("<head>")
    lines.append("<meta charset='UTF-8'>")
    lines.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    lines.append("<title>Transistor IV Plot Gallery</title>")
    lines.append(r"""
<style>
:root {
    color-scheme: light dark;
}

body {
    font-family: Arial, sans-serif;
    margin: 20px;
    background: #ffffff;
    color: #111111;
}

body.dark {
    background: #111111;
    color: #eeeeee;
}

h1 {
    text-align: center;
}

a {
    color: #1a5fb4;
}
body.dark a {
    color: #82aaff;
}

.plot-container {
    margin-top: 60px;
    border-top: 2px solid #aaa;
    padding-top: 20px;
}

.back-to-top {
    margin-top: 10px;
}

/* iframe (main plots) */
iframe.ivframe {
    width: 100%;
    height: 900px;
    border: none;
}

/* nav list */
.nav-list {
    line-height: 1.7;
}

/* status text */
.status {
    font-size: 0.9em;
    color: #555;
    margin-bottom: 8px;
}
body.dark .status {
    color: #ccc;
}
.status.loading::before {
    content: "⏳ ";
}
.status.loaded {
    color: #2b7a0b;
}
.status.loaded::before {
    content: "✔ ";
}
.status.error {
    color: #b00020;
}
.status.error::before {
    content: "⚠ ";
}

/* metadata list */
.meta {
    font-size: 0.9em;
    margin-bottom: 8px;
}
.meta dt {
    font-weight: bold;
}
.meta dd {
    margin: 0 0 4px 0;
}

/* thumbnail grid */
.thumb-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin: 10px 0 20px 0;
}
.thumb-item {
    width: 220px;
    text-align: center;
    font-size: 0.85em;
}
.thumb-item img {
    width: 100%;
    height: auto;
    border-radius: 4px;
    border: 1px solid #aaa;
    display: block;
}
body.dark .thumb-item img {
    border-color: #555;
}

/* fullscreen mode */
.plot-container.fullscreen {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: #000000;
    margin: 0;
    padding: 10px;
    border: none;
    overflow: auto;
}
.plot-container.fullscreen h2,
.plot-container.fullscreen .meta,
.plot-container.fullscreen .back-to-top,
.plot-container.fullscreen .status {
    color: #ffffff;
}
.plot-container.fullscreen iframe.ivframe {
    height: calc(100vh - 80px);
}

/* buttons */
.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    flex-wrap: wrap;
    gap: 8px;
}
button {
    cursor: pointer;
    padding: 4px 10px;
    font-size: 0.9em;
    border-radius: 4px;
    border: 1px solid #666;
    background: #f0f0f0;
    color: #111;
}
body.dark button {
    background: #333;
    color: #eee;
    border-color: #888;
}
.fs-btn {
    margin-bottom: 8px;
}
</style>

<script>
// Theme toggle + persist in localStorage
document.addEventListener('DOMContentLoaded', function() {
    const body = document.body;
    const storedTheme = localStorage.getItem('ivplot_theme');
    if (storedTheme === 'dark') {
        body.classList.add('dark');
    }

    const themeBtn = document.getElementById('themeToggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', function() {
            body.classList.toggle('dark');
            localStorage.setItem('ivplot_theme', body.classList.contains('dark') ? 'dark' : 'light');
        });
    }
});

// Fullscreen toggle
function toggleFullscreen(btn) {
    const container = btn.closest('.plot-container');
    if (!container) return;

    if (!document.fullscreenElement) {
        // Enter fullscreen
        if (container.requestFullscreen) {
            container.requestFullscreen();
        }
        container.classList.add('fullscreen');
        btn.textContent = 'Exit fullscreen';
    } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
        container.classList.remove('fullscreen');
        btn.textContent = 'Fullscreen';
    }
}

// Lazy-load and status handling for iframes
document.addEventListener('DOMContentLoaded', function() {
    const frames = Array.from(document.querySelectorAll('iframe.ivframe'));

    if (!('IntersectionObserver' in window)) {
        frames.forEach(f => startLoad(f));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const iframe = entry.target;
                if (!iframe.dataset.loaded) {
                    startLoad(iframe);
                }
            }
        });
    }, {
        root: null,
        rootMargin: '200px 0px',
        threshold: 0.1
    });

    frames.forEach(f => observer.observe(f));

    function startLoad(iframe) {
        const src = iframe.dataset.src;
        if (!src) return;
        if (iframe.dataset.loading === '1') return;

        iframe.dataset.loading = '1';
        const status = iframe.parentElement.querySelector('.status');
        if (status) {
            status.textContent = 'Loading...';
            status.className = 'status loading';
        }

        iframe.onerror = function() {
            handleError(iframe);
        };
        iframe.onload = function() {
            iframe.dataset.loaded = '1';
            iframe.dataset.loading = '0';
            const st = iframe.parentElement.querySelector('.status');
            if (st) {
                st.textContent = 'Loaded';
                st.className = 'status loaded';
            }
        };
        iframe.src = src;
    }

    function handleError(iframe) {
        const tries = parseInt(iframe.dataset.tries || '0', 10);
        const status = iframe.parentElement.querySelector('.status');
        if (tries < 2) {
            iframe.dataset.tries = String(tries + 1);
            if (status) {
                status.textContent = 'Error loading plot, retrying...';
                status.className = 'status error';
            }
            setTimeout(() => {
                iframe.removeAttribute('src');
                iframe.dataset.loading = '0';
                startLoad(iframe);
            }, 1000);
        } else {
            if (status) {
                status.textContent = 'Error loading plot (gave up).';
                status.className = 'status error';
            }
        }
    }
});
</script>
""")
    lines.append("</head>")
    lines.append("<body>")

    # Toolbar: theme toggle
    lines.append("<div class='toolbar'>")
    lines.append("<h1>Transistor IV Plot Gallery</h1>")
    lines.append("<button id='themeToggle'>Toggle dark / light theme</button>")
    lines.append("</div>")

    # Navigation + thumbnails
    lines.append("<h2>Jump to transistor:</h2>")
    lines.append("<ul class='nav-list'>")
    for name in html_files:
        safe = html.escape(name)
        lines.append(f"<li><a href='#{safe}'>{safe}</a></li>")
    lines.append("</ul>")

    if thumb_files:
        lines.append("<h3>Thumbnails (3D log view)</h3>")
        lines.append("<div class='thumb-grid'>")
        for name, thumb in thumb_files.items():
            safe = html.escape(name)
            thumb_esc = html.escape(thumb)
            lines.append("<div class='thumb-item'>")
            lines.append(
                f"<a href='#{safe}'><img src='{thumb_esc}' alt='Thumbnail: {safe}'></a>"
            )
            lines.append(f"<div>{safe}</div>")
            lines.append("</div>")
        lines.append("</div>")

    lines.append("<hr>")

    # Embedded plots
    for name, file in html_files.items():
        safe = html.escape(name)
        file_esc = html.escape(file)
        meta = meta_by_name.get(name, {})

        lines.append(f"<div class='plot-container' id='{safe}'>")
        lines.append(f"<h2>{safe}</h2>")

        # Metadata
        if meta:
            lines.append("<dl class='meta'>")
            for k, v in meta.items():
                key = html.escape(str(k))
                val = html.escape(str(v))
                lines.append(f"<dt>{key}</dt><dd>{val}</dd>")
            lines.append("</dl>")

        lines.append("<button class='fs-btn' onclick='toggleFullscreen(this)'>Fullscreen</button>")
        lines.append("<div class='status loading'>Waiting to load…</div>")
        lines.append(
            f"<iframe class='ivframe' data-src='{file_esc}' loading='lazy'></iframe>"
        )
        lines.append("<div class='back-to-top'><a href='#'>Back to top</a></div>")
        lines.append("</div>")

    lines.append("</body></html>")

    gallery_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Gallery created: {gallery_file}")

    if auto_open:
        import webbrowser, os
        webbrowser.open("file://" + os.path.abspath(gallery_file))

    return gallery_file
