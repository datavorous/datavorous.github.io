---
title: Post training a model to explore Demoscenes
subtitle: On the grammar of demoscenes and the possibilities of unfinished code
date: October 31, 2026
description: On the grammar of demoscenes and the possibilities of unfinished code
---

<p>Lately, I have been fascinated by the world of demoscening and sizecoding and eventually I came across HellMood’s remarkable MS DOS demo <em>“</em><em><a href="https://youtu.be/Imquk_3oFf4?si=1kp2qgkB6A5yzA4o">Memories</a></em><em>”. </em>Whilst reading through his <a href="http://www.sizecoding.org/wiki/Memories">writeup</a>, I became interested in <em>how</em> the author had <em>arrived</em> at some of its visual effects. I was struggling to create any of my own, so I hoped to squeeze out a little bit of inspiration out of that.   </p>

<p class="article-figure"><a href="media/figure-01.png"><img src="media/figure-01.png" alt="Screenshot of the Memories demo"></a></p>

<p>I noticed that these effects could be traced back to earlier experiments consisting of alternative implementations and several ideas borrowed from previous demos. I began wondering how many other directions the same underlying ideas might have taken. I decided to start with a few existing demos, the simplest ones of all, and modify them character by character to observe how those changes can affect the visual feel. </p>

<p>I came across <a href="https://www.dwitter.net/random">Dwitter.net</a>, which is like Twitter but for 140 character JavaScript demos. They already supported “remix”-ing any <em>dweet</em> so that we can build on top of them. Co incidentally, the most liked Dweet on the site shared the same effect as the parallax checkerboard effect from <em>Memories</em>! </p>

<p class="article-figure"><a href="media/figure-02.png"><img src="media/figure-02.png" alt="Parallax checkerboard effect on Dwitter"></a></p>

<p>Digging a little deeper, I noticed some remixes shared substantial portions of their source code, differing by only a few characters, whilst others achieved similar visual effects through entirely different implementations. </p>

<p>Here is an example, I traced back d/36555 from d/367547 which in turn  is derived from d/36467. The gray underlined substrings show what is common across all of them. Blue shows what’s common in between the first two, and green shows for the next couple. </p>

<p class="article-figure"><a href="media/figure-03.png"><img src="media/figure-03.png" alt="Shared substrings in three related Dweets"></a></p>

<p>In linguistics, language is productive i.e. a finite vocabulary and a finite set of grammatical rules permit an <em>enormous</em> number of different expressions. Programming languages share this property too. Now let’s consider the aforementioned Dweets. They contain overlapping substrings, but their rendered results differ. Suppose you take a 140 character program, and remove its final 30 characters. Even with a hypothetical alphabet of just 64 character, there are almost 1.5 x 10^54 possible completion strings that can be formed. Almost all will be syntactically invalid or produce uninteresting results. Nevertheless, the number of possibilities is astronomical. </p>

<p>It’s not humanly possible to enumerate all of them exhaustively. and it would be foolish to to generate and test all possible strings. However, the continuations of a partial program are not equally plausible.</p>

<p>Given a partial program, certain characters and expressions are considerably more likely to follow than others. This is pretty much how autoregressive language models work. I wondered whether I could use such a model to sample plausible continuations of unfinished Dweets and visualize the different directions each program could have taken. </p>

<p>And then, I could surgically delete substrings or mix-and-match them to my own aesthetic taste. </p>

<p>I had also grown rather frustrated with my own ability to “finish” a demo after starting one, so having an autocomplete that understood the peculiar language of Dweeting rather looked like am appealing prospect to me.</p>

<p>Around the same time, I came across <a href="https://x.com/evilmathkid/status/2112509398883164162?a=roNzU625eISWnnvSnnU&amp;s=20">Mithil Vakde’s tweet</a> (you might have seen him on <a href="https://news.ycombinator.com/item?id=49519939">HackerNews</a> recently).</p>

<p class="article-figure"><a href="media/figure-04.png"><img src="media/figure-04.png" alt="Post about preferences for code art"></a></p>

<p>That gave me another excuse to experiment - could I inject <em>my</em> own aesthetic taste as a prior into my autocomplete model? That’d be really amazing. </p>

<p>I understand that no one can write a function that determines whether a demo is beautiful, but people <em>can</em> <em>express</em> their preferences by comparing examples, right? </p>

<p>With that in mind, I decided to put my GitHub Sponsors payout towards renting a GPU and post training a model of my own.</p>

<hr>

<p>The first hurdle was finding a suitable dataset. I initially experimented with generating synthetic Dweets using Claude Sonnet 5.5 but found them not at all aesthetically pleasant. Fortunately, <a href="https://github.com/lionleaf/dwitter#dwitter-api">Dwitter.net provides an API</a>, which I used to build a modest dataset of 25k Dweets to be used for training along with ~1.3k more as a validation set.</p>

<p>I used Qwen2.5-Code-7B as the base model. It struggled to complete most of the Dweets I tested it on, which was understandable given how peculiar their syntax is. Dweets make extensive use of code golfing tricks and mathematical shorthand, which are rather unusual compared with the code a general purpose coding model typically encounters. </p>

<p>I decided to try continued pretraining (CPT) on the corpus, hoping to shift the model’s probability distribution towards the pecular language of dweeting. To see whether it had worked, I measured the <em>surprisal</em> of individual tokens before and after training. Surprisal is simply the negative log probability a model assigns to a token given everything preceding it. The less likely a token is, the more surprising it is to the model. </p>

