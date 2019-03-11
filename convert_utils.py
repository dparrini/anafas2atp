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

Utilitary functions for field conversion.
"""

def try_int(intstr):
  """
  Try converting a string into int. Trims empty space.
  """
  try:
    num = int(intstr.strip())

  except ValueError:
    num = 0

  return num


def try_float(floatstr):
  """
  Try converting a string into a float. Trims empty space.
  """
  try:
    num = float(floatstr.strip())

  except ValueError:
    num = 0.0

  return num


def try_anafas_float(floatstr):
  """
  Try converting a string into a float. Trims empty space and checks whether
  there is a decimal separator. When a decimal separator is unspecified, assumes
  two decimals separators by default (Anafas' default) dividing the resulting
  number by 100.
  """
  try:
    num = float(floatstr.strip())

    # checks if the decimal separator was omitted
    thereIsDot = not (floatstr.find(".") == -1)
    if not thereIsDot:
      num = num / 100.0

  except ValueError:
    num = 0.0

  return num