#! /bin/bash

rm testlog.txt
touch testlog.txt

echo "#We should see a login FAILURE"  >> testlog.txt
echo "" >> testlog.txt
curl  -H "Content-Type: application/json" -X POST -d '{"username" : "mike", "password" : "bad_password"}' http://mike-werewolf.herokuapp.com/login | cat >> testlog.txt

echo "" >> testlog.txt
echo "#We should see a login success" >> testlog.txt
echo "" >> testlog.txt
echo "" >> testlog.txt
curl  -H "Content-Type: application/json" -X POST -d '{"username" : "mike", "password" : "1234"}' http://mike-werewolf.herokuapp.com/login | cat >> testlog.txt

echo "" >> testlog.txt
echo "" >> testlog.txt
echo "#Create a new game:" >> testlog.txt
echo "" >> testlog.txt
curl  -X POST http://mike-werewolf.herokuapp.com/newgame | cat >> testlog.txt

echo "" >> testlog.txt
echo "" >> testlog.txt
echo "#See living players," >> log.txt
echo "" >> testlog.txt
echo "" >> testlog.txt
curl   http://mike-werewolf.herokuapp.com/townie/votable | cat >> testlog.txt

echo "" >> testlog.txt
echo "#Attemp to kill, will fail because of distance" >> testlog.txt
echo "" >> testlog.txt
curl  -X DELETE http://mike-werewolf.herokuapp.com/werewolf/kill/allevato | cat >> testlog.txt

echo "" >> testlog.txt
echo "" >> testlog.txt
echo "#update position to be close to our victim." >> testlog.txt
echo "" >> testlog.txt

curl  -H "Content-Type: application/json" -X POST -d '{"longitude" : 0.0, "latitude" : 0.0}' http://mike-werewolf.herokuapp.com/position | cat >> testlog.txt


echo "" >> testlog.txt
echo "#Attemp to kill, if last request worked, this should work" >> testlog.txt
echo "" >> testlog.txt
curl  -X DELETE http://mike-werewolf.herokuapp.com/werewolf/kill/allevato | cat >> testlog.txt
echo "" >> testlog.txt



echo "" >> testlog.txt
echo "#As admin, we can see secret information about the players" >> testlog.txt
echo "" >> testlog.txt
curl   http://mike-werewolf.herokuapp.com/debugplayers | cat >> testlog.txt
echo "" >> testlog.txt


echo "" >> testlog.txt
echo "#Is it day or night?  " >> testlog.txt
echo "" >> testlog.txt
curl   http://mike-werewolf.herokuapp.com/debug | cat >> testlog.txt
echo "" >> testlog.txt
echo "" >> testlog.txt
echo "" >> testlog.txt

echo "pausing 21 seconds to let time of day change"
sleep 21
echo "#We paused the bash file, so it should be night now, " >> testlog.txt
echo "" >> testlog.txt
curl   http://mike-werewolf.herokuapp.com/debug | cat >> testlog.txt
echo "" >> testlog.txt