<p>In the figure below, darker red indicates greater surprisal. After CPT, much of the code becomes noticeably less surprising (particularly the unfamiliar programming idioms). </p>

<p class="article-figure"><a href="media/figure-05.png"><img src="media/figure-05.png" alt="Token surprisal before and after continued pretraining"></a></p>

<p>Across 30 held out dweets, perplexity fell from 28.63 to 8.57, which means that the model had become substantially better at predicting the structure of these tiny weird programs. </p>

<p>Although the generated programs were more consistent, they still lacked a certain “charm”. Fortunately, Dwitter has an “awesomeness” score for every Dweet. I decided to use it to construct a curriculum. </p>

<p>I ranked the top 5k dweets by their “awesomeness” scores and constructed a curriculum that gradually favoured the more appreciated programs. Initially, every dweet had an equal probability of being sampled. Over 400 training steps, I progressively increased the weight assigned to higher ranked programs, until the top 1000 accounted for roughly 67% of the sampling probability.</p>

<table><thead><tr><th>Rank bucket</th><th>Step 1</th><th>Step 100</th><th>Step 200</th><th>Step 300</th><th>Step 400</th></tr></thead><tbody><tr><td>1-1000</td><td>20.00%</td><td>35.89%</td><td>48.74%</td><td>59.01%</td><td>67.23%</td></tr><tr><td>1001-2000</td><td>20.00%</td><td>27.97%</td><td>29.60%</td><td>28.01%</td><td>24.99%</td></tr><tr><td>2001-3000</td><td>20.00%</td><td>20.03%</td><td>15.23%</td><td>10.41%</td><td>6.75%</td></tr><tr><td>3001-4000</td><td>20.00%</td><td>12.06%</td><td>5.63%</td><td>2.41%</td><td>0.99%</td></tr><tr><td>4001-5000</td><td>20.00%</td><td>4.05%</td><td>0.81%</td><td>0.16%</td><td>0.03%</td></tr></tbody></table>

<p>This turned out to be a breakthrough! The generated continuations became much more visually interesting. </p>

<p class="article-figure"><a href="media/figure-06.png"><img src="media/figure-06.png" alt="Generated Dweet continuations after curriculum training"></a></p>

<p>Interestingly, the improvements in token likelihood extended even to Dweets that had never been sampled during curriculum training. Perplexity fell from 7.42 to 5.65, although the gains were spread fairly evenly across awesomeness ranks.</p>

<p class="article-figure"><a href="media/figure-07.png"><img src="media/figure-07.png" alt="Token likelihood gains across awesomeness ranks"></a></p>

<p>Across 7000 Dweets, curriculum training improved token likelihood across all awesomeness ranks, including programs never sampled during training. The gains were particularly pronounced for programs the original model found difficult.</p>

<p>I now had a model that could produce rather beautiful continuations. I wondered whether I could take this further by incorporating my own aesthetic preferences.</p>

<p>In mid-September, I came across Surya’s article on <a href="https://surya.website/rling-qwen-to-paint-with-code">Training AI to Paint with Code</a>, where they had used RL to produce watercolor paintings using p5js. They experimented with different reward functions before settling on pairwise comparsions against a collection of hand rated paintings. I remembered that idea and thought of trying sometihng similar with Demoscener (it doesn’t feel alright to call it “the model” repeatedly). </p>

<p>I opted to do RLHF using GRPO, with myself acting as the reward function. </p>

<p>For each unfinished Dweet, I sampled a group of eight completions, rendered them side by side and selected the one I found most aesthetically pleasing. If none appealed to me, I skipped the group. I used these preferences to update Demoscener’s policy, then sampled fresh continuations and repeated the process over roughly 9–10 rounds of 500 groups each. Altogether, I manually inspected around 40,000 animations.</p>

<p class="article-figure"><a href="media/figure-08.png"><img src="media/figure-08.png" alt="Generated Dweet continuations shown side by side"></a></p>

<p>Somewhere around the 10,000th animation, I began to appreciate the existence of VLMs and HPSv3. Sadly, it was too late. </p>

<p>After several rounds of training, I wanted to see how much of my taste had actually rubbed off on Demoscener. I enlisted a rather unwilling friend to judge 400 sets of demos from a few of the checkpoints (I picked 4 randomly), without knowing which model had produced which.</p>

<p class="article-figure"><a href="media/figure-09.png"><img src="media/figure-09.png" alt="Blind preference results across Demoscener checkpoints"></a></p>

<p>The results showed that checkpoint 4 was the most favorable, so I used that to run inference on my Mac. </p>

<p>Now coming to the end of the side quest, I built a little interface where I could generate several continuations from the same prefix, render them side by side and branch off from whichever one caught my eye. I could then tweak the code, generate more continuations, and keep exploring.</p>

<p class="article-figure"><a href="media/figure-10.png"><img src="media/figure-10.png" alt="Interface for comparing generated Dweet continuations"></a></p>

<p>Each branch represents a possible continuation, which I could compare visually, tweak by hand, and use as the starting point for further exploration.</p>

<p class="article-figure"><a href="media/figure-11.png"><img src="media/figure-11.png" alt="Branches of generated Dweet continuations"></a></p>

<p>There is something quite lovely about being able to wander through these possibilities. I think I&#x27;ll be spending a little more time doing just that.</p>

<p>You can find <a href="https://huggingface.co/datavorous/Demoscener-7B">Demoscener-7B</a> and the <a href="https://huggingface.co/datasets/datavorous/Demoscener-Dweets-25k">dataset</a> on HuggingFace.</p>

<p>
</p>
