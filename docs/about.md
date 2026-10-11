# About the Vulgate

The source of this dataset is the electronic text of the Stuttgart Vulgate,
*Biblia Sacra iuxta Vulgatam Versionem*, edited by Robert Weber, as encoded at Tübingen
under the direction of Wilhelm Ott. The Oxford Text Archive distributes it as item 0319,
[Vulgate](http://hdl.handle.net/20.500.14106/0319), in the file `biblelat-0319.txt`.

The catalogue of the Oxford Text Archive gives Wilhelm Ott as contributor, Stuttgart as place,
and 1976 as date of issue. R. A. Kraft describes the text as the Beuron/Stuttgart edition
"as encoded under the direction of Wilhelm Ott at Tuebingen"
([InterNet Bible Texts: Vulgate, 1998](https://sacredbible.org/guide-vulgate.htm)).

The text contains the whole edition: the Old Testament with both Psalters, the Psalter
iuxta Septuaginta (Gallican) and the Psalter iuxta Hebraeos, the New Testament, and the
appendix (Prayer of Manasseh, III and IV Esdras, Psalm 151, the Epistle to the Laodiceans).
It contains the critical apparatus of the edition, and the asterisks, obeli, and metobeli
of the Gallican Psalter and of the Greek parts of Esther and Daniel.

# Corpus

The [source](../source) directory contains the file `biblelat-0319.txt` as downloaded from the
Oxford Text Archive, without modification, and `latin-nt.xml` of the
[PROIEL treebank](https://github.com/proiel/proiel-treebank) (Dag Haug and Marius Jøhndal,
University of Oslo, export of 7 April 2018), whose morphology the New Testament words carry.

These files have been converted into Text-Fabric format by
[tfFromOta.py](../programs/tfFromOta.py).
We have a [specification](transcription.md) of how we model the text in Text-Fabric.
The conversion result is available in the [tf](../tf) directory.

The dataset has 80 books, 1,514 chapters, 39,791 verses, 99,975 stichoi, and 666,884 words,
with 38,930 entries of the critical apparatus: 661,318 written words, with 5,566 clitics
divided from their hosts. *-que* divides and *-ne* and *-ve* do not, unless the treebank or
[clitics.yaml](../yaml/clitics.yaml) says otherwise.

The conversion corrects two defects of the source, declared in
[fixes.yaml](../yaml/fixes.yaml): two stray copies of Isaiah 25:10 after Isaiah 26:8, and a
broken reference of IV Esdras 7:91.

The decoding of the encoding has been checked against the printed edition (fourth edition,
1994). The text, the verse division, the signs of the Gallican Psalter, and the sigla of the
apparatus agree with the print, apart from the corrections made in later editions.

# License and citation

The Oxford Text Archive distributes the text with the statement

```
Distributed by the University of Oxford under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
```

The Text-Fabric data in [tf](../tf) is a modified form of this file:

*   the encoding is decoded into words, signs, and apparatus entries, as described in the
    [transcription](transcription.md),
*   the two defects listed above are corrected,
*   a written word with a clitic is divided,
*   the New Testament words carry the morphology of the PROIEL treebank, itself CC BY-NC-SA 4.0.

CC BY-NC-SA 3.0 allows adaptations under a later version of the license with the same
license elements. The source file and the Text-Fabric data are licensed under the
[CC BY-NC-SA 4.0 license](https://creativecommons.org/licenses/by-nc-sa/4.0/),
see [LICENSE](../LICENSE). They are provided as is, without warranties of any kind,
as stated in Section 5 of the license. You may not use them for commercial purposes.
