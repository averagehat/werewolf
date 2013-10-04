#!~/virtualenv-1.10/myVE/bin/python
from functools import wraps
from flask import g, request, redirect, url_for
import hashlib
from threading import Thread
from pymongo import Connection, GEO2D
from random import shuffle
from flask import Flask, jsonify
from flask import make_response
from flask import *
import forms
from forms import LoginForm
import os
import pymongo
from pymongo import MongoClient
import logging
import time

from flask.ext.login import UserMixin
from flask.ext.login import *

from flask.ext.login import LoginManager
from flask.ext.login import login_required

from flask.ext.httpauth import HTTPBasicAuth
import json
from bson import Binary, Code
from bson.json_util import dumps

from flask.ext.wtf import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required

app = Flask(__name__)
auth = HTTPBasicAuth()
night = False
daynightthread = positionthread = None
#login_manager = LoginManager()
#login_manager.init_app(app)



class Game():

   def __init__(self):
      self.db = self.users = self.kills = self.client = self.players  = None
      self.usercount = 0
      self.running = self.night = False  
      self.currentuser = None
      self.lat = self.lon = -1 #default lat & lon values
      self.smellrange = 10
      self.daylength = 10
      self.positionfrequency = 5
      self.counter = 0
      self.sudo = 'sudo'

   def instantiate_db(self):
      self.running = True
      self.client = MongoClient()
      self.db = self.client.werewolf_db
      db = Connection().geo_example
      db.places.create_index([("loc", GEO2D)])
      self.players = db.places
      self.users = self.db.users
      self.kills = self.db.kills
      # deleting users this time
      self.users.remove()
      self.players.remove()
      self.kills.remove() 

      self.db_up = True
    #  game.users.insert( {"name" : self.sudo, "password" : hashpassword(self.sudo) , "id" : self.usercount, "admin" : True })
      self.usercount += 1



class User():
   def __init__(self, username, hashedpass, id0, isadmin, active=True, password=None):
      self.username = username
      self.hashedpass = hashedpass 
      self.isadmin = isadmin
      self.id0 = id0
      self.password = password

   def isadmin(self):
      return self.isadmin

   def is_authenticated(self):
      return True

   def is_active(self):
      return self.is_authenticated()

   def is_anonymous(self):
      return False

   def get_id(self):
      return self.id0

   def validpassword(self, password):
      return checkpassword(password, self.password)

@app.route("/login", methods=["POST"])
def login():
   if not request.json or not 'username' in request.json or not 'password' in request.json:
      abort(400)
  # user = User(request.json['username'], hashpassword(request.json['username'] + request.json['password']), id0=0, isadmin=False)
   print request.json['username']
   print request.json['password']
   jname = unicode(str(request.json['username']), 'latin1')
   jpassword = unicode(str(request.json['password']), 'latin1')
   print 'at if'
   if game.users.find_one( {'name' : jname, 'password' : hashpassword(jname + jpassword) }):
      print 'in if'
      game.currentuser = jname
      return dumps( {'result' : 'login successful!' })
   else:
      print 'in else'
      redirect('/login_required')
    #user = game.users.find_one( {'username' : form.username.data} )
    #return "yo there"
   
   ''' 
    if form.validate_on_submit():
        # login and validate the user...

       if user is not None and user.valid_password(form.password.data):
           login_user(user, remember=True)
           flash("Logged in successfully.")
           return redirect(request.args.get("next") or url_for("index"))
       
       else:
          flash('Wrong username or password!', 'error')

    return render_template("login.html", form=form)  
   '''
def load_user(userid):
   u = game.users.find_one( {"id" : userid })
   return User(u['name'], userid, u['admin'], active=True)

##########


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if game.currentuser is None:
            return redirect('login')#      url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth.get_password
def get_password(username):

    return getpassword(username)

@auth.error_handler
def unauthorized():
    return make_response(jsonify( { 'error': 'Unauthorized access' } ), 401)


def startnight():
   game.night = True
   game.kills.remove() #remove the last night's kills from the database

   #do all the overnight stuff, that actually happens right before another day starts.

