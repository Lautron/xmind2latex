from json_flatten import flatten, unflatten
import json, zipfile, pprint, csv, sys
from collections import namedtuple
import pyperclip

class Xmind:
    def __init__(self, filename, ignore=None, delete=None):
        self.data = None
        self.clean_data = None
        self.formatted_data = None
        if not ignore:
            self.ignore = [
                    'image', 'style', 'provider', 'id', 
                    'structureClass', 'topicId', 'summaries', 'align',
                    ]
        else:
            self.ignore = ignore

        self.delete = delete if delete else ['.extensions.0', '.attached'] 
        self.get_data(filename)
        self.get_clean_data()
        self.format_data()
        self.build_output()

    def get_data(self, filename):
        zip_file = zipfile.ZipFile(filename, 'r')
        raw_json = zip_file.read('content.json')
        content_data = json.loads(raw_json)[0]['rootTopic']['children']['attached']
        self.data = content_data

    def clean_key(self, key):
        for replacement in self.delete:
            key = key.replace(replacement, "") if replacement in key else key
        return key

    def get_clean_data(self):
        flattened_data = flatten(self.data)
        is_relevant = lambda key: all([ignored_key not in key for ignored_key in self.ignore])
        format_value = lambda key,value: f'${value}$' if 'content' in key else value

        clean_data = { 
                self.clean_key(key): format_value(key, value)
                for key, value in flattened_data.items() 
                if value and is_relevant(key) 
            }
        self.clean_data = clean_data

    def format_data(self):
        get_indent = lambda key: key.count('children')
        # TODO: maybe move this elsewhere
        Node = namedtuple("Node", ["indentation", "value"])
        node_list = [Node(get_indent(key), value) for key, value in self.clean_data.items()]
        #print(res)
        self.formatted_data = node_list

    def use_template(self, indentation, value):
        templates = {
                0: "\subsection*{{{}}}",
                1: "\subsubsection*{{{}}}", 
                }
        default_template = "\\begin{{itemize}}\n{}\n\end{{itemize}}"
        #default_template = "\\paragraph{{{}}}"

        return templates.get(indentation, default_template).format(value)

    def build_output(self):
        below3 = [index for index, item in enumerate(self.formatted_data) if item.indentation < 3]
        ranges = [(index, below3[i+1]) for i, index in enumerate(below3[:-1])]
        res = [self.formatted_data[a:b] for a, b in ranges] + [[self.formatted_data[-1]]]
        #print(res[-1], self.formatted_data[-1], sep="\n")
        #res[-1].append(self.formatted_data[-1])
        format_list = lambda lista: lista[0] if len(lista) == 1 else (3, " ".join([item.value for item in lista]))
        unified_data = [format_list(lista) for lista in res ]
        result = [self.use_template(indentation, value) for indentation, value in unified_data]
        pyperclip.copy("\n".join(result))
        #pprint.pprint(result)

if __name__ == "__main__":
    test = Xmind("Series.xmind")
