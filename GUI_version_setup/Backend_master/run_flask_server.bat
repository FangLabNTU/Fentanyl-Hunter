@echo off
echo Installing dependencies using Chinese mirror...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo Dependencies installed successfully, starting Flask backend...
set FLASK_APP=app.py
set FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5000

pause 