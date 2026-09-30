import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    from pygrister.api import GristApi
    import marimo as mo

    return GristApi, mo


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
    _, data = g.list_records(doc_id="q5aBBVtSotFo4YJdVuoLoD", table_id="Events")
    return (data,)


@app.cell
def _(data, mo):
    mo.ui.table(data)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
