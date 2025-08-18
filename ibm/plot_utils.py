import numpy as np
import matplotlib.pyplot as plt

def _zero_crossings_x(x, y):
    """
    Return all x-positions where y crosses 0 (linear interpolation between points).
    Works even if x is descending. Ignores NaNs. Includes exact zeros.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    m = np.isfinite(x) & np.isfinite(y)
    x = x[m]; y = y[m]
    if x.size < 2:
        return np.array([])

    # exact zeros land directly on x
    hits = x[y == 0]

    # sign changes between consecutive samples
    sgn = np.signbit(y)
    idx = np.flatnonzero(sgn[:-1] != sgn[1:])
    if idx.size:
        x0 = x[idx];      x1 = x[idx + 1]
        y0 = y[idx];      y1 = y[idx + 1]
        # linear interpolation for y=0: x = x0 - y0*(x1-x0)/(y1-y0)
        xc = x0 - y0 * (x1 - x0) / (y1 - y0)
        hits = np.concatenate([hits, xc])

    return np.unique(np.sort(hits))


def add_avg_zero_vline(ax, which='first', ref=None, vline_kws=None,
                       annotate=True, label_fmt='{x:.2g}'):
    """
    Scan all visible Line2D objects in `ax`, find one zero-crossing per line,
    average those x's, and draw a vertical line at the average.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    which : {'first','last','closest'}
        Which crossing to pick per line if a line has multiple.
        - 'first'  : smallest x crossing
        - 'last'   : largest x crossing
        - 'closest': crossing closest to `ref`
    ref : float or None
        Reference x used when which='closest'.
    vline_kws : dict or None
        Passed to `ax.axvline` (e.g., {'linestyle':'--','linewidth':1.5})
    annotate : bool
        If True, annotate the x-value near the axis.
    label_fmt : str
        Format string for the annotation; `{x}` gets substituted.

    Returns
    -------
    x_avg : float or None
        The averaged zero-crossing x, or None if no lines cross zero.
    """
    vline_kws = {'linestyle': '--', 'linewidth': 1.5, 'color': '0.3'} | (vline_kws or {})

    crossings = []
    for line in ax.get_lines():
        if not line.get_visible():
            continue
        x = line.get_xdata(orig=False)
        y = line.get_ydata(orig=False)
        xs = _zero_crossings_x(x, y)
        if xs.size == 0:
            return None
        if which == 'last':
            crossings.append(xs[-1])
        elif which == 'closest' and ref is not None:
            crossings.append(xs[np.argmin(np.abs(xs - ref))])
        else:  # default 'first'
            crossings.append(xs[0])

    if not crossings:
        return None

    x_avg = float(np.mean(crossings))
    ax.axvline(x_avg, **vline_kws)
    if annotate:
        ax.annotate(label_fmt.format(x=x_avg),
                    xy=(x_avg, 0), xytext=(x_avg, 0.9),
                    textcoords='axes fraction',
                    va='bottom', ha='center', bbox=dict(facecolor='white'))
    return x_avg


def add_avg_zero_vline_all_axes(fig=None, **kwargs):
    """
    Apply add_avg_zero_vline to every axes in a figure.
    Returns a dict {ax: x_avg or None}.
    """
    fig = fig or plt.gcf()
    results = {}
    for ax in fig.get_axes():
        results[ax] = add_avg_zero_vline(ax, **kwargs)
    return results
