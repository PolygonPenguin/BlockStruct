import random
import hashlib
import os
from PIL import Image
import json
import zipfile
import requests
from threading import Thread
import scratchattach as sa

allowed_chars_for_id = '!#%()*+,-./:;=?@[]^_`{|}~' +'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
used_ids = {}

def new_id_string():
    return "".join([random.choice(allowed_chars_for_id) for _ in range(20)])

def unique(server="main"):
    if server not in used_ids:
        used_ids[server] = []
    uuid = new_id_string()
    while uuid in used_ids[server]:
        uuid = new_id_string()
    used_ids[server].append(uuid)
    return uuid

class Input:
    def __init__(self, name, type):
        self.name = name
        self.type = type

class Script:
    def __init__(self, a=[], b=None):
        if not b:
            code = a
            hat = None
        else:
            code = b
            hat = a
            hat.topLevel = True
        if hat and code:
            code.insert(0, hat)
        elif hat and not code:
            code = [hat]

        for i, v in enumerate(code):
            if i + 1 < len(code):
                v.next = code[i + 1]
            if i - 1 >= 0:
                if not (hat and i == 0 and v == hat):
                    v.parent = code[i-1]
            elif i == 0 and not (hat and v == hat and v.parent):
                v.parent = None


        self.blocks = code
        if code:
            self.top = code[0]
        else:
            self.top = None

    def toDictionary(self, stage, sprite=None):
        active_blocks = list(self.blocks)
        out = {}
        _queued_builds = []
        _queued_alls_scripts = []
        _queued_alls_parents = []

        def queueBuild_local(block):
            nonlocal _queued_builds
            _queued_builds.insert(0, block)

        def queueAll_local(blocksobj, parent=None):
            nonlocal _queued_alls_scripts, _queued_alls_parents
            _queued_alls_scripts.append(blocksobj)
            _queued_alls_parents.append(parent)
        original_queueBuild = getattr(self, 'queueBuild', None)
        original_queueAll = getattr(self, 'queueAll', None)
        self.queueBuild = queueBuild_local
        self.queueAll = queueAll_local
        
        processing_queue = list(active_blocks)

        while processing_queue:
            block = processing_queue.pop(0)
            if block.id not in out:
                out[block.id] = block.toDictionary(self, stage, sprite)
            while _queued_builds:
                queued_block = _queued_builds.pop(0)
                if queued_block.id not in out:
                    if queued_block not in processing_queue:
                        processing_queue.append(queued_block)
            while _queued_alls_scripts:
                script_obj = _queued_alls_scripts.pop(0)
                parent_block = _queued_alls_parents.pop(0)
                if script_obj.blocks:
                    script_obj.blocks[0].parent = parent_block
                    script_obj.blocks[0].topLevel = False
                    for b in script_obj.blocks:
                        if b.id not in out and b not in processing_queue:
                            processing_queue.append(b)
        if original_queueBuild is not None:
            self.queueBuild = original_queueBuild
        else:
            del self.queueBuild
        if original_queueAll is not None:
            self.queueAll = original_queueAll
        else:
            del self.queueAll
            
        return out

