from invoke import task

@task
def server(ctx):
    ctx.run("python RendezvousServer/server.py")

@task
def client(ctx):
    ctx.run("python Client/client.py")
