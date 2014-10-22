from fabric.api import task
import os

__title__ = 'BanzaiVis deployment fabfile'
__version__ = '0.0.1'
__description__ = "BanzaiVis deployment fabfile"
__author__ = 'Mitchell Stanton-Cook'
__author_email__ = 'm.stantoncook@gmail.com'
__url__ = 'https://github.com/m-emerson/BanzaiVis'


@task
def start_gunicorn_server():
    """
    Start the gunicorn BanzaiVis server

    TODO - support VirtualEnvs?
    """
    cwd   = os.getcwd()
    final = os.path.join(cwd, '../banzaivis')
    cmd = "cd %s && gunicorn application:app -c gunicorn_config.py" % (final)
    os.system(cmd)


@task
def install_nginx():
    """
    """
    pass


@task
def git_clone_src():
    """
    """
    pass


@task
def deploy():
    """
    """
    pass

