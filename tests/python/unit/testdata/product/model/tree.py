

class Properties(object):

    LABEL = 'Atlas'

    def __init__(self, **kwargs):
        self._dict = kwargs
        self.logger = None

    def get(self, k):
        return self._dict.get(k)


class AtlasItem(object):

    def __init__(self):
        self.fakePath = ''
        self.fakeProperties = Properties()
        self.fakeItemType = ''

    def getItemType(self):
        return self.fakeItemType

    def getProperty(self, name):
        return self.fakeProperties.get(name)

    def getPath(self):
        return self.fakePath

    @classmethod
    def createFromFakeAmcVersion(cls, fakeVersion, asRig=False):
        i = cls()
        if asRig:
            i.fakeProperties['motion:path'] = fakeVersion.hyref
            i.fakeItemType = 'rig'
        else:
            i.fakePath = fakeVersion.hyref
        return i


staticItem = AtlasItem()
