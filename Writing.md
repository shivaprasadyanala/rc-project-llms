Scientific work must allow for a falsification of the presented solutions, i.e. the reader must be able to repeat and implement all solutions to be able to prove the approach of a paper wrong. (There are alternative, e.g.\ Bayesian, formulations to epistemology, but these amount to the same consequences for us.) Hence all details should be given (completeness, but feel free to cite) and the paper must be understandable. It is the responsibility of the author to be easily understood (do not complain, that a reviewer did not understand your paper: write better papers instead).

1. Priority: try to be understood. (This really important!)
 - Most of what follows should address this points
 - Always remember: the reader did not work weeks/months/years on the project, so explain everything necessary (that is not in the existing literature, of course you can cite)

2. Priority: be short, try to include all the content in few pages.
 - You should write a short background and other additional information. But this is not the purpose of your work. Big machine learning models (ChatGPT and successors) could write that part.
 - Make an effort to point out the most relevant parts clearly, and remove the irrelevant parts. This might involve several steps of editing your text down. 

3. Verify all claims that are made
 - empirically
 - cite literature
 - math proof
 
4. Explain what is going on
 - theoretical reasons
 - find weeknesses
 - explain weeknesses
 - try (and if possible succeed) to fix weeknesses
 - make ablation studies
 - also make ablation studies for all fixes of weaknesses
 - focus on the results, not necessarily explain everything you did
 - structure the explanations in stories, which summarize the facts.
 - Tell a story about the facts
 
5. When in doubt, write and act similar to the (current) papers in highly ranked venues. (You are reading papers, are you?)

Often (at least for empirical work) structure a text in IMRD:
(Often: Abstract, Summary)
 - Introduction (hard, see below)
 - (Sometimes in PhD theses a list of all publications of the author with a relation to the thesis are listed. Sometimes unstructured as part of the introduction, sometimes structured after the introduction, and sometimes as extra (sub)section.)
 - (Sometimes: State of the art
   The state of the art section should identify structures in the state of the art.  I.e.  it should not only be a listing of several previous publications. Instead structures in the state of the art such as classes of similar research solutions, important research groups or important trends should be described. Referenced publications should come from A-conferences or good journals and enough of them should not be older than 3-4 year. (Main exceptions are seminal works, i.e. publications which are the top publications in a specific field.) 
   Specific Information for Theses:  Normally, the state of the art becomes a chapter of a "Background" or "Fundamentals" part. This part might also comprise a chapter "Theoretical Foundations" which defines notions, notations, terms, mathematical basics etc.)
 - Methods
   - What have you done? (Better: how can one reproduce your steps; I do not need to know about the bugs you did and what you did in which order and how you fixed them; just tell me how to make it work)
   - Which theory did you use?
   - State formal algorithms or mathematical methods. 
     - All steps of algorithms or solution methods must also be explained textually.
   - Which software/data/experiments
   - No interpretation, just facts you could have been given, before doing the actual work
   - (if not in the introduction:) give an overview about the state of the art
   - Only a short description of everything that was known beforehand (but include references), but a detailed description of your changes (because there are no references).
     - A compromise between a clear, formalized presentation and textual explanations should be found.
   - Often figures help to convey the main solution idea. Invest a lot of time in Figures!
     - They should be mostly self explanatory
	 - The figure caption should describe what is happening and give some first interpretation (“due to this something we conclude that something does work good/bad”, “In particular, something specific is demonstrating the superiority of something over something”, …)
	 - It is a good idea to have 1-3 summary figures about the main ideas of the thesis
   - give enough information for others to repeat the results
     - nets/training algorithm/data/data reparation/loss function (in detail!)
	 - references should contain addition information
	 - everything that is not absolutely clear should be made clear
	 - be precise 
	 - If I cannot understand (in detail!) what you did, you are in trouble.
	 - You need to understand enough of the libraries you call to give an abstract description about what is going on.
 - Results
   - Facts in Figures and tables.
   - Describe and mildly interpret the facts
     - Both theoretical (proofs of algorithms/methods, complexity analysis, analysis of correctness, etc.)...
	 - ...and empirical
   - Plots/diagrams/numbers/tables
   - Describe why you did which experiment
   - Evaluate the methods (find flaws in your own approach!)
     - Be honest!
	 - Make a statistically significant number of tests
	 - Normally solution features such as run time, memory consumption and quality criteria such as errors, F1-measure etc. are given. These criteria are normally analyzed statistically.
	 - Compared to baseline solutions, i.e.  previous solutions from other authors.
	 - Clearly say that your approach is better (if it is clearly better)
	 - Only state interpretations, that you demonstrate
   - A little interpretation of the results is ok (leave out the big picture interpretation)
   - Refer back to the research gap
   - Include problems you had to overcome in a thesis (but rarely in a paper)
 - Discussion
   - Give big picture interpretation
   - Answer the research questions in the introduction
     - Why do your methods close the gap?
   - Short abstract summary of results
   - Open questions / next steps / limitations / remaining problems / be honest (otherwise the reviewer will be)
   - Assume that the reader has read everything before.
   - State very clearly what is new (methods/results/interpretations)
