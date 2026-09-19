---
title: Unvibecodable
date: September 19, 2026
author: datavorous
---

The advent of capable coding agents has resulted in the research side of software engineering taking the front seat. Knowing _what_ you want at the end, and _how to search_ to get there are both important, and especially the latter as it allows one to untangle complex systems and hill-climb problem spaces, or we end up operating inside black boxes of ever-local-optima.

Agents lack the ability to challenge their own representations and assumptions reliably. A human has to discover the right representation and objective in order to come out of the doomloops of failures. Anything that provides an opportunity where human judgment plays a bigger role is what we decided to call _unvibecodeable_.

Side projects should increasingly be like research artifacts, that’s perhaps the only way to sustain our relevance as human programmers.

This is an attempt to bring together problems which would require substantial research effort.

But how do we look for them in a structured manner? I came up with a technique last night while staring at the stars. <span class="markline">Take one noun, then attach a lot of verbs to it</span>. Figure out what can be done to make it sound _absurd_. Based on that, we will deal with `{noun, verbs, absurdity factor}` tuples from now onward.

Additionally, in order to make sure we don’t drift away to a wonderland. We will try to find at least one established artifact which was made in an attempt to tackle one particular case. Let’s see a few examples.

<aside class="problem-tuple">
<h3>Example #1</h3>
<dl>
<div><dt>object</dt><dd>file</dd></div>
<div><dt>moves</dt><dd>read, write, compress, search</dd></div>
<div><dt>pressure</dt><dd>100gb of garbage values</dd></div>
</dl>
</aside>

This is probably the best starting noun because it begins as `read()` and can then become a hellhole of external memory algorithms, compression, synchronization and storage engines.

<ol type="1" class="export-list" start="1">
<li>Read as fast as physically possible without blowing RAM. One may look into page cache, mmap, async io, prefetching etc, and after that:
<ol type="a" class="export-list" start="1">
<li>Can you randomly read 1M locations/s? Look into <a href="https://github.com/samtools/samtools">samtools</a> and <a href="https://github.com/mdshw5/pyfaidx">pyfaidx</a>.</li>
</ol>
<ol type="a" class="export-list" start="2">
<li>Can you read 1% of the file without touching the rest? Look into Tabix + BGZF <a href="https://www.htslib.org/doc/tabix.html">here</a>. <a href="https://portal.hdfgroup.org/documentation/hdf5/latest/hdf5_chunking.html">HDF5</a> is another such tool to look into.</li>
</ol>
<ol type="a" class="export-list" start="3">
<li>Can you make an access pattern identifier and swap strategies midrun? <code>ripgrep</code> already does a simpler version where it switches between memory mapped search and buffered incremental reading depending on what it is searching.</li>
</ol>
<p>Training big ML models requires a massive amount of data, it’s very evident that we have got tools to <a href="https://github.com/mosaicml/streaming">stream</a> as we wait, to <a href="https://github.com/webdataset/webdataset">shard</a>, and to <a href="https://docs.nvidia.com/deeplearning/dali/user-guide/docs/index.html">go async</a>. All are prospective rabbit holes for the curious.</p>
</li>
</ol>
<ol type="1" class="export-list" start="2">
<li>(Re)write 1 million random 4KB regions without rewriting the file. <a href="https://rsync.samba.org/tech_report/">rsync</a> was the first thing that came into my mind while writing this.</li>
</ol>
<ol type="1" class="export-list" start="3">
<li>Compress the file before it finishes loading. Look into coding theory, parallelism. I came across <a href="https://code-dev.fb.com/2018/12/19/core-infra/zstandard/">Zstandard</a> while researching about it.</li>
</ol>
<ol type="1" class="export-list" start="4">
<li>Search for an arbitrary 32 byte sequence anywhere inside the file. Very <code>ripgrep</code> and <a href="https://github.com/BurntSushi/memchr"><code>memchr</code></a> coded indeed.</li>
</ol>

Similarly you can go on to explore chunk, hash, search, sort, dedup, sync etc.

<aside class="problem-tuple">
<h3>Example #2</h3>
<dl>
<div><dt>object</dt><dd>coordinates</dd></div>
<div><dt>moves</dt><dd>index, encode, tile</dd></div>
<div><dt>pressure</dt><dd>ten billion (x, y) on your laptop</dd></div>
</dl>
</aside>

