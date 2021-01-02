Title: Program to an Interface: Exercise in Cache Removal
Date: 2020-12-31
Modified: 2021-01-02
Category: Programming
Tags: software-design, vimscript, OOP
Slug: interface-cache
Summary: An example of interface-based programming using OOP in Vimscript.



<figure>
<img src="images/05-1_interface.png" style="width:100%;"
alt="simple diagram representing two different interfaces">
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
workflow-management/fuzzy-finding plugin, which allows its textfile cache to
be disabled. It's my hope that some intermediate-level programmers who are
beginning to think about how to improve the designs of their programs would
find this useful. And while I am aiming to keep the implementation details,
and even more so the specifics of Vimscript light, kindred sprits who enjoy
programming in this quirky language might also find an interesting nugget or
two here.



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
differential behaviors to within the functions implementing the textfile
cache themselves. Doing so allows the call sites of these functions to remain
largely unmodified as long as they still return the correct data regardless of
whether the user chose to enable or disable the cache.

The original textfile cache loads the list of filepaths using the below
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

The code to be executed when the textfile cache is enabled is the exact same,
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



## Program to the Interface

### Design

Astute readers have probably already guessed where this is going. Instead
of adding the logic for disabling the cache inside existing functions
implementing the behaviors of the textfile cache, why not aim for even
greater modularity by partitioning the set of behaviors needed to implement
a functioning textfile cache and a disabled/null cache into two separate
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
cache object methods, which can either come from the `file_cache` or the
`null_cache` object based on however users chose to configure it. The poing
is, dependents of the caching system need not nor care to know about how the
cache produces the files list that they need for their own functionalities.

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
of thousands of files. While making this addition still isn't trivial, the new
interface-based design makes it easily manageable.

At this point, there's no more in the way of engineering principles or design
insights that I can offer you, so you should be fully ready to put the
idea into practice. Though if you're the type that enjoys delving into the
nitty-gritty details, the remaining subsections provide glimpses into the
implementation and usage of this particular interface that we've so far only
been discussing at a high-level.


### Implementation

