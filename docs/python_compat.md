# Python Compatibility

Rules for Python compat data structures:


1. Register their three types for guessing with `guess.register`, including inner types
2. Add a conversion from the compat type to the inner type
3. add a Boxer.box for creating the compat type
