# patent_information

## Installation Guide

1.a. Create virtualenv
```
    python -m venv venv
```
1.b. Activate virtualenv
```
    venv\Scripts\activate (Windows)
    . venv/bin/activate (Unix)
```
2. Upgrade pip
```
    pip install --upgrade pip
```
3. Install requirements
```
    pip install -r requirements.txt
```
4. Run script by year
```
    python script.py 2015
```


```
nohup python -u script.py 2015 > output.log &
```
### Latest Code (Read from 7171patentData.csv)
```
python google_patent.py
```


## Update 15 Feb 2023
Execute the following command to run the script
```python script.py 2011 2012```

