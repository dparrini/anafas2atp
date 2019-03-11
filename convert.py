"""
MIT License

Copyright (c) 2019 David Rodrigues Parrini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from anafas import *
import math

MD_HAMILTON = 0
MD_SUELAINE = 1

md = MD_HAMILTON
# md = MD_SUELAINE


def __empty_comment_line(COLUMN_WIDTH=80):
  return __insertRightWhitespace("C", COLUMN_WIDTH) + "\n"


def __read_data_fformat(line, fields):
  """
  Accepted format (Fortran format expecifier), ex:
  (I5, 1X, A5, 1X, A5, 1X, F4.1, A12)
  """
  data_extr = [None]*len(fields)
  charpos = 0
  ifield = 0
  while len(line) > charpos and len(fields) > ifield:
    field = fields[ifield]
    chars = field[0]
    ftype = field[1]

    fstr = line[charpos:charpos + chars + 1]
    if   "I" == ftype:
      data_extr[ifield] = int(fstr.strip())
    elif "A" == ftype:
      data_extr[ifield] = fstr.strip()
    elif "F" == ftype or "D" == ftype or "E" == ftype:
      data_extr[ifield] = float(fstr.strip())
    else:
      data_extr[ifield] = None

    # next
    charpos = charpos + chars
    ifield = ifield + 1
    # print(fstr, "of type", ftype)

  # remove empty fields (X type)
  data = [val for i, val in enumerate(data_extr) if fields[i][1] != "X" ]
  return data


def __write_data_fformat(line, fields):
  outstr = ""
  ivalue = 0
  for ifield in range(len(fields)):
    value = line[ivalue]
    ftype = fields[ifield][0]
    width = fields[ifield][1]

    if "X" != ftype:
      fformat = ""
      if "I" == ftype:
        fformat = "{:>" + str(width) + "}"
        value = int(value)
      elif "A" == ftype:
        fformat = "{:" + str(width) + "}"
      elif "F" == ftype or "D" == ftype or "E" == ftype:
        precision = fields[ifield][2]
        fformat = "{:" + str(width) + "." + str(precision) + "f}"
        value = float(value)
      else:
        fformat = "{:" + str(width) + "}"

      outstr = outstr + fformat.format(value)
      ivalue = ivalue + 1
    else:
      outstr = outstr + (" " * width)

  return outstr


class NameSuggestion:
  def __init__(self, nbus, bfrom, bsrc, volt, bname):
    self.nbus  = nbus
    self.bfrom = bfrom
    self.bsrc  = bsrc
    self.volt  = volt
    self.bname = bname

  def __str__(self):
    return "<" + str(self.nbus) + " " + self.bname +">"

  def __repr__(self):
    return self.__str__()


def __read_name_suggestions(filename):
  fields = [[5, "I"], [1, "X"], [5, "A"], [1, "X"], [5, "A"], [1, "X"], [4, "F", 1], [12, "A"]]

  suggestions = []
  with open(filename, "r") as file:
    for line in file:
      if "99999" != line[0:5]:
        nbus, bfrom, bsrc, volt, bname = __read_data_fformat(line, fields)
        suggestions.append(NameSuggestion(nbus, bfrom, bsrc, volt, bname))

  return suggestions


def __convertSources(ldcir, ldbar, suggestions = None, Zmax = 5, sbase = 100, xopt = 60.0, freq = 60.0):
  """
  Busca elementos shunts na lista de circuitos.
  """
  GROUND = ""

  branchcards = ""

  calcz = lambda r, x: math.sqrt(r**2 + x**2)

  mixnames = lambda prefix, name1, name2 : prefix[0] + name1[0:2] + name2[0:2]

  if abs(xopt) <= 1E-3:
    """converter dados do Anafas em mH"""
    w = 2*math.pi*freq
    factor = 1 / w * 1E+3
  else:
    """converte da frequência do Anafas para a frequência do ATP."""
    factor = freq / xopt

  for dcir in ldcir:
    r1pu = dcir.r1 / 100.0 # % -> pu
    x1pu = dcir.x1 / 100.0
    r0pu = dcir.r0 / 100.0
    x0pu = dcir.x0 / 100.0

    # Sources
    if (dcir.de == 0 and dcir.para != 0) or (dcir.para == 0 and dcir.de != 0):
      if dcir.de == 0:
        node = dcir.para
      else:
        node = dcir.de

      nome = ""
      vbase = 998.0
      for dbar in ldbar:
        if dbar.nb == node:
          nome  = dbar.nome
          vbase = dbar.vbase

      zbase = ((vbase*1E3)**2)/(sbase*1E6)

      # sugestões de nomes para os nós
      de, para = None, None
      if None != suggestions:
        # utiliza sugestões de nomes
        suggs = list(filter(lambda x: (node == x.nbus) or nome.strip() in x.bname.strip(), suggestions))
        if len(suggs) > 0:
          de   = suggs[0].bsrc
          para = suggs[0].bfrom

      if None == de:
        # cria nomes para os nós terminais
        de   = __getSourceName(nome)
        para = __getAtpName(nome)

      # ignora elementos com impedância de seq+ maiores que determinado valor (em pu)
      if calcz(r1pu, x1pu) < Zmax:
        r1 = r1pu * zbase * factor
        x1 = x1pu * zbase * factor
        r0 = r0pu * zbase * factor
        x0 = x0pu * zbase * factor
        if MD_HAMILTON == md:
          branchcards = branchcards + "C    BARRA: {}".format(nome) + "\n"
        elif MD_SUELAINE == md:
          branchcards = branchcards + "C BARRA {} ({:6.2f} kV)".format(nome, vbase) + "\n"
        branchcards = branchcards + printBranch(de, para, r1, x1, r0, x0, vbase)
        # branchcards = branchcards + __insertRightWhitespace("C ", 80) + "\n"
        branchcards = branchcards + "C" + "\n"

  # ramos entre barras
  trdcount = 0 # trafos d-d
  trycount = 0 # trafos y-y
  for dcir in ldcir:

    r1pu = dcir.r1 / 100.0 # % -> pu
    x1pu = dcir.x1 / 100.0
    r0pu = dcir.r0 / 100.0
    x0pu = dcir.x0 / 100.0

    if (dcir.de > 0 and dcir.para > 0):
      # Series
      for dbar in ldbar:
        if dbar.nb == dcir.de:
          denome  = dbar.nome
          devbase = dbar.vbase

        if dbar.nb == dcir.para:
          paranome  = dbar.nome
          paravbase = dbar.vbase

      adenome   = __getAtpName(denome)
      aparanome = __getAtpName(paranome)

      vbase = devbase
      zbase = ((vbase*1E3)**2)/(sbase*1E6)
      r1 = r1pu * zbase * factor
      x1 = x1pu * zbase * factor
      r0 = r0pu * zbase * factor
      x0 = x0pu * zbase * factor

      # caso 1: mesma tensão, sem isolamento de seq 0 (ramo)
      if abs(paravbase - devbase) < 1E-3 and calcz(r0pu, x0pu) < Zmax:
        branchcards = branchcards + "C BARRAS: {} - {} ({:6.2f} kV)".format(denome, paranome, devbase) + "\n"
        branchcards = branchcards + printBranch(adenome, aparanome, r1, x1, r0, x0, devbase)
        branchcards = branchcards + __empty_comment_line()

      # caso 2: tensões diferentes, sem isolamento de seq 0 (ramo + trafo Y-Y)
      elif calcz(r0pu, x0pu) < Zmax:
        dummynome = mixnames("T", adenome, aparanome)

        branchcards = branchcards + "C ENTRE A BARRA {} E O TRAFO FICTICIO NA BARRA {} ({:6.2f} kV)".format(denome, dummynome, devbase) + "\n"
        branchcards = branchcards + printBranch(adenome, dummynome, r1, x1, r0, x0, devbase)
        branchcards = branchcards + __empty_comment_line()

        branchcards = branchcards + printTransformer(dummynome, aparanome, devbase, paravbase, "y", "y", trycount + 1)
        trycount = trycount + 1

      # caso 3: tensões iguais (ou diferentes), com isolamento de seq 0 (ramo + trafo D-D)
      else:
        dummynome = mixnames("T", adenome, aparanome)

        # programa do Hamilton substitui r0 e x0 por 999.99

        branchcards = branchcards + "C ENTRE A BARRA {} E O TRAFO FICTICIO NA BARRA {} ({:6.2f} kV)".format(denome, dummynome, devbase) + "\n"
        branchcards = branchcards + printBranch(adenome, dummynome, r1, x1, r0, x0, devbase)
        branchcards = branchcards + __empty_comment_line()

        branchcards = branchcards + printTransformer(dummynome, aparanome, devbase, paravbase, "d", "d", trdcount + 1)
        trdcount = trdcount + 1

  return branchcards


def __getAtpName(name):
  """
  Reduz nome de barra para um nome válido no ATP.
  Substitui espaços em branco por "_"
  """
  remove = [".", "#", " "]
  filtered = name
  for ichar in remove:
    filtered = filtered.replace(ichar, "")
  
  return filtered[0:5].upper()


def __getSourceName(name):
  atpname = __getAtpName(name)
  return "F" + atpname[0:4]


def __insertRightWhitespace(astr, columns = 80):
  width = len(astr)
  total = columns - width
  newstr = astr
  for icol in range(total):
    newstr = newstr + " "

  return newstr


def __fixedWidthNumber(num, maxwidth):
  snum = str(num)
  thereIsDot = snum.find(".")

  if len(snum) > maxwidth:
    snum = snum[0:maxwidth]
  
  # if decimal separator is lost...
  # try scientific notation, reducing its precision until the width is met
  if snum.find(".") == -1 and thereIsDot:

    # case where the rounded number fit maxwidth
    if len(str(int(math.floor(num)))) == maxwidth:
      snum = str(int(math.floor(num)))
    else:
      # otherwise... try scientific notation
      for iprec in range(maxwidth - 3, 0, -1):

        snum = "{:.{precision}G}".format(num, precision=iprec)

        if len(snum) <= maxwidth:
          break

  return snum


def printBranch(de, para, r1, x1, r0, x0, vbase):
  """
  R: [27, 32]
  X: [33, 44]
  """
  COLUMN_WIDTH = 80

  nomede   = str(de)
  nomepara = str(para)
  sr1 = __fixedWidthNumber(r1,  6)
  sx1 = __fixedWidthNumber(x1, 12)
  sr0 = __fixedWidthNumber(r0,  6)
  sx0 = __fixedWidthNumber(x0, 12)

  PHASE_A_MASK = "51{:6.6}{:6.6}            {:>6}{:>12}       {{ EM {:>6.2f} KV"
  PHASE_B_MASK = "52{:6.6}{:6.6}            {:>6}{:>12}"
  PHASE_C_MASK = "53{:6.6}{:6.6}"

  phase_a = PHASE_A_MASK.format(nomede + "A", nomepara + "A", sr0, sx0, vbase)
  phase_b = PHASE_B_MASK.format(nomede + "B", nomepara + "B", sr1, sx1)
  phase_c = PHASE_C_MASK.format(nomede + "C", nomepara + "C")

  fields_ab = [["I", 2], ["A", 6], ["A", 6], ["X", 12], ["F", 6, 2], ["F", 12, 2]]
  fields_c = [["I", 2], ["A", 6], ["A", 6]]
  phase_a_values = [51, nomede + "A", nomepara + "A", sr0, sx0]
  phase_b_values = [52, nomede + "B", nomepara + "B", sr1, sx1]
  phase_c_values = [53, nomede + "C", nomepara + "C"]
  
  mystr = __write_data_fformat(phase_a_values, fields_ab)
  mystr = mystr + "       {{ EM {:>5.1f}KV".format(vbase) + "\n"
  mystr = mystr + __write_data_fformat(phase_b_values, fields_ab) + "\n"
  mystr = mystr + __write_data_fformat(phase_c_values, fields_c) + "\n"

  return mystr


def printTransformer(de, para, vbaseDe, vbasePara, tipoDe, tipoPara, bustopNum):
  GROUND = ""

  R = ""
  X = "0.001"

  nomede = de
  nomepara = para

  # parameters: REFBUS name (branco para bustop!=""), BUSTOP name
  TRANSF_MASK = "  TRANSFORMER {:6.6}                  {:6.6}"
  
  # parameters: BUS1, BUS2, R12, X12, V12
  WINDING_1_MASK = " 1{:6.6}{:6.6}           {:>6}{:>6}{:>7}"
  WINDING_2_MASK = " 2{:6.6}{:6.6}           {:>6}{:>6}{:>7}"

  # nome gerado para o bustop
  BUSTOPD_MASK = "TRD{:>02}{}"
  BUSTOPY_MASK = "TRY{:>02}{}"
  BUSTOP_MASK = ""

  # ramo monofásico para a terra
  GROUND_RESIST_MASK = "  {:6.6}                  1.0E06"


  if tipoDe == "y":
    BUSTOP_MASK = BUSTOPY_MASK
  else:
    BUSTOP_MASK + BUSTOPD_MASK

  bustopA = BUSTOPD_MASK.format(bustopNum, "A")
  bustopB = BUSTOPY_MASK.format(bustopNum, "B")
  bustopC = BUSTOPY_MASK.format(bustopNum, "C")

  # mystr =         "C Transformador\n"
  mystr = ""
  # fase A
  mystr = mystr + TRANSF_MASK.format("", bustopA) + "\n"
  mystr = mystr + "            9999" + "\n"
  # LV
  if tipoDe == "y":
    mystr = mystr + WINDING_1_MASK.format(nomede + "A", GROUND, R, X, vbaseDe) + "\n"
  else:
    mystr = mystr + WINDING_1_MASK.format(nomede + "A", nomede + "B", R, X, vbaseDe) + "\n"
  # HV
  if tipoPara == "y":
    mystr = mystr + WINDING_2_MASK.format(nomepara + "A", GROUND, R, X, vbasePara) + "\n"
  else:
    mystr = mystr + WINDING_2_MASK.format(nomepara + "A", nomepara + "B", R, X, vbasePara) + "\n"

  # fase B
  mystr = mystr + TRANSF_MASK.format(bustopA, bustopB) + "\n"
  # LV
  if tipoDe == "y":
    mystr = mystr + WINDING_1_MASK.format(nomede + "B", GROUND, R, X, vbaseDe) + "\n"
  else:
    mystr = mystr + WINDING_1_MASK.format(nomede + "B", nomede + "C", R, X, vbaseDe) + "\n"
  # HV
  if tipoPara == "y":
    mystr = mystr + WINDING_2_MASK.format(nomepara + "B", GROUND, R, X, vbasePara) + "\n"
  else:
    mystr = mystr + WINDING_2_MASK.format(nomepara + "B", nomepara + "C", R, X, vbasePara) + "\n"

  # fase C
  mystr = mystr + TRANSF_MASK.format(bustopA, bustopC) + "\n"
  # LV
  if tipoDe == "y":
    mystr = mystr + WINDING_1_MASK.format(nomede + "C", GROUND, R, X, vbaseDe) + "\n"
  else:
    mystr = mystr + WINDING_1_MASK.format(nomede + "C", nomede + "A", R, X, vbaseDe) + "\n"
  # HV
  if tipoPara == "y":
    mystr = mystr + WINDING_2_MASK.format(nomepara + "C", GROUND, R, X, vbasePara) + "\n"
  else:
    mystr = mystr + WINDING_2_MASK.format(nomepara + "C", nomepara + "A", R, X, vbasePara) + "\n"

  # referencia para terra
  if tipoDe == "d":
    mystr = mystr + GROUND_RESIST_MASK.format(nomede + "A") + "\n"
    mystr = mystr + GROUND_RESIST_MASK.format(nomede + "B") + "\n"
    mystr = mystr + GROUND_RESIST_MASK.format(nomede + "C") + "\n"

  if tipoPara == "d":
    mystr = mystr + GROUND_RESIST_MASK.format(nomepara + "A") + "\n"
    mystr = mystr + GROUND_RESIST_MASK.format(nomepara + "B") + "\n"
    mystr = mystr + GROUND_RESIST_MASK.format(nomepara + "C") + "\n"

  return mystr


def getopts(argv):
  # https://gist.github.com/dideler/2395703
  opts = {}
  while argv:
    if argv[0][0] == '-':
      opts[argv[0]] = argv[1]
    argv = argv[1:]
  return opts


if __name__ == "__main__":
  # lê arquivo anafas e converte para ATP
  # fields = [["I", 2], ["A", 6], ["A", 6], ["X", 12], ["F", 6, 2], ["F", 12, 2]]
  # print(__write_data_fformat([51, "FTET4A", "TA440A", 6.3988, 54.620368], fields))
  # quit()

  from sys import argv
  myargs = getopts(argv)
  if '-i' in myargs and '-o' in myargs:
    # input/processing
    ana  = Anafas(myargs['-i'])

    # conversion
    outp = __convertSources(ana.dcir, ana.dbar)

    # output
    with open(myargs['-o'], "w") as outf:
      outf.write(outp)

  else:
    suggestions = __read_name_suggestions("sp500-440/ESTREITO.DAT")
    print(suggestions)

    print(list(filter(lambda x: "ITUMB" in x.bname, suggestions)))

    # test
    # ana = Anafas("../dados/EQV_3mod.ANA")
    ana = Anafas("sp500-440/BR1812PA_SE-CO_SECO_MOD_RECORTE_EQV_PECO.ANA")

    conv = __convertSources(ana.dcir, ana.dbar, suggestions)
    # conv = __convertSources(ana.dcir, ana.dbar, None)
    with open("./sp500-440/test.pch", "w") as atpfile:
      atpfile.write(conv)

    print(conv)