class Block:
    def __init__(self, opcode, inputs=[], parent=None, mutation=None):
        self.opcode = opcode
        self.inputs = inputs
        self.id = unique()
        self.mutation = mutation
        self.parent = parent
        self.topLevel = False
        self.next = None
        self.shadow = False

    def toDictionary(self, script, stage, sprite=None):
        variables = stage.variables.copy()
        lists = stage.lists.copy()
        if sprite:
            variables.update(sprite.variables)
            lists.update(sprite.lists)
        
        inputs_dict = {}
        fields_dict = {}
        menu_index = 0
        opcode_inputs = []
        if hasattr(self.opcode, 'inputs') and self.opcode.inputs is not None:
            opcode_inputs = self.opcode.inputs

        for i, t in zip(self.inputs, opcode_inputs):
            if t.type == "enum":
                if isinstance(i, str):
                    fields_dict[t.name] = [i, None]
                else:
                    raise ValueError("input must be string for type enum")
            elif t.type == "variable":
                if isinstance(i, str):
                    if i not in variables:
                        raise ValueError(f"Variable '{i}' not found in stage or sprite variables.")
                    fields_dict[t.name] = [i, variables[i]["id"]]
                else:
                    raise ValueError("input must be string for type variable")
            elif t.type == "list":
                if isinstance(i, str):
                    if i not in lists:
                        raise ValueError(f"List '{i}' not found in stage or sprite lists.")
                    fields_dict[t.name] = [i, lists[i]["id"]]
                else:
                    raise ValueError("input must be string for type list")
            elif t.type == "number":
                if isinstance(i, (int, float)):
                    inputs_dict[t.name] = [1, [4, str(i)]]
                elif isinstance(i, Block):
                    i.parent = self
                    script.queueBuild(i)
                    inputs_dict[t.name] = [3, i.id, [4, ""]]
                else:
                    raise ValueError("input must be number or Block for type number")
            elif t.type == "text":
                if isinstance(i, (str, int, float)):
                    inputs_dict[t.name] = [1, [10, str(i)]]
                elif isinstance(i, Block):
                    i.parent = self
                    script.queueBuild(i)
                    inputs_dict[t.name] = [3, i.id, [10, ""]]
                else:
                    raise ValueError("input must be text or Block for type text")
            elif t.type == "boolean":
                if isinstance(i, Block):
                    i.parent = self
                    script.queueBuild(i)
                    inputs_dict[t.name] = [2, i.id]
                else:
                    if i is None:
                         inputs_dict[t.name] = [2, None]
                    else:
                        raise ValueError("input must be a Block or None for type boolean")
            elif t.type == "menu":
                if isinstance(i, str):
                    if menu_index < len(self.opcode.menus):
                        menu_opcode_str = self.opcode.menus[menu_index]
                        menu_block_type = BlockType(menu_opcode_str, [Input(t.name, "string")])
                        menu_block = menu_block_type(i)
                        menu_block.shadow = True
                        menu_block.parent = self
                        script.queueBuild(menu_block)
                        inputs_dict[t.name] = [1, menu_block.id]
                        menu_index += 1
                    else:
                        raise ValueError("Not enough menu definitions in BlockType for given inputs")
                else:
                    raise ValueError("input must be a string for type menu")
            elif t.type == "stack":
                if isinstance(i, list):
                    sub_script = Script(i)
                    if sub_script.top:
                        inputs_dict[t.name] = [2, sub_script.top.id]
                        script.queueAll(sub_script, self)
                    else:
                        inputs_dict[t.name] = [2, None]
                else:
                    raise ValueError("input must be a list of Blocks for type stack")
            elif t.type == "block":
                if isinstance(i, Block):
                    i.parent = self
                    script.queueBuild(i)
                    inputs_dict[t.name] = [1, i.id]
                else:
                    raise ValueError("input must be a Block for type block")
            elif t.type == "message":
                if isinstance(i, str):
                    if i not in stage.broadcasts:
                         raise ValueError(f"Broadcast message '{i}' not found in stage broadcasts.")
                    fields_dict[t.name] = [i, stage.broadcasts[i]]
                else:
                    raise ValueError("input must be string for type message")

            elif t.type == "color":
                if isinstance(i, str):
                    inputs_dict[t.name] = [1, [9, i]]
                else:
                    raise ValueError("input must be string for type color")
        
        out = {
            "opcode": self.opcode.opcode,
            "next": self.next.id if self.next else None,
            "parent": self.parent.id if self.parent else None,
            "inputs": inputs_dict,
            "fields": fields_dict,
            "shadow": self.shadow,
            "topLevel": self.topLevel,
        }
        if self.topLevel:
            out["x"] = 180
            out["y"] = 255
        if self.mutation:
            out["mutation"] = self.mutation
        return out

