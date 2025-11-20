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

    # ---------------------------------------------------------------
    # 1. Generate individual ivplot HTML files
    # ---------------------------------------------------------------
    for name, transistor in transistors.items():
        out_file = output_dir / f"{name}.html"

        kwargs = {
            "surf": False,
            "markersize": 6,
            "marker": "o", 
            "html_path": str(out_file),
            "name": name,
            "auto_open": False
        }

        print(f"Generating IV plot for {name}")
        ivplot(transistor["sweeps"], **kwargs)

        html_files[name] = out_file.name  # relative path

    # ---------------------------------------------------------------
    # 2. Build gallery HTML
    # ---------------------------------------------------------------
    gallery_file = output_dir / "ivplot_gallery.html"

    lines = []

    lines.append("<!DOCTYPE html>")
    lines.append("<html>")
    lines.append("<head>")
    lines.append("<meta charset='UTF-8'>")
    lines.append("<title>Transistor IV Plot Gallery</title>")
    lines.append("""
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
iframe {
    width: 100%;
    height: 900px;
    border: none;
}
.nav-list {
    line-height: 1.7;
}
</style>
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

    # Embedded plots
    for name, file in html_files.items():
        safe = html.escape(name)

        lines.append(f"<div class='plot-container' id='{safe}'>")
        lines.append(f"<h2>{safe}</h2>")

        lines.append(
            f"<iframe src='{html.escape(file)}'></iframe>"
        )

        lines.append(
            f"<div class='back-to-top'><a href='#'>Back to top</a></div>"
        )

        lines.append("</div>")

    lines.append("</body></html>")

    gallery_file.write_text("\n".join(lines), encoding="utf-8")

    print(f"Gallery created: {gallery_file}")
    if auto_open:
        import webbrowser, os
        webbrowser.open("file://" + os.path.abspath(gallery_file))
    
    return gallery_file
