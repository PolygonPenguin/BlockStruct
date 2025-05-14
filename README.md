# Block Struct
Making scratch code directly in python
## Setup
This is still in the very early stages so its not on PyPI so to install it, clone this repo and run `pip install .` on the terminal
## Usage
```python
import BlockStruct as bs #import block struct

@bs.script(bs.Events.WHEN_FLAG_CLICKED()) #define to run when flag is clicked
def flag(): #name anything you want
    bs.Looks.SAY("hello, world") #body
    bs.

sprite1 = bs.Sprite("Sprite1", [flag])
project = bs.Project(bs.Stage(), [sprite1])

project.save_to_file("hello world.sb3")
```