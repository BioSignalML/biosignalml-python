from mevent import MEVENT
from sleep  import SLEEP


class MinervaError(Exception):
#============================
  pass

 
class Minerva(object):
#====================

  _events = { 1: { 1: MEVENT.Respiratory_Obs_Apnea,                # Respiratory
                   2: MEVENT.Respiratory_Cent_Apnea,
                   3: MEVENT.Respiratory_Obs_Hypopnea,
                   4: MEVENT.Respiratory_Cent_Hypopnea,
                   5: MEVENT.Respiratory_Uns_Hypopnea,
                   6: MEVENT.Respiratory_Obs_Nonanonh,
                   7: MEVENT.Respiratory_Cent_Nonanonh,
                   8: MEVENT.Respiratory_Uns_Nonanonh,
                   9: MEVENT.Respiratory_Sus_Fl,
                  10: MEVENT.Respiratory_Per_Br,
                 },

              2: { 1: MEVENT.Neurological_Respiratory_Arousal,     # Neurological
                   2: MEVENT.Neurological_Movement_Linked_Arousal,
                   3: MEVENT.Neurological_Other_Arousal,
                   4: MEVENT.Neurological_Alpha,
                   5: MEVENT.Neurological_Delta,
                   6: MEVENT.Neurological_K_Complex,
                   7: MEVENT.Neurological_Spindle,
                   8: MEVENT.Neurological_Peak_Wave,
                   9: MEVENT.Neurological_Leg_Emg,
                 },

              3: { 1: MEVENT.Snoring_High,                         # Snoring
                   2: MEVENT.Snoring_Low,
                 },

              4: { 1: MEVENT.Saturation_Unfastening,               # Saturation
                   2: MEVENT.Saturation_Desaturation,
                 },

              5: { 1: MEVENT.Urologic_Step,                        # Urologic
                   2: MEVENT.Urologic_Peak,
                 },

              6: { 1: MEVENT.Leg_Movement_Arousal,                 # Leg Movement
                   2: MEVENT.Leg_Movement_Noarousal,
                 },

              7: { 1: MEVENT.Calibration_Minimum,                  # Calibration
                   2: MEVENT.Calibration_Maximum,
                   3: MEVENT.Calibration_Minmax,
                 },

              8: { 1: MEVENT.Research_Flow_Lim,                    # Research
                 },

              9: { 1: MEVENT.Invalid_Invalid,                      # Invalid
                   2: MEVENT.Invalid_Reviewed,
                 },

             10: { 1: MEVENT.User_1_1,                             # User 1
                   2: MEVENT.User_1_2,  
                   3: MEVENT.User_1_3,  
                   4: MEVENT.User_1_4,  
                   5: MEVENT.User_1_5,  
                   6: MEVENT.User_1_6,  
                   7: MEVENT.User_1_7,  
                   8: MEVENT.User_1_8,  
                   9: MEVENT.User_1_9,  
                  10: MEVENT.User_1_10, 
                 },

             11: { 1: MEVENT.User_2_1,                             # User 2
                   2: MEVENT.User_2_2,  
                   3: MEVENT.User_2_3,  
                   4: MEVENT.User_2_4,  
                   5: MEVENT.User_2_5,  
                   6: MEVENT.User_2_6,  
                   7: MEVENT.User_2_7,  
                   8: MEVENT.User_2_8,  
                   9: MEVENT.User_2_9,  
                  10: MEVENT.User_2_10, 
                 },

             12: { 1: MEVENT.User_3_1,                             # User 3
                   2: MEVENT.User_3_2,  
                   3: MEVENT.User_3_3,  
                   4: MEVENT.User_3_4,  
                   5: MEVENT.User_3_5,  
                   6: MEVENT.User_3_6,  
                   7: MEVENT.User_3_7,  
                   8: MEVENT.User_3_8,  
                   9: MEVENT.User_3_9,  
                  10: MEVENT.User_3_10, 
                 },

             13: { 1: MEVENT.User_4_1,                             # User 4
                   2: MEVENT.User_4_2,  
                   3: MEVENT.User_4_3,  
                   4: MEVENT.User_4_4,  
                   5: MEVENT.User_4_5,  
                   6: MEVENT.User_4_6,  
                   7: MEVENT.User_4_7,  
                   8: MEVENT.User_4_8,  
                   9: MEVENT.User_4_9,  
                  10: MEVENT.User_4_10, 
                 },

             14: { 1: MEVENT.User_5_1,                             # User 5
                   2: MEVENT.User_5_2,  
                   3: MEVENT.User_5_3,  
                   4: MEVENT.User_5_4,  
                   5: MEVENT.User_5_5,  
                   6: MEVENT.User_5_6,  
                   7: MEVENT.User_5_7,  
                   8: MEVENT.User_5_8,  
                   9: MEVENT.User_5_9,  
                  10: MEVENT.User_5_10, 
                 },
            }


  @staticmethod
  def event(t, c):
  #--------------
    try:             return Minerva._events[t][c]
    except KeyError: raise MinervaError('Unknown class of event: (%s, %s)' % (t, c))


  _recode = { 1: (8, 1),   # OBS_APNEA_OLD     -> (UNS_NONANONH, OBS_APNEA)
              2: (5, 3),   # OBS_HYPOPNEA_OLD  -> (UNS_HYPOPNEA, OBS_HYPOPNEA)
              3: (8, 6),   # OBS_NONANONH_OLD  -> (UNS_NONANONH, OBS_NONANONH)
              4: (8, 8),   # PRESCORE_OLD      -> (UNS_NONANONH, UNS_NONANONH)
              5: (8, 2),   # CENT_APNEA_OLD    -> (UNS_NONANONH, CENT_APNEA)
              6: (5, 4),   # CENT_HYPOPNEA_OLD -> (UNS_HYPOPNEA, CENT_HYPOPNEA)
              7: (8, 7),   # CENT_NONANONH_OLD -> (UNS_NONANONH, CENT_NONANONH)
            }

  @staticmethod
  def recoded_event(t, c, flags):      # When version < 450
  #-----------------------------
    if t == 1:        # Respiratory event
      e = Minerva._recode[c]  # Check RESP_UNCERTAIN flag
      return Minerva.event(t, e[0]) if (flags & 0x0800) else Minerva.event(t, e[1])
    else:
      return Minerva.event(t, c)


  _sleepstage = { 0: SLEEP.Awake,
                  1: SLEEP.Stage1,
                  2: SLEEP.Stage2,
                  3: SLEEP.Stage3,
                  4: SLEEP.Delta,
                  5: SLEEP.REM,
                }

  @staticmethod
  def sleepstage(s):
  #----------------
    try:             return Minerva._sleepstage[s]
    except KeyError: raise MinervaError('Unknown sleep stage: %s' % s)

