import os
import numpy as np
import matplotlib.pyplot as plt

class PlotProperties:
    def __init__(self, subpath: str, add_v_line: bool = False):
        self.x_label = None
        self.y_label = None
        self.x_vals = None
        self.ys = {}
        self.path = os.path.join("artifacts/Numerical", subpath)
        self.add_v_line = add_v_line

    def update_x(self, x_label: str, x_vlas: np.ndarray):
        if not self.x_label and not self.x_vals:
            self.x_label = x_label
            self.x_vals = x_vlas
        elif self.x_label != x_label and self.x_vals != x_vlas:
            raise ValueError(f"X values do not match: ({self.x_label}, {self.x_vals}) != ({x_label}, {x_vlas})")

    def update_ys(self, y_label: str, y_legend: str, y_vals: np.ndarray, y_lim: tuple[float, float] = None):
        if not self.y_label:
            self.y_label = y_label
        elif self.y_label != y_label:
            raise ValueError(f"Y label does not match: {self.y_label} != {y_label}")

        self.ys[y_legend] = (y_vals, y_lim)

    @staticmethod
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

    @staticmethod
    def _add_avg_zero_vline(ax, which='first', ref=None, vline_kws=None,
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
            xs = PlotProperties._zero_crossings_x(x, y)
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

    # Collect and deduplicate legend handles and labels
    @staticmethod
    def get_unique_legend(ax):
        seen = set()
        unique_handles = []
        unique_labels = []

        handles, labels = ax.get_legend_handles_labels()
        for h, l in zip(handles, labels):
            if l not in seen:
                unique_handles.append(h)
                unique_labels.append(l)
                seen.add(l)

        return unique_handles, unique_labels

    def plot(self):
        fig, axis = plt.subplots()

        for y_legend, (y_values, y_lim) in self.ys.items():
            axis.plot(self.x_vals, y_values, label=y_legend)
            if y_lim:
                axis.set_ylim(y_lim)

        axis.set_xlabel(self.x_label)
        axis.set_ylabel(self.y_label)
        axis.grid(True)

        if self.add_v_line:
            PlotProperties._add_avg_zero_vline(axis, which='first', vline_kws={'color': 'black', 'linestyle': '--'})

        handles, labels = PlotProperties.get_unique_legend(axis)
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        fig.savefig(self.path, bbox_inches='tight')
        plt.close(fig)