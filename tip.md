install
```
pip3 install playwright
python3 -m playwright install
```

codegen
```
python3 -m playwright codegen https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P0YGO0Q2
```


Attach到真人Chrome，要開啟可控的Chrome Browser
```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/tk-chrome
```