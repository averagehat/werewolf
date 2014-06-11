werewolf
========

werewolf web service project for CSCI 420 @ W&amp;M

This is the Web Service portion of a RESTful app designed for Android; The android code is unposted.

This app is available to play at:

http://mike-werewolf.herokuapp.com/


You need to post correct login data to /login first. See the test/tests.sh file for an example.
Better log in as an administrator so you can create the game. Current admin:

username : mike

password : 1234

Then, post to /newgame in order instantiate a new game instance.

####### ROUTINGS ##########

GET
/
/players, 
/townie/votable, 
/townie/vote/<playername>, 
/werewolf/smell, 
/user/<username>, 
/debug, 
/debugplayers, 
/kills, 
/synopsis, 

POST
/position, 
/newgame, 
/login, 
/register, 

DELETE
/werewolf/kill/<playername>
