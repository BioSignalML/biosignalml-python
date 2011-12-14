#include <stdlib.h>
#include <redland.h>

#include "triplestore.h"

char *store = "postgresql" ;
char *storeoptions = "host='localhost',database='BioSignalRDF',user='biosignal',password='biosignal'" ;


TripleStore *new_TripleStore(const char *name, const char *store, const char *storeoptions)
/*=======================================================================================*/
{
  librdf_hash *options = NULL ;

  TripleStore *ts = (TripleStore *)calloc(1, sizeof(TripleStore)) ;
  if (ts) {
    if ((ts->world = librdf_new_world()) {
      librdf_world_open(ts->world) ;
//    librdf_world_set_logger(ts->world, NULL, logger) ;
      options = librdf_new_hash_from_string(ts->world, NULL, storeoptions) ;
      if (options) {
        librdf_hash_put_strings(options, "contexts", "yes") ;
        librdf_hash_put_strings(options, "write", "yes") ;
        if (!(ts->storage = librdf_new_storage_with_options(ts->world, store, name, options)) {
          librdf_hash_put_strings(options, "new", "yes") ;
          ts->storage = librdf_new_storage_with_options(ts->world, store, name, options) ;
          }
        librdf_free_hash(options) ;
        if (ts->storage) return ts ;   // All is well
        }
      }
    free_TripleStore(ts) ;             // Something's failed
    }
  return NULL ;
  }


void free_TripleStore(TripleStore *ts)
/*==================================*/
{
  if (ts) {
    if (ts->storage) librdf_free_storage(ts->storage) ;
    if (ts->world) librdf_free_world(world) ;
    free(ts) ;
    }
  }
