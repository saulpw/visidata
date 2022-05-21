from visidata import vd, options, SequenceSheet, Path, Sheet, VisiData

@VisiData.api
def open_bam(vd, p):
    return BamSheet(p.name, source=p)

vd.option('bam_tagdelimiter', ' ', 'delimiter passed to bam.reader', replay=True)
vd.option('bam_showintqual', False, 'show QUAL phred scores in int form', replay=True)

class BamSheet(SequenceSheet):
    _rowtype = list  # rowdef: list of values

    def iterload(self):
        import pysam
        delim = self.options.delimiter
        rowdelim = self.options.row_delimiter

        source = self.source
        if not isinstance(self.source, Path):
            vd.status('bam file not present for %s' % source)

        with pysam.AlignmentFile(source, 'rb') as fp:
            header = ["QNAME", "FLAG", "RNAME", "POS", "MAPQ", 
                "CIGAR", "RNEXT", "PNEXT", "TLEN", "SEQ", "QUAL",
                "TAGS"]
            yield header

            references = fp.references
            for reference in references:
                for read in fp.fetch(reference):
                    rd = read.to_dict()
                    if 'tags' not in rd: rd['tags'] = None
                    qual = rd['qual']
                    if options.bam_showintqual: # show QUAL from str to int
                        qual = str(read.query_qualities.tolist())[1:-1]
                    row = [
                        rd['name'], 
                        rd['flag'], 
                        rd['ref_name'], 
                        rd['ref_pos'], 
                        rd['map_quality'],
                        rd['cigar'], 
                        rd['next_ref_name'],
                        rd['next_ref_pos'],
                        rd['length'],
                        rd['seq'],
                        qual,
                        options.bam_tagdelimiter.join(rd['tags']),
                    ]

                    if len(row) < self.nVisibleCols:
                        # extend rows that are missing entries
                        row.extend([None]*(self.nVisibleCols-len(row)))

                    yield row

vd.addGlobals({
    'BamSheet': BamSheet,
})
