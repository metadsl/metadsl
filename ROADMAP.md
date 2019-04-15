# Roadmap

This is a preliminary roadmap to drive the direction of development here. 

We would appreciate any input from the community on what would be useful for them, that could serve
to inform this roadmap.

1. Add examples in docs for low level usage
  1. Create  API for doing arithmetic (adding/multipling numbers)
    1. Show how to write translater that does partial evaluation
    2. Show how to write compiler to Python AST
    3. Add variables and show how these show up in Python AST
    4. Show how to create wrapped version that deals with implicit conversion with python types
  2. Create typed lambda calculus API
    1. Show how to convert between [De Bruijn index](https://en.wikipedia.org/wiki/De_Bruijn_index) and named variable
    2. Show how to implement [Church numerals](https://en.wikipedia.org/wiki/Church_encoding#Church_numerals)
       and arithmatic on top of it
    3. Show how to convert between these and python integers
   
2. Support initial use case with NumPy API that translates to other backends
  1. Be able to build up NumPy expression
  2. Create simple transformer to turn numpy expressions into pytorch AST.
