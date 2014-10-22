import multiprocessing
import os

__title__ = 'BanzaiVis gunicorn config file'
__version__ = '0.0.1'
__author__ = 'Mitchell Stanton-Cook'
__author_email__ = 'm.stantoncook@gmail.com'
__url__ = 'https://github.com/m-emerson/BanzaiVis'


BASE = '/'.join(os.getcwd().split('/')[:-1])+"/"
out_dir = os.path.join(BASE, "logs/")
sock_dir = os.path.join(BASE, "sock/")
cpus = multiprocessing.cpu_count()

bind = ["0.0.0.0:8888", "unix:%s" % (sock_dir+"/sock")]
name = "BanzaiVis"
workers = cpus * 2 + 1
threads = cpus * 4
loglevel = "info"
accesslog = os.path.join(out_dir, "access_logs.log")
errorlog = os.path.join(out_dir, "error_logs.log")
daemon = True
