# Disk Scanner
My implementaition of Steffen Gerlach's Scanner2
### Feautures:
- Scan disk on demand.
- Allows to traverse last checked disk while waiting for scan.(click on home button while scanning another disk)
  
![diskscanner](https://github.com/TooManyLs/disk-scanner/assets/105962560/32271886-4c6b-44c8-bdd4-3f2347dbf6b8)

## Build
To build executable using pyinstaller:
- Create virtual environment
- Enter virtual environment
- Install packages from requirements.txt and pyinstaller
  ```
  pip install -r requirements.txt
  ```
  ```
  pip install pyinstaller
  ```
- Build executable
  ### on Linux\Mac
  ```
  pyinstaller --onefile --icon=disk_scan.ico --add-data="html/start.html:html" --add-data="html/loading.html:html" \
  --add-data="public/home.png:public" --add-data="disk_scan.ico:." --noconsole ui.py
  ```
  ### on Windows
  ```
  pyinstaller --onefile --icon=disk_scan.ico --add-data="html/start.html;html" --add-data="html/loading.html;html" \
  --add-data="public/home.png;public" --add-data="disk_scan.ico;." --noconsole ui.py
  ```
  ### Note
  If you get trojan warning from windows defender when trying to build app uninstall pyinstaller
  ```
  pip uninstall pyinstaller
  ```
  and install version 5.13.2
  ```
  pip install pyinstaller==5.13.2
  ```
