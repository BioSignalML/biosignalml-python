# -*- coding: utf-8 -*-
"""
Provide access to the UOME List ontology.

Generated from http://www.sbpax.org/uome/list.owl at Tue May 15 11:54:58 2012
"""

from biosignalml.rdf import Uri, Resource, NS as Namespace

__all__ = [ 'UNITS' ]


class UNITS(object):
  uri = Uri("http://www.sbpax.org/uome/list.owl#")
  NS = Namespace(str(uri))

  Absorbance     = Resource(NS.Absorbance, label="A", desc="absorbance")
  '''absorbance (A)'''

  Ampere         = Resource(NS.Ampere, label="A", desc="ampere")
  '''ampere (A)'''

  Angstrom       = Resource(NS.Angstrom, label="Å", desc="angstrom")
  '''angstrom (Å)'''

  Atmosphere     = Resource(NS.Atmosphere, label="atm", desc="atmosphere")
  '''atmosphere (atm)'''

  Attomole       = Resource(NS.Attomole, label="amol", desc="attomole")
  '''attomole (amol)'''

  BasePairs      = Resource(NS.BasePairs, label="base pairs", desc="base pairs")
  '''base pairs (base pairs)'''

  Becquerel      = Resource(NS.Becquerel, label="Bq", desc="becquerel")
  '''becquerel (Bq)'''

  Bel            = Resource(NS.Bel, label="B", desc="bel")
  '''bel (B)'''

  Bit            = Resource(NS.Bit, label="bit", desc="bit")
  '''bit (bit)'''

  Byte           = Resource(NS.Byte, label="B", desc="byte")
  '''byte (B)'''

  Candela        = Resource(NS.Candela, label="cd", desc="candela")
  '''candela (cd)'''

  CandelaPerSquareMetre = Resource(NS.CandelaPerSquareMetre, label="C/m^2", desc="candela per square metre")
  '''candela per square metre (C/m^2)'''

  Centimetre     = Resource(NS.Centimetre, label="cm", desc="centimetre")
  '''centimetre (cm)'''

  Century        = Resource(NS.Century, label="century", desc="century")
  '''century (century)'''

  Coulomb        = Resource(NS.Coulomb, label="C", desc="coulomb")
  '''coulomb (C)'''

  CoulombPerKilogram = Resource(NS.CoulombPerKilogram, label="C/kg", desc="coulomb per kilogram")
  '''coulomb per kilogram (C/kg)'''

  Count          = Resource(NS.Count, label="", desc="count")
  '''count ()'''

  CountPerMillilitre = Resource(NS.CountPerMillilitre, label="1/ml", desc="count per millilitre")
  '''count per millilitre (1/ml)'''

  CountPerMolarSecond = Resource(NS.CountPerMolarSecond, label="1/(M*s)", desc="count per molar second")
  '''count per molar second (1/(M*s))'''

  CountPerNanomolarSecond = Resource(NS.CountPerNanomolarSecond, label="1/(nM*s)", desc="count per nanomolar second")
  '''count per nanomolar second (1/(nM*s))'''

  CountsPerMinute = Resource(NS.CountsPerMinute, label="cpm", desc="counts per minute")
  '''counts per minute (cpm)'''

  CubicCentimetre = Resource(NS.CubicCentimetre, label="cm^3", desc="cubic centimetre")
  '''cubic centimetre (cm^3)'''

  CubicCentimetrePerMole = Resource(NS.CubicCentimetrePerMole, label="cm^3/mol", desc="cubic centimetre per mole")
  '''cubic centimetre per mole (cm^3/mol)'''

  CubicDecimetre = Resource(NS.CubicDecimetre, label="dm^3", desc="cubic decimetre")
  '''cubic decimetre (dm^3)'''

  CubicMetre     = Resource(NS.CubicMetre, label="m^3", desc="cubic metre")
  '''cubic metre (m^3)'''

  CubicMetrePerKilogram = Resource(NS.CubicMetrePerKilogram, label="m^3/kg", desc="cubic metre per kilogram")
  '''cubic metre per kilogram (m^3/kg)'''

  CubicMetrePerMole = Resource(NS.CubicMetrePerMole, label="m^3/mol", desc="cubic metre per mole")
  '''cubic metre per mole (m^3/mol)'''

  Curie          = Resource(NS.Curie, label="Ci", desc="curie")
  '''curie (Ci)'''

  Dalton         = Resource(NS.Dalton, label="Da", desc="dalton")
  '''dalton (Da)'''

  Day            = Resource(NS.Day, label="d", desc="day")
  '''day (d)'''

  Decibel        = Resource(NS.Decibel, label="dB", desc="decibel")
  '''decibel (dB)'''

  Decilitre      = Resource(NS.Decilitre, label="dl", desc="decilitre")
  '''decilitre (dl)'''

  Decimetre      = Resource(NS.Decimetre, label="dm", desc="decimetre")
  '''decimetre (dm)'''

  DegreeCelsius  = Resource(NS.DegreeCelsius, label="°C", desc="degree celsius")
  '''degree celsius (°C)'''

  DegreeCelsiusScaledToFahrenheit = Resource(NS.DegreeCelsiusScaledToFahrenheit, label="1.8 °C", desc="degree celsius scaled to fahrenheit")
  '''degree celsius scaled to fahrenheit (1.8 °C)'''

  DegreeFahrenheit = Resource(NS.DegreeFahrenheit, label="°F", desc="degree fahrenheit")
  '''degree fahrenheit (°F)'''

  DegreeOfArc    = Resource(NS.DegreeOfArc, label="°", desc="degree of arc")
  '''degree of arc (°)'''

  Dimensionless  = Resource(NS.Dimensionless, label="", desc="Dimensionless")
  '''Dimensionless ()'''

  DisintegrationsPerMinute = Resource(NS.DisintegrationsPerMinute, label="dpm", desc="disintegrations per minute")
  '''disintegrations per minute (dpm)'''

  DisintegrationsPerSecond = Resource(NS.DisintegrationsPerSecond, label="disintegrations per second", desc="disintegrations per second")
  '''disintegrations per second (disintegrations per second)'''

  DotsPerInch    = Resource(NS.DotsPerInch, label="DPI", desc="dots per inch")
  '''dots per inch (DPI)'''

  Dyne           = Resource(NS.Dyne, label="dyn", desc="dyne")
  '''dyne (dyn)'''

  DynePerCentimetre = Resource(NS.DynePerCentimetre, label="dyn/cm", desc="dyne per centimetre")
  '''dyne per centimetre (dyn/cm)'''

  Einstein       = Resource(NS.Einstein, label="einstein", desc="einstein")
  '''einstein (einstein)'''

  EinsteinPerSquareMetrePerSecond = Resource(NS.EinsteinPerSquareMetrePerSecond, label="einstein/(m^2s)", desc="einstein per square metre per second")
  '''einstein per square metre per second (einstein/(m^2s))'''

  Electronvolt   = Resource(NS.Electronvolt, label="eV", desc="electronvolt")
  '''electronvolt (eV)'''

  ElementaryCharge = Resource(NS.ElementaryCharge, label="e", desc="elementary charge")
  '''elementary charge (e)'''

  EnzymeUnit     = Resource(NS.EnzymeUnit, label="U", desc="enzyme unit")
  '''enzyme unit (U)'''

  Farad          = Resource(NS.Farad, label="F", desc="farad")
  '''farad (F)'''

  Femtogram      = Resource(NS.Femtogram, label="fg", desc="femtogram")
  '''femtogram (fg)'''

  Femtolitre     = Resource(NS.Femtolitre, label="fl", desc="femtolitre")
  '''femtolitre (fl)'''

  Femtomolar     = Resource(NS.Femtomolar, label="fM", desc="femtomolar")
  '''femtomolar (fM)'''

  Femtomole      = Resource(NS.Femtomole, label="pmol", desc="femtomole")
  '''femtomole (pmol)'''

  Foot           = Resource(NS.Foot, label="ft", desc="foot")
  '''foot (ft)'''

  FootCandle     = Resource(NS.FootCandle, label="fc", desc="foot-candle")
  '''foot-candle (fc)'''

  Fraction       = Resource(NS.Fraction, label="", desc="fraction")
  '''fraction ()'''

  Gram           = Resource(NS.Gram, label="g", desc="gram")
  '''gram (g)'''

  GramPerCubicCentimetre = Resource(NS.GramPerCubicCentimetre, label="g/cm^3", desc="gram per cubic centimetre")
  '''gram per cubic centimetre (g/cm^3)'''

  GramPerDecilitre = Resource(NS.GramPerDecilitre, label="g/dl", desc="gram per decilitre")
  '''gram per decilitre (g/dl)'''

  GramPerLitre   = Resource(NS.GramPerLitre, label="g/l", desc="gram per litre")
  '''gram per litre (g/l)'''

  GramPerMillilitre = Resource(NS.GramPerMillilitre, label="g/ml", desc="gram per millilitre")
  '''gram per millilitre (g/ml)'''

  GramPerMole    = Resource(NS.GramPerMole, label="g/mol", desc="gram per mole")
  '''gram per mole (g/mol)'''

  Gray           = Resource(NS.Gray, label="Gy", desc="gray")
  '''gray (Gy)'''

  Hectare        = Resource(NS.Hectare, label="ha", desc="hectare")
  '''hectare (ha)'''

  Henry          = Resource(NS.Henry, label="H", desc="henry")
  '''henry (H)'''

  Hertz          = Resource(NS.Hertz, label="Hz", desc="hertz")
  '''hertz (Hz)'''

  Hour           = Resource(NS.Hour, label="h", desc="hour")
  '''hour (h)'''

  Inch           = Resource(NS.Inch, label="in", desc="inch")
  '''inch (in)'''

  Joule          = Resource(NS.Joule, label="J", desc="joule")
  '''joule (J)'''

  Katal          = Resource(NS.Katal, label="kat", desc="katal")
  '''katal (kat)'''

  KatalPerCubicMetre = Resource(NS.KatalPerCubicMetre, label="kat/m^3", desc="katal per cubic metre")
  '''katal per cubic metre (kat/m^3)'''

  KatalPerLitre  = Resource(NS.KatalPerLitre, label="kat/l", desc="katal per litre")
  '''katal per litre (kat/l)'''

  Kelvin         = Resource(NS.Kelvin, label="K", desc="kelvin")
  '''kelvin (K)'''

  Kibibyte       = Resource(NS.Kibibyte, label="KiB", desc="kibibyte")
  '''kibibyte (KiB)'''

  Kilobyte       = Resource(NS.Kilobyte, label="kB", desc="kilobyte")
  '''kilobyte (kB)'''

  Kilodalton     = Resource(NS.Kilodalton, label="kDa", desc="kilodalton")
  '''kilodalton (kDa)'''

  Kilogram       = Resource(NS.Kilogram, label="kg", desc="kilogram")
  '''kilogram (kg)'''

  KilogramMetre  = Resource(NS.KilogramMetre, label="kg*m", desc="kilogram metre")
  '''kilogram metre (kg*m)'''

  KilogramMetrePerSecond = Resource(NS.KilogramMetrePerSecond, label="kg*m/s", desc="kilogram metre per second")
  '''kilogram metre per second (kg*m/s)'''

  KilogramPerCubicMetre = Resource(NS.KilogramPerCubicMetre, label="kg/m^3", desc="kilogram per cubic metre")
  '''kilogram per cubic metre (kg/m^3)'''

  KilogramPerLitre = Resource(NS.KilogramPerLitre, label="kg/l", desc="kilogram per litre")
  '''kilogram per litre (kg/l)'''

  KilogramPerMetre = Resource(NS.KilogramPerMetre, label="kg/m", desc="kilogram per metre")
  '''kilogram per metre (kg/m)'''

  KilogramPerMole = Resource(NS.KilogramPerMole, label="kg/mol", desc="kilogram per mole")
  '''kilogram per mole (kg/mol)'''

  KilogramPerSquareMetre = Resource(NS.KilogramPerSquareMetre, label="kg/m^2", desc="kilogram per square metre")
  '''kilogram per square metre (kg/m^2)'''

  KilogramTimesMetre = Resource(NS.KilogramTimesMetre, label="kg*m", desc="kilogram times metre")
  '''kilogram times metre (kg*m)'''

  Kilovolt       = Resource(NS.Kilovolt, label="kV", desc="kilovolt")
  '''kilovolt (kV)'''

  KilovoltHour   = Resource(NS.KilovoltHour, label="kVh", desc="kilovolt-hour")
  '''kilovolt-hour (kVh)'''

  Kilowatt       = Resource(NS.Kilowatt, label="kW", desc="kilowatt")
  '''kilowatt (kW)'''

  KilowattHour   = Resource(NS.KilowattHour, label="kWh", desc="kilowatt-hour")
  '''kilowatt-hour (kWh)'''

  Litre          = Resource(NS.Litre, label="l", desc="litre")
  '''litre (l)'''

  LitrePerKilogram = Resource(NS.LitrePerKilogram, label="l/kg", desc="litre per kilogram")
  '''litre per kilogram (l/kg)'''

  Lumen          = Resource(NS.Lumen, label="lm", desc="lumen")
  '''lumen (lm)'''

  Lux            = Resource(NS.Lux, label="lx", desc="lux")
  '''lux (lx)'''

  Mebibyte       = Resource(NS.Mebibyte, label="MiB", desc="mebibyte")
  '''mebibyte (MiB)'''

  Megabyte       = Resource(NS.Megabyte, label="MB", desc="megabyte")
  '''megabyte (MB)'''

  Megavolt       = Resource(NS.Megavolt, label="MV", desc="megavolt")
  '''megavolt (MV)'''

  Metre          = Resource(NS.Metre, label="m", desc="metre")
  '''metre (m)'''

  MetreKelvin    = Resource(NS.MetreKelvin, label="m*K", desc="metre kelvin")
  '''metre kelvin (m*K)'''

  MetrePerSecond = Resource(NS.MetrePerSecond, label="m/s", desc="metre per second")
  '''metre per second (m/s)'''

  MetrePerSecondSquared = Resource(NS.MetrePerSecondSquared, label="m/s^2", desc="metre per second squared")
  '''metre per second squared (m/s^2)'''

  MicroEinsteinPerSquareMetrePerSecond = Resource(NS.MicroEinsteinPerSquareMetrePerSecond, label=u"μeinstein/(m^2s)", desc="microeinstein per square metre per second")
  '''microeinstein per square metre per second (μeinstein/(m^2s))'''

  Microampere    = Resource(NS.Microampere, label=u"μA", desc="microampere")
  '''microampere (μA)'''

  Microcurie     = Resource(NS.Microcurie, label=u"μCi", desc="microcurie")
  '''microcurie (μCi)'''

  Microgram      = Resource(NS.Microgram, label=u"μg", desc="microgram")
  '''microgram (μg)'''

  MicrogramPerMillilitre = Resource(NS.MicrogramPerMillilitre, label=u"μg/ml", desc="microgram per millilitre")
  '''microgram per millilitre (μg/ml)'''

  Microgray      = Resource(NS.Microgray, label=u"μGy", desc="microgray")
  '''microgray (μGy)'''

  Microlitre     = Resource(NS.Microlitre, label=u"μl", desc="microlitre")
  '''microlitre (μl)'''

  MicrolitrePerKilogram = Resource(NS.MicrolitrePerKilogram, label=u"μl/kg", desc="microlitre per kilogram")
  '''microlitre per kilogram (μl/kg)'''

  MicrolitrePerMinute = Resource(NS.MicrolitrePerMinute, label=u"μl/min", desc="microlitre per minute")
  '''microlitre per minute (μl/min)'''

  Micrometre     = Resource(NS.Micrometre, label=u"μm", desc="micrometre")
  '''micrometre (μm)'''

  Micromolal     = Resource(NS.Micromolal, label=u"μmol/kg", desc="micromolal")
  '''micromolal (μmol/kg)'''

  Micromolar     = Resource(NS.Micromolar, label=u"μM", desc="micromolar")
  '''micromolar (μM)'''

  Micromole      = Resource(NS.Micromole, label=u"μmol", desc="micromole")
  '''micromole (μmol)'''

  MicromolePerMilligramMinute = Resource(NS.MicromolePerMilligramMinute, label=u"μmol/(mg*min)", desc="micromole per milligram minute")
  '''micromole per milligram minute (μmol/(mg*min))'''

  MicronPixel    = Resource(NS.MicronPixel, label=u"μm/dot", desc="micron pixel")
  '''micron pixel (μm/dot)'''

  Microsecond    = Resource(NS.Microsecond, label=u"μs", desc="microsecond")
  '''microsecond (μs)'''

  Microsievert   = Resource(NS.Microsievert, label=u"μSv", desc="microsievert")
  '''microsievert (μSv)'''

  Microvolt      = Resource(NS.Microvolt, label=u"μV", desc="microvolt")
  '''microvolt (μV)'''
  uV             = Microvolt

  Milliampere    = Resource(NS.Milliampere, label="mA", desc="milliampere")
  '''milliampere (mA)'''

  Millicurie     = Resource(NS.Millicurie, label="mCi", desc="millicurie")
  '''millicurie (mCi)'''

  Milligram      = Resource(NS.Milligram, label="mg", desc="milligram")
  '''milligram (mg)'''

  MilligramMinute = Resource(NS.MilligramMinute, label="mg*min", desc="milligram minute")
  '''milligram minute (mg*min)'''

  MilligramPerLitre = Resource(NS.MilligramPerLitre, label="mg/l", desc="milligram per litre")
  '''milligram per litre (mg/l)'''

  MilligramPerMillilitre = Resource(NS.MilligramPerMillilitre, label="mg/ml", desc="milligram per millilitre")
  '''milligram per millilitre (mg/ml)'''

  Milligray      = Resource(NS.Milligray, label="mGy", desc="milligray")
  '''milligray (mGy)'''

  Millilitre     = Resource(NS.Millilitre, label="ml", desc="millilitre")
  '''millilitre (ml)'''

  MillilitrePerCubicMetre = Resource(NS.MillilitrePerCubicMetre, label="ml/m^3", desc="millilitre per cubic metre")
  '''millilitre per cubic metre (ml/m^3)'''

  MillilitrePerKilogram = Resource(NS.MillilitrePerKilogram, label="ml/kg", desc="millilitre per kilogram")
  '''millilitre per kilogram (ml/kg)'''

  MillilitrePerLitre = Resource(NS.MillilitrePerLitre, label="ml/l", desc="millilitre per litre")
  '''millilitre per litre (ml/l)'''

  Millimetre     = Resource(NS.Millimetre, label="mm", desc="millimetre")
  '''millimetre (mm)'''

  MillimetresOfMercury = Resource(NS.MillimetresOfMercury, label="mmHg", desc="millimetres of mercury")
  '''millimetres of mercury (mmHg)'''

  Millimolal     = Resource(NS.Millimolal, label="mmol/kg", desc="millimolal")
  '''millimolal (mmol/kg)'''

  Millimolar     = Resource(NS.Millimolar, label="mM", desc="millimolar")
  '''millimolar (mM)'''

  Millimole      = Resource(NS.Millimole, label="mmol", desc="millimole")
  '''millimole (mmol)'''

  Millisecond    = Resource(NS.Millisecond, label="ms", desc="millisecond")
  '''millisecond (ms)'''

  Millisievert   = Resource(NS.Millisievert, label="mSv", desc="millisievert")
  '''millisievert (mSv)'''

  Millivolt      = Resource(NS.Millivolt, label="mV", desc="millivolt")
  '''millivolt (mV)'''
  mV             = Millivolt

  Minute         = Resource(NS.Minute, label="min", desc="minute")
  '''minute (min)'''

  MinuteOfArc    = Resource(NS.MinuteOfArc, label="'", desc="minute of arc")
  '''minute of arc (')'''

  Molal          = Resource(NS.Molal, label="mol/kg", desc="molal")
  '''molal (mol/kg)'''

  Molar          = Resource(NS.Molar, label="M", desc="molar")
  '''molar (M)'''

  MolarSecond    = Resource(NS.MolarSecond, label="M*s", desc="molar second")
  '''molar second (M*s)'''

  Mole           = Resource(NS.Mole, label="mol", desc="mole")
  '''mole (mol)'''

  MoleFraction   = Resource(NS.MoleFraction, label="", desc="mole fraction")
  '''mole fraction ()'''

  MolePerMilligram = Resource(NS.MolePerMilligram, label="mol/mg", desc="mole per milligram")
  '''mole per milligram (mol/mg)'''

  MolePerMilligramMinute = Resource(NS.MolePerMilligramMinute, label="mol/(mg*min)", desc="mole per milligram minute")
  '''mole per milligram minute (mol/(mg*min))'''

  MoleculeCount  = Resource(NS.MoleculeCount, label="", desc="molecule count")
  '''molecule count ()'''

  Month          = Resource(NS.Month, label="mon", desc="month")
  '''month (mon)'''

  Nanogram       = Resource(NS.Nanogram, label="ng", desc="nanogram")
  '''nanogram (ng)'''

  NanogramPerMillilitre = Resource(NS.NanogramPerMillilitre, label="ng/ml", desc="nanogram per millilitre")
  '''nanogram per millilitre (ng/ml)'''

  Nanogray       = Resource(NS.Nanogray, label="nGy", desc="nanogray")
  '''nanogray (nGy)'''

  Nanolitre      = Resource(NS.Nanolitre, label="nl", desc="nanolitre")
  '''nanolitre (nl)'''

  Nanometre      = Resource(NS.Nanometre, label="nm", desc="nanometre")
  '''nanometre (nm)'''

  Nanomolal      = Resource(NS.Nanomolal, label="nmol/kg", desc="nanomolal")
  '''nanomolal (nmol/kg)'''

  Nanomolar      = Resource(NS.Nanomolar, label="nM", desc="nanomolar")
  '''nanomolar (nM)'''

  NanomolarSecond = Resource(NS.NanomolarSecond, label="nM*s", desc="nanomolar second")
  '''nanomolar second (nM*s)'''

  Nanomole       = Resource(NS.Nanomole, label="nmol", desc="nanomole")
  '''nanomole (nmol)'''

  Nanosecond     = Resource(NS.Nanosecond, label="ns", desc="nanosecond")
  '''nanosecond (ns)'''

  Nanosievert    = Resource(NS.Nanosievert, label="nSv", desc="nanosievert")
  '''nanosievert (nSv)'''

  Nanovolt       = Resource(NS.Nanovolt, label="nV", desc="nanovolt")
  '''nanovolt (nV)'''

  Newton         = Resource(NS.Newton, label="kg*m/s^2", desc="newton")
  '''newton (kg*m/s^2)'''

  NewtonPerMetre = Resource(NS.NewtonPerMetre, label="N/m", desc="newton per metre")
  '''newton per metre (N/m)'''

  Normal         = Resource(NS.Normal, label="N", desc="normal")
  '''normal (N)'''

  Ohm            = Resource(NS.Ohm, label="Ω", desc="ohm")
  '''ohm (Ω)'''

  PH             = Resource(NS.PH, label="", desc="pH")
  '''pH ()'''

  PartsPerBillion = Resource(NS.PartsPerBillion, label="ppb", desc="parts per billion")
  '''parts per billion (ppb)'''

  PartsPerHundred = Resource(NS.PartsPerHundred, label="%", desc="parts per hundred")
  '''parts per hundred (%)'''

  PartsPerMillion = Resource(NS.PartsPerMillion, label="ppm", desc="parts per million")
  '''parts per million (ppm)'''

  PartsPerQuadrillion = Resource(NS.PartsPerQuadrillion, label="ppt", desc="parts per quadrillion")
  '''parts per quadrillion (ppt)'''

  PartsPerThousand = Resource(NS.PartsPerThousand, label="‰", desc="parts per thousand")
  '''parts per thousand (‰)'''

  PartsPerTrillion = Resource(NS.PartsPerTrillion, label="ppt", desc="parts per trillion")
  '''parts per trillion (ppt)'''

  Pascal         = Resource(NS.Pascal, label="Pa", desc="pascal")
  '''pascal (Pa)'''

  PascalSecond   = Resource(NS.PascalSecond, label="Pa*s", desc="pascal second")
  '''pascal second (Pa*s)'''

  PerMinute      = Resource(NS.PerMinute, label="1/min", desc="per minute")
  '''per minute (1/min)'''

  PerSecond      = Resource(NS.PerSecond, label="1/s", desc="per second")
  '''per second (1/s)'''

  Percent        = Resource(NS.Percent, label="%", desc="percent")
  '''percent (%)'''

  Pi             = Resource(NS.Pi, label="π", desc="pi")
  '''pi (π)'''

  Picogram       = Resource(NS.Picogram, label="pg", desc="picogram")
  '''picogram (pg)'''

  Picolitre      = Resource(NS.Picolitre, label="pl", desc="picolitre")
  '''picolitre (pl)'''

  Picometre      = Resource(NS.Picometre, label="pm", desc="picometre")
  '''picometre (pm)'''

  Picomolal      = Resource(NS.Picomolal, label="pmol/kg", desc="picomolal")
  '''picomolal (pmol/kg)'''

  Picomolar      = Resource(NS.Picomolar, label="pM", desc="Picomolar")
  '''Picomolar (pM)'''

  Picomole       = Resource(NS.Picomole, label="pmol", desc="picomole")
  '''picomole (pmol)'''

  Picosecond     = Resource(NS.Picosecond, label="ps", desc="picosecond")
  '''picosecond (ps)'''

  Picosiemens    = Resource(NS.Picosiemens, label="pS", desc="picosiemens")
  '''picosiemens (pS)'''

  Picovolt       = Resource(NS.Picovolt, label="pV", desc="picovolt")
  '''picovolt (pV)'''

  PixelsPerInch  = Resource(NS.PixelsPerInch, label="dots/in", desc="pixels per inch")
  '''pixels per inch (dots/in)'''

  PixelsPerMillimetre = Resource(NS.PixelsPerMillimetre, label="dots/mm", desc="pixels per millimetre")
  '''pixels per millimetre (dots/mm)'''

  Poise          = Resource(NS.Poise, label="P", desc="poise")
  '''poise (P)'''

  Rad            = Resource(NS.Rad, label="rad", desc="rad")
  '''rad (rad)'''

  Radian         = Resource(NS.Radian, label="rad", desc="radian")
  '''radian (rad)'''

  RadianPerSecond = Resource(NS.RadianPerSecond, label="rad/s", desc="radian per second")
  '''radian per second (rad/s)'''

  RadianPerSecondSquared = Resource(NS.RadianPerSecondSquared, label="rad/s^2", desc="radian per second squared")
  '''radian per second squared (rad/s^2)'''

  Ratio          = Resource(NS.Ratio, label="", desc="ratio")
  '''ratio ()'''

  Roentgen       = Resource(NS.Roentgen, label="R", desc="roentgen")
  '''roentgen (R)'''

  RoentgenEquivalentMan = Resource(NS.RoentgenEquivalentMan, label="rem", desc="roentgen equivalent man")
  '''roentgen equivalent man (rem)'''

  Second         = Resource(NS.Second, label="s", desc="second")
  '''second (s)'''

  SecondOfArc    = Resource(NS.SecondOfArc, label="\"", desc="second of arc")
  '''second of arc (")'''

  SecondSquared  = Resource(NS.SecondSquared, label="s^2", desc="second squared")
  '''second squared (s^2)'''

  Siemens        = Resource(NS.Siemens, label="S", desc="Siemens")
  '''Siemens (S)'''

  Sievert        = Resource(NS.Sievert, label="Sv", desc="sievert")
  '''sievert (Sv)'''

  SquareCentimetre = Resource(NS.SquareCentimetre, label="cm^2", desc="square centimetre")
  '''square centimetre (cm^2)'''

  SquareFoot     = Resource(NS.SquareFoot, label="ft^2", desc="square foot")
  '''square foot (ft^2)'''

  SquareMetre    = Resource(NS.SquareMetre, label="m^2", desc="square metre")
  '''square metre (m^2)'''

  SquareMetreSecond = Resource(NS.SquareMetreSecond, label="m^2s", desc="square metre second")
  '''square metre second (m^2s)'''

  SquareMillimetre = Resource(NS.SquareMillimetre, label="mm^2", desc="square millimetre")
  '''square millimetre (mm^2)'''

  Steradian      = Resource(NS.Steradian, label="sr", desc="steradian")
  '''steradian (sr)'''

  SteradianSquareMetre = Resource(NS.SteradianSquareMetre, label="sr*m^2", desc="steradian square metre")
  '''steradian square metre (sr*m^2)'''

  Tesla          = Resource(NS.Tesla, label="T", desc="tesla")
  '''tesla (T)'''

  Tonne          = Resource(NS.Tonne, label="t", desc="tonne")
  '''tonne (t)'''

  Torr           = Resource(NS.Torr, label="Torr", desc="torr")
  '''torr (Torr)'''

  TurnsPerSecond = Resource(NS.TurnsPerSecond, label="1/s", desc="turns per second")
  '''turns per second (1/s)'''

  Volt           = Resource(NS.Volt, label="V", desc="volt")
  '''volt (V)'''

  VoltHour       = Resource(NS.VoltHour, label="Vh", desc="volt-hour")
  '''volt-hour (Vh)'''

  VoltPerMetre   = Resource(NS.VoltPerMetre, label="V/m", desc="volt per metre")
  '''volt per metre (V/m)'''

  VoltSecond     = Resource(NS.VoltSecond, label="V*s", desc="volt second")
  '''volt second (V*s)'''

  Watt           = Resource(NS.Watt, label="W", desc="watt")
  '''watt (W)'''

  WattHour       = Resource(NS.WattHour, label="Wh", desc="watt-hour")
  '''watt-hour (Wh)'''

  WattPerMetreKelvin = Resource(NS.WattPerMetreKelvin, label="W/(m*K)", desc="watt per metre kelvin")
  '''watt per metre kelvin (W/(m*K))'''

  WattPerSquareMetre = Resource(NS.WattPerSquareMetre, label="W/m^2", desc="watt per square metre")
  '''watt per square metre (W/m^2)'''

  WattPerSteradian = Resource(NS.WattPerSteradian, label="W/sr", desc="watt per steradian")
  '''watt per steradian (W/sr)'''

  WattPerSteradianPerSquareMetre = Resource(NS.WattPerSteradianPerSquareMetre, label="W/(sr*m^2)", desc="watt per steradian per square metre")
  '''watt per steradian per square metre (W/(sr*m^2))'''

  Weber          = Resource(NS.Weber, label="Wb", desc="weber")
  '''weber (Wb)'''

  Week           = Resource(NS.Week, label="week", desc="week")
  '''week (week)'''

  Year           = Resource(NS.Year, label="a", desc="year")
  '''year (a)'''


  EXTRA = Namespace("http://www.biosignalml.org/ontologies/examples/unit#")

  Beat           = Resource(EXTRA.Beat, label="beat", desc="beat")
  '''beat (beat)'''

  BeatsPerMinute = Resource(EXTRA.BeatsPerMinute, label="bpm", desc="beats per minute")
  '''beats per minute (bpm)'''

  Centilitre = Resource(EXTRA.Centilitre, label="cl", desc="centilitre")
  '''centilitre (cl)'''

  LitrePerMinute = Resource(EXTRA.LitrePerMinute, label="l/min", desc="litre per minute")
  '''litre per minute (l/min)'''

  DecilitrePerMinute = Resource(EXTRA.DecilitrePerMinute, label="dl/min", desc="decilitre per minute")
  '''decilitre per minute (dl/min)'''

  CentilitrePerMinute = Resource(EXTRA.CentilitrePerMinute, label="cl/min", desc="centilitre per minute")
  '''centilitre per minute (cl/min)'''

  CentimetresOfWater = Resource(EXTRA.CentimetresOfWater, label="cmH2O", desc="centimetres of water")
  '''centimetres of water (cmH2O)'''

  MillimetresOfWater = Resource(EXTRA.MillimetresOfWater, label="mmH2O", desc="millimetres of water")
  '''millimetres of water (mmH2O)'''

  Bar = Resource(EXTRA.Bar, label="bar", desc="bar")
  '''bar'''

  Millibar = Resource(EXTRA.Millibar, label="mbar", desc="millibar")
  '''millibar'''


  AnnotationData = Resource(EXTRA.AnnotationData, label='annotation', desc='annotation')


RESOURCES = { str(o.uri): o for o in UNITS.__dict__.itervalues() if isinstance(o, Resource) }
