import pandas as pd
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, LinearColorMapper, HoverTool
from bokeh.palettes import TolRainbow10

def plate_viz(df):
    df_empty = pd.DataFrame({
    "well": [f"{row}{col}" for row in "ABCDEFGH" for col in range(1, 13)],
    })

    df_empty.head()
    df_res = df_empty.merge(df, on="well", how="left")

    # well to row, col
    df_res["row"] = df_res["well"].str.extract(r"([A-H])")
    df_res["col"] = df_res["well"].str.extract(r"(\d+)").astype(int)

    # bokeh axis
    row_order = list("HGFEDCBA")
    df_res["y"] = df_res["row"].apply(lambda r: row_order.index(r))
    df_res["x"] = df_res["col"] - 1

    # axis label
    df_res["row_label"] = df_res["row"]
    df_res["col_label"] = df_res["col"]
    df_res.fillna({'count':0}, inplace=True)
    df_res['content'] = df_res['content'].astype('str')

    # color mapper
    mapper = LinearColorMapper(palette=TolRainbow10, low=0, high=10)
    source = ColumnDataSource(df_res)

    p = figure(width=600, height=300,
            x_range=[str(i) for i in range(1, 14)],
            y_range=list("HGFEDCBA"),
            tools="hover", toolbar_location=None)

    p.rect(x='col_label', y='row_label', width=0.95, height=0.95,
        source=source,
        fill_color={'field': 'count', 'transform': mapper},
        line_color="black")

    # Write counts
    p.text(x='col_label', y='row_label', text='count',
        source=source,
        text_align="center", text_baseline="middle", text_font_size="14pt", text_color="black")

    hover = p.select_one(HoverTool)
    hover.tooltips = [
        ("Well", "@well"),
        ("Count", "@count"),
        ("Content", "@content")
    ]

    p.xaxis.axis_label = "Column"
    p.yaxis.axis_label = "Row"
    p.xaxis.major_label_orientation = 0
    p.yaxis.major_label_orientation = 0
    p.grid.visible = False

    return p
