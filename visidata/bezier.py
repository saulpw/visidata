import math


def bezier(x1, y1, x2, y2, x3, y3):
    'Generate (x,y) coordinates on quadratic curve from (x1,y1) to (x3,y3) with control point at (x2,y2).'
    yield (x1, y1)
    yield from _recursive_bezier(x1, y1, x2, y2, x3, y3)
    yield (x3, y3)


def _recursive_bezier(x1, y1, x2, y2, x3, y3, level=0):
    'from http://www.antigrain.com/research/adaptive_bezier/'
    m_approximation_scale = 10.0
    m_distance_tolerance = (0.5 / m_approximation_scale) ** 2
    m_angle_tolerance = 1 * 2*math.pi/360  # 15 degrees in rads
    curve_angle_tolerance_epsilon = 0.01
    curve_recursion_limit = 32
    curve_collinearity_epsilon = 1e-30

    if level > curve_recursion_limit:
        return

    # Calculate all the mid-points of the line segments

    x12   = (x1 + x2) / 2
    y12   = (y1 + y2) / 2
    x23   = (x2 + x3) / 2
    y23   = (y2 + y3) / 2
    x123  = (x12 + x23) / 2
    y123  = (y12 + y23) / 2

    dx = x3-x1
    dy = y3-y1
    d = abs(((x2 - x3) * dy - (y2 - y3) * dx))

    if d > curve_collinearity_epsilon:
        # Regular care
        if d*d <= m_distance_tolerance * (dx*dx + dy*dy):
            # If the curvature doesn't exceed the distance_tolerance value, we tend to finish subdivisions.
            if m_angle_tolerance < curve_angle_tolerance_epsilon:
                yield (x123, y123)
                return

            # Angle & Cusp Condition
            da = abs(math.atan2(y3 - y2, x3 - x2) - math.atan2(y2 - y1, x2 - x1))
            if da >= math.pi:
                da = 2*math.pi - da

            if da < m_angle_tolerance:
                # Finally we can stop the recursion
                yield (x123, y123)
                return
    else:
        # Collinear case
        dx = x123 - (x1 + x3) / 2
        dy = y123 - (y1 + y3) / 2
        if dx*dx + dy*dy <= m_distance_tolerance:
            yield (x123, y123)
            return

    # Continue subdivision
    yield from _recursive_bezier(x1, y1, x12, y12, x123, y123, level + 1)
    yield from _recursive_bezier(x123, y123, x23, y23, x3, y3, level + 1)
