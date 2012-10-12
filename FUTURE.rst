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
  * Best to leave latest unchange but point an empty resource
    at it? For a recording graph:::

      <uri_xxx> a prv:dataItem ;
        # a <DeletedClass> .
        prv:preceededBy <del_record> ;
        prv:createdBy [ ] ;
        dct:subject <recording> .

      <del_record> a prv:dataItem ;
        a bsml:RecordingGraph ;
        prv:createdBy [ ] ;
        dct:subject <recording> .

Abstract Model
--------------

* Store either the recording graph's URI or a Provenance
  object with all resources?

* Remove `graph` attribute from AbstractObject (and replace
  with graph URI? Provenance?

* Add a 'provenance()' method to AbstractObject that returns
  a Provenance object?? **BEST**
