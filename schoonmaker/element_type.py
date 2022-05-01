from enum import Enum


# this is the `Type` in an `attrib`
class ElementType(Enum):
    OUTLINE_1 = 'Outline 1'
    OUTLINE_2 = 'Outline 2'
    OUTLINE_3 = 'Outline 3'
    OUTLINE_4 = 'Outline 4'
    OUTLINE_BODY = 'Outline Body'
    SHOT = 'Shot'
    ACTION = 'Action'
    CHARACTER = 'Character'
    DIALOGUE = 'Dialogue'
    SCENE_HEADING = 'Scene Heading'
    TRANSITION = 'Transition'
    PARENTHETICAL = 'Parenthetical'
    GENERAL = 'General'
    CAST_LIST = 'Cast List'
    NEW_ACT = 'New Act'
    END_OF_ACT = 'End of Act'
