from pathlib import Path
import html

try:
    # Package import
    from .ivplot import ivplot
except ImportError:
    # Fallback: standalone script
    from ivplot import ivplot

def ivplot_gallery(transistors, output_dir, auto_open=True):
    """
    For each transistor, call ivplot() to generate an individual HTML file,
    then build a gallery HTML combining all plots into one scrollable page.

    Parameters
    ----------
    transistors : dict
        Dict mapping transistor names to dicts that contain:
        - 'sweeps': sweep data (the input to ivplot)
    output_dir : str or Path
        Directory where plot HTML files and gallery HTML will be saved.

    Returns
    -------
    Path to gallery HTML file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    html_files = {}

    # 1. Generate individual ivplot HTML files
    for name, transistor in transistors.items():
        out_file = output_dir / f"{name}.html"
        kwargs = {
            "surf": False,
            "markersize": 6,
            "html_path": str(out_file),
            "name": name,
            "marker":"o", 
            "auto_open":False,
        }
        print(f"Generating IV plot for {name}")
        ivplot(transistor["sweeps"], **kwargs)
        html_files[name] = out_file.name  # relative filename

    # 2. Build gallery HTML with lazy-loading iframes
    gallery_file = output_dir / "index.html"
    lines = []

    lines.append("<!DOCTYPE html>")
    lines.append("<html>")
    lines.append("<head>")
    lines.append("<meta charset='UTF-8'>")
    lines.append("<title>Transistor IV Plot Gallery</title>")
    lines.append(r"""
<style>
body {
    font-family: Arial, sans-serif;
    margin: 20px;
}
h1 {
    text-align: center;
}
.plot-container {
    margin-top: 60px;
    border-top: 2px solid #aaa;
    padding-top: 20px;
}
.back-to-top {
    margin-top: 10px;
}
iframe.ivframe {
    width: 100%;
    height: 900px;
    border: none;
}
.nav-list {
    line-height: 1.7;
}
.status {
    font-size: 0.9em;
    color: #555;
    margin-bottom: 8px;
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
</style>
<script>
// Lazy-load and status handling for iframes
document.addEventListener('DOMContentLoaded', function() {
    const frames = Array.from(document.querySelectorAll('iframe.ivframe'));

    if (!('IntersectionObserver' in window)) {
        // Fallback: just load all at once (old browsers)
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
        rootMargin: '200px 0px',  // start loading a bit before it enters
        threshold: 0.1
    });

    frames.forEach(f => observer.observe(f));

    function startLoad(iframe) {
        const src = iframe.dataset.src;
        if (!src) return;
        if (iframe.dataset.loading === '1') return;  // already loading

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
        // Begin load
        iframe.src = src;
    }

    function handleError(iframe) {
        const tries = parseInt(iframe.dataset.tries || '0', 10);
        const status = iframe.parentElement.querySelector('.status');
        if (tries < 2) { // retry up to 2 times
            iframe.dataset.tries = String(tries + 1);
            if (status) {
                status.textContent = 'Error loading plot, retrying...';
                status.className = 'status error';
            }
            // Small delay then retry
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

    # Navigation links at the top
    lines.append("<h1>Transistor IV Plot Gallery</h1>")
    lines.append("<h2>Jump to transistor:</h2>")
    lines.append("<ul class='nav-list'>")
    for name in html_files:
        safe = html.escape(name)
        lines.append(f"<li><a href='#{safe}'>{safe}</a></li>")
    lines.append("</ul>")
    lines.append("<hr>")

    # Embedded plots (lazy-loaded)
    for name, file in html_files.items():
        safe = html.escape(name)
        file_esc = html.escape(file)
        lines.append(f"<div class='plot-container' id='{safe}'>")
        lines.append(f"<h2>{safe}</h2>")
        lines.append("<div class='status loading'>Waiting to load…</div>")
        # Use data-src for lazy loading, not src
        lines.append(
            f"<iframe class='ivframe' data-src='{file_esc}' loading='lazy'></iframe>"
        )
        lines.append(
            "<div class='back-to-top'><a href='#'>Back to top</a></div>"
        )
        lines.append("</div>")

    lines.append("</body></html>")

    gallery_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Gallery created: {gallery_file}")
    if auto_open:
        import webbrowser, os
        webbrowser.open("file://" + os.path.abspath(gallery_file))    
    return gallery_file
