import weakref
from defcon.objects.base import BaseDictObject
from defcon.objects.color import Color

_defaultTransformation = {
    "xScale"  : 1,
    "xyScale" : 0,
    "yxScale" : 0,
    "yScale"  : 1,
    "xOffset" : 0,
    "yOffset" : 0
}


class Image(BaseDictObject):

    """
    This object represents an image reference in a glyph.

    **This object posts the following notifications:**

    ===========================
    Name
    ===========================
    Image.Changed
    Image.FileNameChanged
    Image.TransformationChanged
    Image.ColorChanged
    Image.ImageDataChanged
    ===========================

    During initialization an image dictionary, following the format defined
    in the UFO spec, can be passed. If so, the new object will be populated
    with the data from the dictionary.
    """

    changeNotificationName = "Image.Changed"
    representationFactories = {}

    def __init__(self, glyph=None, imageDict=None):
        self._font = None
        self._layerSet = None
        self._layer = None
        self._glyph = None
        self.glyph = glyph
        super(Image, self).__init__()
        self.beginSelfNotificationObservation()
        self["fileName"] = None
        self["color"] = None
        if imageDict is not None:
            self.update(imageDict)
        for key, value in _defaultTransformation.items():
            if self.get(key) is None:
                self[key] = value
        self._dirty = False

    def __len__(self):
        # this is a little hack for glifLib writing.
        # when a GLIF is written, glyph.image is chekced with:
        #     if glyph.image:
        # fileName is required, so if that isn't defined
        # return 0. this tells glifLib to skip the image.
        if self["fileName"] is None:
            return 0
        return super(Image, self).__len__()

    # --------------
    # Parent Objects
    # --------------

    def getParent(self):
        return self.glyph

    def _get_font(self):
        font = None
        if self._font is None:
            glyph = self.glyph
            if glyph is not None:
                font = glyph.font
                if font is not None:
                    self._font = weakref.ref(font)
        else:
            font = self._font()
        return font

    font = property(_get_font, doc="The :class:`Font` that this image belongs to.")

    def _get_layerSet(self):
        layerSet = None
        if self._layerSet is None:
            glyph = self.glyph
            if glyph is not None:
                layerSet = glyph.layerSet
                if layerSet is not None:
                    self._layerSet = weakref.ref(layerSet)
        else:
            layerSet = self._layerSet()
        return layerSet

    layerSet = property(_get_layerSet, doc="The :class:`LayerSet` that this image belongs to.")

    def _get_layer(self):
        layer = None
        if self._layer is None:
            glyph = self.glyph
            if glyph is not None:
                layer = glyph.layer
                if layer is not None:
                    self._layer = weakref.ref(layer)
        else:
            layer = self._layer()
        return layer

    layer = property(_get_layer, doc="The :class:`Layer` that this image belongs to.")

    def _get_glyph(self):
        if self._glyph is None:
            return None
        return self._glyph()

    def _set_glyph(self, glyph):
        assert self._glyph is None
        if glyph is not None:
            glyph = weakref.ref(glyph)
        self._font = None
        self._layerSet = None
        self._layer = None
        self._glyph = glyph

    glyph = property(_get_glyph, _set_glyph, doc="The :class:`Glyph` that this image belongs to. This should not be set externally.")

    # ----------
    # Attributes
    # ----------

    # file name

    def _get_fileName(self):
        return self["fileName"]

    def _set_fileName(self, fileName):
        oldFileName = self.get("fileName")
        if fileName == oldFileName:
            return
        self["fileName"] = fileName
        self.postNotification("Image.FileNameChanged", data=dict(oldValue=oldFileName, newValue=fileName))

    fileName = property(_get_fileName, _set_fileName, doc="The file name the image. Setting this will posts *Image.Changed* and *Image.FileNameChanged* notifications.")

    # transformation

    def _get_transformation(self):
        if "xScale" not in self:
            return
        return (self["xScale"], self["xyScale"], self["yxScale"], self["yScale"], self["xOffset"], self["yOffset"])

    def _set_transformation(self, transformation):
        oldTransformation = self.transformation
        if oldTransformation == transformation:
            return
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = transformation
        # hold the notifications so that only one is sent out
        self.holdNotifications()
        self["xScale"] = xScale
        self["xyScale"] = xyScale
        self["yxScale"] = yxScale
        self["yScale"] = yScale
        self["xOffset"] = xOffset
        self["yOffset"] = yOffset
        self.releaseHeldNotifications()
        self.postNotification("Image.TransformationChanged", data=dict(oldValue=oldTransformation, newValue=transformation))

    transformation = property(_get_transformation, _set_transformation, doc="The transformation matrix for the image. Setting this will posts *Image.Changed* and *Image.TransformationChanged* notifications.")

    # color

    def _get_color(self):
        return self.get("color")

    def _set_color(self, color):
        if color is None:
            newColor = None
        else:
            newColor = Color(color)
        oldColor = self.get("color")
        if newColor == oldColor:
            return
        self["color"] = newColor
        self.postNotification("Image.ColorChanged", data=dict(oldValue=oldColor, newValue=newColor))

    color = property(_get_color, _set_color, doc="The image's :class:`Color` object. When setting, the value can be a UFO color string, a sequence of (r, g, b, a) or a :class:`Color` object. Setting this posts *Image.ColorChanged* and *Image.Changed* notifications.")

    # ------------------------
    # Notification Observation
    # ------------------------

    def beginSelfNotificationObservation(self):
        super(Image, self).beginSelfNotificationObservation()
        self.beginSelfImageSetNotificationObservation()

    def endSelfNotificationObservation(self):
        self.endImageSetNotificationObservation()
        super(Image, self).endSelfNotificationObservation()
        self._font = None
        self._layerSet = None
        self._layer = None
        self._glyph = None

    def beginSelfImageSetNotificationObservation(self):
        font = self.font
        if font is None:
            return
        imageSet = font.images
        imageSet.addObserver(self, "imageSetImageAddedNotificationCallback", "ImageSet.ImageAdded")
        imageSet.addObserver(self, "imageSetImageDeletedNotificationCallback", "ImageSet.ImageDeleted")
        imageSet.addObserver(self, "imageSetImageChangedNotificationCallback", "ImageSet.ImageChanged")
        layer = self.layer
        layer.addObserver(self, "layerColorChangedNotificationCallback", "Layer.ColorChanged")

    def endImageSetNotificationObservation(self):
        font = self.font
        if font is None:
            return
        imageSet = font.images
        imageSet.removeObserver(self, "ImageSet.ImageAdded")
        imageSet.removeObserver(self, "ImageSet.ImageDeleted")
        imageSet.removeObserver(self, "ImageSet.ImageChanged")
        layer = self.layer
        layer.removeObserver(self, "Layer.ColorChanged")

    def imageSetImageAddedNotificationCallback(self, notification):
        name = notification.data["name"]
        if name != self.fileName:
            return
        self.postNotification("Image.ImageDataChanged")

    def imageSetImageDeletedNotificationCallback(self, notification):
        name = notification.data["name"]
        if name != self.fileName:
            return
        self.postNotification("Image.ImageDataChanged")

    def imageSetImageChangedNotificationCallback(self, notification):
        name = notification.data["name"]
        if name != self.fileName:
            return
        self.postNotification("Image.ImageDataChanged")

    def layerColorChangedNotificationCallback(self, notification):
        if self.color is not None:
            self.postNotification("Image.ColorChanged", data=notification.data)