class BlockType:
    def __init__(self, opcode, inputs=[], menus=[], mutation={}, defaults=[]):
        self.opcode = opcode
        self.inputs = inputs
        self.menus = menus
        self.mutation = mutation
        self.defaults = defaults
    
    def __call__(self, *args, parent=None, mutation=None, shadow=False):
        args = list(args)
        if len(args) < len(self.inputs):
            args.extend(self.defaults[len(args) - len(self.inputs):])

        if not mutation and self.mutation:
            mutation_to_use = self.mutation
        else:
            mutation_to_use = mutation

        b = Block(self, args, parent, mutation_to_use)
        b.shadow = shadow
        return b

    def __repr__(self):
        return self.opcode
    def __str__(self):
        return self.opcode

def parseBlock(block_str, menus=[]):
    parts = block_str.split(": ", 1)
    name = parts[0]
    inputs = []
    types = {
        "n":"number", "t": "text", "b": "boolean", "m": "menu",
        "e": "enum", "s": "stack", "k": "block", "r": "message",
        "c": "color", "v": "variable", "l": "list"
    }
    if len(parts) > 1 and parts[1].strip():
        for i_str in parts[1].split(", "):
            if not i_str or len(i_str) < 2:
                continue
            input_type_char = i_str[0]
            input_name = i_str[2:]
            if input_type_char in types:
                inputs.append(Input(input_name, types[input_type_char]))
            else:
                raise ValueError(f"Unknown type character '{input_type_char}' in block string '{block_str}'")
    return BlockType(name, inputs, menus)

class Motion:
    MOVE_STEPS = parseBlock("motion_movesteps: n STEPS")
    TURN_CW_DEGREES = parseBlock("motion_turnright: n DEGREES")
    TURN_CCW_DEGREES = parseBlock("motion_turnleft: n DEGREES")
    GO_TO = parseBlock("motion_goto: m TO", ["motion_goto_menu"])
    GO_TO_XY = parseBlock("motion_gotoxy: n X, n Y")
    GLIDE_TO = parseBlock("motion_glideto: n SECS, m TO", ["motion_glideto_menu"])
    GLIDE_TO_XY = parseBlock("motion_glidesecstoxy: n SECS, n X, n Y")
    POINT_IN_DIRECTION = parseBlock("motion_pointindirection: n DIRECTION")
    POINT_TOWARDS = parseBlock("motion_pointtowards: m TOWARDS", ["motion_pointtowards_menu"])
    CHANGE_X = parseBlock("motion_changexby: n DX")
    SET_X = parseBlock("motion_setx: n X")
    CHANGE_Y = parseBlock("motion_changeyby: n DY")
    SET_Y = parseBlock("motion_sety: n Y")
    IF_ON_EDGE_BOUNCE = parseBlock("motion_ifonedgebounce: ")
    SET_ROTATION_STYLE = parseBlock("motion_setrotationstyle: e STYLE")
    X_POSITION = parseBlock("motion_xposition: ")
    Y_POSITION = parseBlock("motion_yposition: ")
    DIRECTION = parseBlock("motion_direction: ")

class Looks:
    SAY_FOR_SECS = parseBlock("looks_sayforsecs: t MESSAGE, n SECS")
    SAY = parseBlock("looks_say: t MESSAGE")
    THINK_FOR_SECS = parseBlock("looks_thinkforsecs: t MESSAGE, n SECS")
    THINK = parseBlock("looks_think: t MESSAGE")
    SWITCH_COSTUME = parseBlock("looks_switchcostumeto: m COSTUME", ["looks_costume"])
    NEXT_COSTUME = parseBlock("looks_nextcostume: ")
    SWITCH_BACKDROP = parseBlock("looks_switchbackdropto: m BACKDROP", ["looks_backdrops"])
    SWITCH_BACKDROP_AND_WAIT = parseBlock("looks_switchbackdroptoandwait: m BACKDROP", ["looks_backdrops"])
    NEXT_BACKDROP = parseBlock("looks_nextbackdrop: ")
    CHANGE_SIZE = parseBlock("looks_changesizeby: n CHANGE")
    SET_SIZE_TO = parseBlock("looks_setsizeto: n SIZE")
    CHANGE_EFFECT = parseBlock("looks_changeeffectby: e EFFECT, n CHANGE")
    SET_EFFECT = parseBlock("looks_seteffectto: e EFFECT, n VALUE")
    CLEAR_GRAPHICS_EFFECTS = parseBlock("looks_cleargraphiceffects: ")
    SHOW = parseBlock("looks_show: ")
    HIDE = parseBlock("looks_hide: ")
    GO_TO_LAYER = parseBlock("looks_gotofrontback: e FRONT_BACK")
    MOVE_LAYERS = parseBlock("looks_goforwardbackwardlayers: e FORWARD_BACKWARD, n NUM")
    COSTUME = parseBlock("looks_costumenumbername: e NUMBER_NAME")
    BACKDROP = parseBlock("looks_backdropnumbername: e NUMBER_NAME")
    SIZE = parseBlock("looks_size: ")

