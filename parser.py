import re

class Extractor:
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)
        self.matches = []
    def __call__(self, string):
        result = self.pattern.findall(string)
        self.matches += result
        return self.matches

IPExtractor = Extractor('((?:(?:(?:\d){1,3}\.){3})(?:\d){1,3})')
