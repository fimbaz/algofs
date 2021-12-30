APP_1=$(./algofs.bash new)
APP_2=$(./algofs.bash new)
APP_3=$(./algofs.bash new)
./algofs.bash append $APP_1 "$(openssl rand -hex 500 )"
./algofs.bash append $APP_1 "$(openssl rand -hex 500 )"
./algofs.bash append $APP_1 "$(openssl rand -hex 500 )"
./algofs.bash append $APP_1 "$(openssl rand -hex 500 )"
./algofs.bash append $APP_1 "$(openssl rand -hex 500 )"
./algofs.bash append $APP_1 "$(openssl rand -hex 500 )"
./algofs.bash append $APP_1 "$(openssl rand -hex 500 )"
exit
./algofs.bash copy $APP_1 $APP_2 2
for i in {1..8}; do
    ./algofs.bash nowait copy $APP_1 $APP_2 4
done
./algofs.bash settail $APP_2 $APP_3
./algofs.bash sethead $APP_2 $APP_3
./algofs.bash copy $APP_2 $APP_3
