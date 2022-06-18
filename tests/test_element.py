import unittest
from xml.etree.ElementTree import Element as XMLElement
from schoonmaker.element import Element
from .helpers import Helpers


class TestElement(unittest.TestCase):

    def setUp(self):
        self.paragraph_element = Helpers.paragraph_element()
        self.assertIsNotNone(self.paragraph_element)
        self.text_element = Helpers.text_element()
        self.assertIsNotNone(self.text_element)

    def test_paragraph_element(self):
        expected_tag = 'Paragraph'
        expected_attrib = {'Type': 'Action'}
        self.assertIsInstance(self.paragraph_element, XMLElement)
        self.assertEqual(expected_tag, self.paragraph_element.tag)
        self.assertDictEqual(expected_attrib, self.paragraph_element.attrib)
        element = Element(self.paragraph_element)
        self.assertIsNotNone(element)
        self.assertEqual(expected_tag, element.tag)
        self.assertDictEqual(expected_attrib, element.attrib)

    def test_text_element(self):
        expected_tag = 'Text'
        self.assertIsInstance(self.text_element, XMLElement)
        self.assertEqual(expected_tag, self.text_element.tag)
        element = Element(self.text_element)
        self.assertIsNotNone(element)
        self.assertEqual(expected_tag, element.tag)


if __name__ == '__main__':
    unittest.main()
