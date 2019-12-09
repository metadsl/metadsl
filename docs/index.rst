metadsl
=======

*Domain Specific Languages Embedded in Python*

`metadsl` inserts a layer between calling a function and computing its result,
so that we can build up a bunch of calls, transform them, and then execute
them all at once.

.. literalinclude:: index_example.py
   :language: python


Seperating the user facing API of your DSL from its implementation enables
other library authors to experiment with how it executes while preserving
user expectations.

In this documentation we give some examples of using `metadsl`,
provide a roadmap, and lay out the motivation for this library.

.. toctree::
   :maxdepth: 3

   Usage
   Motivation
   Simple Arrays
   Concepts
   Roadmap
   Contributing
   api/index
