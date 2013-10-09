#!~/virtualenv-1.10/myVE/bin/python

# all of the modules!
from functools import wraps ; from flask import g, request, redirect, url_for
import hashlib ; from threading import Thread
from pymongo import Connection, GEO2D ; from random import shuffle
from flask import Flask, jsonify ; from flask import make_response ; from flask import *
import os ; import pymongo ; from pymongo import MongoClient
import logging ; import time

#some deprecated flask stuff
from flask.ext.login import UserMixin
from flask.ext.login import * 
from flask.ext.login import LoginManager
from flask.ext.login import login_required 
from flask.ext.httpauth import HTTPBasicAuth

from bson.json_util import dumps
import json
from bson import Binary, Code


'''
TODO:
   * Split this up into multiple files
   * Registration page for new users
   * Customization widget for the admin

'''


#do we want users in the database automatically?
# yes, because you can't start a new game without an admin.
withusers = True

HEROKU = True
#HEROKU = not( os.environ.get('HEROKU') is None )

#auth = HTTPBasicAuth()
app = Flask(__name__)
daynightthread = positionthread = None

# Customizable globals! Currently, everything happens very quickly, except the position request, so that players don't die within 10 seconds.
_smellrange = _daylength = 20
_killrange = _positionfrequency = 5
_positionfrequency = 10000


# game object holds all of our 'globals,' currently without any methods.
# Globals should be made true variables and scrap the Game object, or else
# consolidate some of the methods into Game and probably an inner database manager class.
class Game():

   def __init__(self):
      self.db = self.users = self.kills = self.client = self.players  = None
      self.usercount = self.updatecounter = self.daycounter = 0
      self.running = self.night = False  
      self.currentuser = None
      self.lat = self.lon = -1 #default lat & lon values
      self.smellrange = _smellrange
      self.daylength = _daylength
      self.positionfrequency = _positionfrequency
      self.killrange = _killrange
      self.sudo = 'sudo'

   def instantiate_db(self):
      self.running = True
      ###############
      ############### solution below from:
      ##############http://stackoverflow.com/questions/8859532/how-can-i-use-the-mongolab-add-on-to-heroku-from-python
      ###############
      ###############
      if HEROKU:
         client = MongoClient(os.environ['MONGOLAB_URI'])
         self.db = client.get_default_database()
     #    con = Connection(os.environ['MONGOLAB_URI'])
     #    db = client.geo_example
         self.db.places.create_index([("loc", GEO2D)])
         self.players = self.db.places
      else:
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
      if withusers:
         add_user0("mike", ("1234"), True)

      self.db_up = True
    #  game.users.insert( {"name" : self.sudo, "password" : hashpassword(self.sudo) , "id" : self.usercount, "admin" : True })
      self.usercount += 1



'''
#DEPRECATED 
@auth.get_password
def get_password(username):

    return getpassword(username)

@auth.error_handler
def unauthorized():

    return make_response(jsonify( { 'error': 'Unauthorized access' } ), 401)
'''


def isadmin(playername):
   print 'in begin of isadmin'
   userdict = game.users.find_one( {"name" : playername } )
   print 'userdict' + str(userdict)
   return userdict['admin']

def kills():
   # return the last night's kills
   if not game.running:
      return dumps ( { 'kills' : 'game not started yet,' } )
   if game.night:
      return dumps ( { 'kills' : 'townspeople are not notified until morning!' } )
   
   else:
      if game.kills:
         return dumps ( { 'kills' :  list ( game.kills.find() ) }) 
      else:
         return dumps ( {'kills' : 'everyone survived . . . last night.' } )


def startday():
   game.night = False
   poll()  #kill the voted-out player
   

def startnight():
   game.night = True
   game.kills.remove() #remove the last night's kills from the database
   

def maintain():
   #game starts out as daytime
   while game.running:
      #should check every few minutes for the last time players updated their location.
      
      time.sleep(game.daylength)
      game.daycounter += 1
      startnight()
      print "night started"
      time.sleep(game.daylength)
      startday()
      print "day started"

