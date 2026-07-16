@echo off
rem Rotina diaria do GovHub (Plano A): ingestao + score + verificacao + triagem
cd /d D:\Documentos\GOVHUB_AI\apps\api
python -m govhub.pipeline daily avintis >> govhub_daily.log 2>&1
