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
        # relied on official pyconll guidance for migrating v3 to v4
        # https://pyconll.readthedocs.io/en/stable/migration.html
        pyconll = vd.importExternal('pyconll')
        try: #succeeds for pyconll version >= 4
            import pyconll.conllu
            v4 = True
        except ModuleNotFoundError:
            v4 = False

        # sent_id + token_id will be unique
        self.setKeys([self.columns[0], self.columns[1]])
        if v4:
            conllu = pyconll.conllu.conllu
            for sent in conllu.iter_from_file(self.source.given):
                for token in sent.tokens:
                    yield [sent.meta['sent_id'], token.id, token.form, token.lemma, token.upos,
                            token.xpos, token.feats, token.head, token.deprel, token.deps, token.misc]
        else:
            with self.source.open(encoding='utf-8') as fp:
                for sent in pyconll.load.iter_sentences(fp):
                    sent_id = sent.id
                    for token in sent:
                        yield [sent_id, token.id, token._form, token.lemma, token.upos,
                                token.xpos, token.feats, token.head, token.deprel, token.deps, token.misc]
