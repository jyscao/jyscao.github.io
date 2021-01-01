Title: Programming to an Interface by Example (Part 1)
Date: 2020-12-31
Modified: 2020-12-31
Category: Programming
Tags: software-design, vimscript, OOP
Slug: interface-cache
Summary: An Exercise in Cache Removal



<figure>
<img src="images/05-1_interface.png" style="width:100%;">
<figcaption style="text-align: center;">post banner image</figcaption>
</figure>



## Preamble

In software engineering, there is this simple yet powerful idea of
programming to an interface. While the precise manner it's put into
practice differs depending on the specifics of a given project, the
core principle behind the idea remains the same. When implemented
well, software systems that effectively utilize [interface-based
programming](https://en.wikipedia.org/wiki/Interface-based_programming)
will tend to exhibit desirable characteristics such as loose coupling, high
cohesion, and better modularity, thereby leading to improved maintainability
and extensibility.

In this post, I shall demonstrate how to program to an
interface using the example of a recent contribution I made to
[Vim-CtrlSpace](https://github.com/vim-ctrlspace/vim-ctrlspace), a
workflow-management/fuzzy-finding plugin, which allows its files cache to
be disabled. It's my hope that some intermediate-level programmers who are
beginning to think about how to improve the designs of their programs would
find this useful. And while I aim to keep the implementation details, and even
more so the specifics of Vimscript to a minimum, kindred sprits who enjoy
programming in this (euphemistically speaking) quirky language might also find
an interesting nugget or two here.



## Problem Context

Like most fuzzy finders, CtrlSpace provides a files mode for users to search
and open files in their projects. To populate the list of files used in this
mode, upon encountering a new project (marked by version control directories
such as `.git/`), CtrlSpace indexes all relevant files and stores their paths
in a plain textfile. For large projects (the Linux kernel with 70k+ files
for instance), this indexing process can take a while, but once complete,
subsequent lookups in this project are effectively instantaneous, since all
filepaths are now cached.

While this existing workflow mostly works quit well, especially on mature
projects where the file structures are fairly static, it does bring with it
the usual problem of using caches: how and when to invalidate it. Indeed,
whenever one creates or removes files, or even just switching to branches
with slightly different sets of files, the cache becomes outdated, and would
require a manual refresh by reindexing if one wishes to access the newly
created files (and such) through CtrlSpace. Moreover projects whose file
structures undergo high flux, and are typically smaller in their sizes, where
the (re)indexing times are sufficiently fast, an option to disable this files
cache can offer better convenience.



## Preliminary Tries

A naive but by no means easy approach would be to write new and separate sets
of functions and procedures to add the functionality of a disabled cache.
Where the plugin currently always opens and reads the contents of the cached
textfile when entering files mode, the new system can be implemented to use a
number of conditional checks to determine the appropriate set of procedures
to be executed. I won't bother showing code examples of this approach, as
it'll mostly consist of a myriad of scattered if-statments and seemingly
unrelated function calls, which I daresay is probably something most of us
are familiar with by firsthand experience during our more novice programming
years. Needless to say, such an approach greatly increases complexity, tight
coupling and repetitions, easily leading to the dreaded spaghettification of
the codebase over time. In short, it should never recommended.

A slightly better approach would be to limit the conditional checks and
differential behaviors to within the functions implementing the files cache
themselves. Doing so allows the call sites of these functions to remain
largely unmodified as long as they still return the correct data regardless
of whether the user chose to enable or disable the cache.

The original files cache loads the list of filepaths using the below
`s:loadFilesFromCache` function:

```viml
function! s:loadFilesFromCache() abort
    let filename = ctrlspace#util#FilesCache()
    if empty(filename) || !filereadable(filename)
        return
    endif
    let s:files = readfile(filename)
endfunction
```

The above function gets the path to the actual cached file for the current
project, ensures it's non-empty and is readable, then reads its contents into
the list `s:files`.

To implement the approach described earlier, something along the lines of the
following should work:

```viml
function! s:loadFilesFromCache() abort
    if s:config.EnableFilesCache
        let filename = ctrlspace#util#FilesCache()
        if empty(filename) || !filereadable(filename)
            return
        endif
        let s:files = readfile(filename)
    else
        " ...
        " populate the list s:files w/o reading cache file
        " ...
    endif
endfunction
```

The code to be executed when the files cache is enabled is the exact same,
it's just been wrapped in an if-block; while in the else-block, the logic for
a disabled cache must be added. But as long as the function can still populate
the list `s:files` with the project's filepaths, for example by calling the
file indexing function everytime, then any caller of `s:loadFilesFromCache`
should still be satisfied.

The underlying idea presented by the approach above is actually not far off in
its intent to that of programming to an interface. The key insight is that if
the API of the cache system is treated as an unbreakable contract, then its
functions effectively become black boxes, thereby freeing their callers from
having to be concerned over the cache's implementation details. Where it falls
short however, is that it doesn't take the idea far enough.

In addition to the function `s:loadFilesFromCache`, there are
also `s:saveFilesInCache`, `ctrlspace#files#RefreshFiles` and
`ctrlspace#files#CollectFiles`; so the same conditional checks and branching
logic would need to be added to those functions too, which will certainly lead
to a non-trivial amount of code duplication. Furthermore, if you were to later
decide to add another entirely different approach to retrieving and handling
your project files, the internal implementations of these functions would
quickly become unwieldy, and thus error-prone.



## Programming to an Interface

### The Design

Astute readers have probably already guessed where this is going. Instead
of adding the logic for disabling the cache inside existing functions
implementing the behaviors of the files cache, why not aim for even greater
modularity by partitioning the set of behaviors needed to implement a
functioning files cache and a disabled/null cache into two separate
components? With the help of some Vimscript-styled OOP, that's exactly what I
did.

In effect, both caches are implemented as objects with common attributes such
as the `files` list, a couple getter methods, and most importantly the 4 key
methods that define their shared interface:

* `cache.load`, drop-in replacement for `s:loadFilesFromCache`
* `cache.save`, drop-in replacement for `s:saveFilesInCache`
* `cache.refresh`, replaces parts of `ctrlspace#files#RefreshFiles`
* `cache.collect`, replaces the internals of and is wrapped by `ctrlspace#files#CollectFiles`

Callers of the original cache's functions will now call the corresponding
cache object's methods, which can either come from the `file_cache` or the
`null_cache` based on whatever users set it as in their config option.
The poing is, dependents of the caching system need not nor care to know
about how the cache produces the files list that they need for their own
functionalities.

This well-defined interface with its clear-cut boundaries also makes both
maintenace of and extensions to the cache system significantly simpler. When
it comes to maintenance, as the two caches have zero interactions, bugs that
occur in one are necessarily contained within its own code. As for extensions,
I've been meaning to implement a new hybrid cache that'll be able to reap the
benefits of both existing caches. The idea is for this hybrid cache to behave
as the `null_cache` when working on projects containing less than _N_ number
of files to get the convenience of not needing to manually refresh the cache
on file structure changes; and as the `file_cache` for projects over that
threshold to enjoy the fast filepaths lookups even with tens or even hundreds
of thousands of files. While this addition might not necessarily be a trivial
task, with the interfaced design it should be easily manageable.
