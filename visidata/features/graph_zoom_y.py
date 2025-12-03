# contributed by Ram Rachum (@cool-RR) via ChatGPT  #2751

from visidata import GraphSheet

@GraphSheet.api
def zoom_all_y(sheet):
    """Find the lowest and highest y values in the current visible plot and set the y range to that."""
    ymin, ymax = None, None
    
    # Find the min and max y values of all points within the current x range
    xmin, xmax = sheet.visibleBox.xmin, sheet.visibleBox.xmax
    
    for vertexes, attr, row in sheet.polylines:
        if attr in sheet.hiddenAttrs:
            continue
            
        for x, y in vertexes:
            # Check if the point is within the current x range
            if xmin <= x <= xmax:
                if ymin is None or y < ymin:
                    ymin = y
                if ymax is None or y > ymax:
                    ymax = y
    
    if ymin is None or ymax is None:
        # No visible points found
        return
    
    # Add a 5% margin on both top and bottom
    y_range = ymax - ymin
    margin = sheet.ycols[0].type(y_range * 0.05)
    
    # Calculate adjusted min/max with margin
    adj_ymin = ymin - margin
    adj_ymax = ymax + margin
    
    # Create 5 equally spaced y ticks from real min to real max (not adjusted with margin)
    step = (ymax - ymin) / 4  # 5 ticks means 4 intervals
    y_ticks = tuple(ymin + step * i for i in range(5))
    
    # Set the y range with margin
    sheet.set_y(f"{adj_ymin} {adj_ymax}")
    
    # Set custom y ticks (using the real min/max, not the adjusted ones)
    sheet.forced_y_ticks = y_ticks

GraphSheet.addCommand('g_', 'zoom-all-y', 'zoom_all_y()', 'Zoom y-axis to fit all visible data points')
