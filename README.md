# Vitai_Sign_Ground_Truth
 
## HKG_07B with NI
### Hardware
- [HKG-07B](https://item.taobao.com/item.htm?spm=a21n57.1.0.0.73f2523csk56k7&id=9548137112&ns=1&abbucket=1#detail) infrared pulse sensor
- High-speed data acquisition card [NI USB-6210](https://item.taobao.com/item.htm?spm=a1z10.3-c-s.w4002-23261250367.11.67244729vNnsQM&id=665039455388)

### Environment Setup
- Download [NI-DAQmx driver](https://www.ni.com/zh-cn/support/downloads/drivers/download.ni-daq-mx.html#494676) (Only support Windows and Linux)
- Python requirements 
```
    conda create -n vital_gt python==3.8.8
    conda activate vital_gt
    pip install pyside6 -i  https://pypi.mirrors.ustc.edu.cn/simple/
    pip install scikit-learn==1.3.2 -i  https://pypi.mirrors.ustc.edu.cn/simple/
    python -m pip install nidaqmx
    pip install pglive
```

### Run
```
conda activate vital_gt
cd .\HKG_07B_with_NI\
python .\main.py
```