This one bridges geometry, indexing, bit manipulation and distributed partitioning, and is definitely one of my favorites.

<ol type="1" class="export-list" start="1">
<li>indexing to answer "what points are near (x, y)?" without scanning all the coordinates. Google has <a href="https://s2geometry.io/">S2 Geometry</a> as a prospective answer to that question.</li>
</ol>
<ol type="1" class="export-list" start="2">
<li>encode (lat, long) into an integer where the hierarchy remains useful. <a href="https://www.uber.com/us/en/blog/h3/">Uber built H3</a> to do something similar. Imagine encoding information in a 64 bit integer while preserving representation. This technique is usually implemented while building chess engines as well.</li>
</ol>
<ol type="1" class="export-list" start="3">
<li>tile a planet scale coordinate dataset to render on a weak phone.</li>
</ol>

This is a beautiful problem space, one can aggregate, query, move, rank, route and it'd still be a cascade of rabbit holes. Almost everything tries to answer these major questions:

<ol type="1" class="export-list" start="1">
<li>how do I represent space?</li>
</ol>
<ol type="1" class="export-list" start="2">
<li>how do I analyze activity in space?</li>
</ol>
<ol type="1" class="export-list" start="3">
<li>how do I serve enormous space interactively?</li>
</ol>

and then there's matching/routing on top.

<aside class="problem-tuple">
<h3>Example #3</h3>
<dl>
<div><dt>object</dt><dd>vector</dd></div>
<div><dt>moves</dt><dd>retrieve, compress, truncate</dd></div>
<div><dt>pressure</dt><dd>tradeoffs{billions in number, memory is expensive, updates cannot stop, accuracy cannot collapse}</dd></div>
</dl>
</aside>

