from enum import Enum


class ElementAttribute(Enum):
    DOCUMENT_TYPE = 'DocumentType'
    TEMPLATE = 'Template'
    VERSION = 'Version'
    TYPE = 'Type'
    ALIGNMENT = 'Alignment'
    FIRST_INDENT = 'FirstIndent'
    LEADING = 'Leading'
    LEFT_INDENT = 'LeftIndent'
    RIGHT_INDENT = 'RightIndent'
    SPACE_BEFORE = 'SpaceBefore'
    SPACING = 'Spacing'
    STARTS_NEW_PAGE = 'StartsNewPage'
    ADORNMENT_STYLE = 'AdornmentStyle'
    BACKGROUND = 'Background'
    COLOR = 'Color'
    FONT = 'Font'
    REVISION_ID = 'RevisionID'
    SIZE = 'Size'
    # `STYLE` has a lot going one. This can be concatenated
    # with `+` or a single value. Examples:
    # `'Bold+Underline'`, `'Bold+Underline+AllCaps'`,
    # `'Bold'`, `''`, `'Italic'`, `'Underline'`, `'Italic+AllCaps'`
    # note the empty string (`''`) as a possible value
    STYLE = 'Style'
    LENGTH = 'Length'
    PAGE = 'Page'
    TITLE = 'Title'
    CURRENT = 'Current'  # used for `ElementAttribute.ALTS`

    # WATERMARKING
    OPACITY = 'Opacity'
    POSITION = 'Position'

    # HEADER_AND_FOOTER
    FOOTER_FIRST_PAGE = 'FooterFirstPage'
    FOOTER_VISIBLE = 'FooterVisible'
    HEADER_FIRST_PAGE = 'HeaderFirstPage'
    HEADER_VISIBLE = 'HeaderVisible'
    STARTING_PAGE = 'StartingPage'

    # PAGE_LAYOUT
    BACKGROUND_COLOR = 'BackgroundColor'
    BOTTOM_MARGIN = 'BottomMargin'
    BREAK_DIALOGUE_AND_ACTIONS_AT_SENTENCES = \
        'BreakDialogueAndActionAtSentences'
    DOCUMENT_LEADING = 'DocumentLeading'
    FOOTER_MARGIN = 'FooterMargin'
    FOREGROUND_COLOR = 'ForegroundColor'
    HEADER_MARGIN = 'HeaderMargin'
    INVISIBLE_COLOR = 'InvisiblesColor'
    TOP_MARGIN = 'TopMargin'
    USES_SMART_QUOTES = 'UsesSmartQuotes'

    # WINDOW_STATE
    HEIGHT = 'Height'
    LEFT = 'Left'
    MODE = 'Mode'
    TOP = 'Top'
    WIDTH = 'Width'

    # TEXT_STATE
    SCALING = 'Scaling'
    SELECTION = 'Selection'
    SHOW_INVISIBLES = 'ShowInvisibles'

    # REVISIONS
    ACTIVE_SET = 'ActiveSet'
    LOCATION = 'Location'
    REVISION_MODE = 'RevisionMode'
    REVISIONS_SHOWN = 'RevisionsShown'
    SHOW_PAGE_COLOR = 'ShowPageColor'

    # SPLIT_STATE
    ACTIVE_PANEL = 'ActivePanel'
    CARDS_ACROSS = 'CardsAcross'
    SHOW_ACTION = 'ShowAction'
    SHOW_SCENE_TITLE = 'ShowSceneTitle'
    SHOW_SUMMARY = 'ShowSummary'
    SPLIT_MODE = 'SplitMode'
    SPLITTER_POSITION = 'SplitterPosition'

    # SCENE_NUMBER_OPTIONS
    LEFT_LOCATION = 'LeftLocation'
    NUMBER_SCHEME = 'NumberScheme'
    RIGHT_LOCATION = 'RightLocation'
    SHOW_NUMBERS_ON_LEFT = 'ShowNumbersOnLeft'
    SHOW_NUMBERS_ON_RIGHT = 'ShowNumbersOnRight'

    # CAST_LIST
    SORT_OPTION = 'SortOption'

    # TAGS_NAVIGATOR_PREFERENCES
    IS_SORT_ASCENDING = 'IsSortAscending'
    SORT_COLUMN = 'SortColumn'

    # WRITER_MARKUP
    STATE = 'State'

    # OUTLINES
    HIDDEN = 'Hidden'
