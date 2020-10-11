Title: SpaceVim: A Vimmer's Eval
Date: 2019-10-14
Modified: 2020-10-11
Category: Tools
Tags: text-editor, spacevim, neovim, vim
Slug: spacevim-intro
Summary: An opinionated overview of SpaceVim and its basic features & functionalities.





[SpaceVim](https://spacevim.org) describes itself as "A community-driven
modular vim distribution - The ultimate vim configuration". It's an
excellent project targeting new or busy Vim users who don't have
the time to set up their own configs. It comes with a rich feature
set, which provides all the essential tools needed to streamline the
workflows of programmers, allowing them to just focus on writing code. I
will introduce SpaceVim by offering some practical customization advice
and demonstrating a few essential features. However it's not absent of
rough edges, which I shall also be informing potential users of.

<figure>
<img src="images/01-1_startup.png" style="width:100%;">
<figcaption style="text-align: center;">SpaceVim's startup splash screen</figcaption>
</figure>



## Author's Background

I first started using Vim back in 2015, and was soon sucked down the
rabbit hole of customizing my `.vimrc`. After stumbling across the
Vim plugins ecosystem, it quickly became painfully clear to me that
all attempts to achieve a "perfect" Vim configuration are fantasies.
This is the dilemma SpaceVim aims to resolve. The distribution can be
easily installed on both Linux/macOS and Windows, and fully supports
both Neovim and Vim. My own environment is Neovim on Linux, but the
experience should be comparable for all setups. I'll begin by explaining
how to do basic customizations in SpaceVim, then showcase a couple
useful cool tools, so that newcomers can hit the editor coding!



## What's Available

SpaceVim provides sensible enough defaults that makes it ready for use
straight out-of-the-box. It diverges from the `~/.vimrc` tradition,
instead opting for a `~/.Spacevim.d/init.toml` config file, which is
well-suited for doing high-level customizations on top of SpaceVim's
modular design.

<figure>
<img src="images/01-2_toml-config.png" style="width:100%;">
<figcaption style="text-align: center;">An example of a user TOML config file</figcaption>
</figure>

This TOML config can be quickly opened in a new buffer via the
`SPC f v d` keybinding, where you can set SpaceVim global options and
activate its layers, which are the building blocks of SpaceVim. More
concretely, each SpaceVim layer packages related plugins and configures
them to work together. It also adds a consistent set of keybindings on
top, thereby combining everything into a whole that's greater than the
sum of its parts.

As an example, the git layer makes available both [tpope's
vim-fugitive](https://github.com/tpope/vim-fugitive) and [lambdalisue's
gina.vim](https://github.com/lambdalisue/gina.vim) git wrappers. It also
bundles in [junegunn's gv.vim](https://github.com/junegunn/gv.vim) and
[airblade's vim-gitgutter](https://github.com/airblade/vim-gitgutter). The
main commands provided by all these plugins are hooked up to mnemonic keybinds
under the `SPC g` submenu.

<figure>
<img src="images/01-3_git-guide.png" style="width:100%;">
<figcaption style="text-align: center;">SpaceVim's submenu guide for its git layer</figcaption>
</figure>

For example, `SPC g s` opens up a git-status buffer in a new window
split, where you can conveniently stage files and write commit messages.

<figure>
<img src="images/01-a_gstatus.gif" style="width:100%;">
<figcaption style="text-align: center;">git status with vim-fugitive</figcaption>
</figure>

And `SPC g d` opens a git-diff buffer, where you can review the changes
side-by-side before committing them.

<figure>
<img src="images/01-b_gdiff.gif" style="width:100%;">
<figcaption style="text-align: center;">git diff with vim-fugitive</figcaption>
</figure>

It's also worth noting that SpaceVim's wide array of features and
functionalities are discoverable through its `SPC`-leader guide UI, as
you saw from the `SPC g` example above. In addition to these utilities
layers like git, autocompletion, debugging, grepping, fuzzy finding,
tags, shell, LSP, etc., there also exists 80+ layers for specific
programming languages providing support for things such as syntax
checking, code formatting, code running and more. The complete list
of available layers can be pulled up with `SPC h l`, or by executing
`:SPLayer -l`.

<figure>
<img src="images/01-4_available-layers.png" style="width:100%;">
<figcaption style="text-align: center;">Some of SpaceVim's available layers</figcaption>
</figure>

At the time of this writing, there are 124 available layers, with new
ones being added all the time. Also note that all plugins pulled in
by enabled layers are loaded lazily, and can be easily updated with
`:SPUpdate`. This command also updates SpaceVim itself.



## Configuration Basics

#### Options

Inside your `~/.SpaceVim.d/init.toml`, there is an `[options]` section,
under which all general SpaceVim options should be set. Any key defined
here gets converted to a global vim variable by SpaceVim. So adding the
line `foo = "hello"` creates `g:spacevim_foo` with value `"hello"`.
SpaceVim scripts look for these `g:spacevim_` prefixed global variables
to configure its various settings.

For example, if you wish to use [Shougo's
defx.nvim](https://github.com/Shougo/defx.nvim) as your filemanager,
you can set the option `filemanager = "defx"` in your TOML. To display
absolute line numbers instead of the default relative ones, set
`relativenumber = false`. To opt-out of having SpaceVim manage your
CWD, you can set `project_rooter_automatically = false`. A good portion
of these general SpaceVim options are listed in the [SpaceVim help
manual](`:help spacevim` or open `~/.SpaceVim/doc/SpaceVim.txt`), which
unfortunately don't appear to be fully updated. So to get a list of
all global variables used by SpaceVim, you can always do `:let g:` and
filter on `"g:spacevim_"`.


#### Layers

Layers can come with their own layer-local options. Going back to the
earlier example of the git layer, the git wrapper I use is vim-fugitive,
but if you prefer lambdalisue's gina.vim, then just add the last line
under your enabled git layer.

```toml
[[layers]]
  name = "git"
  git-plugin = "gina"
```

It's always worth first checking both SpaceVim's built-in
help manual (`:help spacevim-layers`) and [the online
documentation](https://spacevim.org/layers/) for usage info and
options regarding your layer of interest. However as only 104 of 124
available layers are documented online, the most reliable method is
reading the layer's source itself, which can all be found inside
`~/.SpaceVim/autoload/SpaceVim/layers/`.


#### Vim-Style Config

Once SpaceVim's options become insufficient for your customization
needs, or if you wish to migrate without abandoning the gems from
your own `.vimrc`, you can supply them to SpaceVim through its hooks
mechanism, which SpaceVim calls its "bootstrap functions". These two
functions can be specified with `bootstrap_before` and `bootstrap_after`
in the `[options]` section of your `init.toml` config like so:

```toml
[options]
  # ...
  # your other options
  # ...
  bootstrap_before = "my_config#before"
  bootstrap_after = "my_config#after"
```

`bootstrap_before` is called prior to the loading of any layers
and plugins, while `bootstrap_after` is called after that when the
`VimEnter` event trigger occurs. In the example above, SpaceVim will
look for `my_config.vim` and call its `my_config#after` function. This
script should be placed inside your `~/.SpaceVim.d/autoload/` directory,
which SpaceVim has already conveniently added to your `runtimepath`.
Here is an example of a `my_config#after` bootstrap function that sets
some options not available via the TOML config:

```viml
function! my_config#after() abort
  call SpaceVim#logger#info("bootstrap_after called")     " log bootstrap_after call
  set inccommand=nosplit    " display result of incremental commands (ex. :%s/patt1/patt2/g)
  set updatetime=500        " GitGutter uses this as its update interval 
  set formatprg=par         " use par for reflowing text lines
  tnoremap jk <C-\><C-n>    " allow jk to exit into normal mode in terminal buffer
endfunction
```

It's also a good place for you to load and configure custom plugins not
belonging to any SpaceVim layer. For example:

```viml
let g:spacevim_custom_plugins = [
      \['tpope/vim-eunuch'],
      \['tpope/vim-rhubarb'],
      \['dahu/vimple'],
      \['AndrewRadev/linediff.vim'],
      \]
```
<!-- fix code block above; currently generated w/ class="error" -->



## Features

SpaceVim is integrated with many valuable tools, such as debugging,
testing, tags, offline documentation, etc. But two features I've
personally found to be indispensable are the fuzzy finding and grepping
utilities.


#### Fuzzy Finding

Currently, there is a choice of 5 fuzzy finders:

* [ctrlp.vim](https://github.com/kien/ctrlp.vim) by Kien
* [denite.nvim](https://github.com/Shougo/denite.nvim) by Shougo
* [fzf.vim](https://github.com/junegunn/fzf.vim) by Junegunn
* [LeaderF](https://github.com/Yggdroot/LeaderF) by Yggdroot
* [unite.vim](https://github.com/Shougo/unite.vim) also by Shougo

What SpaceVim offers on top of these individual plugins is standardized
keybindings. So if you know the SpaceVim keybindings (all discoverable
through the `SPC`-leader guide if you recall), then trying out a
different fuzzy finder becomes a trivial one-line change in your TOML
config. For example, `SPC f f` opens up a fuzzy finder buffer that
recursively searches for files inside your current active buffer's
directory; and `SPC p f` recursively searches from your project's root.

<figure>
<img src="images/01-c_fzf-files.gif" style="width:100%;">
<figcaption style="text-align: center;">fuzzy finding files with fzf</figcaption>
</figure>

While `SPC b b` will do the same, but through your list of all loaded
buffers.

<figure>
<img src="images/01-d_fzf-buffers.gif" style="width:100%;">
<figcaption style="text-align: center;">fuzzy finding loaded buffers with fzf</figcaption>
</figure>


#### Grepping

SpaceVim also has great support for grepping with tools like
[vim-grepper](https://github.com/mhinz/vim-grepper) and
[FlyGrep.vim](https://github.com/wsdjeg/FlyGrep.vim). These utilize
the power of your existing system grepping tools (such as `rg`, `ag`,
`ack` or just plain old `grep`) to search through your entire project
directory for occurrences of whatever query pattern you've specified.
vim-grepper presents its search results in a quickfix buffer.

<figure>
<img src="images/01-e_grepper.gif" style="width:100%;">
<figcaption style="text-align: center;">grepping with vim-grepper</figcaption>
</figure>

While FlyGrep dynamically updates its matches as you narrow down your
query.

<figure>
<img src="images/01-f_flygrep.gif" style="width:100%;">
<figcaption style="text-align: center;">grepping with FlyGrep</figcaption>
</figure>



## Stability

I've made the case for the viability of SpaceVim as your vim config.
However as alluded to earlier in the introduction, it's not without some
rough edges. With the project being 2+ years old and many thousands of
users, SpaceVim's core layers and support for popular languages like
Python, Ruby, JavaScript, Java, C++, C# and such are rock solid. But its
hiccups (though mostly minor) do become more apparent as you explore
its more niche features, and use it for less popular languages like
Lua, for which I experienced noticeable delays when working with even
modestly-sized buffers due to performance issues of `foldexpr` (current
workaround is to not use `expr` as the method for creating folds).
     
Furthermore, although it's certainly great to have many choices of
tools, it sometimes feels like SpaceVim has spread itself a bit too thin
as a result, thereby giving an under-polished user experience with some
features. For example, denite was in a broken state for a while due to
upstream breaking the API. And while there are many layers, not all are
well documented, leaving one to sometimes rely on the source to fully
figure out how to configure them.

When it comes to grepping, the different ways vim-grepper and FlyGrep
present their matches (quickfix vs. dynamically updated temp buffer) are
arguably both useful depending on the situation. But making the same case
for having a glut of grepper tools is harder, which is the default state in
SpaceVim. IMO a better UX would be provided by simply using the best grepper
([ripgrep](https://github.com/BurntSushi/ripgrep)), with perhaps the runner-up
(`ag`, [The Silver Searcher](https://github.com/ggreer/the_silver_searcher))
included as a failsafe. This inconsistency was exacerbated by the fact that
vim-grepper and FlyGrep were originally configured to use different lists of
grepping tools, until I standardized them in a pull request.



## Community

Technical details aside, at almost 200 contributors, 1k+ forks and 12k+
stars [on GitHub](https://github.com/SpaceVim/SpaceVim), SpaceVim's
extremely active community, spearheaded by its founder Wang Shidong, is
arguably the project's greatest strength. The maintainer is proactively
opens issues and merges pull requests, and diligently fixes bugs as
soon as they appear. He and other knowledgeable members frequently help
out users in the various chat channels listed below, which you should
definitely check out if you ever find yourself needing assistance.

* SpaceVim/SpaceVim [on Gitter](https://gitter.im/SpaceVim/SpaceVim)
* &#35;spacevim [on FreeNode](https://webchat.freenode.net/#spacevim)
* t.me/SpaceVim [on Telegram](https://t.me/SpaceVim)
* &#35;spacevim:matrix.org [on Matrix](https://riot.im/app/#/room/%23spacevim:matrix.org)
* &#35;spacevim on [Slack](https://spacevim.slack.com/messages/C88CTJ62J)
* &#35;spacevim on [Discord](https://discord.gg/xcRQnF8)
* SpaceVim on [WhatsApp](https://chat.whatsapp.com/invite/E3HvOvKmFfHDDIq82Rfflx)

Note that all messages sent through any one of the above chat platforms
are relayed to the rest with a bot, so just pick your favorite.



## Final Words

SpaceVim comes preconfigured and works nicely out-of-the-box. It's
modular design is not only a great choice from a development POV, it
also allows for convenient high-level customizations.

Although the core and commonly used aspects of the project are quite
stable and cohesive, I do believe the project will be even better
served by being less accommodating in granting users the freedom to
mix-and-match available components and configurations, as it's simply
impossible for all combinations of tools and settings to produce optimal
development environments. SpaceVim's current paradigm may occasionally
lead to minor instabilities and inconsistencies, but if you don't mind
venturing off the well-beaten path, nor getting your hands a bit dirty
from time to time, then it can still nonetheless be a great option for
you.

I wholeheartedly welcome newcomers to SpaceVim as both users and
contributors, especially given its welcoming and helpful community,
where issues are tackled quickly and PRs merged regularly.



<hr>

###### This post originally appeared on [Medium](https://medium.com/@jyscao/spacevim-a-vimmers-eval-d2020118b517?source=friends_link&sk=54d2f94d9cd95aeaa5feb223abea7d51).