Here I'll only be showcasing 2 of the 4 methods required to implement
the interface designed earlier, since the other two basically just wrap
these two while adding some minor functionalities for convenience.
But if you're interested, the complete implementation of the plugin's
cache system (and only that) resides in the single source file:
[cache.vim](https://github.com/vim-ctrlspace/vim-ctrlspace/blob/master/autoload/ctrlspace/cache.vim).

Comparing the `load` methods of both caches, we have:

```viml
function! s:file_cache.load() dict abort
    let filename = ctrlspace#util#FilesCache()
    if empty(filename) || !filereadable(filename)
        return
    endif
    let self.files = readfile(filename)
endfunction

function! s:null_cache.load() dict abort
    let self.files = s:glob_project_files()
endfunction
```

The `s:file_cache.load` method is almost a line for line copy of the
original `s:loadFilesFromCache` function, with the only deviation being
the last line, which reads and assigns the contents in the textfile to the
instance variable `self.files` (more on how this works in Vimscript soon),
instead of the script-scoped global variable `s:files` in the original
implementation. The `null_cache.load` method on the other hand just calls the
`s:glob_project_files` helper each time, which is the same function used by
the `file_cache` to index and populate its textfile cache as well. In both
cases, their respective `self.files` list will contain the filepaths of the
project, and can be passed to whichever functions or methods that need them.

Onto the `save` methods of both, we have:

```viml
function! s:file_cache.save() dict abort
    let filename = ctrlspace#util#FilesCache()
    if empty(filename)
        return
    endif
    call writefile(self.files, filename)
endfunction

function! s:null_cache.save() abort
    return
endfunction
```

I didn't show the implementation of the original `s:saveFilesInCache` function
earlier, but `s:file_cache.save` essentially does the same thing, which is to
perform the inverse operation as that of `s:file_cache.load`, i.e. move data
from `self.files` into a textfile by writing to it. The `s:null_cache.save`
method instead just performs a no-op.

#### OOP in Vimscript

For the Vimscript enthusiasts, all methods except for `s:null_cache.save`
(since a no-op of course does not need access to the `self` instance) are
implemented as Vim's dictionary-functions (see: `:help dictionary-function`).
This is made possible by the `dict` attribute following the function
definitons, which grants the function access to the local variable `self` that
points to the object instance it's invoked from.

The dot notation used in the function definition line is just syntactic sugar.
Under-the-hood these objects are simply Vimscript dictionaries, meaning that
the following is an equally valid way to define the `s:null_cache.load` method
for instance:

```viml
function! s:load_by_glob() dict abort
    let self.files = s:glob_project_files()
endfunction

let s:null_cache = {'files': [], 'load': function("s:load_by_glob")}
```

The method name is a key in the dictionary, with the value being its
corresponding function reference (see `:help Funcref`). But with multiple
functions needed for both caches, it's more succinct to just create these
dictionaries once as follows, then directly add the required interface methods
onto them as was done earlier.

```viml
let s:file_cache = {}

let s:null_cache = {}
```

As a final word on OOP in Vimscript, I'd just like to point out that it more
so resembles JavaScript's prototype-based OOP, as opposed to the class-based
system used by most OO-languages. So if you're familiar with the OO-semantics
of JS, then Vimscript's should feel quite natural (or if you're like me, OOP
in Vimscript can help you learn JavaScript's instead). For example, to inherit
from an existing 'prototype' object, you can use Vim's built-in `deepcopy`
function to clone the dictionary, then modify the new object instance however
you like.


### Usage

With there being no classes in Vimscript, that means there are no constructors
either. But we can create a rough equivalent like so:

```viml
function! ctrlspace#cache#Init() abort
  let cache = s:config.EnableFilesCache ? s:file_cache : s:null_cache
  call s:cache_common(cache)
  return cache
endfunction

function! s:cache_common(cache) abort
  let a:cache.files = []
  let a:cache.items = []
  let a:cache.clear_all = function('s:clear_all')
  let a:cache.get_files = function('s:get_files')
  let a:cache.get_items = function('s:get_items')
  let a:cache.map_files2items = function('s:map_files2items')
endfunction
```

We select the correct type of cache to use by checking the value of
`s:config.EnableFilesCache`, which is actually a Vim global variable (see
`:help g:`) that can be set by the user in their `.vimrc`. Then some
common data and methods are initialized and attached to `cache` by calling
`s:cache_common(cache)`. And finally, this `cache` is simply returned.

Note that the ternary conditional in `ctrlspace#cache#Init` above is the only
place in the entire codebase where the check for whether the user enabled or
disabled the cache is done. This tidyness is often one of the many benefits
that comes out of a well-designed interface.

Now inside of the `autoload/ctrlspace/files.vim` source, where the cache
object is actually used, all that's needed is:

```viml
let s:Cache = ctrlspace#cache#Init()
```

And once more, functions inside of `files.vim` are completely agnostic about
how this cache actually works. All they know is that they can invoke the
`load()`, `save()`, `collect()` and `refresh()` methods of the `s:Cache`
object wherever those might be needed, and they can count on the correct
behaviors guaranteed by the cache's interface to take place.



## Beyond OOP-Based Interfaces

As mentioned in the introduction, programming to an interface is ultimately
quite a simple idea, and once internalized, you'd naturally start to think in
its terms when designing your programs. But despite its conceptual simplicity,
or perhaps because of it, it is also a very powerful idea. This is because a
simple idea is usually a generalizable one.

In this context, it means that although the idea of programming to an
interface seems to naturally lend itself to the OOP paradigm, to the point that
`interface` is even a built-in construct in some languages like
[Java](https://docs.oracle.com/javase/tutorial/java/IandI/createinterface.html)
and [PHP](https://www.php.net/manual/en/language.oop5.interfaces.php)
(and alternatively termed as a
[protocol](https://en.wikipedia.org/wiki/Protocol_(object-oriented_programming))
in others), the fundamental principle behind it is completely independent of
object-oriented concepts.

This generalized take on programming to an interface is precisely what I aim
to demonstrate in a [follow-up post](#). I don't expect it to impart any
additional insights onto the reader, but there will plenty of gory cool hacks,
all in Vimscript of coruse!



