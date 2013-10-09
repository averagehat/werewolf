touch log.txt

cat >> log.txt #We should see a login FAILURE
curl -i -H "Content-Type: application/json" -X POST -d '{"username" : "mike", "password" : "bad_password"}' http://mike-werewolf.herokuapp.com/login | cat >> log.txt

cat >> log.txt #We should see a login success
curl -i -H "Content-Type: application/json" -X POST -d '{"username" : "mike", "password" : "1234"}' http://mike-werewolf.herokuapp.com/login | cat >> log.txt

curl -i  http://mike-werewolf.herokuapp.com/townie/votable

