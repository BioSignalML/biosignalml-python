#ifndef _TRIPLESTORE_H
#define _TRIPLESTORE_H  1

#ifdef __cplusplus
extern "C" {
#endif

typedef struct TripleStore {
  librdf_world   *world ;
  librdf_storage *storage ;
  } TripleStore ;


TripleStore *new_TripleStore(const char *, const char *, const char *) ;

void free_TripleStore(TripleStore *) ;


#ifdef __cplusplus
  } ;
#endif

#endif
