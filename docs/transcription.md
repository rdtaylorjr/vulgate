# Feature documentation

Here you find a description of the transcription of the Hebrew Bible of the Vulgate,
the
[Text-Fabric model](https://annotation.github.io/text-fabric/tf/about/datamodel.html)
in general, and the node types and features of the Vulgate corpus in particular.

See also

*   [about](about.md) for the provenance of the data;
*   [TF docs](https://annotation.github.io/text-fabric/tf) for documentation on Text-Fabric.

## Transcription

The sources are the Vulgate of LatinISE, version 6, and the Vulgate of the IntraText Digital
Library, `LAT0001`. The dataset holds the books of the Hebrew Bible. Tobit, Judith, Wisdom,
Sirach, the books of Maccabees, and the New Testament are left out.

LatinISE gives one token per line, with its lemma and part-of-speech tag, in documents per
book, sections per chapter, and paragraphs. A paragraph of LatinISE is a paragraph of
IntraText. A `<g/>` between two tokens means that no space separates them.

IntraText gives one page per chapter. A verse is a paragraph that starts with its verse
number. A paragraph without a number continues the verse before it, as in the poetic books,
where a verse is set in lines. A paragraph that holds only a number and a full stop is the
heading of the chapter, and is left out.

Every chapter of these books in the table of contents of IntraText becomes a [*chapter*](#node-type-chapter),
and every verse of its page a [*verse*](#node-type-verse), with the verse number of IntraText.

Where LatinISE has as many paragraphs in a chapter as IntraText, the words of every verse
are the tokens of the LatinISE paragraphs of that verse, and `source` is `latinise`.
This holds for 21,596 verses.

Elsewhere the words of a verse are the words of IntraText, split on spaces, and `source` is
`intratext`. This holds for the 1,209 verses of Numbers and Zephaniah, which LatinISE lacks.

The tokens of LatinISE are lowercase, apart from names, and without punctuation.
Joshua 21:36, which the edition omits, is `[`, `;`, `]` in LatinISE, written `[;]`.
A word of IntraText is the stretch of text between two spaces. LatinISE sometimes splits what
IntraText writes as one word, as in `se cum` for `secum`.

The trailer of a word is a space, or empty where LatinISE has a `<g/>` after it.
A `<g/>` at the start of a paragraph is left out: this happens once, in Joshua 21.

The verse numbers are those of IntraText, with two corrections.

A verse number that is lower than the number before it, and ends in the digit of the next
number, has a misprinted tens digit, and is replaced by the next number. IntraText has such
numbers in 11 chapters, mostly 10 to 19 for 30 to 39:

chapter | numbers of IntraText
--- | ---
Genesis 49 | 31, 12
Leviticus 22 | 29, 10 to 13
Leviticus 25 | 30, 11 to 19, 40
Numbers 3 | 36, 17 to 19, 40
1 Chronicles 1 | 29, 10 to 15, 36, 17, 38
2 Chronicles 32 | 32, 13
Nehemiah 11 | 34, 15, 16
Psalms 36 | 29, 10 to 19, 40
Psalms 77 | 29, 10 to 16, 37
Jeremiah 51 | 36, 17 to 19, 40
Ezekiel 34 | 29, 10, 11

In Joshua 19, IntraText gives verse 3 as the paragraphs `et Asersual` and `Bala et Asem`,
and verse 19 as `et Afaraim` and `Seon et Anaarath`, each with a number of its own, so that it
counts 53 verses up to its second verse 22. The two paragraphs of each verse form one verse,
and the 51 verses of the chapter are numbered in order. This division is that of the Vulgate at
[vulgate.org](https://vulgate.org/ot/joshua_19.htm).

Nehemiah 7 has no verse 68, which the Vulgate omits.

Psalm 115 starts at verse 10, after the Greek numbering, where Psalm 114 holds verses 1 to 9.

Book names are those of the BHSA.

## Text-Fabric model

The Text-Fabric model views the text as a series of atomic units, called
*slots*. In this corpus [*words*](#node-type-word) are the slots.

On top of that, more complex textual objects can be represented as *nodes*. In
this corpus we have node types for:

[*word*](#node-type-word),
[*verse*](#node-type-verse),
[*chapter*](#node-type-chapter),
[*book*](#node-type-book).

The type of every node is given by the feature
[*`otype`*](https://annotation.github.io/text-fabric/tf/cheatsheet.html#f-node-features).
Every node is linked to a subset of slots by
[*`oslots`*](https://annotation.github.io/text-fabric/tf/cheatsheet.html#special-edge-feature-oslots).

Nodes can be annotated with features.
See the table below.

Text-Fabric supports up to three customisable section levels.
In this corpus we use
[*book*](#node-type-book), [*chapter*](#node-type-chapter), and [*verse*](#node-type-verse).

# Reference table of features

*(Keep this under your pillow)*

## *absent*

When we say that a feature is *absent* for a node, we mean that the node has no value
for the feature. For example, if the feature `trailer` is absent for node `n`, then
`F.trailer.v(n)` results in the Python value `None`, not the string `'None'`.

In queries, you can test for absence by means of `#`:

```
word trailer#
```

gives all words where the feature `trailer` is absent.

See also
[search templates](https://annotation.github.io/text-fabric/tf/about/searchusage.html)
under **Value specifications**.

## Node type [*word*](#word)

A word of the text.

feature | values | description
------- | ------ | ------
*`word`* | `in` `principio` `Dominus` | the text of a word
*`trailer`* | ` ` | after-word material until the next word, empty where no space follows

## Node type [*verse*](#verse)

Section level 3.

feature | values | description
------- | ------ | ------
*`verse`* | `1` `2` | verse number of IntraText
*`source`* | `latinise` `intratext` | source of the words of the verse

## Node type [*chapter*](#chapter)

Section level 2.

feature | values | description
------- | ------ | ------
*`chapter`* | `1` `2` | chapter number

## Node type [*book*](#book)

Section level 1.

feature | values | description
------- | ------ | ------
*`book`* | `Genesis` `Samuel_II` `Psalmi` `Jesaia` | book name in Latin, as in the BHSA
*`book@en`* | `Genesis` `2_Samuel` `Psalms` `Isaiah` | book name in English, as in the BHSA

# Text formats

The following text formats are defined (you can also list them with `T.formats`).

format | description
--- | ---
`text-orig-full`     | the text of all words, each followed by its trailer
