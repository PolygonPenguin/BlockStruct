import scratchattach as sa
import zipfile
import requests
from threading import Thread
from Costume import Costume
class Project:
    def __init__(self, stage=None, sprites=[]):
        self.sprites = sprites
        self.sprites.insert(0, stage)
        self.stage = stage
    
    def toDictionary(self):
        out = {
            "targets": [s.toDictionary(self.stage) for s in self.sprites],
            "monitors":[],
            "extensions":[],
            "meta": {
                "semver": "3.0.0",
                "vm": "11.1.0",
                "agent": "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0"
            }
        }
        return out
    def toJSON(self):
        import json
        return json.dumps(self.toDictionary(), indent=4)
    
    def save_to_file(self, location):
        
        project=self.toJSON()
        files = {"project.json":project}
        for i in self.sprites:
            for j in i.costumes:
                c = j.toDictionary()
                with open(c[1], 'rb') as f:
                    files[c[2]] = f.read()
        with zipfile.ZipFile(location, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for name, content in files.items():
                if isinstance(content, str):
                    content = content.encode('utf-8')
                zipf.writestr(name, content)
        return project
    def save_to_scratch(self, session: sa.Session, project_id_or_name):
        project = session.connect_project(project_id_or_name)
        threads = [Thread(target=project.set_json, args=(self.toJSON(),))]
        for i in self.sprites:
            for j in i.costumes:
                j = j.toDictionary()
                with open(j[1], 'rb') as f:
                    data = f.read()
                threads.append(Thread(target=requests.post, args=(
                    "https://assets.scratch.mit.edu/"+j[2],
                    data,
                    {
                        "headers": project._headers,
                        "cookies": project._cookies
                    }
                )))
        for i in threads:
            i.start()
        for i in threads:
            i.join()
        