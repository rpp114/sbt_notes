#!flask/bin/python
import sys

from flup.server.fcgi import WSGIServer

sys.path.insert(0, '/home/titlow/notes.sarahbryantherapy.com/sbt_notes') # change to the directory of the app in production

from app import app

if __name__ == '__main__':
  WSGIServer(app).run()
