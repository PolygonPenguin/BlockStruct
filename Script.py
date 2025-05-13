class Script:
    def __init__(self, a=[], b=None):
        if not b:
            code = a
            hat = None
        else:
            code = b
            hat = a
            hat.topLevel = True
        if hat:
            code.insert(0, hat)
        for i, v in enumerate(code):
            if i+1<len(code):
                v.next = code[i+1]
            if i-1 >= 0:
                v.parent=code[i-1]
        self.blocks = code
        self.top = code[0]
    def toDictionary(self, stage, sprite=None):
        blocks = self.blocks
        out = {}
        def queueBuild(block):
            nonlocal blocks
            blocks.insert(0, block)
        def queueAll(blocksobj, parent=None):
            nonlocal blocks
            blocksobj.blocks[0].parent = parent
            blocksobj.blocks[0].topLevel = False
            b = blocksobj.blocks
            b.extend(blocks)
            blocks = b
        self.queueBuild = queueBuild
        self.queueAll = queueAll
        while blocks:
            block = blocks.pop(0)
            out[block.id] = block.toDictionary(self, stage, sprite)
        return out
    