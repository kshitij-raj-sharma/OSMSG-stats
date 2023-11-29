## Installation

Follow [windows_installation](./docs/Install_windows.md) for Windows Users .

- Install [osmium](https://github.com/osmcode/pyosmium) lib on your machine

```
pip install osmium
```

- Install osmsg

```
pip install osmsg
```

### Development 

Fork the repo 

```
git clone https://github.com/kshitijrajsharma/OSMSG.git
cd OSMSG
```

Install osmsg in editable mode to make changes locally and test 

```
pip install -e .    
```

### [DOCKER] Install with Docker locally

- Clone repo & Build Local container : 

  ```
  docker build -t osmsg:latest .
  ```

- Run Container terminal to run osmsg commands: 

  ```
  docker run -it osmsg
  ```

  Attach your volume for stats generation if necessary 

  ```
  docker run -it -v /home/user/data:/app/data osmsg
  ```