Feel free to change (add/split sections) the structure, if it helps to be understood.
 - E.g. Split "Methods" into "ML-Methods" and "Application Domain"
 - E.g. Split "Methods" into "State of the Art" and "Methods"
 - E.g. Add (one or more) theory section(s) between methods and results
 - E.g. Split "Results" into several distinct result sections for several experiments
 - E.g. Split "Discussion" into "Discussion" and "Conclusion"
 - E.g. give an additioal background section

# Writing style

 - priority 1: be understood
 - priority 2: be short
   - go over the text and shorten it
   - can you say the same with fewer word?
   - do not waste the readers time
   - Use LLMs
 - be objective
 - please use English (mandatory for Master IT students) or German
 - Use short sentences (easier in English)
 - Use active instead of passive voice. (passive does not mean objective!)
   Tell me who did what instead of what was done to whom.
   Write "This thesis looks at XXX" instead of "XXX was researched".
 - I don't care to much about "I" or "we". If it is important that you did it, use "I". If we (you and the reader) are doing (e.g. understanding your text) it use "we" ("we can interpret from the data"); this is the default. If it is objective what was done, like in software experiments, than formulate objectively (but try to avoid too much passive, e.g. "With these settings, Pytorch achieved an accuracy of ..."). The objective version should be the default. (Still, try to prevent passive voice.) Hence, in practice, "I" is rarely used, but not forbidden.
 - Paragraphs (Absätze) often in 5 sentences
   - "In this paragraph we look at A, B, and C."
   - "A means ...".
   - "We can see from B ..."
   - "Now, C is ..."
   - "So in summary we have ..."
   This helps me to skip the paragraph, if I know whats in it.
 - No suspense, always tell me where you are going. And: start with the main idea, give details afterwards.
 - Summarize each chapter/section/paragraph at the beginning. Allows to skip chapter/section/paragraph, and lets the reader know where you are going.
 - Short sentences, short text, but keep all information. 
   - Remove unnecessary words
   - Remove repetition (up to some really important points)
   - Avoid "weak verbs" like "be", "have", "become"
     - often a sentence with a weak verbs can be converted to an adverb or subclause or something similar
   - Should be 1 (resp. 10) loop(s) while preprating your thesis (resp. paper)
 - Convention: do not use future tense to refer to upcoming sections of your paper. (wrong: "in section 3 we will look at" (also weak verb), better: "section 3 introduces ...")
 - Feel free to show me code or pseudocode (if it helps), but also feel free to include it in the appendix.
 - Give names to things (mathmatical objects, objects, models)
 - Do both (i) show facts and (ii) interpret them. Clearly separate them. The interpretation needs to rely on the facts. If you cannot (yet) reasonably interpret: do more experiments.
 - It is ok to write text. It is ok to write formulas. Note though: it is easier to convey ideas in text and it is easier to be precise in formulas. Since you should both convey ideas and be precise, you should use both text and formulas.
 - It is very hard in scientific writing that something "must" or "has to" or "cannot" be. Such statements need a clear justification. And note that there are often many alternatives possible. 
 - Do not tell we what you did do. Instead tell me, which challenges you had and how you overcame them.
 - Introduce abstract notation and then use it. (No need for abstract notation if it is not used. On the other hand, if you again and again describe something with words, then use abstract notation or new names.)

