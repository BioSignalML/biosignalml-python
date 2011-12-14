from minerva import EventFile, HypnogramFile


class MinervaEvent(model.Event):

  def __init__(self, uri, ...):
    super(MinervaEvent, self).__init__(uri)





# Need to ger model.Recording (in triplestore) from URI

  recording = model.Recording.create_from_RDFmodel(uri)

  # Ensure seq. no. unique and not already in store... ??

     tm = recording.interval(a.onset, a.duration)
     evt = model.Event(str(uri) + '/event/%d' % n, class, tm)
     evt.factor = recording


     evt.add_to_RDFmodel(model, mapping, graph)
