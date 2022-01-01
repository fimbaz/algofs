APP_1=$(./algofs.bash new)
APP_2=$(./algofs.bash new)
APP_3=$(./algofs.bash new)
APP_4=$(./algofs.bash new)
echo $APP_1 $APP_2 $APP_3 $APP_4
for i in {1..4}; do # message 1
    ./algofs.bash nowait append $APP_1 "$(openssl rand -hex 500 )"
done
./algofs.bash append $APP_1 "$(openssl rand -hex 500 )"
./algofs.bash read $APP_1
for i in {1..8}; do  # message 2
    ./algofs.bash nowait append $APP_4 "$(openssl rand -hex 500 )"
done
./algofs.bash append $APP_4 "$(openssl rand -hex 500 )"
./algofs.bash read $APP_4
./algofs.bash copy $APP_1 $APP_2 2
./algofs.bash read $APP_2
for i in {1..8}; do
    ./algofs.bash nowait copy $APP_1 $APP_2 4
done
./algofs.bash copy $APP_1 $APP_2 4
./algofs.bash read $APP_2
for i in {1..8}; do
    ./algofs.bash nowait copy $APP_4 $APP_2
done
./algofs.bash copy $APP_4 $APP_2
./algofs.bash read $APP_4
./algofs.bash settail $APP_2 $APP_3
./algofs.bash sethead $APP_3 $APP_2
./algofs.bash read $APP_2
./algofs.bash read $APP_3
for i in {1..8}; do
    ./algofs.bash nowait copy $APP_4 $APP_3
done

