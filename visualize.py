#!/usr/bin/env python3
"""
Visualizes ddrescue log files as a horizontal bar chart.
Supports terminal output, PNG image, and interactive HTML.
"""

import sys
import argparse
from pathlib import Path


def parse_ddrescue_log(filename):
    """Parse a ddrescue log file and return list of (pos, size, status) tuples."""
    regions = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) == 3:
                # Check if parts[1] is a valid hex number
                try:
                    pos = int(parts[0], 16)
                    size = int(parts[1], 16)
                    status = parts[2]
                    regions.append((pos, size, status))
                except ValueError:
                    # Skip lines that don't match the format (like current position)
                    continue

    return regions


def get_color_code(status):
    """Return ANSI color code for status."""
    colors = {
        '+': '\033[92m',  # Green - successfully copied
        '*': '\033[93m',  # Yellow - scraping/partial
        '?': '\033[91m',  # Red - non-tried
        '-': '\033[95m',  # Magenta - failed
    }
    return colors.get(status, '\033[0m')


def get_rgb_color(status):
    """Return RGB color tuple for status."""
    colors = {
        '+': (76, 175, 80),   # Green - successfully copied
        '*': (255, 193, 7),   # Yellow - scraping/partial
        '?': (244, 67, 54),   # Red - non-tried
        '-': (156, 39, 176),  # Magenta - failed
    }
    return colors.get(status, (128, 128, 128))


def format_size(bytes_val):
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} EB"


def visualize_ddrescue(filename, width=100):
    """Create a horizontal bar chart visualization of ddrescue log."""
    regions = parse_ddrescue_log(filename)

    if not regions:
        print("No data found in log file")
        return

    # Calculate total disk size
    max_pos = max(pos + size for pos, size, _ in regions)

    # Create visualization
    print(f"\nDisk Size: {format_size(max_pos)}")
    print(f"Total Regions: {len(regions)}\n")

    # Calculate statistics
    stats = {'+': 0, '*': 0, '?': 0, '-': 0}
    for pos, size, status in regions:
        stats[status] = stats.get(status, 0) + size

    print("Legend:")
    print(f"  {get_color_code('+')}█\033[0m Green  (+) - Successfully copied: {format_size(stats.get('+', 0))}")
    print(f"  {get_color_code('*')}█\033[0m Yellow (*) - Scraping/partial:   {format_size(stats.get('*', 0))}")
    print(f"  {get_color_code('?')}█\033[0m Red    (?) - Non-tried:          {format_size(stats.get('?', 0))}")
    print(f"  {get_color_code('-')}█\033[0m Magenta(-) - Failed:             {format_size(stats.get('-', 0))}")
    print()

    # Build the bar
    bar = [''] * width
    reset = '\033[0m'

    for pos, size, status in regions:
        start_idx = int((pos / max_pos) * width)
        end_idx = int(((pos + size) / max_pos) * width)

        # Ensure at least one character for very small regions
        if start_idx == end_idx and size > 0:
            end_idx = start_idx + 1

        end_idx = min(end_idx, width)

        color = get_color_code(status)
        for i in range(start_idx, end_idx):
            if i < width:
                bar[i] = f"{color}█{reset}"

    # Fill empty spaces
    for i in range(width):
        if bar[i] == '':
            bar[i] = ' '

    # Print the bar
    print("Disk map:")
    print("├" + "─" * width + "┤")
    print("│" + "".join(bar) + "│")
    print("└" + "─" * width + "┘")
    print("0%" + " " * (width - 7) + "100%")
    print()


def calculate_statistics(regions):
    """Calculate statistics for regions."""
    stats = {'+': 0, '*': 0, '?': 0, '-': 0}
    for pos, size, status in regions:
        stats[status] = stats.get(status, 0) + size
    return stats