def isadmin(playername):
   userdict = users.find_one( {"name" : playername }
   return userdict['admin']

def startday():
   time.sleep(3)
   game.night = False
   poll()  #kill the voted-out player
   #notify the players about the kills?

def maintain():
   #game starts out as daytime
   while game.running:
      #should check every few minutes for the last time players updated their location.
      
      time.sleep(3)
      game.counter += 1
      startnight()
      print "night started"
      time.sleep(3)
      startday()
      print "day started"





def hashpassword(password):
   m = hashlib.md5()
   m.update(password)
   return unicode(m.digest(), "latin1")

#returns false if that user is already in the database and isn't added.
def add_user(username, hashedpassword, isadmin):
   game.usercount += 1

   if game.users.find_one( {"name" : username} ) == None:
      #missing the hash
      game.users.insert( {"name" : username , "password" : (hashedpassword) , "id" : game.usercount, "admin" : isadmin })
      return True

   else:
      return False


def player(playerName):

   return game.players.find_one( {"name" : playerName} )


#This is to return to the client for securtiy reasons. 
def basicplayer(playerName):
   fullplayer = player(playerName)
   if not fullplayer:
      return
   return { "name" : fullplayer["name"], "alive" : fullplayer['alive'] }  
      
def iswerewolf(playerName):
   return game.players.find_one( {"name" : playerName} )['werewolf']

def isalive(playerName):
   return game.players.find_one( {"name" : playerName} )['alive']


# returns True if kill succeeds.
def kill(victimName):
   if not game.night:
      return False
   killer = game.players.find_one( {"name" : game.currentuser} )
   victim = game.players.find_one( {"name" : victimName} )
   killerid = killer['_id']
   victimid = victim['_id']
   if killer["werewolf"] and victim['alive'] and inKillRange(killerid, victimid):
      game.players.update( {"_id" : victimid}, {"$set" : {"alive" : False} } )

      game.players.update( {'_id' : killerid}, {"$inc" : {"kills" : 1 } } )
      return True
   else:
      return False

def inKillRange(killerid, victimid):
   for player in game.players.find( { "loc" : {"$near" : game.players.find_one({"name" : game.currentuser})}}).limit(game.killrange):

      if player["_id"] == vitimid:
            return true
   return false

def allplayers():
   return simplifyplayers( list(game.players.find()) )

def smell():
   return simplifyplayers( list (game.players.find( { "loc" : {"$near" : game.players.find_one({"name" : game.currentuser})}}).limit(game.smellrange)))


def simplifyplayers(playerlist):
   t = []
   for player in playerlist:
      t.append(simplify(player))
   return t

def simplify(playerdict):
   return { "name" : playerdict['name'], 'alive' : playerdict['alive'] }



def poll():
   liveplayers = game.players.find( {'alive' : True } )
   
   for player in liveplayers:
      votedfor = player["votedfor"]
      if votedfor in liveplayers:
         liveplayers["votedfor"]["votesagainst"] += 1
   
   max = 0
   mostvotes = None
   for player in liveplayers:
      game.players.update( {'_id' : player['_id'] }, {"$set" : {"votedfor" : ""} } )
      
      if player["votesagaisnt"] > max:
         max = player["votesagainst"]
         mostvotes = player

      game.players.update( {'_id' : player['_id'] }, {"$set" : {"votesagainst" : 0} } )

      #in case of tie, just kill the first one.
      
  
      #Add a kill to the kill collection to represent the voting that happened?
   if mostvotes:
      dokill(mostvotes['name'], {"method" : 'voting', 'votes' : max} )
  
  # if no one votes, no one dies   



      #info should include stuff like method, killer
def dokill(victimname, info={}):
   game.players.update( {'name' : victimname, 'alive' : False } )
   killdict = {'victim' : victimname}
   killdict.update(info)
   game.kills.insert( {killdict} )
         
def gamesummary():
   if game.running:
      return "Game summary available only when game is finished."
   
   else:

      playerstats = []
      for player in game.players.find():
         playerstats.append( { "name" : player['name'], 
            'kills' : player['kills'],  'alive' : player['alive']})
      return playerstats


# assume that votes got cleared out after last vote
# return True if vote succeeded.
def vote(voter, target):
   
   if isalive(target) and not iswerewolf(game.currentuser) and game.night :
      game.players.update( {'name' : voter }, {"$set" : {"votedfor" : target} } )
      game.players.update( {'name' : target }, {"$inc" : {"votesagainst" : 1 } } )
      return True
   return False


def votable():
   return simplifyplayers( game.players.find( {"alive" : True} ) )

def postposition(player, lon, lat):
   pass

def synopsis():
   pass

def insertplayer(userid, username, werewolf):
   game.players.insert( {"id" : userid, "name" : username, "werewolf" : werewolf, 
      "alive" : True, "loc" : [game.lon, game.lat], "image" : None ,
      'kills' : 0, "votedfor" : "", 'votesagainst' : 0 } )


# checks that the player last updated his position recently.
def checkpositions():
   pass

   
def add_user0(username, password, iswerewolf):
   add_user(username,  hashpassword(username + password), iswerewolf )

def newgame():

   game.instantiate_db()


   #clear out the players and kills collections
   daynightthread = Thread(target=maintain)
   daynightthread.start()

#   positionthread = Thread(target = checkpositions, args=[])
#   positionthread.start()
   
   usercount = playercount = 0

   add_user0("mike", ("1234"), True)
   add_user0("allevato", ("allevato"), False)

   count = 0
   users = list(game.users.find())
   shuffle(users)
   for user in (users):
      if (count % 3) == 0:
         werewolf = True
      else:
         werewolf = False
         
         #if statement below is unnecessary
      if game.players.find_one( {"name" : user["name"] }) == None:
         insertplayer(user["id"], user["name"], werewolf)
 
      count += 1
   pass

#return the player that is the current client.
def thisplayer():
   return None

class Player:

   def __init__(self, userID, werewolf):
      self.userid = userID
      self.werewolf = werewolf
      self.alive = true

   def __init__(self):
      self.id = None
      self.name = None
      self.userid = None
      self.location = None
      self.werewolf = False
      self.alive = True



class BasicPlayer:
   #To be passed to the client, gutted of sensitive info.

   def __init__(self):
      self.name = None
      self.alive = None
      pass

   def __init__(playerObj):
      self.name = playerObj.name
      self.alive = playerObl.alive

def new_game():
   if isadmin(game.currentuser):
      newgame()
      return dumps( {"result" : "Game Created!" } )

   else:
      return False
# We use https:// so we don't need a login page

#game = GameFactor.getCurrentGame   ??
#regularly scheduled check that players have updated location recently

@app.route("/login_required")
def loginrequired():
   return dumps( {"result" : "Login requered at /login"} )

@app.route("/")
def home():
   return "Welcome to werewolf,\nLogin at /login to play.\n"

@app.route("/players")
@login_required
def allPlayers():
   return dumps(({'players' : allplayers()}))

@app.route("/werewolf/smell")
@login_required
   #return a list of all players within the scent range
def smell():
   return dumps ( {'response' : "login successful\n" } )

@app.route("/werewolf/kill/<string:victim>")
@login_required
def akill(victim):

   if kill(victim):
     response = dumps( { "result" : 'success' } )
   else:
      response = dumps( { "result" : 'failure' } )

   return response
   #use ID to attempt a kill a player

@app.route("/townie/vote/<string:playerName>")
@login_required
def vote(playerName):
   

   pass   #vote the player out if townie 

@app.route("/townie/votable")
@login_required
def votablelist():
   return dumps( { 'votable' : votable() })

@app.route("/position" ,methods=["POST"])
@login_required
def postPosition():
   pass #post the lat & long from the client

@app.route("/synopsis")
def synopsis():
   return dumps ( gamesummary() )
   #get synopsis/highscore list

@app.route("/townie/kills")
@login_required
def kills():
   pass #returns list of the last night's kills.

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login_required")
#Check that the client has admin priveleges

@app.route("/newgame")
@login_required
def instantiate_game():
   
   return new_game()
#allow admin to create a new game from a user bank.

@app.route("/nodb")
def nodb():
   return "nodb\n"

@app.route("/debugplayers")
def debugplayers():
   return dumps( { 'players' : list( game.players.find() ) } )

@app.route("/debugusers")
def debugusers():
   return dumps( { 'users' : list( game.users.find() ) } )

@app.route("/user/<string:username>")
def getuser(username):
   return dumps ( {'user' : game.users.find_one( {"name" : username} ) } )

@app.route("/debug")
@login_required
def debug():
   return dumps ( {'Night' : game.night, 'counter' : game.counter })

@app.route("/switch")
@login_required
def switch():
   if game.night:
      startday()
   else:
      startnight()
   return dumps ( {'Night' : game.night, 'counter' : game.counter })

game = Game()

if __name__ == "__main__":
   app.run()
   game.running = False
   
#teardown_appcontext(error=None):


# print list( game.users.find())

logging.basicConfig(filename='example.log',level=logging.DEBUG)
logging.warning('This message should go to the log file')

