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

from convert_utils import *


class Anafas:
  """
  Representa um arquivo/caso do Anafas.
  """

  def __init__(self, file):

    # inicializa cartões vazios
    self.dbar = []
    self.dcir = []

    self.__read(file)

  def __iscomment(self, line):
    """
    Check if its a line comment
    """
    return line[0] == "("

  def __getCard(self, line, lastcard = "", validrows = 0):
    
    card = lastcard
    # no card were read
    if lastcard == "":
      # TIPO
      if line[0:4] == "TIPO" or line[0:3] == "  0":
        card = "TIPO"

      # TITU
      if line[0:4] == "TITU" or line[0:3] == "  1":
        card = "TITU"

      # CMNT
      if line[0:4] == "CMNT" or line[0:3] == "  2":
        card = "CMNT"

      # BASE
      if line[0:4] == "BASE" or line[0:3] == "100":
        card = "BASE"

      # DBAR
      if line[0:4] == "DBAR" or line[0:3] == " 38":
        card = "DBAR"

      # DCIR
      if line[0:4] == "DCIR" or line[0:3] == " 37":
        card = "DCIR"

      # DMUT
      if line[0:4] == "DMUT" or line[0:3] == " 39":
        card = "DMUT"

      # DMOV
      if line[0:4] == "DMOV" or line[0:3] == " 36":
        card = "DMOV"

      # DSHL
      if line[0:4] == "DSHL" or line[0:3] == " 35":
        card = "DSHL"

      # DEOL
      if line[0:4] == "DEOL":
        card = "DEOL"

      # DARE
      if line[0:4] == "DARE":
        card = "DARE"

    elif (lastcard == "TIPO") or (
          lastcard == "TITU") or (
          lastcard == "CMNT") or (
          lastcard == "BASE"):
      # one valid row cards
      if not self.__iscomment(line) and validrows == 1:
        # read at least 1 valid row, then closes the card
        card = ""

    else:
      # inside a multiple rows card (DBAR, DCIR, etc)
      if line[0:5] == "99999":
        card = ""

    return card

  def __read(self, file):
    """
    Lê arquivo do Anafas e extrai dados de barras e circuitos.
    """
    # lê dados de barras
    self.__read_dbar(file)

    # lê dados de circuitos
    self.__read_dcir(file)

  def __read_dbar(self, file):
    """
    Lê o cartão DBAR
    """
    with open(file) as f:
      inDbar = False
      lastcard = ""
      validrows = 0

      for line in f:
        newcard = self.__getCard(line, lastcard, validrows)
        inDbar  = (newcard == "DBAR")

        if not (newcard == lastcard):
          validrows = 0

        else:
          added = False
          if inDbar and not(self.__iscomment(line)):
            # linha de dados válida dentro do cartão DBAR
            self.dbar.append(DBar(line))
            added = True

          if not self.__iscomment(line):
            validrows = validrows + 1

        lastcard = newcard

  def __read_dcir(self, file):
    """
    Lê o cartão DCIR
    """
    with open(file) as f:
      inDcir = False
      lastcard = ""
      validrows = 0

      for line in f:
        newcard = self.__getCard(line, lastcard, validrows)
        inDcir  = (newcard == "DCIR")

        if not (newcard == lastcard):
          validrows = 0

        else:
          added = False
          if inDcir and not(self.__iscomment(line)):
            # linha de dados válida dentro do cartão DCIR
            self.dcir.append(DCir(line))
            added = True

          if not self.__iscomment(line):
            validrows = validrows + 1

        lastcard = newcard


class DBar:
  """
  Cartão do Anafas de dados de Barra.

  Formato do cartão (versão 7.10):
  (NB  CEM      BN               VBAS DISJUN          DDMMAAAADDMMAAAA IA SA  F
  (----=-= ------------          ---- ------          --------======== ---=== -
  """

  COLS_NB   = ( 0,  4)    # número da barra
  COLS_BN   = ( 9, 20)    # nome da barra
  COLS_VBAS = (31, 34)    # tensão base da barra (kV)

  DEFAULT_NB = 0          # número padrão de barra em caso de erro de leitura
  DEFAULT_BN = "BARRA"    # nome padrão de barra em caso de erro de leitura
  DEFAULT_VBAS = 500      # tensão base padrão em caso de erro de leitura


  def __init__(self, line=""):
    self.nb = 0
    self.nome = ""
    self.vbase = 500.0
    self.__parse(line)

  def __str__(self):
    return "Barra #{0} {1} de {2} kV".format(self.nb, self.nome, self.vbase)

  def __repr__(self):
    return self.__str__()

  def __parse(self, line):
    """
    Interpreta linha de cartão. Utiliza índices contidos nas tuplas/constantes
    COLS_NB, COLS_BN, COLS_VBAS
    """
    line_end = False

    # número da barra
    if len(line) >= self.COLS_NB[1]:
      start = self.COLS_NB[0]
      end   = self.COLS_NB[1] + 1
      self.nb = try_int(line[start : end])

    else:
      self.nb = self.DEFAULT_NB
      line_end = True

    # nome da barra
    if not(line_end) and len(line) >= self.COLS_BN[1]:
      start = self.COLS_BN[0]
      end   = self.COLS_BN[1] + 1
      self.nome = line[start : end]

    else:
      self.nome = self.DEFAULT_BN
      line_end = True

    # tensão base
    if not(line_end) and len(line) >= self.COLS_VBAS[1]:
      start = self.COLS_VBAS[0]
      end   = self.COLS_VBAS[1] + 1
      self.vbase = try_float(line[start : end])

    else:
      self.vbase = self.DEFAULT_VBAS
      line_end = True


