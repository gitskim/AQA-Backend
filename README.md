# AQA-Backend

start the server by:

```c
FLASK_APP=diving_flask.py flask run
```

Send a video to make an inferene of by:

```c
curl -F video=@chen.mp4 http://127.0.0.1:5000/predict
```
