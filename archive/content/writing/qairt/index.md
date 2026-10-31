---
title: Reverse engineering the Qualcomm NPU compiler
description: An investigation into the Qualcomm NPU compiler, including VTCM placement and Hextimate.
subtitle: What I pulled out of a stripped QAIRT binary
date: June 19, 2026
author: datavorous
---

My work is to maximise the usage of NPUs to make edge deployment faster for whatever models we want to run on them. But NPU documentation on the web is basically nonexistent, and the little that's out there was so disappointing that at one point I thought of quitting - so I reverse engineered the compiler instead. I previously wrote a small primer on [NPUs: what, and where they break](https://datavorous.com/writing/npu/), it should be enough to understand for what's coming next.

For none of the SoC's did Qualcomm publish the memory capacity of VTCMs. How am I supposed to understand whether my tensors were spilling all over? Or whether quantisation is really needed? Add to that my curiousty to know how they simulate the working of a model even before it runs on the actual hardware, and which optimization algorithms are involved.

I (equipped with [Claude Code](https://claude.com/product/claude-code)) doubled down on the `*.so` files of [QNPU SDK](https://www.qualcomm.com/developer/software/neural-processing-sdk-for-ai) (v2.46.0.260424), and banked on the unmangled names that survived stripping, the raw machine code decompiled with [Ghidra](https://github.com/NationalSecurityAgency/ghidra), and some empirical parameter sweeping on my Linux.

Some of the novel findings are (no one has the attention span to read the entire writeup anyway):

1. HTP solves VTCM placement as an MILP and solves it using [HiGHS](https://highs.dev/) (optimization solver rather than heuristics) which was completely unknown publicly
2. VTCM placement uses a recursive backtracking allocator operating in a 3D coordinate space
3. The compiler can automatically alter weight precision (without you knowing) during placement to relieve memory pressure
4. The effective fit/spill boundary depends on the target architecture even when different SoCs report the same `vtcmSize`
5. HTP contains a hidden analytical simulator called Hextimate from where we recovered roofline equations and contention models

The appendix contains more information, which I could not fit in my content body.

That's the gist, rest of this piece will cover three things I found, which I think were never publicly documented anywhere on the internet, and will benefit anyone willing to do edge deployment on Qualcomm NPUs.

## The memory wall

The Hexagon chip has a small pool of on chip scratch memory called VTCM (vector tightly coupled memory). On the other side we have the DDR which is the main memory, but it's slow. The significant bottleneck for ML inference is caused by how much it takes to move your data around. The entire job of the compiler in this case is to decide what gets to sit on the VTCM at each moment, because anything that doesn't fit has to be taken out to DDR and fetched back later, which is *expensive* and energy inefficient.

Every tensor in your model has a lifetime. At any instant during the execution, some set of tensors is alive (can be termed as working set). If that fits in VTCM, then everything will be fast. If not, then the compiler will start inserting spill operations (pushing a tensor out to DDR) and fill operatoins (pull it back). This is the cliff I wanted find out.

Using the same model (Qwen 0.8B), on an SM8350 the compiler reported spilling 5.46 MB and filling 33.9 MB, with total DDR of 37.9 MB, whereas on an SM8650 (V75), nothing spilled out and the DDR read 1.15 MB. 33x time jump in DDR read traffic from nothing but the target chip (which is expected). But for some peculiar reason, the chips reported the same VTCM size in the compiled output - a field that just says 4. Now I don't know 4 "what", or whether it's some code. The behaviour is completely different anyway. I didn't recover the actual capacities, that's something I wish to do next.

The compiled binary carries a metadata field called `spillFillBufferSize`, which when 0 indicates that the model weights fit entirely on chip. It can help anyone determine quickly to find the causal relation for their inference being slow.

Now I can confidently spend my time on quantising my model if my target chip is an SM8350, instead of second guessing it.

One more thing decides whether you fit, and things get a little more exciting there.

## The scheduler playing tetris with time

The order in which the chip runs operations decides how long each tensor stays alive, which decides how big the working set gets, which decides whether you hit the cliff. Hence the task of the compiler's scheduler is to find the correct order which will keep the working set smallest and within the limits of VTCM.

It does this with something called "Priority BFS". It walks the graph, and measures the peak VTCM that order would require, and then `peak_tcm <= tcm_capacity`-s it. It returns SMALL/LARGE after this, indicating no spill/spill respectively. The fill/spill decision is therefore the outcome of whether the best order it found keeps the peak working set under capacity. Then the ordering metric underneath is an op's position in a depth first topological sort of the graph, which has a nice property of keeping a value's producer and consumer as close together in time as possible. When two ops are tied, that tie is broken with a stack of heuristics, some of them being graph distance between an op's inputs and outputs, depth within a branch, scheduling the heaviest branch first etc.

Once the order is fixed, the compiler has to physically place each tensor on the VTCM. It sorts tensors with the longest lived one first, and eventually the short lived ones next, to cut down fragmentation. The placement is not a simple 1D address by the way, the code assigns each block a [three dimensional coordinate](https://stackoverflow.com/questions/2192087/3-dimensional-bin-packing-algorithms) `(d0, d1, d2)` in the tile space, and the packer (which is recursive) backtracks. The exact retry condition lived in a few kilobytes of inlined SIMD which I didn't try to decode, yet.

That backtracking packer is the fallback path. When the compiler runs its full optimizer instead, placement takes a more striking form, which is a formal optimization problem I had seen before elsewhere.

It's pretty evident by now that placing tensors in VTCM is the same kind of problem as packing suitcases into a small trunk, where we are allowed to leave some suitcases at home but it costs us to fetch them later. When it can, the compiler doesn't wing this with heuristics, but instead it writes the whole thing out as a formal Mixed Integer Linear Program, and hands it over to HiGHS which is a well known open source optimization package.

The compiler dumps the exact problem it's handling into a standard solver file format `.mps` for debugging. I found some trivial things from the decompiled binary after that:

1. The goal it minimizes is total moved (sum of bytes spilled to DDR, filled back from there, and on multi core chips sent and received between cores)
2. Two tensors that are alive at the same time can't occupy the same on chip bytes
3. Either a tensor lives on the workbench at some valid address, or it's banished to DDR. It's semi continuous.

Your model's numeric precision can be rewritten without you being informed. There are operations called `relaxed_precision_cast` that convert tensors between float, FP16 and BF16 *during placement*, in order to relieve memory pressure. Hence now we know that the compiler can insert a downgrade on its own, our float32 tensor can become a FP16 if that's how the bytes fit. (I confirmed these casts are inserted during placement; whether they're a variable inside the solver itself or a separate pass, I can't say from what I pulled.)

There's a lot more in the optimizer than I can fit here. Some of them are;

1. Graph are partitioned with a min-cut to decide where to cut the model for spilling
2. A separate, neat little algorithm makes concatenation free in the common case by having producers write directly into the final layout instead of copying
3. Convolutions are turned into matrix multiplies via im2col
4. Duplicate operations are found by checksumming their contents and merged

## Hexagon + estimate = Hextimate (??)

All of this - the scheduler hunting for the smallest working set, the optimizer minimizing bytes moved rests on one thing the compiler can't actually have. To choose between two schedules, or to decide a spill is worth avoiding, it has to know how *expensive* each option is, in time. But the chip isn't there. The compiler is running on my Linux box, placing thousands of bets against hardware that won't exist until the model ships to a phone. So how does it price anything?

It guesses, and it has a whole simulator built just for guessing. It's called Hextimate (Hexagon estimate, right?) and the compiler is full of references to it. It's a small analytical model of the entire chip which pretends to run your model and adds up the cost piece by piece, in two buckets - compute and memory movement.

It also models *contention* (what happens when two parts of the chip want the same resource and one has to wait?) and it doesn't return a single number but a *range*. It happens to run the workload once assuming everything overlaps perfectly, once assuming nothing does, and reports both ends. This should qualify it as a simulator rather than a lookup table interface.

Most of Hextimate's shape I pieced together from the names of its internal pieces. But for the memory side I got the actual formula, straight out of the machine code (thanks Sonnet 4.6), and it's the textbook roofline model every performance engineer already knows:

```
bandwidth = channels * width * efficiency * frequency
time = bytes/bandwidth
```

The simulator keeps a *separate* cost for certain things instead of lumping them together, which are think are pretty trivial. Although, I could read the names of these separate cost factors, the actual values stored in them I was not able to extract.

1. Integer and floating point compute are priced separately (trivial)
2. Writing one piece of data to many places at once (multicast) is priced apart from writing it one at a time (also trivial)
3. KV cache tensors and weights get their own "fast DDR" factor.

It also carries dedicated detectors that recognizes FlashAttention, MoEs, KVCache, rotary embeddings etc.

## Conclusion

So what?

The key takeaways from this RE attempt, which I think are useful for everyone who are into edge ML:

1. It tells the custom scheduler authors that placement quality is solver bounded, and not bounded by heuristics, and that the objective is pure byte traffic.
2. A custom scheduler can mirror the beliefs of Hextimate to predict the compiler's decisions
3. The cost model is biased toward LLM workloads at the coefficient level (hence recognizable things KV/weight tensors are a big plus)
4. Precision is a knob the solver will pull whether you asked or not, hence quality can differ in actual hardware
5. `spillFillBufferSize` can be used a static fit/spill oracle

Whether it directly helps anyone, or simply quenches anyone's curiousity is a separate question in itself, but I got the answers I was unable to find everywhere. If you've done edge work on Hexagon and want to compare notes - or tell me where I'm wrong - [I'd like that](mailto:hi@datavorous.com).

## Notes

The question is how much to trust it. The file (`libHtpPrepare.so`) was our sole target (x86_64 host build, QAIRT 2.46.0.260424). My previous RE attempts were easy/medium crackmes, not proprietary compilers, and this one was only possible with the help of Claude Code. Hence read every claim with that grain of salt. I will wait till I figure out all the legalities before publishing the steps I perfomed to get the insights.

1. The only finds which I could not place anywhere in NPU related literature are the ones stated at the very beginning of this writeup. "Not publicly documented in this SDK version" is a claim I can stand behind.
2. This is one SDK version of one binary. The numbers (the 33x DDR jump, the 5.46/33.9 MB spill/fill, the `spillFillBufferSize` verdicts) are reproducible on my box with Qualcomm's own tools as the oracle, but a different QAIRT release could reshuffle any of it.
3. The binary is littered with names like `dp_tcm_threshold_selector`, `TCM_THRESH_75_predictor`, `special_mlp_features`, it really looks like as if there's a trained model in there choosing when to spill. There isn't, at least not in this binary. I could not find any weight matrix, no forward pass, nothing that smells like inference. `special_mlp_features` turned out to be a function that exports features to Python i.e. training data going out. The cost path is a plain CSV lookup table. So the learned part, if it exists, lives upstream at Qualcomm's training time and ships as a table. I could not prove a weight bearing model runs at compile time, and I'd bet against it
