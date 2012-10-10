Future Enhancments for BioSignalML Model
========================================

General
-------

* Be consistent in specifying intervals -- do we *always*
  use `start` and `end` times, with `duration1 a property?
  The same way should be used in all Python code that deals
  with intervals as well as RDF representations.

* Deleting recordings from a RDF store -- what happens
  in provenance graph?

  * Do we create a (empty) resource whose predecessor is the
    recording being deleted?
  * Or do we use some other property, including marking the
    latest version with a 'deleted' flag?