class Sound:
    PLAY_UNTIL_DONE = parseBlock("sound_playuntildone: m SOUND_MENU", ["sound_sounds_menu"])
    START_SOUND = parseBlock("sound_play: m SOUND_MENU", ["sound_sounds_menu"])
    STOP_ALL_SOUNDS = parseBlock("sound_stopallsounds: ")
    CHANGE_EFFECT = parseBlock("sound_changeeffectby: e EFFECT, n VALUE")
    SET_EFFECT = parseBlock("sound_seteffectto: e EFFECT, n VALUE")
    CLEAR_SOUND_EFFECTS = parseBlock("sound_cleareffects: ")
    CHANGE_VOLUME = parseBlock("sound_changevolumeby: n VOLUME")
    SET_VOLUME = parseBlock("sound_setvolumeto: n VOLUME")
    VOLUME = parseBlock("sound_volume: ")

class Events:
    WHEN_FLAG_CLICKED = parseBlock("event_whenflagclicked: ")
    WHEN_KEY_PRESSED = parseBlock("event_whenkeypressed: e KEY_OPTION")
    WHEN_THIS_SPRITE_CLICKED = parseBlock("event_whenthisspriteclicked: ")
    WHEN_STAGE_CLICKED = parseBlock("event_whenstageclicked: ")
    WHEN_GREATER_THAN = parseBlock("event_whengreaterthan: e WHENGREATERTHANMENU, n VALUE")
    WHEN_I_RECEIVE = parseBlock("event_whenbroadcastreceived: e BROADCAST_OPTION")
    BROADCAST = parseBlock("event_broadcast: r BROADCAST_INPUT")
    BROADCAST_AND_WAIT = parseBlock("event_broadcastandwait: r BROADCAST_INPUT")

class Control:
    WAIT_SECONDS = parseBlock("control_wait: n DURATION")
    REPEAT = parseBlock("control_repeat: n TIMES, s SUBSTACK")
    FOREVER = parseBlock("control_forever: s SUBSTACK")
    IF = parseBlock("control_if: b CONDITION, s SUBSTACK")
    IF_ELSE = parseBlock("control_if_else: b CONDITION, s SUBSTACK1, s SUBSTACK2")
    WAIT_UNTIL = parseBlock("control_wait_until: b CONDITION")
    REPEAT_UNTIL = parseBlock("control_repeat_until: b CONDITION, s SUBSTACK")
    STOP = parseBlock("control_stop: e STOP_OPTION")
    WHEN_I_START_AS_CLONE = parseBlock("control_start_as_clone: ")
    CREATE_CLONE_OF = parseBlock("control_create_clone_of: m CLONE_OPTION", ["control_create_clone_of_menu"])
    DELETE_THIS_CLONE = parseBlock("control_delete_this_clone: ")