class DCir:
  """
  Cartão do Anafas de dados de Circuito.
  """

  COLS_BF = ( 0,  4)    # número da barra DE
  COLS_BT = ( 7, 11)    # número da barra PARA
  COLS_NC = (14, 15)    # número do circuito
  COLS_R1 = (17, 22)    # resistência de sequência positiva
  COLS_X1 = (23, 28)    # reatância de sequência positiva
  COLS_R0 = (29, 34)    # resistência de sequência zero
  COLS_X0 = (35, 40)    # reatância de sequência zero

  DEFAULT_BF = 1    # número da barra DE padrão, em caso de erro de leitura
  DEFAULT_BT = 2    # número da barra PARA padrão, em caso de erro de leitura
  DEFAULT_NC = 1    # número do circuito padrão, em caso de erro de leitura
  DEFAULT_R1 =  0.0  # resistência de sequência positiva padrão, em caso de erro de leitura
  DEFAULT_X1 =  0.0  # reatância de sequência positiva padrão, em caso de erro de leitura
  DEFAULT_R0 =  0.0  # resistência de sequência zero padrão, em caso de erro de leitura
  DEFAULT_X0 =  0.0  # reatância de sequência zero padrão, em caso de erro de leitura


  def __init__(self, line = ""):
    self.de   = 0
    self.para = 0
    self.num  = 1
    self.r1 = 0.0
    self.x1 = 0.0
    self.r0 = 0.0
    self.x0 = 0.0
    
    self.__parse(line)

  def __str__(self):
    return "Circuito C{0} #{1}-{2}".format(self.num, self.de, self.para)

  def __repr__(self):
    return self.__str__()

  def __parse(self, line):
    """
    Interpreta linha de cartão. Utiliza índices contidos nas tuplas/constantes
    COLS_BF, COLS_BT, COLS_NC, COLS_R1, COLS_X1, COLS_R0, COLS_X0
    """
    line_end = False

    # barra de
    if len(line) >= self.COLS_BF[1]:
      start = self.COLS_BF[0]
      end   = self.COLS_BF[1] + 1
      self.de = try_int(line[start : end])

    else:
      self.de = self.DEFAULT_BF
      line_end = True

    # barra para
    if not(line_end) and len(line) >= self.COLS_BT[1]:
      start = self.COLS_BT[0]
      end   = self.COLS_BT[1] + 1
      self.para = try_int(line[start : end])

    else:
      self.para = self.DEFAULT_BT
      line_end = True

    # número do circuito
    if not(line_end) and len(line) >= self.COLS_NC[1]:
      start = self.COLS_NC[0]
      end   = self.COLS_NC[1] + 1
      self.num = try_int(line[start : end])

    else:
      self.num = self.DEFAULT_NC
      line_end = True

    # Resistência de Sequência Positiva
    if not(line_end) and len(line) >= self.COLS_R1[1]:
      start = self.COLS_R1[0]
      end   = self.COLS_R1[1] + 1
      self.r1 = try_anafas_float(line[start : end])

    else:
      self.r1 = self.DEFAULT_R1
      line_end = True

    # Reatância de Sequência Positiva
    if not(line_end) and len(line) >= self.COLS_X1[1]:
      start = self.COLS_X1[0]
      end   = self.COLS_X1[1] + 1
      self.x1 = try_anafas_float(line[start : end])

    else:
      self.x1 = self.DEFAULT_X1
      line_end = True

    # Resistência de Sequência Zero
    if not(line_end) and len(line) >= self.COLS_R0[1]:
      start = self.COLS_R0[0]
      end   = self.COLS_R0[1] + 1
      self.r0 = try_anafas_float(line[start : end])

    else:
      self.r0 = self.DEFAULT_R0
      line_end = True

    # Reatância de Sequência Zero
    if not(line_end) and len(line) >= self.COLS_X0[1]:
      start = self.COLS_X0[0]
      end   = self.COLS_X0[1] + 1
      self.x0 = try_anafas_float(line[start : end])

    else:
      self.x0 = self.DEFAULT_X0
      line_end = True


if __name__ == "__main__":
  ana = Anafas("../dados/EQV_4mod.ANA")