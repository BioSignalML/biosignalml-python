import RDF


class MEVENT(object):
#===================

  uri = RDF.Uri('http://www.biosignalml.org/ontologies/2009/10/minerva#')
  NS = RDF.NS(str(uri))

# OWL classes:
  Event = NS.Event

  Calibration               = NS.Calibration
  Calibration_Maximum       = NS.Calibration_Maximum
  Calibration_Minimum       = NS.Calibration_Minimum
  Calibration_Minmax        = NS.Calibration_Minmax

  Invalid                   = NS.Invalid
  Invalid_Invalid           = NS.Invalid_Invalid
  Invalid_Reviewed          = NS.Invalid_Reviewed

  Leg_Movement              = NS.Leg_Movement
  Leg_Movement_Arousal      = NS.Leg_Movement_Arousal
  Leg_Movement_Noarousal    = NS.Leg_Movement_Noarousal

  Neurological                         = NS.Neurological
  Neurological_Alpha                   = NS.Neurological_Alpha
  Neurological_Delta                   = NS.Neurological_Delta
  Neurological_K_Complex               = NS.Neurological_K_Complex
  Neurological_Leg_Emg                 = NS.Neurological_Leg_Emg
  Neurological_Movement_Linked_Arousal = NS.Neurological_Movement_Linked_Arousal
  Neurological_Other_Arousal           = NS.Neurological_Other_Arousal
  Neurological_Peak_Wave               = NS.Neurological_Peak_Wave
  Neurological_Respiratory_Arousal     = NS.Neurological_Respiratory_Arousal
  Neurological_Spindle                 = NS.Neurological_Spindle

  Research                  = NS.Research
  Research_Flow_Lim         = NS.Research_Flow_Lim

  Respiratory               = NS.Respiratory
  Respiratory_Cent_Apnea    = NS.Respiratory_Cent_Apnea
  Respiratory_Cent_Hypopnea = NS.Respiratory_Cent_Hypopnea
  Respiratory_Cent_Nonanonh = NS.Respiratory_Cent_Nonanonh
  Respiratory_Obs_Apnea     = NS.Respiratory_Obs_Apnea
  Respiratory_Obs_Hypopnea  = NS.Respiratory_Obs_Hypopnea
  Respiratory_Obs_Nonanonh  = NS.Respiratory_Obs_Nonanonh
  Respiratory_Per_Br        = NS.Respiratory_Per_Br
  Respiratory_Sus_Fl        = NS.Respiratory_Sus_Fl
  Respiratory_Uns_Hypopnea  = NS.Respiratory_Uns_Hypopnea
  Respiratory_Uns_Nonanonh  = NS.Respiratory_Uns_Nonanonh

  Saturation                = NS.Saturation
  Saturation_Desaturation   = NS.Saturation_Desaturation
  Saturation_Unfastening    = NS.Saturation_Unfastening

  Snoring                   = NS.Snoring
  Snoring_High              = NS.Snoring_High
  Snoring_Low               = NS.Snoring_Low

  Urologic                  = NS.Urologic
  Urologic_Peak             = NS.Urologic_Peak
  Urologic_Step             = NS.Urologic_Step

  User_1    = NS.User_1
  User_1_1  = NS.User_1_1
  User_1_2  = NS.User_1_2
  User_1_3  = NS.User_1_3
  User_1_4  = NS.User_1_4
  User_1_5  = NS.User_1_5
  User_1_6  = NS.User_1_6
  User_1_7  = NS.User_1_7
  User_1_8  = NS.User_1_8
  User_1_9  = NS.User_1_9
  User_1_10 = NS.User_1_10

  User_2    = NS.User_2
  User_2_1  = NS.User_2_1
  User_2_2  = NS.User_2_2
  User_2_3  = NS.User_2_3
  User_2_4  = NS.User_2_4
  User_2_5  = NS.User_2_5
  User_2_6  = NS.User_2_6
  User_2_7  = NS.User_2_7
  User_2_8  = NS.User_2_8
  User_2_9  = NS.User_2_9
  User_2_10 = NS.User_2_10

  User_3    = NS.User_3
  User_3_1  = NS.User_3_1
  User_3_2  = NS.User_3_2
  User_3_3  = NS.User_3_3
  User_3_4  = NS.User_3_4
  User_3_5  = NS.User_3_5
  User_3_6  = NS.User_3_6
  User_3_7  = NS.User_3_7
  User_3_8  = NS.User_3_8
  User_3_9  = NS.User_3_9
  User_3_10 = NS.User_3_10

  User_4    = NS.User_4
  User_4_1  = NS.User_4_1
  User_4_2  = NS.User_4_2
  User_4_3  = NS.User_4_3
  User_4_4  = NS.User_4_4
  User_4_5  = NS.User_4_5
  User_4_6  = NS.User_4_6
  User_4_7  = NS.User_4_7
  User_4_8  = NS.User_4_8
  User_4_9  = NS.User_4_9
  User_4_10 = NS.User_4_10

  User_5    = NS.User_5
  User_5_1  = NS.User_5_1
  User_5_2  = NS.User_5_2
  User_5_3  = NS.User_5_3
  User_5_4  = NS.User_5_4
  User_5_5  = NS.User_5_5
  User_5_6  = NS.User_5_6
  User_5_7  = NS.User_5_7
  User_5_8  = NS.User_5_8
  User_5_9  = NS.User_5_9
  User_5_10 = NS.User_5_10

# OWL data properties:
  mode      = NS.mode
  flags     = NS.flags
  position  = NS.position
  type      = NS.type