1. retrieve 10 music playlists out of a few million in a few milliseconds. Spotify built [Voyager](https://engineering.atspotify.com/2023/10/introducing-voyager-spotifys-new-nearest-neighbor-search-library) to solve a bunch of problems which requires playing around with embedding vectors.

2. compress radically the memory consumption without losing accuracy. Google’s [TurboQuant](https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/) tried to tackle the same problem. Quantization is a vast field.

3. truncate so that you don't need to compare all the floating-point numbers in a vector. It turns out you can take a 4096 dimensional vector, chop off everything except the first 256 dimensions, and retain much of its meaning. But how do you do it reliably? Exa has [some answers](https://exa.ai/blog/building-web-scale-vector-db) to that using Matryoshka embeddings.

Weaviate, Pinecone, turbopuffer etc are playing with vectors to experiment with different verbs. Filter, update, synchronize are some of them from the top of my head.

Spotify itself is a forest of diverse ideas. Despite the foundational concepts being the same, **Blends** must have been modeled differently than **For You** or **Weekly**, which are totally different from a simple **Search**. Unrelated, but the [engineering behind Spotify Wrapped](https://engineering.atspotify.com/2026/3/inside-the-archive-2025-wrapped) is a heck of an interesting read.

I believe that with the same ritual, one can definitely pump out a massive problem space consisting of events, strings, keys, tasks, (API) calls, graphs, logs, transactions, packets, timestamps, and whatnot.

A few ordinary parts of speech, when chained together, can help to generate an endless number of hard projects. That's the whole charm of it!

---

Time for some calibration amongst all the fearmongering. It’s best to figure out what actually is sought after first, because no one wants to be obsolete. Speaking of which Exa has some great project ideas in their [career](https://exa.ai/careers) page:

1. Recreate Google level keyword search over 10 billion pages in 1 month

2. Build a custom vector database that runs over a billion vectors in under 100ms

3. Build a SOTA crawling system that works optimally for any website

4. Build a distributed crawler that can handle 100M+ pages per day

5. Design a lakehouse architecture that handles 100+ PB of web crawl data

6. Build streaming pipelines that process billions of documents per day for real time indexing

7. Scale infrastructure to process the whole web on GPUs cost efficiently

8. Design an eval system to answer: "how do we know we're actually advancing search quality?"

9. Build scalable eval pipelines tracking regressions, drift, and quality signals across billions of documents

10. Write a manifesto of what "perfect search" means

As absurd as all of these sound, people do end up pulling them off. Take [a look](https://blog.wilsonl.in/search-engine/)! I do not think a course or book can effectively hand a manual over to anyone, as these tasks require a substantial amount of literature review, analyzing existing work, and whether things can be plugged in together or not. How one acquires the abstract components to efficiently reason and think about the whole system is left upon the reader to decide. Some of us like to go top to bottom, some of us like the other way around.

If you are dealing with analysis paralysis, start stealing ideas from the public repos of startups and bigger orgs. I spent the most painful week of my life trying to understand ONE file from Redis’ codebase — but I did learn a lot that time. Maybe take a look into what Meta has got for us? Or heck, [Prime Intellect](https://github.com/PrimeIntellect-ai)? I sincerely hope reading, forking and modifying scoped sections are still a valid way to get one’s hands dirty.

Now, some of us chronically online on X, various forums, obscure discord servers, and ideas just come to us. I saw a post about [building faster query plans](https://rohanbansal.com/qorl?v=3) & another about [painting flowers using p5.js](https://huggingface.co/blog/train-to-paint-with-code) on X a few days back, and I was hit with ideas instantly. Knowing a lot of terms and how to poke a system to expose its hidden regions is perhaps the best superpower out there. Everyone should use it! I see the 'compacting...' word pop up on Codex, and I wonder how can one shrink the context passed to the LLM by a huge factor without losing the critical bits of information? That’s obviously a tough question to answer!

So if you are a newcomer who recently learned to make an API call to Gemini API, and are happy about your little LM conversation tool, well don’t. If your project is like a pokemon, keep on evolving it to make it _research_-rich, not just _feature-rich_. You can add 3 providers, build a nice little frontend, prompt it to be your shiny new portfolio project, but at the end of the day, 50k people probably did the same last weekend, and the week before. Here take an example, you have your little python script sending POST/GET requests to and fro, now figure out how to make it call itself from inside. Yes, those are called [RLMs](https://www.youtube.com/watch?v=nxaVvvrezbY). Then figure out how to call a million of them on your machine. Congratulations, you just went from being a wrapper to exploring ten rabbit holes related to harness, context, concurrency, and ingestion pipelines. No, adding a new shiny system prompt won’t reliably make your AI wrapper projects look cutting edge. Stare at the rollouts, and try to establish a behavioral pattern which is emerging (read [this](https://arxiv.org/pdf/2609.02371) paper), run ablations, find out possible reasons governing the behavior. Build your own evals, verifiers, graders, if you want to scale up and validate if anything you did is causing the model behavior to drift away or not. Seems convincing? What if you change the type of work you were trying to solve? What if they take a _long_ time? Long horizon tasks? How will you verify if the model is working towards the right thing? No, slapping in an AI API over a trivial pretty cute front-end won’t make you special. RAGs aren’t the end of the world, what if I have a book on fiction and another on math? How will you route to have better indexing and chunking strategy? How? I am baffled by the lack of ingenuity and creativity in people, when probing into a system and dialing the stakes higher can themselves be the source of countless questions and research directions.

Oh, you like to open() files in Python? Oh, what — now you want to learn about ML engineering? Fine, here’s a 100 GB CSV file, figure out a way to train your little whimsy classifier model as fast as possible while streaming the file at light speed. Spend enough time to rip your hair out and then tell me who can call your projects lame. I sure won’t, nor will any of my friends who are called out as _cracked_. Good luck.

Wait, this will be the last paragraph. I know Python and HTML, you know Python and HTML. What can we do with it? How do I figure out a way to check if a tag has been closed or not? That is the most common obstacle one used to face while they learnt HTML. Then, how can I devise a way to convert my normal text into HTML where I just mention the style I want before every paragraph. Wait, how about I build an HTML renderer myself? How about I build something which will filter out any HTML file into text files? Can I store the common portions of various HTML files, so that I won’t need to fetch all of that again and again? What if _ ? What can happen if I _ ?

You see?

As demoralizing as it sounds, working on hard problems that people are already working on lets one see through things that others miss, and therefore opens doors to unexplored territory. That’s what I have been told to do, and observed firsthand.

---

This document was written over a period of a few days, and the abrupt change in writing style is a reflection of that. Focus on what matters, cheers!
