# ddrescue Log Visualizer

A tool to visualize GNU ddrescue mapfiles as horizontal bar charts with color-coded regions.

## Features

- **Terminal output**: Color-coded ASCII visualization
- **PNG export**: Generate static image files
- **Interactive HTML**: Hover over regions for detailed tooltips showing position, size, and status

## Status Colors

- **Green** (+): Successfully copied
- **Yellow** (*): Scraping/partial recovery
- **Red** (?): Non-tried regions
- **Magenta** (-): Failed regions

## Usage

### Terminal Output
```bash
./visualize.py rescue.log
```

### Generate PNG
```bash
./visualize.py rescue.log --png output.png
```

### Generate Interactive HTML
```bash
./visualize.py rescue.log --html output.html
```

### Generate Both
```bash
./visualize.py rescue.log --png --html
```

### Custom Terminal Width
```bash
./visualize.py rescue.log --width 150
```

## Requirements

- Python 3.6+
- For PNG output: `pip install Pillow`

## Example Output

The tool shows:
- Total disk size
- Number of regions
- Statistics for each status type
- Visual bar chart representation
- Percentage completion

For the HTML output, hover over any region to see detailed information including exact position and size.
