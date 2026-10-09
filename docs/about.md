# About the Vulgate

This dataset holds the books of the Hebrew Bible in the Vulgate.

The source of this dataset is the Vulgate of the LatinISE corpus, version 6
([LINDAT, hdl.handle.net/11372/LRT-6140](http://hdl.handle.net/11372/LRT-6140)),
by Barbara McGillivray, completed from the Vulgate of the IntraText Digital Library,
"Vulgata Hyeronimiana versio, IntraText Edition CT", document `LAT0001`.

LatinISE took its Vulgate from the IntraText edition. It gives the words of every verse,
lowercase and without punctuation, in one paragraph per paragraph of IntraText, without verse
numbers. IntraText gives the verse numbers, and the chapters that LatinISE lacks.

The Psalter is the Psalter iuxta Hebraeos. Psalms are numbered as in the Vulgate, after the
Greek: Psalm 22 is Psalm 23 of the Hebrew Bible.

# Corpus

The [source](../source) directory holds both sources.

*   [latinise/latin14_vulgata.txt](../source/0.1/latinise/latin14_vulgata.txt) holds the
    70 documents of the Vulgate (`n="LAT0001"`) of the LatinISE file `latin14.txt`, copied
    unchanged, line for line. The whole file is 227 MB, over the file size limit of GitHub.
*   [intratext](../source/0.1/intratext) holds the table of contents and the 1,307 chapter
    pages of the IntraText Vulgate, as served by the Internet Archive.

The books of the Hebrew Bible in these files have been converted into Text-Fabric format by
[tfFromLatinISE.py](../programs/tfFromLatinISE.py).
We have a [specification](transcription.md) of how we model the text in Text-Fabric.
The conversion result is available in the [tf](../tf) directory.

The dataset has 39 books, 915 chapters, 22,805 verses, and 399,123 words.
The words of 21,596 verses come from LatinISE, and the words of the 1,209 verses of Numbers and
Zephaniah, which LatinISE lacks, from IntraText.

The lemmas and part-of-speech tags of LatinISE are automatic, and are not included in the
Text-Fabric data. They remain in the source file.

Both sources lack Numbers 33 to 36, and both stop Daniel at 3:23.
Psalms 146 and 147 of the Hebrew Bible are one Psalm, Psalm 146, so the Psalter has 149 Psalms.

# License and citation

LatinISE is published under the
[CC BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/).
Cite it as

```
McGillivray, Barbara, 2026, LatinISE corpus (version 6) (2026-04-29), LINDAT/CLARIAH-CZ digital
library at the Institute of Formal and Applied Linguistics (ÚFAL),
http://hdl.handle.net/11372/LRT-6140.
```

The IntraText Digital Library is published by EuloTech SRL under the
[CC BY-NC-SA 3.0 license](https://creativecommons.org/licenses/by-nc-sa/3.0/),
with the attribution

```
The IntraText Digital Library - www.intratext.com
```

The text of LatinISE is the text of IntraText, so the NonCommercial condition of IntraText
applies to both. CC BY-NC-SA 3.0 allows adaptations under a later version of the license with
the same elements.

The files in [source](../source) are the files as downloaded, without modification, apart from
the extraction of the Vulgate documents from `latin14.txt`.

The Text-Fabric data in [tf](../tf) is a modified form of these files:

*   the words of LatinISE are grouped into the verses of IntraText, with the verse numbers of
    IntraText, corrected where IntraText misprints them or splits a verse;
*   where LatinISE lacks a book, the words are those of IntraText;
*   Tobit, Judith, Wisdom, Sirach, the books of Maccabees, and the New Testament are left out;
*   books are named as in the BHSA, in Latin in `book` and in English in `book@en`;
*   the lemmas and part-of-speech tags of LatinISE are left out.

The [transcription](transcription.md) describes the conversion in full.

The source files and the Text-Fabric data are licensed under the
[CC BY-NC-SA 4.0 license](https://creativecommons.org/licenses/by-nc-sa/4.0/),
see [LICENSE](../LICENSE). They are provided as is, without warranties of any kind,
as stated in Section 5 of the license. You may not use them for commercial purposes.
