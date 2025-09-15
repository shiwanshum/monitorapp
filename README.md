# monitorapp

git push token:   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


my system is ubuntu arm64 (aarch64)
db  configuration setup in docker 

image: mysql:8.0.43 (if latest version select mysql.connector doesnt work with python flask or fastapi)
image: postgres:17

main_metric.py is flask based code

app.py is fastapi based code


 i have setup 3 node of both db in different docker vms, if you setup single node or double node of db cluster in docker make sure update the files as below :
 * db_config.py
 * main_metrics.py
 * app.py 
 * dashboard.html
 * dashboard.js
 
