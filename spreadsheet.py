import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    from pygrister.api import GristApi
    import marimo as mo

    return GristApi, mo


@app.cell
def _(GristApi):
    grist = GristApi()
    return (grist,)


@app.cell
def _(grist):
    _code, result = grist.list_workspaces()
    return (result,)


@app.cell
def _(result):
    result
    return


@app.cell
def _(result):
    doc_id = result[0]["docs"][0]["id"]
    return (doc_id,)


@app.cell
def _(doc_id, grist):
    _code, tables = grist.list_tables(doc_id=doc_id)
    return (tables,)


@app.cell
def _(tables):
    table_id = tables[0]["id"]
    return (table_id,)


@app.cell
def _(doc_id, grist, table_id):
    _code, records = grist.list_records(doc_id=doc_id, table_id=table_id)
    return (records,)


@app.cell
def _(mo, records):
    mo.ui.table(records)
    return


@app.cell
def _(doc_id, grist, mo):
    _code, results = grist.run_sql(
        sql="""
        select "Activity", 
        DATETIME(ROUND("Start" ), 'unixepoch'), 
        DATETIME(ROUND("End"), 'unixepoch'), 
        "All_Day", "Category" from Events""",
        doc_id=doc_id,
    )
    mo.ui.table(results)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