class Sensing:
    TOUCHING = parseBlock("sensing_touchingobject: m TOUCHINGOBJECTMENU", ["sensing_touchingobjectmenu"])
    TOUCHING_COLOR = parseBlock("sensing_touchingcolor: c COLOR")
    COLOR_IS_TOUCHING = parseBlock("sensing_coloristouchingcolor: c COLOR, c COLOR2")
    DISTANCE_TO = parseBlock("sensing_distanceto: m DISTANCETOMENU", ["sensing_distancetomenu"])
    ASK_AND_WAIT = parseBlock("sensing_askandwait: t QUESTION")
    ANSWER = parseBlock("sensing_answer: ")
    KEY_PRESSED = parseBlock("sensing_keypressed: m KEY_OPTION", ["sensing_keyoptions"])
    MOUSE_DOWN = parseBlock("sensing_mousedown: ")
    MOUSE_X = parseBlock("sensing_mousex: ")
    MOUSE_Y = parseBlock("sensing_mousey: ")
    SET_DRAG_MODE = parseBlock("sensing_setdragmode: e DRAG_MODE")
    LOUDNESS = parseBlock("sensing_loudness: ")
    TIMER = parseBlock("sensing_timer: ")
    RESET_TIMER = parseBlock("sensing_resettimer: ")
    OF = parseBlock("sensing_of: e PROPERTY, m OBJECT", ["sensing_of_object_menu"])
    CURRENT = parseBlock("sensing_current: e CURRENTMENU")
    DAYS_SINCE_2000 = parseBlock("sensing_dayssince2000: ")
    USERNAME = parseBlock("sensing_username: ")

class Operators:
    ADD = parseBlock("operator_add: n NUM1, n NUM2")
    SUBTRACT = parseBlock("operator_subtract: n NUM1, n NUM2")
    MULTIPLY = parseBlock("operator_multiply: n NUM1, n NUM2")
    DIVIDE = parseBlock("operator_divide: n NUM1, n NUM2")
    PICK_RANDOM = parseBlock("operator_random: n FROM, n TO")
    GREATER_THAN = parseBlock("operator_gt: t OPERAND1, t OPERAND2")
    LESS_THAN = parseBlock("operator_lt: t OPERAND1, t OPERAND2")
    EQUALS = parseBlock("operator_equals: t OPERAND1, t OPERAND2")
    AND = parseBlock("operator_and: b OPERAND1, b OPERAND2")
    OR = parseBlock("operator_or: b OPERAND1, b OPERAND2")
    NOT = parseBlock("operator_not: b OPERAND")
    JOIN = parseBlock("operator_join: t STRING1, t STRING2")
    LETTER = parseBlock("operator_letter_of: n LETTER, t STRING")
    LENGTH = parseBlock("operator_length: t STRING")
    CONTAINS = parseBlock("operator_contains: t STRING1, t STRING2")
    MOD = parseBlock("operator_mod: n NUM1, n NUM2")
    ROUND = parseBlock("operator_round: n NUM")
    OF = parseBlock("operator_mathop: e OPERATOR, n NUM")

class Variables:
    VARIABLE = parseBlock("data_variable: v VARIABLE")
    SET_VARIABLE = parseBlock("data_setvariableto: v VARIABLE, t VALUE")
    CHANGE_VARIABLE = parseBlock("data_changevariableby: v VARIABLE, n VALUE")
    SHOW_VARIABLE = parseBlock("data_showvariable: v VARIABLE")
    HIDE_VARIABLE = parseBlock("data_hidevariable: v VARIABLE")
    
    class Lists:
        LIST = parseBlock("data_listcontents: l LIST")
        ADD_TO_LIST = parseBlock("data_addtolist: t ITEM, l LIST")
        DELETE_OF_LIST = parseBlock("data_deleteoflist: n INDEX, l LIST")
        DELETE_ALL_OF_LIST = parseBlock("data_deletealloflist: l LIST")
        INSERT_IN_LIST = parseBlock("data_insertatlist: t ITEM, n INDEX, l LIST")
        REPLACE_IN_LIST = parseBlock("data_replaceitemoflist: n INDEX, t ITEM, l LIST")
        ITEM_OF_LIST = parseBlock("data_itemoflist: n INDEX, l LIST")
        ITEM_NUMBER_IN_LIST = parseBlock("data_itemnumoflist: t ITEM, l LIST")
        LENGTH_OF_LIST = parseBlock("data_lengthoflist: l LIST")
        LIST_CONTAINS = parseBlock("data_listcontainsitem: t ITEM, l LIST")
        SHOW_LIST = parseBlock("data_showlist: l LIST")
        HIDE_LIST = parseBlock("data_hidelist: l LIST")