def generate_png(filename, output_file, width=1200, height=200):
    """Generate a PNG visualization of the ddrescue log."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Error: PIL/Pillow is required for PNG output.")
        print("Install with: pip install Pillow")
        sys.exit(1)

    regions = parse_ddrescue_log(filename)
    if not regions:
        print("No data found in log file")
        return

    max_pos = max(pos + size for pos, size, _ in regions)
    stats = calculate_statistics(regions)

    # Create image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw title and stats
    title_height = 80
    bar_height = 60
    bar_y = title_height + 20

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Title
    draw.text((10, 10), f"Disk Size: {format_size(max_pos)}", fill='black', font=font_title)

    # Legend
    legend_y = 35
    legend_items = [
        ('+', 'Successfully copied', stats.get('+', 0)),
        ('*', 'Scraping/partial', stats.get('*', 0)),
        ('?', 'Non-tried', stats.get('?', 0)),
        ('-', 'Failed', stats.get('-', 0)),
    ]

    x_offset = 10
    for status, label, size in legend_items:
        color = get_rgb_color(status)
        draw.rectangle([x_offset, legend_y, x_offset + 15, legend_y + 15], fill=color, outline='black')
        text = f"{label}: {format_size(size)}"
        draw.text((x_offset + 20, legend_y), text, fill='black', font=font_text)
        x_offset += 250

    # Draw bar
    bar_margin = 40
    bar_width = width - 2 * bar_margin

    for pos, size, status in regions:
        start_x = bar_margin + int((pos / max_pos) * bar_width)
        end_x = bar_margin + int(((pos + size) / max_pos) * bar_width)

        if end_x <= start_x:
            end_x = start_x + 1

        color = get_rgb_color(status)
        draw.rectangle([start_x, bar_y, end_x, bar_y + bar_height], fill=color)

    # Draw border around bar
    draw.rectangle([bar_margin, bar_y, bar_margin + bar_width, bar_y + bar_height], outline='black', width=2)

    # Draw percentage labels
    draw.text((bar_margin - 10, bar_y + bar_height + 10), "0%", fill='black', font=font_text)
    draw.text((bar_margin + bar_width - 20, bar_y + bar_height + 10), "100%", fill='black', font=font_text)

    img.save(output_file)
    print(f"PNG saved to: {output_file}")


def generate_html(filename, output_file, width=1200):
    """Generate an interactive HTML visualization of the ddrescue log."""
    regions = parse_ddrescue_log(filename)
    if not regions:
        print("No data found in log file")
        return

    max_pos = max(pos + size for pos, size, _ in regions)
    stats = calculate_statistics(regions)

    # Build SVG elements for regions
    svg_elements = []
    for i, (pos, size, status) in enumerate(regions):
        start_pct = (pos / max_pos) * 100
        width_pct = (size / max_pos) * 100

        if width_pct < 0.01:
            width_pct = 0.01

        color = get_rgb_color(status)
        color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

        status_names = {
            '+': 'Successfully copied',
            '*': 'Scraping/partial',
            '?': 'Non-tried',
            '-': 'Failed'
        }

        tooltip = f"Region {i+1}\\nStatus: {status_names.get(status, 'Unknown')}\\nPosition: {format_size(pos)}\\nSize: {format_size(size)}\\nRange: {format_size(pos)} - {format_size(pos + size)}"

        svg_elements.append(f'''
        <rect x="{start_pct}%" y="0" width="{width_pct}%" height="100%"
              fill="{color_hex}"
              class="region region-{status}"
              data-tooltip="{tooltip}">
        </rect>''')

    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ddrescue Log Visualization</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: {width}px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid;
        }}
        .stat-box.success {{ border-color: rgb(76, 175, 80); background: rgba(76, 175, 80, 0.1); }}
        .stat-box.scraping {{ border-color: rgb(255, 193, 7); background: rgba(255, 193, 7, 0.1); }}
        .stat-box.nontried {{ border-color: rgb(244, 67, 54); background: rgba(244, 67, 54, 0.1); }}
        .stat-box.failed {{ border-color: rgb(156, 39, 176); background: rgba(156, 39, 176, 0.1); }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin: 5px 0;
        }}
        .stat-desc {{
            font-size: 14px;
            color: #999;
        }}
        .visualization {{
            margin: 30px 0;
        }}
        .bar-container {{
            position: relative;
            height: 80px;
            border: 2px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
            background: #f9f9f9;
        }}
        svg {{
            width: 100%;
            height: 100%;
        }}
        .region {{
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .region:hover {{
            opacity: 0.8;
        }}
        .labels {{
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 12px;
            color: #666;
        }}
        .tooltip {{
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 13px;
            pointer-events: none;
            display: none;
            z-index: 1000;
            white-space: pre-line;
            max-width: 300px;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ddrescue Log Visualization</h1>
        <p>Disk Size: <strong>{format_size(max_pos)}</strong> | Total Regions: <strong>{len(regions)}</strong></p>

        <div class="stats">
            <div class="stat-box success">
                <div class="stat-label">Successfully Copied</div>
                <div class="stat-value">{format_size(stats.get('+', 0))}</div>
                <div class="stat-desc">{(stats.get('+', 0) / max_pos * 100):.2f}% of disk</div>
            </div>
            <div class="stat-box scraping">
                <div class="stat-label">Scraping/Partial</div>
                <div class="stat-value">{format_size(stats.get('*', 0))}</div>
                <div class="stat-desc">{(stats.get('*', 0) / max_pos * 100):.2f}% of disk</div>
            </div>
            <div class="stat-box nontried">
                <div class="stat-label">Non-tried</div>
                <div class="stat-value">{format_size(stats.get('?', 0))}</div>
                <div class="stat-desc">{(stats.get('?', 0) / max_pos * 100):.2f}% of disk</div>
            </div>
            <div class="stat-box failed">
                <div class="stat-label">Failed</div>
                <div class="stat-value">{format_size(stats.get('-', 0))}</div>
                <div class="stat-desc">{(stats.get('-', 0) / max_pos * 100):.2f}% of disk</div>
            </div>
        </div>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: rgb(76, 175, 80);"></div>
                <span>Successfully copied (+)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgb(255, 193, 7);"></div>
                <span>Scraping/partial (*)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgb(244, 67, 54);"></div>
                <span>Non-tried (?)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgb(156, 39, 176);"></div>
                <span>Failed (-)</span>
            </div>
        </div>

        <div class="visualization">
            <div class="bar-container">
                <svg viewBox="0 0 100 100" preserveAspectRatio="none">
                    {''.join(svg_elements)}
                </svg>
            </div>
            <div class="labels">
                <span>0%</span>
                <span>100%</span>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const regions = document.querySelectorAll('.region');
        const tooltip = document.getElementById('tooltip');

        regions.forEach(region => {{
            region.addEventListener('mouseenter', (e) => {{
                tooltip.textContent = e.target.dataset.tooltip;
                tooltip.style.display = 'block';
            }});

            region.addEventListener('mousemove', (e) => {{
                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
            }});

            region.addEventListener('mouseleave', () => {{
                tooltip.style.display = 'none';
            }});
        }});
    </script>
</body>
</html>'''

    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"HTML saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Visualize ddrescue log files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s rescue.log                    # Terminal output
  %(prog)s rescue.log --png output.png   # PNG output
  %(prog)s rescue.log --html output.html # Interactive HTML
  %(prog)s rescue.log --png --html       # Generate both
        '''
    )
    parser.add_argument('logfile', help='ddrescue log file to visualize')
    parser.add_argument('--png', nargs='?', const='rescue.png', metavar='FILE',
                        help='Generate PNG output (default: rescue.png)')
    parser.add_argument('--html', nargs='?', const='rescue.html', metavar='FILE',
                        help='Generate HTML output (default: rescue.html)')
    parser.add_argument('--width', type=int, default=100,
                        help='Width for terminal output (default: 100)')

    args = parser.parse_args()

    # If no output format specified, show terminal output
    if not args.png and not args.html:
        visualize_ddrescue(args.logfile, args.width)
    else:
        if args.png:
            generate_png(args.logfile, args.png)
        if args.html:
            generate_html(args.logfile, args.html)
