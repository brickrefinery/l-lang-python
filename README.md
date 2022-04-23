# L Lang, Python implementation

A basic implementation of the [L language](https://github.com/brickrefinery/l-lang-spec) in Python.

## Status

While the spec itself is fairly functional as a concept, this implementation is not yet where it can be a full demo of the spec itself.

Tokens implemented:

* META token remapping
* Literals (strings, numbers, boolean)
* Variables
* Print (including appropriate header/footers)
* Command line argument passthrough
* Math (addition/subtraction)

Current major steps remaining:

* Conditionals (if/then)
* Looping
* Submodels/submodules

Those above are what's being considered the 1.0 release and the script will be published to pypi for easier installation. Once it's on pypi this readme will be rewritten to conform closer to the style of the spec including installation and some basic howto examples.s