def _testAttributes():
    """
    >>> i = Image()
    >>> i.dirty
    False

    >>> i.fileName = "foo"
    >>> i.fileName
    'foo'
    >>> i.dirty
    True

    >>> i = Image()
    >>> i.transformation = (1, 2, 3, 4, 5, 6)
    >>> i.transformation
    (1, 2, 3, 4, 5, 6)
    >>> i.dirty
    True

    >>> i = Image()
    >>> i.color = "1, 1, 1, 1"
    >>> i.color
    '1,1,1,1'
    >>> i.dirty
    True

    >>> i = Image(imageDict=dict(fileName="foo.png", xScale="1", xyScale="2", yxScale="3", yScale="4", xOffset="5", yOffset="6", color="0,0,0,0"))
    >>> i.fileName, i.transformation, i.color
    ('foo.png', ('1', '2', '3', '4', '5', '6'), '0,0,0,0')
    """

def _testRead():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> glyph = font.layers["Layer 1"]["A"]
    >>> image = glyph.image
    >>> image.fileName
    'image 1.png'
    >>> image.color
    '0.1,0.2,0.3,0.4'
    >>> image.transformation
    (0.5, 0, 0, 0.5, 0, 0)
    """

def _testWrite():
    """
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> glyph = font.layers[None]["A"]
    >>> glyph.image = glyph.instantiateImage()
    >>> glyph.image.color = "1,1,1,1"
    >>> glyph.image.fileName = "foo.png"
    >>> glyph.image.transformation = (1, 2, 3, 4, 5, 6)
    >>> font.save()
    >>> font = Font(path)
    >>> glyph = font.layers[None]["A"]
    >>> sorted(glyph.image.items())
    [('color', '1,1,1,1'), ('fileName', 'foo.png'), ('xOffset', 5), ('xScale', 1), ('xyScale', 2), ('yOffset', 6), ('yScale', 4), ('yxScale', 3)]
    >>> tearDownTestFontCopy()
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
