metadsl
=======
A framework for creating domain specific language libraries in Python.


The goal here is to share representation and optimization logic between different DSLs in Python, allowing
different projects to plug in at different levels and work together easily, and allowing users to transparently
switch how they execute their code without rewriting it.

For example, if someone comes up with a new way of executing linear algebra or wants to try out a new way of optimizing
expressions, they should be able to write those things in a pluggable manner, so that users can try them out with minimal
effort. 

This means we have to explicitly expose the protocols of the different levels to foster distributed collaboration and reuse. 
This library is a place to standardize on those descriptions.

If you have a place where you think this might be useful, please reach out. We would appreciate any questions or thoughts.

In this documentation, we lay out some examples using metadsl, and provide a roadmap as well as the inspiration.

.. toctree::
   :maxdepth: 3

   Why
   Simple Arrays
   Lambda Calculus
   Introduction
   Roadmap
   api/index
