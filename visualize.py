#!/usr/bin/env python3
"""
Visualizes ddrescue log files as a horizontal bar chart.
"""

import sys
import re


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


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <ddrescue_log_file>")
        sys.exit(1)

    visualize_ddrescue(sys.argv[1])
