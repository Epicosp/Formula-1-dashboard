import numpy as np
import panel as pn

pn.extension("echarts", "plotly")
import plotly.express as px
import pandas as pd
import hvplot.pandas
import matplotlib.pyplot as plt
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import dashboard_functions as ds
from panel.interact import interact

dashboard = pn.Column("Formula Dank")

# TAB 1
# video
video = pn.pane.Video("../Extras/intro_video.mp4", width=1080, height=720, loop=False)

# three seperate guages
gauge1 = ds.top_driver_points_gauge()
gauge2 = ds.time_to_next_race_gauge()
gauge3 = ds.top_constructor_points_gauge()

# generate tab for dashboard
row1 = pn.Row(video, ds.drivers_per_country())
row2 = pn.Row(gauge1, gauge2, gauge3)

tab1 = pn.Column(row1, row2)

# TAB 5
# generate list of paths to fetch circuit images
p = Path("../images/circuits").glob("*")
files = [str(x) for x in p if x.is_file()]

# selector widget for selecting circuit images
selector = pn.widgets.Select(name="Selector", options=files)
image = pn.pane.PNG(width=700, height=500)

# function to update image pane
def update_image(event):
    image.object = event
    return image


# panel interact to push selector selection to image object
interact(update_image, event=selector)

# layout of panes/columns/rows
circuits = pn.Column(selector, image)
row1 = pn.Row(ds.pit_pos_tracks(), circuits)
row2 = pn.Row(ds.pit_pos())
col1 = pn.Column(row1, row2, ds.pit_improvements())
tab5 = col1

# tech imporement data grab
tech_data = ds.tech_improvement_data()
scatter_tech = ds.tech_imp_scatterPlot(tech_data["f1_quali"])
scatter_pct_tech = ds.tech_pct_scatterPlot(tech_data["f1_pct_change"])

tab2 = pn.Row(
    pn.Column(scatter_tech[0], scatter_tech[1], scatter_tech[2]),
    pn.Column(
        pn.pane.PNG(
            "https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Monoco_Circuit.png.transform/9col-retina/image.png",
            width=825,
        ),
        pn.pane.PNG(
            "https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Australia_Circuit.png.transform/9col-retina/image.png",
            width=825,
        ),
        pn.pane.PNG(
            "https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Italy_Circuit.png.transform/9col-retina/image.png",
            width=825,
        ),
    ),
    pn.Column(
        scatter_pct_tech,
        pn.pane.Markdown(
            """
This is a scatter plot that shows the percentage change over time, as you can see there are peaks at 2013 and 2019 this can be attributed to the fact that these were the years before big regulation changes,
as teams prepare for new regulation they will focus their money and resources into future sessions instead of focusing on the current season, therefore there is a drop in performance during these years.
"""
        ),
    ),
)
tab3 = pn.Row()
tab4 = pn.Row(ds.budget_by_constructor(), ds.constructor_sunburst())

tabs = pn.Tabs(
    ("Welcome", tab1), ("Technology", tab2), ("Strategy", tab5), ("Budget", tab4)
)

dashboard.append(tabs)

dashboard.servable()