# Introduction
 - "write it last" vs. "write it first"
 - Structure an introduction
   - Motivation: Begin with the big picure (society has problem ...) and lose in to introduce your problem and summarize the state of the art (give citations)
     The motivation answers the question "Why ist he problem a problem?". I.e. it outlines why the content of the paper is relevant, both from an academic point of view but also from a market point of view. Normally this requires quotes and references from studies written by well-know researchers, associations, organization and politics since in most cases the author does not have the standing to make such claims. If it is possible, describe the state of the art in abstract terms. Otherwise refer to a later section about the state of the art. The state of the art shows needs to be thorough enough to show that the following research question/gap are not finally answered. For this, a sufficient number of previous recent works are referenced. A gap exists as long as the research questions or research hypotheses are not finally answered, i.e. no standardized, commonly-accepted solutions exist.
   - PRECISELY STATE YOUR PROBLEM (RESEARCH GAP / RESEARCH QUESTION) - usually in one sentence. THIS IS THE MOST IMPORTANT PART OF A PAPER!
     - You have to know enough about the state of the art to be able to precisely state what is new in your approach.
	 - You have to explain the context beforehand, such that stating the research gap is possible in a single sentence.
	 - The research gap should not be buried in a long paragraph. Attract the reader to it. Place it prominently, usually in a short paragraph and/or at the beginng of a paragraph.
	 - A research question defines a question which could be answered (at least partially) in the publication. I.e. the question "How can we use unsupervised machine learning to identify a model of the system behavior?" is not a research question since it could never be answered to a significant extent in one publication. But the question "How can we integrate a variance variable into the outpout and loss function of an VAE to express prediction uncertainty for time series?" is a research question since it could be answered in one publication. So a research questions must be detailed, precise, unambiguous, short (usually one sentence) and answerable in one publication.
	 - The author will be measured according to the research questions: relevance and completeness of the answer. A publication can be rejected if either the research questions are already answered, irrelevant or if the the answers given to the research questions are not sufficiently supported by proofs, experiments or are even wrong. Furthermore, incomplete answers are ground for rejection, if the imcompleteness is not mentioned shortly after the research gap. 
   - Contribution, part 1: Describe how you close this gap (short version of the methods)
   - Contribution, part 2: Describe the results and interpretation you are getting (short version of results and discussion)
   - The contribution might be done by a list.
   - The CONTRIBUTION MAKES PROMISES, about the content of the thesis. Make sure, that these promises are kept in the subsequent text. Make sure that all major contributions of the later text are written here.
   - At the end of the introduction, normally the paper structure is explained shortly: "section 2 introduces ..., section 3 summarizes ..." (table of contents in words)
 - cite a lot, in particular in the first half of the introduction
 - The introduction is a story, as is the whole paper. Make the story flow.
Do not assume that the reader knows the details, so please do not use formulas and only few technical phrases.
 
Format
 - (La)TeX is optimal, word might suffice for a Bachelor or Master thesis
 - Observe formal rules (like number of pages or so)
 - Use: Blocksatz / justified text / each line has the same length
 - Use a font with serifs (e.g. Times New Roman or Computer Modern)
 - Stick to black&white (only exception: figures, images)
 - Don't underline. Use bold rarely (attracts reader). Use italic (in latex: \emph, not \textit) for emphasis or definitions.
 - Never begin a sentence with a symbol or a formula or a reference or a citation or a number. Every sentence begins with a word. Bad example: "The result is 1. 2 is too big."

Equations
 - inline or a single lines: both are ok
 - inline for not so important and short equations
 - Numbered equations are optional
 - do not set words in formulas in italic, as $p_{model}$ reads like $p_{m*o*d*e*l}$, instead use $p_\text{model}$ (symbols in italic, words in normal mode)
 - names of functions (log, exp) are not italic (use: $\log$, $\exp$).
 - integals: dx has an italic x, but many people typeset the d in normal font.
 - It is often helpful to give formal names for things. Thereby, you can clearly reference it.

Algorithms
 - Have inputs, describe those
 - Have outputs, describe those, and describe which properties set them apart in connection to the inputs
 - if nontrivial: justify termination
 - justify correctness (if there is nothing to justify, you probably have not described inputs and outputs correctly)
 - Often, you should say something about complexity of the algorithms

