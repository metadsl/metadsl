# Python Compatibility

Rules for Python compat data structures:


1. Register their types for guessing with `guess_type.register`
2. Add a conversion from the compat type to the inner type
3. add a Boxer.box for creating the compat type
