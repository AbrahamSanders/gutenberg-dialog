import os


# These can also be set as arguments via the command line.
class Config:
    dialog_gap = 150
    include_surrounding_narratives = False
    max_narrative_length = 250  # max number of words in 1 narrative (250)
    min_intermediate_narrative_length = 5  # min number of words in 1 intermediate narrative (5)
    max_utterance_length = 100  # max number of words in 1 utterance (100)
    max_books = 100000  # limit size of the dataset
    min_delimiters = 150  # per 10.000 words (150)
    kl_threshold = 2  # (2)
    size_threshold = 20000  # minimum number of words in a book for filtering
    vocab_threshold = 0.2  # (0.2)
    min_double_delim = 40  # for latin languages and hungarian
    clean_dialogs = False  # if True, run preprocessing on dialogs
    languages = ['hu']
    download = False
    pre_filter = False
    extract = False
    post_filter = False
    create_dataset = False
    run_all = False
    directory = os.path.join('data', 'filtered')
