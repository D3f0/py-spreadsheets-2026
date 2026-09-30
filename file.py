import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium", layout_file="layouts/file.slides.json")


@app.cell
def _():
    from invoke_toolkit import run
    import pygrister

    return (run,)


@app.cell
def _(run):
    run('ls')
    return


@app.cell
def _():
    import os

    return (os,)


@app.cell
def _(os):
    grist_env = {
        k: v for k, v in os.environ.items() if k.startswith("GRIST_")
    }
    grist_env
    return


@app.cell
def _():
    from pygrister.api import GristApi

    return (GristApi,)


@app.cell
def _(GristApi):
    g = GristApi()
    return (g,)


@app.cell
def _(g):
    g.list_workspaces()
    return


@app.cell
def _(g):
    g.list_tables(doc_id="q5aBBVtSotFo4YJdVuoLoD")
    return


@app.cell
def _(g):
    g.list_records(doc_id="q5aBBVtSotFo4YJdVuoLoD", table_id="Table1")
    return


@app.cell
def _(g):
    (a,b), _ = g.list_records(doc_id="q5aBBVtSotFo4YJdVuoLoD", table_id="Table1")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
