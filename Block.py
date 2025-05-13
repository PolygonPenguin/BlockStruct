import id
import json
import BlockTypes
from Script import Script
class Block:
    def __init__(self, opcode, inputs=[], parent=None, mutation=None):
        self.opcode = opcode
        self.inputs = inputs
        self.id = id.unique()
        self.mutation = mutation
        self.parent = parent
        self.topLevel = False
        self.next = None
        self.shadow = False
    def toDictionary(self, script, stage, sprite=None):

        variables = stage.variables
        lists = stage.lists
        if sprite:
            variables.update(sprite.variables)
            lists.update(sprite.lists)
        inputs = {}
        fields = {}
        menu_index=0
        for i, t in zip(self.inputs, self.opcode.inputs):
            if t.type == "enum":
                if isinstance(i, str):
                    fields[t.name] = [i, None]
                else:
                    raise ValueError("input must be string for type enum")
            if t.type == "variable":
                if isinstance(i, str):
                    fields[t.name] = [i, variables[i]["id"]]
                else:
                    raise ValueError("input must be string for type variable")
            if t.type == "list":
                if isinstance(i, str):
                    fields[t.name] = [i, lists[i]["id"]]
                else:
                    raise ValueError("input must be string for type list")
            if t.type == "number":
                if isinstance(i, int) or isinstance(i, float):
                    inputs[t.name] = [1, [4, str(i)]]
                elif isinstance(i, Block):
                    i.parent = self
                    script.queueBuild(i)
                    inputs[t.name] = [3, i.id, [4, ""]]
                else:
                    raise ValueError("input must be number for type number")
            if t.type == "text":
                if isinstance(i, str) or isinstance(i, int) or isinstance(i, float):
                    inputs[t.name] = [1, [10, str(i)]]
                elif isinstance(i, Block):
                    i.parent = self
                    script.queueBuild(i)
                    inputs[t.name] = [3, i.id, [10, ""]]
                else:
                    raise ValueError("input must be text for type text")
            if t.type == "boolean":
                if isinstance(i, Block):
                    i.parent = self
                    script.queueBuild(i)
                    inputs[t.name] = [2, i.id]
                else:
                    raise ValueError("input must be a block for type boolean")
            if t.type == "menu":
                if isinstance(i, str):
                    menu = BlockTypes.BlockType(self.opcode.menus[menu_index], [BlockTypes.Input(t.name, "string")])
                    menu=menu(i)
                    script.queueBuild(menu)
                    inputs[t.name] = [1, menu.id]
                    menu_index+=1
                else:
                    raise ValueError("input must be a string for type menu")
            if t.type == "stack":
                s = Script(i)
                inputs[t.name] = [2, s.top.id]
                script.queueAll(s, self)
            if t.type == "block":
                i.parent = self
                inputs[t.name] = [1, i.id]
                script.queueBuild(i)
            if t.type == "message":
                fields[t.name] = [i, stage.broadcasts[i]]
            if t.type == "color":
                if isinstance(i, str):
                    fields[t.name] = [1, [9, i]]
                else:
                    raise ValueError("input must be string for type color")
        out = {
            "opcode": self.opcode.opcode,
            "next": self.next.id if self.next else None,
            "parent": self.parent.id if self.parent else None,
            "inputs": inputs,
            "fields": fields,
            "shadow": self.shadow,
            "topLevel": self.topLevel,
        }
        if self.topLevel:
            out["x"]=180
            out["y"]=255
        if self.mutation:
            out["mutation"] = self.mutation
        return out  