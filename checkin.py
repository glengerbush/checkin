from app import create_app, db


app = create_app()

# Whatever models are passed into the shell context allow for messing around with them in the command line


@app.shell_context_processor
def make_shell_context():
    return{'db': db}
