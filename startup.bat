@echo off
cd /d %~dp0
streamlit run app.py --server.address=localhost --server.port=8501
pause
