"""Konfigurasi visualisasi bersama untuk seluruh dashboard."""


KONFIGURASI_PLOTLY = {
    "responsive": True,
    "displayModeBar": False,
    "displaylogo": False,
    "scrollZoom": False,
    "doubleClick": False,
}


def kunci_grafik(figure, ada_tanggal=False):
    """Mengunci interaksi grafik dan menghapus tampilan jam dari sumbu tanggal."""
    figure.update_layout(
        dragmode=False,
        margin=dict(t=60, b=20, l=20, r=20),
    )
    figure.update_xaxes(fixedrange=True)
    figure.update_yaxes(fixedrange=True)

    if ada_tanggal:
        figure.update_xaxes(
            tickformat="%d %b",
            hoverformat="%d %b",
            automargin=True,
        )

    return figure
