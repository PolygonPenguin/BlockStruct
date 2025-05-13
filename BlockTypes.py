from enum import Enum
import json
from Block import Block
import id
class Input:
    def __init__(self, name, type):
        self.name = name
        self.type = type
class BlockType:
    def __init__(self, opcode, inputs=[], menus=[], mutation={}, defaults=[]):
        self.opcode = opcode
        self.inputs = inputs
        self.menus = menus
        self.mutation = mutation
        self.defaults = defaults
    
    def __call__(self, *args, parent=None, mutation=None, shadow=False):
        args = list(args)
        args.extend(self.defaults)
        if not mutation:
            mutation = self.mutation
        b= Block(self, args, parent, mutation)
        b.shadow = shadow
        return b
    def __repr__(self):
        return self.opcode
    def __str__(self):
        return self.opcode


def parseBlock(block, menus=[]):
    name = block.split(": ")[0]
    inputs = []
    types = {
        "n":"number",
        "t": "text",
        "b": "boolean",
        "m": "menu",
        "e": "enum",
        "s": "stack",
        "k": "block",
        "r": "message",
        "c": "color",
        "v": "variable",
        "l": "list"
    }
    for i in block.split(": ")[1].split(", "):
        if i == "":
            continue
        inputs.append(Input(i[2:], types[i[0]]))
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
    SWITCH_BACKDROP_AND_WAIT = parseBlock("looks_switchbackdroptoandwait: m BACKDROP")
    NEXT_BACKDROP = parseBlock("looks_nextbackdrop: ")
    CHANGE_SIZE = parseBlock("looks_changesizeby: n CHANGE")
    SET_SIZE_TO = parseBlock("looks_setsizeto: n SIZE")
    CHANGE_EFFECT = parseBlock("looks_changeeffectby: e EFFECT, n CHANGE")
    SET_EFFECT = parseBlock("looks_seteffectto: e EFFECT, n VALUE")
    CLEAR_GRAPHICS_EFFECTS = parseBlock("looks_cleargraphiceffects: ")
    SHOW = parseBlock("looks_show: ")
    HIDE = parseBlock("looks_hide: ")
    GO_TO_LAYER = parseBlock("looks_gotofrontback: e FRONT_BACK")
    GO_FORWARD_BACKWARD_LAYERS = parseBlock("looks_goforwardbackwardlayers: e FORWARD_BACKWARD, n NUM")
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
    WAIT_UNTIL = parseBlock("control_repeat_until: b CONDITION")
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
    ADD = parseBlock("operators_add: n NUM1, n NUM2")
    SUBTRACT = parseBlock("operators_subtract: n NUM1, n NUM2")
    MULTIPLY = parseBlock("operators_multiply: n NUM1, n NUM2")
    DIVIDE = parseBlock("operators_divide: n NUM1, n NUM2")
    PICK_RANDOM = parseBlock("operator_random: n FROM, n TO")
    GREATER_THAN = parseBlock("operator_gt: n OPERAND1, n OPERAND2")
    LESS_THAN = parseBlock("operator_lt: n OPERAND1, n OPERAND2")
    EQUALS = parseBlock("operator_equals: n OPERAND1, n OPERAND2")
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
        LENGTH_OF_LIST = parseBlock("data_lengthoflist: e LIST")
        LIST_CONTAINS = parseBlock("data_listcontainsitem: t ITEM, l LIST")
        SHOW_LIST = parseBlock("data_showlist: l LIST")
        HIDE_LIST = parseBlock("data_hidelist: l LIST")

class MyBlocks:
    def DEFINE(block_name, inputs, runWithoutScreenRefresh=False, ref=None):
        
        argument_ids = [id.unique() for _ in inputs]
        count = block_name
        for i in inputs:
            match i.type:
                case "number":
                    setattr(MyBlocks.NumberOrText, i.name, BlockType("argument_reporter_string_number", [Input("VALUE", "enum")], defaults=[i.name]))
                    if "%s" in count:
                        count = count.replace("%s", "", 1)
                    else:
                        block_name+=" %s"
                case "text":
                    setattr(MyBlocks.NumberOrText, i.name, BlockType("argument_reporter_string_number", [Input("VALUE", "enum")], defaults=[i.name]))
                    if "%s" in count:
                        count = count.replace("%s", "", 1)
                    else:
                        block_name+=" %s"
                case "boolean":
                    setattr(MyBlocks.Booleans, i.name, BlockType("argument_reporter_boolean", [Input("VALUE", "enum")], defaults=[i.name]))
                    if "%b" in count:
                        count = count.replace("%b", "", 1)
                    else:
                        block_name+=" %b"
        mutation = {
            "tagName": "mutation",
            "children": [],
            "proccode": block_name,
            "argumentids": json.dumps(argument_ids),
            "argumentnames": json.dumps([i.name for i in inputs]),
            "argumentdefaults": json.dumps([(False if i.type=="boolean" else "") for i in inputs]),
            "warp": str(runWithoutScreenRefresh).lower()
        }
        b = BlockType("procedures_prototype", [Input(i, "block") for i in argument_ids])

        b=Block(b, [MyBlocks.Booleans.ARGUMENT(i.name, shadow=True) if i.type =="boolean" else MyBlocks.NumberOrText.ARGUMENT(i.name, shadow=True) for i in inputs], mutation=mutation)
        b.shadow=True
        defi = parseBlock("procedures_definition: k custom_block")
        out=defi(b)
        b.parent=out
        if ref == None:
            allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
            ref = ""
            for i in block_name:
                if i in allowed:
                    ref+=i
                elif i==" ":
                    ref+="_"
            if ref[0] in "0123456789":
                ref = "_"+ref
        setattr(MyBlocks, ref, BlockType("procedures_call", [Input(argument_ids[i], inputs[i].type) for i in range(len(inputs))], mutation=mutation))
        return out





    class Booleans:
        ARGUMENT = parseBlock("argument_reporter_boolean: e VALUE")

    class NumberOrText:
        ARGUMENT = parseBlock("argument_reporter_string_number: e VALUE")