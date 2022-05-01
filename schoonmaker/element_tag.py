from enum import Enum


class ElementTag(Enum):
    # ROOT TAG
    FINAL_DRAFT = 'FinalDraft'

    # HIGH LEVEL
    CONTENT = 'Content'
    WATERMARKING = 'Watermarking'
    HEADER_AND_FOOTER = 'HeaderAndFooter'
    SPELLCHECK_IGNORE_LISTS = 'SpellCheckIgnoreLists'
    PAGE_LAYOUT = 'PageLayout'
    WINDOW_STATE = 'WindowState'
    TEXT_STATE = 'TextState'
    ELEMENT_SETTINGS = 'ElementSettings'
    TITLE_PAGE = 'TitlePage'
    SMART_TYPE = 'SmartType'
    MORES_AND_CONTINUEDS = 'MoresAndContinueds'
    LOCKED_PAGES = 'LockedPages'
    REVISIONS = 'Revisions'
    SPLIT_STATE = 'SplitState'
    MACROS = 'Macros'
    ACTORS = 'Actors'
    CAST = 'Cast'
    SCENE_NUMBER_OPTIONS = 'SceneNumberOptions'
    CAST_LIST = 'CastList'
    CHARACTER_HIGHLIGHTING = 'CharacterHighlighting'
    SCENE_NAVIGATOR_PREFERENCES = 'SceneNavigatorPreferences'
    TAGS_NAVIGATOR_PREFERENCES = 'TagsNavigatorPreferences'
    ALT_COLLECTION = 'AltCollection'
    TARGET_SCRIPT_LENGTH = 'TargetScriptLength'
    LIST_ITEMS = 'ListItems'
    DISPLAY_BOARDS = 'DisplayBoards'
    WRITERS = 'Writers'
    WRITER_MARKUP = 'WriterMarkup'
    TAG_DATA = 'TagData'
    CHARACTERS = 'Characters'
    SCRIPT_NOTES = 'ScriptNotes'
    IMAGES = 'Images'
    OUTLINES = 'Outlines'

    # CONTENT
    PARAGRAPH = 'Paragraph'