Tables/figures/images
 - get a number
 - have a heading (table) or subtext (figures, images)
 - only include this which to refer to in the text by number (everything else -> appendix)
 - The description of tables and figures is mostly self-sufficent: I need to be able to understand them without the need of reading the text in detail.
 - if you use colors: make it still readable in black/white and for colorblind people
 - text in readable size (~main text, similar or same font as in the main text); in particular relevant if you output plots from python (and not re-do them with tikZ)
 - Tell me, what I should read from the tables or figures. What is important? What does the figure/table tell me? Summarize the conclusion of the figure/table in its caption.
 - if necessary, copy images or tables from other sources, but then I need precise references
 - Figures/images are normally defined as vector graphics or in tikz (you can export matplotlib to tikz)
 - follow all copyright regulations.
Figures help the reader to understand the problemand the solution. Well-done figure are essential for the acceptance of a publication.

Citations
 - Read a lot
 - Read more
 - Read much more
 - Cite a lot
 - citations are for two reasons:
   - give background (or use the authority)
   - give credit for people who did something before
 - Give precise references (into books), like page number or Theorem~XXX
 - blog articles only count partially (might be unreliable, never use them as authority, but they might be cited for interesting background)
 - feel free to cite older sources (if applicable), but also cite new sources.
 - if you describe (e.g.) neural networks, just give 2-3 textbooks at the beginning of a section.
 - paraphrase in a way that suits your reader
 - Citations are either part of a sentence (and are treated as a word) like "The paper [42] says ..." or follow after a statement "a does b [42]".
 - I do not care to much about the citation style, as long as it is one of the standard ones.
 - All information in the bibliography must be complete and correct. The references must look alike.
 - It is important to note that it is not a problem if previous works on the publication's topic are found. If no previous works are found, maybe the research topic is simply not relevant.

Think about different types of readers, and make sure everyone gets something from your text:
 - Your parents 
 - Yourself in 5 years (this is a documentation)
 - your work colleagues (this is a documentation)
 - Your professor (who wants to learn something new and does not want you to repeat the literature)
 - Your fellow students (who want to learn)

Some mistakes and possible minor improvement:
 - Introduce all abbreviations ("we consider artificial intelligence (AI). The AI ...") Feel free to re-introduce an abbreviation if it was not used for a long time. In case of many abbreviations use \usepackage{glossaries-extra} or similar packages.
 - Never use two symbols or formulas or references or numbers after another.
 - Often: replace "but" with "and"
 - "Appendix I"

# TeX or Word

I do not care

TeX (also consider this in Word):
 - math mode for all mathmatical symbols. Wrong: "The function f". Good: "The function $f$"
 - \cdot instead of * for products
 - TeX makes a lager space after a ".". This makes sense for full stops at the end of a setence. This does not make sense after abbreviations. Use "Fig.~\ref{}" or "Fig.\ \ref{}" instead of "Fig. \ref{}".
 - Follow precisely the formatting instructions and templates from the journals. Read some typical last papers and identify typical issues, writing styles and layouts.
 - Take care of a correct capitalization in bibtex. 

# LLMs

https://neurips.cc/Conferences/2024/CallForPapers
Use of Large Language Models (LLMs): We welcome authors to use any tool that is suitable for preparing high-quality papers and research. However, we ask authors to keep in mind two important criteria. First, we expect papers to fully describe their methodology, and any tool that is important to that methodology, including the use of LLMs, should be described also. For example, authors should mention tools (including LLMs) that were used for data processing or filtering, visualization, facilitating or running experiments, and proving theorems. It may also be advisable to describe the use of LLMs in implementing the method (if this corresponds to an important, original, or non-standard component of the approach). Second, authors are responsible for the entire content of the paper, including all text and figures, so while authors are welcome to use any tool they wish for writing the paper, they must ensure that all text is correct and original.

# Presentations

Stick to your time
Be prepared for all questions
Having slides is a good idea
Focus on all things that were important enough to be mentioned in the introduction (but give details)
formalities can be shown on slides, but usually formulas should not be explained in detail
tell a story
details are only necessary if they are relevant for the story (I can ask the details or read them in your text)
images > text
There are many conference presentations only (youtube etc.), look some of those and emulate. Good conferences: NeurIPS, ICML, ICLR, COLT, AISTATS, CVPR, UAI, AAAI, ...

