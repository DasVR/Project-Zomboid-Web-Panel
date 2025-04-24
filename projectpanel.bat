@echo off
set token=3b5942ed-4611-4e57-b909-62643428875d
set domain=projectzed
curl "https://www.duckdns.org/update?domains=%domain%&token=%token%&ip="
