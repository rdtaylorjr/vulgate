# Feature documentation

Here you find a description of the transcription of the Vulgate,
the
[Text-Fabric model](https://annotation.github.io/text-fabric/tf/about/datamodel.html)
in general, and the node types and features of the Vulgate corpus in particular.

See also

*   [about](about.md) for the provenance of the data,
*   [TF docs](https://annotation.github.io/text-fabric/tf) for documentation on Text-Fabric.

## Transcription

The source file has one line per stichos of the edition, the text printed *per cola et
commata*. A line holds the text of the stichos with the apparatus entries that belong to it,
a `|`, the book, chapter, and verse, and a line number. A line that does not fit ends in `\`
and continues on the next line. Lines of `P` and `0` separate the books.

The text is in capitals, and the encoding marks by codes what the print shows otherwise.
The meaning of every code below has been checked against the printed edition.

### Text

code | meaning | example
--- | --- | ---
`<` ... `>` | shift: letters in between are capitals, `;` is `:` | `<D>EUS` Deus
`<n>`, ` n ` | verse `n` starts inside the line | `ESCAM <30> ET` escam ³⁰et
`=` | obelus ÷, before a word | `=NON SIC<;>` ÷non sic:
`*` | asteriscus ※, before a word | `*GRANDO` ※grando
`<;>` | metobelus `:`, after a word | `SIC<;>` sic:
`!O` | Greek ω | `<A> ET <!O>` A et ω
`<>` | an empty shift, nothing | 

The obelus stands before every stichos of an obelized passage and the metobelus after its
last word, as in the print.

### Apparatus

An entry of the apparatus is enclosed in `(` ... `)` after the word it belongs to.
An entry before the first word of a line belongs to that word.

code | meaning | example | printed
--- | --- | --- | ---
`@` ... `'` | italic: sigla and editorial words | `@<A>'` | A
`!` + letter, shifted | Greek siglum | `<!S>`, `<!L>`, `<!F>`, `<!T>`, `<!O>` | Σ Λ Φ Θ Ω
`!` + letter, not shifted | Gothic siglum of an edition | `!C`, `!R`, `!O`, `!B`, `!H`, `!S`, `!V`, `!D`, `!W` | 𝔠 𝔯 𝔬 𝔟 𝔥 𝔰 𝔳 𝔡 𝔴
`*` after a siglum | first hand | `@<A*>'` | A*
`"` after a siglum | second hand | `@<A">'` | A2
`;` in italic | between readings | `FERENTEM @<TM'!F>@;' FACIENTEM !C` | `ferentem T M Φ; facientem 𝔠`
`.` after sigla | no further manuscript in the big editions | `@<O>'.` | O.
`+` | addition | `+ ERANT @<A>'!C` | + erant A 𝔠
`%` | omission of one word | `% % @<AM>'` | om. om. A M
`?` | transposition, words by their initials | `? L. M. @<C>'!C` | ~ l. m. C 𝔠
`-` + letters | other ending of the word | `-IS @<T'!F>!C` | -is T Φ 𝔠
first reading empty | witnesses of the text | `@<GAO>'!R!B@;' <A>DAE @CET'.` | `G A O 𝔯 𝔟; Adae cet.`
`[` ... `]` | variant inside a reading | `+ CUM [EIUS @<A>'] @<A'!L>!C` | + cum (eius A) A Λ 𝔠
`-MG`, `-TXT` | margin, text of a manuscript | `@<S>-MG'.` | S (marg.)

Lower case letters in italic are sigla of fragments, one letter each, as `@<A>HM'` for
`A h m`, or editorial words: `cet.` (ceteri), `lapsu`, `partim`, `om.`, `omnes`, `vel`, `codd.`,
`supplenda`, `an`, `et sic semper`, `et sic in seqq.`, `pro rege Iuda`. A capital followed by
lower case letters is a name: `Light.`, the edition of Lightfoot named in the preface for the
Epistle to the Laodiceans, and `Ver.`.

### Conversion

Every line of the source becomes a [*stichos*](#node-type-stichos) and every word a
[*word*](#node-type-word), with its book, chapter, and verse.

*   The obelus or asteriscus before a word is `prefix`, the metobelus after a word is part of
    `trailer`.
*   The apparatus entries after a word are `apparatus`, entries before the first word of a
    stichos are `apparatus_before`, each decoded into the notation of the print in the
    tables above, several entries separated by ` | `.
*   A line with apparatus entries and no words, a line added by some witnesses, gives its
    entries to the last word before it in the same book, and at the start of a book to the
    first word. Such a line with an obelus gives the obelus to the text it adds:
    `+ ÷et perfice subsequentes te C Σ Λ` (Daniel 3:40).
*   Books without chapters are chapter 1.

### Books

The name of a book is its code in the references of the source, decoded as the text: `<G>N`
is `Gn`, `1<S>M` is `1Sm`, `<P>S<G>` (the Psalter iuxta Septuaginta) is `PsG`, and `<P>S<H>`
(the Psalter iuxta Hebraeos) is `PsH`. The source gives the prologue of Sirach as a separate
book, `<S>IR<P>`, so it is the book `SirP`.

### Corrections

The conversion applies the corrections declared in [fixes.yaml](../yaml/fixes.yaml), each
with its line number, the text found, the text put in its place, and the reason:

*   lines 65979 and 65980: two copies of Isaiah 25:10 after Isaiah 26:8, removed (the print
    has Isaiah 25:10 in its place only),
*   lines 113261 and 113262: IV Esdras 7:91 lacks its continuation mark, and its reference is
    coded as sigla.

### Limits of the source

*   An ending `-is` gives only the ending: the encoding does not say how many letters of the
    word it replaces. The print gives the whole word.
*   Greek readings of the apparatus are in Latin letters, as `+ asphalos` for the printed
    `+ ασφαλως` (Mark 14:44).
*   Notes of Jerome in the text, printed in small capitals, are not distinguished, such as
    `quae habentur in Hebraeo plena fide expressi` (Esther 10:3) and `hucusque non habetur in
    Hebraeo` (Daniel 3:90). The titles of the Psalms, also printed in small capitals, are not
    distinguished either.
*   The text is that of the edition before 1994: for example Zacharias 13:9 has `eas`, which
    the fourth edition corrects to `eos`.

## Text-Fabric model

The Text-Fabric model views the text as a series of atomic units, called
*slots*. In this corpus [*words*](#node-type-word) are the slots.

On top of that, more complex textual objects can be represented as *nodes*. In
this corpus we have node types for:

[*word*](#node-type-word),
[*lex*](#node-type-lex),
[*stichos*](#node-type-stichos),
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

A stichos can start in one verse and end in the next, so stichoi and verses do not nest.

# Reference table of features

*(Keep this under your pillow)*

## *absent*

When we say that a feature is *absent* for a node, we mean that the node has no value
for the feature. For example, if the feature `prefix` is absent for node `n`, then
`F.prefix.v(n)` results in the Python value `None`, not the string `'None'`.

In queries, you can test for absence by means of `#`:

```
word prefix#
```

gives all words where the feature `prefix` is absent.

See also
[search templates](https://annotation.github.io/text-fabric/tf/about/searchusage.html)
under **Value specifications**.

## Node type [*word*](#word)

A word of the text, or a clitic divided from its host.

feature | values | description
------- | ------ | ------
*`word`* | `in` `principio` `Deus` `que` `ω` | the text of a word
*`prefix`* | `÷` `※` | sign printed before the word: ÷ obelus, ※ asteriscus
*`trailer`* | ` ` `: ` `` | material after the word until the next word: a space, or the metobelus and a space, nothing before a clitic
*`apparatus`* | `+ erant A 𝔠` | entries of the critical apparatus that follow the word, separated by ` \| `
*`apparatus_before`* | `+ et 𝔠` | entries of the critical apparatus that stand before the first word of a stichos
*`language`* | `Latin` | language of the word
*`languageISO`* | `lat` | language of the word in ISO 639 code
*`freq_occ`* | `52652` `1` | number of occurrences of the form
*`rank_occ`* | `0` `3` | number of forms with a higher frequency
*`lex`* | `dico[` `terra/` `et` `ut=` | lexeme of the PROIEL lemma: `[` after verbs, `/` after nouns and adjectives, `=` per homograph
*`sp`* | `subs` `nmpr` `verb` `adjv` `advb` `prep` `conj` `prps` `prde` `prin` `pron` `intj` `nega` `inrg` | part of speech of the lexeme
*`pdp`* | as `sp` | part of speech of the occurrence
*`ls`* | `card` `ordn` `poss` `indf` `rela` `refl` `recp` `ccrd` `csub` `none` | lexical set of the lexeme
*`ps`* | `p1` `p2` `p3` `NA` `unknown` | person
*`nu`* | `sg` `pl` `NA` `unknown` | number
*`gn`* | `m` `f` `n` `NA` `unknown` | gender
*`case`* | `nominative` `genitive` `dative` `accusative` `ablative` `vocative` `locative` `NA` `unknown` | case
*`tense`* | `present` `imperfect` `future` `perfect` `pluperfect` `futureperfect` `NA` `unknown` | tense
*`mood`* | `indicative` `subjunctive` `imperative` `infinitive` `participle` `gerund` `gerundive` `supine` `NA` `unknown` | mood
*`voice`* | `active` `passive` `NA` `unknown` | voice
*`degree`* | `comparative` `superlative` `NA` `unknown` | degree
*`freq_lex`* | `6153` `1` | number of occurrences of the lexeme
*`rank_lex`* | `0` `3` | number of lexemes with a higher frequency

## Node type [*lex*](#lex)

A lexeme, spanning its words. It has `lex`, `sp`, `ls`, `language`, `languageISO`, `freq_lex` and `rank_lex`.

## Node type [*stichos*](#stichos)

A line of the edition, printed *per cola et commata*. It has no features.

## Node type [*verse*](#verse)

Section level 3.

feature | values | description
------- | ------ | ------
*`verse`* | `1` `2` | verse number

## Node type [*chapter*](#chapter)

Section level 2.

feature | values | description
------- | ------ | ------
*`chapter`* | `1` `2` | chapter number, 1 for books without chapters

## Node type [*book*](#book)

Section level 1.

feature | values | description
------- | ------ | ------
*`book`* | `Gn` `PsH` `SirP` `Mt` | book name as the source gives it

# Text formats

The following text formats are defined (you can also list them with `T.formats`).

format | description
--- | ---
`text-orig-full`     | the text of all words with their signs, each followed by its trailer
`lex-orig-full`      | the lexemes of all words