class MyBlocks:
    @staticmethod
    def DEFINE(block_name_format, inputs, runWithoutScreenRefresh=False, ref=None):
        argument_ids = [unique() for _ in inputs]
        proccode = block_name_format
        arg_names_ordered = []
        prototype_inputs_definitions = []
        arg_block_instances = []

        for i, inp_def in enumerate(inputs):
            arg_id = argument_ids[i]
            arg_name = inp_def.name
            arg_names_ordered.append(arg_name)

            if inp_def.type in ["number", "text"]:
                if not "%s" in proccode:
                    proccode += f" %s"
                arg_reporter_bt = BlockType("argument_reporter_string_number", [Input("VALUE", "enum")], defaults=[arg_name])
                setattr(MyBlocks.NumberOrText, arg_name.upper(), arg_reporter_bt)
                
                arg_block_instance = MyBlocks.NumberOrText.ARGUMENT(arg_name, shadow=True)

            elif inp_def.type == "boolean":
                if not "%b" in proccode:
                    proccode += f" %b"
                arg_reporter_bt = BlockType("argument_reporter_boolean", [Input("VALUE", "enum")], defaults=[arg_name])
                setattr(MyBlocks.Booleans, arg_name, arg_reporter_bt)
                
                arg_block_instance = MyBlocks.Booleans.ARGUMENT(arg_name, shadow=True)
            else:
                raise ValueError(f"Unsupported input type for custom block argument: {inp_def.type}")

            prototype_inputs_definitions.append(Input(arg_id, "block"))
            arg_block_instances.append(arg_block_instance)


        mutation = {
            "tagName": "mutation",
            "children": [],
            "proccode": proccode,
            "argumentids": json.dumps(argument_ids),
            "argumentnames": json.dumps(arg_names_ordered),
            "argumentdefaults": json.dumps([(False if i.type=="boolean" else "") for i in inputs]),
            "warp": str(runWithoutScreenRefresh).lower()
        }
        prototype_blocktype = BlockType("procedures_prototype", prototype_inputs_definitions, mutation=mutation)
        prototype_block_instance = prototype_blocktype(*arg_block_instances)
        prototype_block_instance.shadow = True
        definition_hat_blocktype = parseBlock("procedures_definition: k custom_block")
        definition_hat_instance = definition_hat_blocktype(prototype_block_instance)
        prototype_block_instance.parent = definition_hat_instance
        block_name_format.replace("%b", "").replace("%s", "")
        if ref is None:
            allowed_ref_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
            ref = ""
            temp_ref_name = block_name_format 
            for char_proc in temp_ref_name:
                if char_proc in allowed_ref_chars:
                    ref += char_proc
                elif char_proc == " ":
                    ref += "_"
            ref = ref.replace("__", "_").strip("_")
            if not ref or ref[0] in "0123456789":
                ref = "_" + ref
            if not ref:
                ref = "custom_block"
        call_inputs = []
        for i in range(len(inputs)):
            call_inputs.append(Input(argument_ids[i], inputs[i].type))

        callable_block_type = BlockType("procedures_call", call_inputs, mutation=mutation.copy())
        setattr(MyBlocks, ref.upper(), callable_block_type)
        
        return definition_hat_instance

    class Booleans:
        ARGUMENT = parseBlock("argument_reporter_boolean: e VALUE")

    class NumberOrText:
        ARGUMENT = parseBlock("argument_reporter_string_number: e VALUE")

