'''
Functions for geographic overlap of STAC bboxes against named places.

`.visidatarc`: ``import visidata.experimental.search_geo``

Adds three functions to the VisiData expression namespace, usable from
``addcol-expr`` and ``setcol-expr`` against any sheet that has a STAC-shaped
``extent`` column:

- ``overlaps(extent, place)`` -> intersection bbox ``[w, s, e, n]`` or ``None``
  (``place`` may be a name from the gazetteer or a literal ``[w, s, e, n]``).
- ``area(bbox)`` -> degree² (rough; longitude degrees aren't equal-area).
- ``bbox_for(place)`` -> the gazetteer bbox, for inspection.

Demo flow on ``catalog.jsonl``::

    =ov=overlaps(extent, "Seattle")          # intersection bbox or None
    =overlap_area=area(ov)                   # sort desc -> most overlap
    =dataset_area=area(extent)               # sort asc  -> most specific dataset
'''
from visidata import vd  # pyright: ignore[reportMissingImports]


# Canned demo gazetteer: lowercased name -> [west, south, east, north].
# Roughly metro-region scale so real overlaps register, not point hits.
GAZETTEER = {
    "seattle":         [-122.46,  47.49, -122.22,  47.78],
    "san-francisco":   [-122.55,  37.70, -122.35,  37.83],
    "sf":              [-122.55,  37.70, -122.35,  37.83],
    "los-angeles":     [-118.67,  33.70, -118.15,  34.34],
    "la":              [-118.67,  33.70, -118.15,  34.34],
    "denver":          [-105.11,  39.61, -104.83,  39.91],
    "boulder":         [-105.30,  39.96, -105.18,  40.09],
    "new-york":        [ -74.26,  40.49,  -73.70,  40.92],
    "nyc":             [ -74.26,  40.49,  -73.70,  40.92],
    "washington-dc":   [ -77.12,  38.79,  -76.91,  38.99],
    "philadelphia":    [ -75.28,  39.87,  -74.96,  40.14],
    "philly":          [ -75.28,  39.87,  -74.96,  40.14],
    "vancouver":       [-123.27,  49.20, -123.02,  49.32],
    "mexico-city":     [ -99.36,  19.18,  -98.94,  19.59],
    "sao-paulo":       [ -46.83, -23.78,  -46.36, -23.39],
    "london":          [  -0.51,  51.28,   0.33,  51.69],
    "paris":           [   2.22,  48.81,   2.47,  48.91],
    "berlin":          [  13.09,  52.34,  13.76,  52.68],
    "copenhagen":      [  12.45,  55.61,  12.71,  55.73],
    "lagos":           [   3.11,   6.39,   3.68,   6.71],
    "cairo":           [  31.16,  29.95,  31.42,  30.18],
    "johannesburg":    [  27.92, -26.32,  28.18, -26.04],
    "mumbai":          [  72.78,  18.89,  72.99,  19.27],
    "tokyo":           [ 139.55,  35.52, 139.92,  35.82],
    "sydney":          [ 150.97, -34.12, 151.34, -33.69],
    # whole-region helpers
    "conus":           [-124.74,  24.52,  -66.95,  49.38],
    "europe":          [ -10.0,   34.0,    40.0,   71.0],
}


def _coerce_to_boxes(value):
    """Normalize ``value`` into a list of ``[w,s,e,n]`` boxes, or ``[]``.

    Accepts: gazetteer name (str), single bbox ``[w,s,e,n]``, list-of-bboxes,
    or a STAC ``extent`` dict ``{spatial: {bbox: [...]}}``.
    """
    if value is None:
        return []
    if isinstance(value, str):
        key = value.strip().lower().replace(" ", "-")
        if key in GAZETTEER:
            return [GAZETTEER[key]]
        return []
    if isinstance(value, dict):
        sp = value.get("spatial")
        if isinstance(sp, dict):
            return _coerce_to_boxes(sp.get("bbox"))
        return _coerce_to_boxes(value.get("bbox"))
    if isinstance(value, (list, tuple)) and value:
        if isinstance(value[0], (list, tuple)):
            return [list(b) for b in value if b and len(b) >= 4]
        if len(value) >= 4 and all(isinstance(x, (int, float)) for x in value[:4]):
            return [list(value[:4])]
    return []


def _intersect(a, b):
    """Intersection of two ``[w,s,e,n]`` boxes, or ``None`` if disjoint.

    Antimeridian wraps are not handled; treat as a known limitation for the
    demo. (No place in the gazetteer crosses 180°.)
    """
    w = max(a[0], b[0])
    s = max(a[1], b[1])
    e = min(a[2], b[2])
    n = min(a[3], b[3])
    if w >= e or s >= n:
        return None
    return [w, s, e, n]


def overlaps(extent, place):
    """Intersection bbox of ``extent`` (any accepted shape) and ``place``.

    Returns the union of all per-pair intersections as a single covering
    bbox, or ``None`` if disjoint. Good enough for the demo's ranking use.
    """
    a_boxes = _coerce_to_boxes(extent)
    b_boxes = _coerce_to_boxes(place)
    if not a_boxes or not b_boxes:
        return None
    parts = []
    for a in a_boxes:
        for b in b_boxes:
            p = _intersect(a, b)
            if p:
                parts.append(p)
    if not parts:
        return None
    w = min(p[0] for p in parts)
    s = min(p[1] for p in parts)
    e = max(p[2] for p in parts)
    n = max(p[3] for p in parts)
    return [w, s, e, n]


def area(value):
    """Sum of degree² area across one-or-more ``[w,s,e,n]`` boxes.

    Returns 0.0 if ``value`` doesn't reduce to any box. This is planar
    degrees-squared; longitude degrees shrink toward the poles, so use
    this for ranking only, not for real area math.
    """
    total = 0.0
    for b in _coerce_to_boxes(value):
        total += max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return total


def bbox_for(place):
    """Return the gazetteer bbox for ``place``, or ``None``."""
    boxes = _coerce_to_boxes(place)
    return boxes[0] if boxes else None


vd.addGlobals({
    "overlaps":  overlaps,
    "area":      area,
    "bbox_for":  bbox_for,
    "GEO_PLACES": GAZETTEER,
})
