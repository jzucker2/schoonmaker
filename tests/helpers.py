from xml.etree.ElementTree import Element as XMLElement


DEFAULT_TEXT = "She reaches in a pocket... " \
               "takes out the necklace of knitted leaves " \
               "-- from where the gold key hangs like a charm."


DEFAULT_PARAGRAPH_TYPE = 'Action'


class Helpers(object):
    @classmethod
    def base_element(cls, tag, text=None, attrib=None, **kwargs):
        if not attrib:
            attrib = {}
        if text:
            text = text.strip('\n')
            attrib['text'] = text
        if kwargs:
            attrib.update(kwargs)
        return XMLElement(tag, attrib=attrib)

    @classmethod
    def text_element(cls, text=DEFAULT_TEXT):
        return cls.base_element('Text', text=text)

    # notice the capital `T` in `Type` for FinalDraft
    @classmethod
    def paragraph_element(cls, Type=DEFAULT_PARAGRAPH_TYPE):
        return cls.base_element('Paragraph', Type=Type)
