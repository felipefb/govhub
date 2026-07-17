@echo off
rem Cockpit do GovHub — http://localhost:8777
cd /d D:\Documentos\GOVHUB_AI\apps\api
python -m uvicorn govhub.main:app --host 127.0.0.1 --port 8777 >> govhub_server.log 2>&1