class Costume:
    def __init__(self, file_path: str, name: str):
        self.file_path = file_path
        self.name = name
        if self.file_path == "DEFAULT.svg":
            self.assetId = hashlib.md5("""<svg version="1.1" width="2" height="2" viewBox="-1 -1 2 2" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<!-- Exported by Scratch - http://scratch.mit.edu/ -->
</svg>""".encode()).hexdigest()
            self.dataFormat = "svg"
            self.rotationCenterX = 1
            self.rotationCenterY = 1
        else:
            self.assetId = self._compute_md5()
            self.dataFormat = self._get_data_format()
            self._analyze_image()

        self.md5ext = f"{self.assetId}.{self.dataFormat}"
        if not hasattr(self, 'rotationCenterX'):
            self.rotationCenterX = 0 
            self.rotationCenterY = 0


    def _compute_md5(self) -> str:
        with open(self.file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_data_format(self) -> str:
        return os.path.splitext(self.file_path)[1].lower().strip(".")

    def _analyze_image(self):
        try:
            with Image.open(self.file_path) as img:
                self.rotationCenterX = img.width // 2
                self.rotationCenterY = img.height // 2
        except Exception:
            if self.dataFormat not in ['svg']:
                print(f"Warning: Could not analyze image {self.file_path} to determine center. Using 0,0.")
            self.rotationCenterX = 0
            self.rotationCenterY = 0


    def toDictionary(self):
        data = {
            "assetId": self.assetId,
            "name": self.name,
            "md5ext": self.md5ext,
            "dataFormat": self.dataFormat,
        }
        data["rotationCenterX"] = self.rotationCenterX
        data["rotationCenterY"] = self.rotationCenterY
        return (data, self.file_path, self.md5ext)

class Sprite:
    def __init__(self, name, scripts=[], costumes=[Costume("DEFAULT.svg", "costume1")], currentCostume=0, sounds=[], variables={}, lists={}, broadcasts=[], volume=100, layer=1, visible=True, x=0, y=0, size=100, direction=90, draggable=False, rotationStyle="all around"):
        self.name = name
        self.variables = {k:{"id": unique(), "value": v} for k, v in variables.items()}
        self.lists = {k:{"id": unique(), "value": v} for k, v in lists.items()}
        self.broadcasts= {i: unique() for i in broadcasts}
        self.scripts = scripts
        self.costumes = costumes if costumes else [Costume("DEFAULT.svg", "costume1")]
        self.currentCostume = currentCostume
        self.sounds = sounds
        self.isStage = False
        self.volume = volume
        self.layer = layer
        self.visible = visible
        self.x = x
        self.y = y
        self.size = size
        self.direction = direction
        self.draggable = draggable
        self.rotationStyle = rotationStyle

    def toDictionary(self, stage_instance):
        blocks_dict = {}
        for script_obj in self.scripts:
            sprite_context = self if not self.isStage else None
            blocks_dict.update(script_obj.toDictionary(stage_instance, sprite_context))
        
        out = {
            "isStage": self.isStage,
            "name": self.name,
            "variables": {v["id"]:[k, v["value"]] for k, v in self.variables.items()},
            "lists": {v["id"]:[k, v["value"]] for k, v in self.lists.items()},
            "broadcasts": {v:k for k, v in self.broadcasts.items()},
            "blocks": blocks_dict,
            "comments": {},
            "currentCostume": self.currentCostume,
            "costumes": [c.toDictionary()[0] for c in self.costumes],
            "sounds": self.sounds,
            "volume": self.volume,
            "layerOrder": self.layer,
        }
        if not self.isStage:
            out.update({
                "visible": self.visible,
                "x": self.x,
                "y": self.y,
                "size": self.size,
                "direction": self.direction,
                "draggable": self.draggable,
                "rotationStyle": self.rotationStyle,
            })
        return out

class Stage(Sprite):
    def __init__(self, scripts=[], backdrops=[Costume("DEFAULT.svg", "backdrop1")], currentBackdrop=0, sounds=[], variables={}, lists={}, broadcasts=[], volume=100, tempo=60, videoTransparency=50, videoState="on", textToSpeechLanguage=None):
        super().__init__("Stage", scripts, backdrops, currentBackdrop, sounds, variables, lists, broadcasts, volume, layer=0)
        self.isStage = True
        self.tempo = tempo
        self.videoTransparency = videoTransparency
        self.videoState = videoState
        self.textToSpeechLanguage = textToSpeechLanguage

    def toDictionary(self, stage_instance=None):
        base_dict = super().toDictionary(self) 
        base_dict.update({
            "tempo": self.tempo,
            "videoTransparency": self.videoTransparency,
            "videoState": self.videoState,
        })
        if self.textToSpeechLanguage is not None:
            base_dict["textToSpeechLanguage"] = self.textToSpeechLanguage
        base_dict["broadcasts"] = {v:k for k, v in self.broadcasts.items()}
        return base_dict

class Project:
    def __init__(self, stage=None, sprites=[]):
        self.stage = stage if stage else Stage()
        self.sprites = sprites
    
    def toDictionary(self):
        targets_list = [self.stage.toDictionary()]
        for s in self.sprites:
            targets_list.append(s.toDictionary(self.stage))

        out = {
            "targets": targets_list,
            "monitors":[],
            "extensions":[],
            "meta": {
                "semver": "3.0.0",
                "vm": "11.1.0",
                "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
            }
        }
        return out

    def toJSON(self):
        return json.dumps(self.toDictionary(), indent=4)
    
    def save_to_file(self, location):
        project_json_str = self.toJSON()
        files_to_zip = {"project.json": project_json_str.encode('utf-8')}

        all_targets = [self.stage] + self.sprites
        for target in all_targets:
            for costume_obj in target.costumes:
                costume_dict_tuple = costume_obj.toDictionary()
                file_path = costume_dict_tuple[1]
                md5ext_name = costume_dict_tuple[2]
                
                if file_path == "DEFAULT.svg":
                    files_to_zip[md5ext_name] = """<svg version="1.1" width="2" height="2" viewBox="-1 -1 2 2" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<!-- Exported by Scratch - http://scratch.mit.edu/ -->
</svg>""".encode('utf-8')
                elif os.path.exists(file_path):
                    with open(file_path, 'rb') as f_asset:
                        files_to_zip[md5ext_name] = f_asset.read()
                else:
                    print(f"Warning: Costume file not found {file_path}, skipping for {md5ext_name}")

        with zipfile.ZipFile(location, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for name, content_bytes in files_to_zip.items():
                zipf.writestr(name, content_bytes)
        return project_json_str

    def save_to_scratch(self, session: sa.Session, project_id_or_name):
        
        try:
            cloud_project = session.connect_project(project_id_or_name)

            threads = []
            json_thread = Thread(target=cloud_project.set_json, args=(self.toJSON(),))
            threads.append(json_thread)
            all_targets = [self.stage] + self.sprites
            assets_to_upload = {}

            for target in all_targets:
                for costume_obj in target.costumes:
                    _, file_path, md5ext = costume_obj.toDictionary()
                    if file_path != "DEFAULT.svg" and os.path.exists(file_path):
                        assets_to_upload[md5ext] = file_path

            for md5ext, filepath in assets_to_upload.items():
                with open(filepath, 'rb') as f:
                    asset_data = f.read()
                asset_url = f"https://assets.scratch.mit.edu/{md5ext}"
   
                headers = getattr(cloud_project, '_headers', session._headers)
                cookies = getattr(cloud_project, '_cookies', session._cookies)
                
                if headers and cookies:
                    asset_thread = Thread(target=requests.post, args=(asset_url, asset_data), kwargs={"headers": headers, "cookies": cookies})
                    threads.append(asset_thread)
                else:
                    print(f"Warning: Could not get headers/cookies for asset upload: {md5ext}")


            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            print(f"Project '{project_id_or_name}' update process initiated.")

        except Exception as e:
            print(f"Error saving to Scratch: {e}")
            print("Ensure you are logged in with scratchattach and the project ID/name is correct.")