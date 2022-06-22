import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from magpylib._src.display.traces_generic import get_frames
from magpylib._src.display.traces_generic import subdivide_mesh_by_facecolor

# from magpylib._src.utility import format_obj_input


def generic_trace_to_matplotlib(trace):
    """Transform a generic trace into a matplotlib trace"""
    traces_mpl = []
    if trace["type"] == "mesh3d":
        subtraces = [trace]
        if trace.get("facecolor", None) is not None:
            subtraces = subdivide_mesh_by_facecolor(trace)
        for subtrace in subtraces:
            x, y, z = np.array([subtrace[k] for k in "xyz"], dtype=float)
            triangles = np.array([subtrace[k] for k in "ijk"]).T
            trace_mpl = {
                "constructor": "plot_trisurf",
                "args": (x, y, z),
                "kwargs": {
                    "triangles": triangles,
                    "alpha": subtrace.get("opacity", None),
                    "color": subtrace.get("color", None),
                },
            }
            traces_mpl.append(trace_mpl)
    elif trace["type"] == "scatter3d":
        x, y, z = np.array([trace[k] for k in "xyz"], dtype=float)
        mode = trace.get("mode", None)
        props = {
            k: trace.get(v[0], {}).get(v[1], trace.get("_".join(v), None))
            for k, v in {
                "ls": ("line", "dash"),
                "lw": ("line", "width"),
                "color": ("line", "color"),
                "marker": ("marker", "symbol"),
                "mfc": ("marker", "color"),
                "mec": ("marker", "color"),
                "ms": ("marker", "size"),
            }.items()
        }
        if mode is not None and "lines" not in mode:
            props["ls"] = ""

        trace_mpl = {
            "constructor": "plot",
            "args": (x, y, z),
            "kwargs": {
                **{k: v for k, v in props.items() if v is not None},
                "alpha": trace.get("opacity", 1),
            },
        }
        traces_mpl.append(trace_mpl)
    else:
        raise ValueError(
            f"Trace type {trace['type']!r} cannot be transformed into matplotlib trace"
        )
    return traces_mpl


def display_matplotlib_auto(
    *obj_list,
    zoom=1,
    canvas=None,
    animation=False,
    repeat=False,
    colorsequence=None,
    return_animation=False,
    **kwargs,
):

    """
    Display objects and paths graphically using the matplotlib library.

    Parameters
    ----------
    objects: sources, collections or sensors
        Objects to be displayed.

    zoom: float, default = 1
        Adjust plot zoom-level. When zoom=0 all objects are just inside the 3D-axes.

    canvas: `matplotlib.axes._subplots.AxesSubplot` with `projection=3d, default=None
        Display graphical output in a given canvas
        By default a new `Figure` is created and displayed.

    title: str, default = "3D-Paths Animation"
        When zoom=0 all objects are just inside the 3D-axes.

    colorsequence: list or array_like, iterable, default=
            ['#2E91E5', '#E15F99', '#1CA71C', '#FB0D0D', '#DA16FF', '#222A2A',
            '#B68100', '#750D86', '#EB663B', '#511CFB', '#00A08B', '#FB00D1',
            '#FC0080', '#B2828D', '#6C7C32', '#778AAE', '#862A16', '#A777F1',
            '#620042', '#1616A7', '#DA60CA', '#6C4516', '#0D2A63', '#AF0038']
        An iterable of color values used to cycle trough for every object displayed.
        A color and may be specified as:
      - A hex string (e.g. '#ff0000')
      - An rgb/rgba string (e.g. 'rgb(255,0,0)')
      - An hsl/hsla string (e.g. 'hsl(0,100%,50%)')
      - An hsv/hsva string (e.g. 'hsv(0,100%,100%)')
      - A named CSS color
    """
    data = get_frames(
        objs=obj_list,
        colorsequence=colorsequence,
        zoom=zoom,
        animation=animation,
        mag_arrows=True,
        **kwargs,
    )
    frames = data["frames"]
    ranges = data["ranges"]

    for fr in frames:
        fr["data"] = [
            tr0 for tr1 in fr["data"] for tr0 in generic_trace_to_matplotlib(tr1)
        ]
    show_canvas = False
    if canvas is None:
        show_canvas = True
        fig = plt.figure(dpi=80, figsize=(8, 8))
        canvas = fig.add_subplot(111, projection="3d")
        canvas.set_box_aspect((1, 1, 1))

    def draw_frame(ind):
        for tr in frames[ind]["data"]:
            constructor = tr["constructor"]
            args = tr["args"]
            kwargs = tr["kwargs"]
            getattr(canvas, constructor)(*args, **kwargs)
        canvas.set(
            **{f"{k}label": f"{k} [mm]" for k in "xyz"},
            **{f"{k}lim": r for k, r in zip("xyz", ranges)},
        )

    def animate(ind):
        plt.cla()
        draw_frame(ind)
        return [canvas]

    if len(frames) == 1:
        draw_frame(0)
    else:
        anim = FuncAnimation(
            fig,
            animate,
            frames=range(len(frames)),
            interval=100,
            blit=False,
            repeat=repeat,
        )
    if return_animation and len(frames) != 1:
        return anim
    elif show_canvas:
        plt.show()
