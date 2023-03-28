import typer

from toolbelt.check import check_app
from toolbelt.prepare import prepare_app
from toolbelt.update import update_app
from toolbelt.k8s import k8s_app

app = typer.Typer()
app.add_typer(check_app, name="check")
app.add_typer(prepare_app, name="prepare")
app.add_typer(update_app, name="update")
app.add_typer(k8s_app, name="k8s")

if __name__ == "__main__":
    app()
