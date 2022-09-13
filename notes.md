
## data types
Difference between Using constructors for a union versus a type with a match?

It's really cumbersome to construct data types... See Args for code data. Have to test
each accessor, and duplicate them, obscures meaning.

**Can we use datatypes instead? Frozen ones?** Do we translate to expressions or do
we just keep them as is and add another core type? 

Maybe just treat them as macro. it's just how do we reference function of each property
then, since they are no longer actually properties but just attrbutes?

We could add properties to the class, hm....

for another day!

## Maybe types
How should I type things with error return types? Should they be a maybe type? How should the traceback
be preserved?

For now just lets assert they never error...


## Rules
Can we use matching rules in definitions to make it easier to write rules instead
of having to write them seperately from the def?