def nologin(): 
   return dumps ( { "result" : "You are not logged on. Please post login info to /login"} )

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

def postposition(lon, lat):
   game.players.update( {"username" : game.currentuser }, {"$set" : {"loc" : [lon, lat]} } )
   return dumps({"Result" : "Success"})

# returns True if kill succeeds.
def kill(victimName):
   if not game.night:
      return False
   killer = game.players.find_one( {"name" : game.currentuser} )
   victim = game.players.find_one( {"name" : victimName} )
   killerid = killer['_id']
   victimid = victim['_id']
   if killer["werewolf"] and victim['alive'] and inKillRange(killerid, victimid):
      dokill(victim['name'],  'murder' )
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
      dokill(mostvotes['name'], 'voting' )
  
  # if no one votes, no one dies   



      #info should include stuff like method, killer
def gamesummary():
   if game.running:
      return "Game summary available only when game is finished."
   else:

      playerstats = []
      for player in game.players.find():
         playerstats.append( { "name" : player['name'], 
            'kills' : player['kills'],  'alive' : player['alive'] })
      return playerstats



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if game.currentuser is None:
            return nologin()# redirect('login')#      url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function



def startnight():
   game.night = True
   game.kills.remove() #remove the last night's kills from the database

   #do all the overnight stuff, that actually happens right before another day starts.

def isadmin(playername):
   userdict = game.users.find_one( {"name" : playername } )
   return userdict['admin']



def startday():
   game.night = False
   poll()  #kill the voted-out player
   #notify the players about the kills?
   

def nologin(): 
   return dumps ( { "result" : "You are not logged on. Please post login info to /login"} )

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
      dokill(victim['name'], {'method' : 'murder'} )
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
      dokill(mostvotes['name'], "method"  )
  
  # if no one votes, no one dies   


      #info should include stuff like method, killer
def dokill(victimname, method):
   game.players.update( {'name' : victimname}, { "$set" : {'alive' : False } } )
   game.kills.insert( {'victim' : victimname, 'method' : method} )

# assume that votes got cleared out after last vote
# return True if vote succeeded.
def vote(target):
   
   if isalive(target) and not iswerewolf(game.currentuser) and game.night :
      game.players.update( {'name' : game.currentuser }, {"$set" : {"votedfor" : target} } )
      game.players.update( {'name' : target }, {"$inc" : {"votesagainst" : 1 } } )
      return dumps( {'result' : 'success'} )
   return dumps( {'result' : 'failure'} ) 


def votable():
   return simplifyplayers( game.players.find( {"alive" : True} ) )


def synopsis():
   return dumps ( list( game.kills.find() ) )


def insertplayer(userid, username, werewolf):
   game.players.insert( {"id" : userid, "name" : username, "werewolf" : werewolf, 
      "alive" : True, "loc" : [game.lon, game.lat], "image" : None ,
      'kills' : 0, "votedfor" : "", 'votesagainst' : 0, 'lastupdate' : game.updatecounter } )


# checks that the player last updated his position recently.
def checkpositions():
   while game.running:
      print "Checking for player updates . . . "
      for player in game.players.find({"alive" : True}):
         lastupdate = player['lastupdate']
         if ( game.updatecounter - lastupdate) > 1:
            # kick that player out of the game, and alert the user
           dokill(player['name'], 'timed out' )
      time.sleep(game.positionfrequency)
      game.updatecounter += 1


   
def add_user0(username, password, iswerewolf):
   add_user(username,  hashpassword(username + password), iswerewolf )

def newgame():

   #clear out the players and kills collections
   daynightthread = Thread(target=maintain)
   daynightthread.start()

   positionthread = Thread(target = checkpositions, args=[])
   positionthread.start()
   print 'threads started'
   usercount = playercount = 0


   if withusers:
      add_user0("allevato", ("allevato"), False)
      print 'users added'
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


