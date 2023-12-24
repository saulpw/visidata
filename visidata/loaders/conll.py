__author__ = "Paul McCann <polm@dampfkraft.com>"

from visidata import vd, VisiData, TableSheet, ItemColumn

@VisiData.api
def open_conll(vd, p):
    return ConllSheet(p.base_stem, source=p)


@VisiData.api
def open_conllu(vd, p):
    return ConllSheet(p.base_stem, source=p)


class ConllSheet(TableSheet):
    rowtype='tokens'
    # see here for reference:
    # https://universaldependencies.org/format.html
    columns=[
        # Usually an integer, but can be prefixed like "dev-s1"
        ItemColumn('sent_id', 0, type=str),
        # token ID is almost always an integer, but can be technically be a decimal between 0 and 1.
        # starts from 1 for each sentence.
        ItemColumn('token_id', 1, type=int),
        # form from the raw input, aka surface
        ItemColumn('form', 2, type=str),
        ItemColumn('lemma', 3, type=str),
        ItemColumn('upos', 4, type=str),
        ItemColumn('xpos', 5, type=str),
        ItemColumn('feats', 6, type=dict),
        ItemColumn('head', 7, type=int),
        ItemColumn('deprel', 8, type=str),
        # possibly list of pairs, but often? unused
        ItemColumn('deps', 9),
        # empty or a dictionary
        ItemColumn('misc', 10, type=dict),
    ]
    def iterload(self):
        pyconll = vd.importExternal('pyconll')

        # sent_id + token_id will be unique
        self.setKeys([self.columns[0], self.columns[1]])

        with self.source.open(encoding='utf-8') as fp:
            for sent in pyconll.load.iter_sentences(fp):
                sent_id = sent.id
                for token in sent:
                    yield [sent_id, token.id, token._form, token.lemma, token.upos,
                            token.xpos, token.feats, token.head, token.deprel, token.deps, token.misc]
