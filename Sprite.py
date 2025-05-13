import id
from Costume import Costume
class Sprite:
    def __init__(self, name, scripts=[], costumes=[Costume("empty.svg", "costume1")], currentCostume=0, sounds=[], variables={}, lists={}, broadcasts=[], volume=100, layer=1, visible=True, x=0, y=0, size=100, direction=90, draggable=False, rotationStyle="all around"):
        self.name = name
        self.variables = {k:{"id": id.unique(), "value": v} for k, v in variables.items()}
        self.lists = {k:{"id": id.unique(), "value": v} for k, v in lists.items()}
        self.broadcasts= {i: id.unique() for i in broadcasts}
        self.scripts = scripts
        self.costumes = costumes
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

    def toDictionary(self, stage):
        blocks = {}
        for i in self.scripts:
            blocks.update(i.toDictionary(stage, None if self.isStage else self))
        out = {
            "isStage": self.isStage,
            "name": self.name,
            "variables": {v["id"]:[k, v["value"]] for k, v in self.variables.items()},
            "lists": {v["id"]:[k, v["value"]] for k, v in self.lists.items()},
            "broadcasts": {v:k for k, v in self.broadcasts.items()},
            "costumes": [i.toDictionary()[0] for i in self.costumes],
            "currentCostume": self.currentCostume,
            "comments":{},
            "sounds": self.sounds,
            "blocks": blocks,
            "layerOrder": self.layer,
            "volume": self.volume,
        }
        if self.isStage:
            out["tempo"] = self.tempo
            out["videoTransparency"] = self.videoTransparency
            out["videoState"] = self.videoState
            out["textToSpeechLanguage"] = self.textToSpeechLanguage
        else:
            out["visible"] = self.visible
            out["x"] = self.x
            out["y"] = self.y
            out["size"] = self.size
            out["direction"] = self.direction
            out["draggable"] = self.draggable
            out["rotationStyle"] = self.rotationStyle
        return out
class Stage(Sprite):
    def __init__(self, scripts=[], backdrops=[Costume("empty.svg", "backdrop1")], currentBackdrop=0, sounds=[], variables={}, lists={}, broadcasts=[], volume=100, tempo=60, videoTransparency=50, videoState="on", textToSpeechLanguage=None):
        super().__init__("Stage", scripts, backdrops, currentBackdrop, sounds, variables, lists, broadcasts, volume, 0)
        self.isStage = True
        self.tempo = tempo
        self.videoTransparency = videoTransparency
        self.videoState = videoState
        self.textToSpeechLanguage = textToSpeechLanguage
