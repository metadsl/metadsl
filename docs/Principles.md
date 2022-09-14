# Principles


## Works with MyPy out of the box

One of the core constraints of this package is that it is meant to work with Mypy, or
other type checkers, out of the box, without any custom plugins. This greatly constrains
our design space, which is intentional. It means that any functionality should be typed
in a way that is compatible with Mypy, without relying on any metaprogramming to define
the type signatures of objects.

The reason for this constraint is to keep us "pythonic", to make any code we write
look closer to regular Python and keep us from veering too much off into our own
custom language. In this way, at least looking at the expression at the type level,
we support a subset of Python semantics.