Title: Program to an Interface: An Exercise in Cache Removal
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



In software engineering, there is the simple yet powerful idea of
programming to an interface. While the precise manner this is put
into practice differs depending on the specifics of a given program,
the core principle behind the idea remains the same. When implemented
well, software systems that effectively utilize [interface-based
programming](https://en.wikipedia.org/wiki/Interface-based_programming)
will tend to exhibit desirable characteristics such as loose coupling, high
cohesion, and better modularity, thereby improving code maintainability and
extensibility.

In this post, I'll be explaining how to program to an
interface by walking-through a recent contribution I'd made to
[Vim-CtrlSpace](https://github.com/vim-ctrlspace/vim-ctrlspace) (a
workflow-management / fuzzy-finder plugin), which added the ability to
disable the use of its default files cache. It's my hope that at least some
intermediate-leveled programmers, who might want to improve the designs of
their programs, would find this useful. And while I'm aiming to keep the
implementation details, and even more so the specifics of Vimscript light,
kindred spirits who enjoy programming in this quirky language might also find
an interesting nugget or two in here.



## Problem Context

Like other fuzzy finders, CtrlSpace has a files mode where users can search
and open files from their projects. To make this work, upon encountering a new
project (marked by VCS directories like `.git/` and `.hg/`), CtrlSpace will
index all relevant files through globbing, then store their paths in a plain
textfile. For large projects (the Linux kernel with 70k+ files for instance),
this indexing process can take a while; but once complete, subsequent file
lookups become effectively instantaneous, as all filepaths are cached at that
point.

While this workflow mostly works well, especially on mature projects with
relatively static file structures, it comes with the attendant problem of
using a cache, i.e. how and when to invalidate it. Indeed, whenever one
creates or removes a file, or even just switching to a branch with a slightly
different set of files, the cache becomes outdated, and requires a manual
refresh by reindexing if one wishes to access the newly created file (and
such) through CtrlSpace. Therefore having an option to disable the use of this
textfile cache can be more convenient, especially for projects whose file
structure experiences high flux, and for those that are smaller in sizes.


## Preliminary Tries

A naive but by no means easy approach would be to write new procedural logic
that wires up the plugin's requisite functionalities without executing the
caching operations. So where it currently always reads the contents of the
cached textfile when entering the files mode, the new logic might skip this
step under the right conditions. I won't bother showing code examples for this
approach, as it'll most likely just amount to a myriad of scattered if-blocks
executing seemingly unrelated functions, which is a type of programming I'm
sure most of us have enough firsthand experience with. Needless to say, such
an approach greatly increases complexity, coupling and repetitions in the
codebase, which tend to lead to the dreaded spaghettification over time. Not
recommended.

A slightly better approach would be to limit the conditional branching to
within the scopes of the functions implementing the actual textfile cache.
Doing so allows their call sites to remain unmodified as long as they still
return the correct data or execute the appropriate procedures.

Let's see how this can be applied to the function that loads the contents of
the textfile cache `s:loadFilesFromCache`:

```viml
function! s:loadFilesFromCache() abort
    let filename = ctrlspace#util#FilesCache()
    if empty(filename) || !filereadable(filename)
        return
    endif
    let s:files = readfile(filename)
endfunction
```

So `s:loadFilesFromCache` first gets the path to the textfile cache for the
current project, ensures it's non-empty and is readable, then reads its
contents into the script-local list `s:files`.

To implement the approach just described, something along the lines of the
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
        " store filepaths into s:files w/o reading from the textfile cache
        " ...
    endif
endfunction
```

The code to be executed when the textfile cache is enabled is the exact same,
just now wrapped in an if-block; while in the else-block, logic for a disabled
cache can be added. And as long as the function can still populate `s:files`
with the project's filepaths, by calling the files indexing function in the
else-branch for example, then all callers of `s:loadFilesFromCache` should
remain satisfied.

The underlying idea embodied in the approach above isn't far off in spirit to
that of programming to an interface. The key insight is that if the API of
the cache system can be made into an unbreakable contract, then its functions
can be treated as black boxes, thereby freeing their callers from having care
about the implementation details of the cache. Where this approach fell short
is that it doesn't take the idea far enough.

In addition to the function `s:loadFilesFromCache`, there are
also `s:saveFilesInCache`, `ctrlspace#files#RefreshFiles` and
`ctrlspace#files#CollectFiles`; so the same conditional checks and branching
logic would need to be added into those functions as well. This will
definitely result in a non-trivial amount of code duplication. Furthermore,
if you later wanted to add an entirely new system for retrieving and handling
project files, the internal implementations of these functions can quickly
become unwieldy, making the code error-prone and brittle.



## Program to the Interface

### Design

Astute readers have probably already guessed where this is going. Instead of
adding the logic to disable the cache inside existing functions implementing
the textfile cache, why not strive for even greater modularity by partitioning
the set of behaviors needed to implement the functioning textfile cache and
a disabling null cache into two non-overlapping components? With the help of
some Vimscript-styled OOP, that's exactly what I did.

In effect, both cache objects contain common data attributes like a `files`
list, and some shared helper methods. But most importantly, they both
implement 4 key methods that define a uniform interface:

* `cache.load`, replaces `s:loadFilesFromCache` entirely
* `cache.save`, replaces `s:saveFilesInCache` entirely
* `cache.refresh`, replaces `ctrlspace#files#RefreshFiles` in part
* `cache.collect`, replaces the internals of and is wrapped by `ctrlspace#files#CollectFiles`

Callers of the original cache system's functions will now call the equivalent
methods on a cache object, which can either be the `file_cache` or the
`null_cache` depending on how the user has configured it. The point is,
functions that the cache system neither know nor care to know exactly how it
works.

This well-defined interface with its clear-cut boundaries also significantly
simplifies both the maintenance of and extensions to the cache system. With
regards to maintenance, since the two caches have zero interactions, bugs
that occur in one are necessarily contained within its own code. As for
extensions, I've been meaning to add a new hybrid cache that'll be able to
reap the benefits of both existing caches. The idea is it can behave like the
`null_cache` when working on projects containing less than _N_ files to get
the convenience of never needing to manually refresh the cache; and as the
`file_cache` for projects over that threshold to enjoy fast filepaths lookups
with tens or even hundreds of thousands of files. Adding this still won't be
trivial, but the new interface-based design should make it quite manageable.

This is essentially all the engineering principles I can offer you in this
article, and you really should be ready to put the theory into practice.
Though if you're the type to enjoy delving into the nitty-gritty details,
the remaining subsections do provide some glimpses into the implementation
and usage of this specific interface that we've only been discussing at a
high-level so far.


### Implementation

I'll only showcase 2 of the 4 methods required to implement the interface
designed above, since the other two are basically just wrappers around these
that add a couple of minor conveniences. But if you're interested, the
complete implementation of the plugin's cache system (and only that) resides
entirely in the source [cache.vim](https://github.com/vim-ctrlspace/vim-ctrlspace/blob/master/autoload/ctrlspace/cache.vim).

The snippet below shows the `load` methods for both caches:

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
the last line, which reads and assigns the contents in the textfile to
the instance variable `self.files` (more on how this works in Vimscript
below), instead of the script-local variable `s:files` in the original
implementation. The `null_cache.load` method on the other hand just calls the
`s:glob_project_files` helper each time, which is the same function used by
the `file_cache` to index and populate its textfile cache as well. In both
cases, their respective `self.files` attribute will contain the filepaths of
the project, and can be passed onto whichever functions that need them.

Comparing both `save` methods, we have:

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

I had not shown the implementation of the original `s:saveFilesInCache`
function, but `s:file_cache.save` also just reimplements it and does the exact
same thing, which is to perform the inverse operation to `s:file_cache.load`,
i.e. move the in-memory filepaths data stored in `self.files` onto disk by
writing to the textfile. The `s:null_cache.save` method instead just performs
a no-op.

##### OOP in Vimscript

A brief aside for the Vimscript enthusiasts, all cache methods except
for `s:null_cache.save` (because a no-op needs no access to its own data
of course) are implemented using Vim's dictionary-functions (run `:help
dictionary-function` inside Vim). This is facilitated by the `dict` attribute
following the function definitions, which grants the function access to the
local variable `self` that points to the dictionary instance it's invoked
from, thereby effectively emulating an object in OOP.

The dot notation used in the function definition is just syntactic sugar.
Under-the-hood these objects are still plain Vimscript dictionaries, meaning
that the following is an equally valid way to define the `s:null_cache.load`
method as an example:

```viml
function! s:load_by_glob() dict abort
    let self.files = s:glob_project_files()
endfunction

let s:null_cache = {'files': [], 'load': function("s:load_by_glob")}
" now s:null_cache.load() works as before
```

The method name `load` is a string key in the dictionary, with its
corresponding value being the function reference (see `:help Funcref`) that
actually implements it. With multiple methods needing to be defined on both
caches however, it's more succinct to just create the dictionary objects once
like below, then attach their respective methods directly, as shown earlier.

```
let s:file_cache = {}

let s:null_cache = {}
```

As a final word on OOP in Vimscript, I'd just like to point out that it more
so resembles JavaScript's prototype-based OOP, as opposed to the class-based
kind used by most OO-languages. So if you're familiar with the OO-semantics
of JS, then Vimscript's should be very easy to pick-up (or if you're like me,
writing OOP in Vimscript can help you learn JavaScript's instead). If one
wants to do prototypal inheritance for example, one can use Vim's built-in
`deepcopy` function to clone the an existing dictionary object, then modify
the new instance however one sees fit.


### Usage

No class in Vimscript also means no constructors. But we can ape a rough
functionally equivalent like so:

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

Inside the `ctrlspace#cache#Init` "constructor", the correct type of cache
is selected by checking the value of `s:config.EnableFilesCache`, which is
actually a Vim global variable (see `:help g:`) that can be set by the user in
their `.vimrc`. Note that this is the only place in the entire codebase where
this conditional check is done. Then some common data initialized and methods
attached with `call s:cache_common(cache)`. And finally, this `cache` object
is returned.

Now inside of the
[`files.vim`](https://github.com/vim-ctrlspace/vim-ctrlspace/blob/master/autoload/ctrlspace/files.vim)
source, where the cache object is actually used, all that's needed is:

```
let s:Cache = ctrlspace#cache#Init()
```

Once more, functions inside of `files.vim` are completely agnostic about how
its cache actually works. All they know is that they can invoke its `load()`,
`save()`, `collect()` and `refresh()` methods; and count on these methods to
behave correctly due to the guarantees of the interface.



## Beyond OOP-Based Interfaces

As mentioned in the introduction, programming to an interface is ultimately
quite a simple idea, and once internalized, you'd naturally start to think in
its terms when designing your programs. But despite its conceptual simplicity,
or perhaps because of it, it's also extremely powerful.

Simple ideas tend to be generalizable ones. So although programming to an
interface seems to naturally lend itself to the OOP paradigm, to the point
that `interface` is even a built-in construct in some languages like
[Java](https://docs.oracle.com/javase/tutorial/java/IandI/createinterface.html)
and [PHP](https://www.php.net/manual/en/language.oop5.interfaces.php)
(and alternatively termed a
[protocol](https://en.wikipedia.org/wiki/Protocol_(object-oriented_programming))
in others), its fundamental principle is orthogonal to object-oriented
concepts.

This more general approach on how to program to an interface is precisely what
I'd like to demonstrate in a [follow-up post](#). I don't expect it'll impart
any additional insights onto the reader, but there will be plenty of gory cool
hacks, all in Vimscript of course!



