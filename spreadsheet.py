import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return


@app.cell
def _():
    import requests

    return (requests,)


@app.cell
def _(requests):
    requests.get('http://grist:8484/api').text
    return


if __name__ == "__main__":
    app.run()