def new_game():
   if isadmin(game.currentuser):
      newgame()
      return dumps( {"result" : "Game Created!" } )
   else:
      return dumps( {"result" : "you must be an admin to create a new game! for shame!"} )


################
''' ROUTING '''
################


#define our authentication decorator.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if game.currentuser is None:
            return nologin()# redirect('login')#      url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["POST"])
def login():
   if not request.json or not 'username' in request.json or not 'password' in request.json:
      abort(400)
  # user = User(request.json['username'], hashpassword(request.json['username'] + request.json['password']), id0=0, isadmin=False)
   jname = unicode(str(request.json['username']), 'latin1')
   jpassword = unicode(str(request.json['password']), 'latin1')
   if game.users.find_one( {'name' : jname, 'password' : hashpassword(jname + jpassword) }):
      game.currentuser = jname
      return dumps( {'result' : 'login successful!' })
   else:
      game.currentuser = None
      return dumps( { "result" : "failed" })
    #user = game.users.find_one( {'username' : form.username.data} )
    #return "yo there"
   
def load_user(userid):
   u = game.users.find_one( {"id" : userid })
   return User(u['name'], userid, u['admin'], active=True)

@app.route("/login_required")
def loginrequired():
   return dumps( {"result" : "Login required at /login"} )

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
   return dumps ( smell() )
 #  return dumps ( {'response' : "login successful\n" } )

@app.route("/werewolf/kill/<string:victim>", methods=["DELETE"])
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
   return vote(playername)
     #vote the player out if townie 

@app.route("/townie/votable")
@login_required
def votablelist():
   return dumps( { 'votable' : votable() })

@app.route("/position" ,methods=["POST"])
@login_required
def postPosition():
   if not request.json or not 'longitude' in request.json or not 'latitude' in request.json:
      abort(400)
  # user = User(request.json['username'], hashpassword(request.json['username'] + request.json['password']), id0=0, isadmin=False)
   else:
      return dumps (postposition(request.json['longitude'], request.json['latitude']) )

@app.route("/synopsis")
def synopsis():
   return dumps ( gamesummary() )
   #get synopsis/highscore list

@app.route("/kills")
@login_required
def kills0():
   print 'in kills0 routing'
   return kills()
   #returns list of the last night's kills.

@app.route("/logout")
@login_required
def logout():
   # logout_user()   is required, can't find the module for it
   return ''

@app.route("/register", methods=["POST"])
def register():
   if not request.json or not 'username' in request.json or not 'password' in request.json:
      abort(400)
  # user = User(request.json['username'], hashpassword(request.json['username'] + request.json['password']), id0=0, isadmin=False)
   jname = unicode(str(request.json['username']), 'latin1')
   jpassword = unicode(str(request.json['password']), 'latin1')
   if game.users.find_one( {'name' : jname, 'password' : hashpassword(jname + jpassword) }):
      return dumps( { "result" : "failed" })
   else:
      game.currentuser = jname
      add_user0(jname, jpassword, False)
      return dumps( { "result" : "success!"})
    #user = game.users.find_one( {'username' : form.username.data} )
    #return "yo there"

@app.route("/newgame", methods=["POST"])
@login_required
def instantiate_game():
   return new_game()
#allow admin to create a new game from a user bank.


@app.route("/debugplayers")
@login_required
def debugplayers():
   return dumps( { 'players' : list( game.players.find() ) } )

@app.route("/debugusers")
@login_required
def debugusers():
   return dumps( { 'users' : list( game.users.find() ) } )

@app.route("/user/<string:username>")
def getuser(username):
   return dumps ( {'user' : game.users.find_one( {"name" : username} ) } )

@app.route("/debug")
@login_required
def debug():
   return dumps ( {'Night' : game.night, 'days passed' : game.daycounter })

@app.route("/switch")
@login_required
def switch():
   if game.night:
      startday()
   else:
      startnight()
   return dumps ( {'Night' : game.night, 'dayspassed' : game.daycounter })

game = Game()
game.instantiate_db()
if __name__ == "__main__":
   app.run()
   game.running = False
   
