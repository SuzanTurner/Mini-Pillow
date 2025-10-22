from Photoshop.base.base import base
import typer

app = typer.Typer(help="Command Line Interface for small image editing")


app.add_typer(base.base())

def main():
    app()

if __name__ == "__main__":
    main()
